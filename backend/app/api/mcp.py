from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jsonschema

from ..mcp_tools import (
    search_web,
    search_social,
    check_breach,
    score_risk,
    generate_remediation,
    reverse_image_search,
)


router = APIRouter()


TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "searchWeb": {
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
        "output_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "snippet": {"type": "string"},
                    "url": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["title", "snippet", "url"],
            },
        },
    },
    "reverseImageSearch": {
        "input_schema": {
            "type": "object",
            "properties": {
                "image_hash": {"type": "string"},
            },
            "required": ["image_hash"],
        },
        "output_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "similarity": {"type": "number"},
                    "context": {"type": "string"},
                },
                "required": ["url", "similarity"],
            },
        },
    },
    "searchSocial": {
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["service", "query"],
        },
        "output_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "url": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "meta": {"type": "object"},
                },
                "required": ["id", "text", "url"],
            },
        },
    },
    "checkBreach": {
        "input_schema": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "pwned": {"type": "boolean"},
                "breaches": {"type": "array"},
            },
            "required": ["pwned", "breaches"],
        },
    },
    "scoreRisk": {
        "input_schema": {
            "type": "object",
            "properties": {"items": {"type": "array"}},
            "required": ["items"],
        },
        "output_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "risk_score": {"type": "number"},
                    "category": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["item_id", "risk_score", "category"],
            },
        },
    },
    "generateRemediation": {
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "tone": {"type": "string"},
            },
            "required": ["item_id"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "draft_email": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "string"}},
                "settings_links": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["draft_email", "steps", "settings_links"],
        },
    },
}


class ToolCallRequest(BaseModel):
    tool: str
    args: Dict[str, Any]


@router.get("/tools")
async def list_tools() -> Dict[str, Any]:
    tools = [
        {
            "name": name,
            "input_schema": spec["input_schema"],
            "output_schema": spec["output_schema"],
        }
        for name, spec in TOOL_SCHEMAS.items()
    ]
    return {"tools": tools}


@router.post("/call")
async def call_tool(request: ToolCallRequest) -> Dict[str, Any]:
    tool_name = request.tool
    args = request.args

    if tool_name not in TOOL_SCHEMAS:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

    schemas = TOOL_SCHEMAS[tool_name]

    # Validate input args
    try:
        jsonschema.validate(instance=args, schema=schemas["input_schema"])
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid args for {tool_name}: {exc.message}")

    # Dispatch to tool implementation
    if tool_name == "searchWeb":
        result = await search_web.search_web(**args)
    elif tool_name == "searchSocial":
        result = await search_social.search_social(**args)
    elif tool_name == "checkBreach":
        result = await check_breach.check_breach(**args)
    elif tool_name == "scoreRisk":
        result = await score_risk.score_risk(**args.get("items", []))
    elif tool_name == "generateRemediation":
        result = await generate_remediation.generate_remediation(**args)
    elif tool_name == "reverseImageSearch":
        result = await reverse_image_search.reverse_image_search(**args)
    else:
        raise HTTPException(status_code=400, detail=f"Tool not implemented: {tool_name}")

    # Validate output
    try:
        jsonschema.validate(instance=result, schema=schemas["output_schema"])
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Tool output invalid for {tool_name}: {exc.message}")

    return {"result": result}
