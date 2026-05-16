"""Chat API – the primary conversational endpoint for PrivacyProtector.

Routing logic:
  1. If the user's message looks like a **search request** (contains keywords
     like "search", "find", "look up", "scan", mentions a person's name, etc.)
     → call Serper via search_web, classify results with Ollama, then return a
     structured response with the search results.
  2. Otherwise, treat it as a **general question** and answer using Ollama
     directly.

All messages are persisted to the database per-user so chat history survives
across sessions and devices.
"""

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core import ollama_client
from ..core.auth_utils import decode_token
from ..db.session import get_session
from ..db.models import ChatMessageRecord
from ..mcp_tools import search_web
from ..mcp_tools.classify_items import _fallback_classification


router = APIRouter()


# ---- Request / Response models ----

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    date: str = ""
    risk_label: str = ""  # "High" | "Medium" | "Low"
    risk_score: float = 0.0
    rationale: str = ""


class ChatResponse(BaseModel):
    reply: str
    search_results: Optional[List[SearchResult]] = None
    is_search: bool = False


class HistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    search_results: Optional[List[SearchResult]] = None
    is_search: bool = False
    created_at: str


# ---- Helpers ----

def _extract_user_id(authorization: Optional[str]) -> Optional[int]:
    """Extract user_id from an Authorization header if present."""
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        return decode_token(token)
    return None


# ---- Intent detection ----

_SEARCH_PATTERNS = [
    r"\bsearch\b",
    r"\bfind\b",
    r"\blook\s*up\b",
    r"\bscan\b",
    r"\bcheck\b.*\b(web|online|internet|data|breach|leak)\b",
    r"\bwhere\b.*\b(my|name|data|info|email|photo)\b",
    r"\bexposed\b",
    r"\bleak(ed|s)?\b",
    r"\bbreach(es|ed)?\b",
    r"\bprivacy\b.*\b(check|scan|report)\b",
    r"\bmy\s+(name|data|email|info|information|photos?|images?)\b",
    r"\b(websites?|sites?)\s+(that\s+)?(have|contain|show|display)\b",
]


def _is_search_intent(text: str) -> bool:
    """Heuristic check: does the user want a web search / privacy scan?"""
    lower = text.lower()
    for pat in _SEARCH_PATTERNS:
        if re.search(pat, lower):
            return True
    return False


def _extract_search_query(text: str) -> str:
    return text.strip()


def _risk_label(score: float) -> str:
    if score >= 0.5:
        return "High"
    if score >= 0.2:
        return "Medium"
    return "Low"


# ---- Endpoints ----

@router.get("/history")
async def get_chat_history(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> List[HistoryMessage]:
    """Return all chat messages for the authenticated user.

    Messages are ordered by creation time (oldest first) so the frontend
    can render them as a linear conversation.
    """

    user_id = _extract_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    statement = (
        select(ChatMessageRecord)
        .where(ChatMessageRecord.user_id == user_id)
        .order_by(ChatMessageRecord.created_at)
    )
    records = session.exec(statement).all()

    result: List[HistoryMessage] = []
    for rec in records:
        search_results = None
        if rec.search_results_json:
            try:
                raw = json.loads(rec.search_results_json)
                search_results = [SearchResult(**sr) for sr in raw]
            except Exception:
                pass
        result.append(
            HistoryMessage(
                id=rec.id,
                role=rec.role,
                content=rec.content,
                search_results=search_results,
                is_search=rec.is_search,
                created_at=rec.created_at.isoformat(),
            )
        )
    return result


@router.delete("/history")
async def clear_chat_history(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Delete all chat messages for the authenticated user."""

    user_id = _extract_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    statement = select(ChatMessageRecord).where(ChatMessageRecord.user_id == user_id)
    records = session.exec(statement).all()
    for rec in records:
        session.delete(rec)
    session.commit()
    return {"deleted": len(records)}


@router.post("")
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> ChatResponse:
    """Main chat endpoint.

    Accepts a list of messages (conversation history) and returns an
    assistant reply.  If the latest user message is a search request, also
    returns structured search_results.

    If the user is authenticated (Bearer token), messages are persisted to the DB.
    """

    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list is empty")

    user_id = _extract_user_id(authorization)
    last_user_msg = request.messages[-1].content

    # Persist the user message
    if user_id:
        user_record = ChatMessageRecord(
            user_id=user_id,
            role="user",
            content=last_user_msg,
            is_search=False,
        )
        session.add(user_record)
        session.commit()

    # --- SEARCH PATH ---
    if _is_search_intent(last_user_msg):
        query = _extract_search_query(last_user_msg)

        # 1) Serper web search
        raw_results = await search_web.search_web(query=query, limit=10)

        # 2) Classify results for risk scoring
        items_payload = [
            {
                "id": str(i),
                "category": "web_result",
                "confidence": 0.7,
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "url": r.get("url", ""),
                "metadata": {},
            }
            for i, r in enumerate(raw_results)
        ]

        # Try Ollama-based classification; fall back to rule-based
        try:
            ollama_ok = await ollama_client.is_available()
            if ollama_ok:
                classify_prompt = (
                    "You are a privacy risk analyst. For each web search result below, "
                    "assess whether the page likely contains personal/private data about a person. "
                    "Return ONLY a JSON array of objects with keys: item_id, category, risk_score (0-1), rationale. "
                    "risk_score: 0 = no privacy concern, 1 = severe privacy risk."
                )
                classify_msgs = [
                    {"role": "system", "content": classify_prompt},
                    {"role": "user", "content": json.dumps({"items": items_payload}, ensure_ascii=False)},
                ]
                classifications_raw = await ollama_client.chat_completion_json(classify_msgs, temperature=0.0)
                if isinstance(classifications_raw, list):
                    by_id = {str(c.get("item_id")): c for c in classifications_raw}
                else:
                    by_id = {}
            else:
                by_id = {}
        except Exception:
            by_id = {}

        # Fall back to rule-based for items that weren't classified
        if not by_id:
            fallback = _fallback_classification(items_payload)
            by_id = {c["item_id"]: c for c in fallback}

        # Build search results
        search_results: List[SearchResult] = []
        for i, r in enumerate(raw_results):
            cls = by_id.get(str(i), {})
            score = float(cls.get("risk_score", 0.3))
            search_results.append(
                SearchResult(
                    title=r.get("title", ""),
                    snippet=r.get("snippet", ""),
                    url=r.get("url", ""),
                    date=r.get("date", ""),
                    risk_label=_risk_label(score),
                    risk_score=score,
                    rationale=cls.get("rationale", ""),
                )
            )

        # 3) Generate a natural-language summary using Ollama
        summary_text = _generate_summary_text(query, search_results)

        try:
            ollama_ok = await ollama_client.is_available()
            if ollama_ok:
                summary_msgs = [
                    {
                        "role": "system",
                        "content": (
                            "You are PrivacyProtector, an AI assistant that helps users understand "
                            "their digital footprint. You just searched the web for the user. "
                            "Summarize the findings in a helpful, concise way. Mention which sites "
                            "contain the user's data, highlight any high-risk results, and suggest "
                            "next steps. Be conversational but precise."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"I searched the web for: \"{query}\"\n\n"
                            f"Here are the results:\n{json.dumps([sr.dict() for sr in search_results], indent=2)}\n\n"
                            f"Please summarize these findings for me."
                        ),
                    },
                ]
                summary_text = await ollama_client.chat_completion(summary_msgs, temperature=0.4)
        except Exception:
            pass  # keep the fallback summary_text

        # Persist assistant reply with search results
        if user_id:
            assistant_record = ChatMessageRecord(
                user_id=user_id,
                role="assistant",
                content=summary_text,
                search_results_json=json.dumps([sr.dict() for sr in search_results]),
                is_search=True,
            )
            session.add(assistant_record)
            session.commit()

        return ChatResponse(
            reply=summary_text,
            search_results=search_results,
            is_search=True,
        )

    # --- GENERAL QUESTION PATH ---
    ollama_ok = await ollama_client.is_available()
    if not ollama_ok:
        reply_text = (
            "I'm sorry, the AI engine (Ollama) is not currently available. "
            "Please make sure Ollama is running locally (`ollama serve`) and try again."
        )
        if user_id:
            session.add(ChatMessageRecord(user_id=user_id, role="assistant", content=reply_text))
            session.commit()
        return ChatResponse(reply=reply_text, is_search=False)

    messages = [
        {
            "role": "system",
            "content": (
                "You are PrivacyProtector, a friendly and knowledgeable AI assistant "
                "specializing in online privacy, data protection, and digital security. "
                "Help users understand privacy risks, explain data protection regulations "
                "(GDPR, CCPA, etc.), suggest best practices, and answer general questions. "
                "If the user wants to search the web for their data, remind them to ask "
                "you to 'search for' or 'scan' their information."
            ),
        },
    ]

    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    try:
        reply = await ollama_client.chat_completion(messages, temperature=0.5)

        # Persist assistant reply
        if user_id:
            assistant_record = ChatMessageRecord(
                user_id=user_id,
                role="assistant",
                content=reply,
                is_search=False,
            )
            session.add(assistant_record)
            session.commit()

        return ChatResponse(reply=reply, is_search=False)
    except Exception as exc:
        # Never crash — return a friendly error message to the user
        error_msg = (
            "I'm sorry, I encountered an error while processing your question. "
            f"Details: {str(exc)}. "
            "Please make sure Ollama is running and try again."
        )
        if user_id:
            try:
                session.add(ChatMessageRecord(user_id=user_id, role="assistant", content=error_msg))
                session.commit()
            except Exception:
                pass  # Don't crash if DB write fails too
        return ChatResponse(reply=error_msg, is_search=False)


def _generate_summary_text(query: str, results: List[SearchResult]) -> str:
    """Fallback summary when Ollama isn't available."""
    high_risk = [r for r in results if r.risk_label == "High"]
    medium_risk = [r for r in results if r.risk_label == "Medium"]

    lines = [f"I searched the web for **\"{query}\"** and found **{len(results)} results**.\n"]

    if high_risk:
        lines.append(f"⚠️ **{len(high_risk)} high-risk result(s)** were found that may expose sensitive data:\n")
        for r in high_risk[:3]:
            lines.append(f"  • **{r.title}** — {r.url}")

    if medium_risk:
        lines.append(f"\n⚡ **{len(medium_risk)} medium-risk result(s)** were also found.\n")

    lines.append(
        "\nYou can review each result below. For high-risk items, consider requesting "
        "data removal from the website."
    )

    return "\n".join(lines)
