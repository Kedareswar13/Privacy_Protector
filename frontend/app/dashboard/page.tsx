"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  sendChat,
  getChatHistory,
  clearChatHistory,
  ChatMessageType,
  SearchResultType,
} from "@/lib/api";

interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
  searchResults?: SearchResultType[] | null;
  isSearch?: boolean;
  timestamp: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load token + chat history from server on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const t = localStorage.getItem("pp_token");
    if (!t) {
      router.replace("/");
      return;
    }
    setToken(t);

    // Decode email from JWT payload (base64)
    try {
      const email = localStorage.getItem("pp_email");
      if (email) setUserEmail(email);
    } catch {
      // ignore
    }

    // Load chat history from server
    (async () => {
      try {
        const history = await getChatHistory(t);
        const converted: DisplayMessage[] = history.map((h) => ({
          role: h.role as "user" | "assistant",
          content: h.content,
          searchResults: h.search_results,
          isSearch: h.is_search,
          timestamp: new Date(h.created_at).getTime(),
        }));
        setMessages(converted);
      } catch {
        // If history loading fails, start with empty
      } finally {
        setHistoryLoading(false);
      }
    })();
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading || !token) return;

    const userMsg: DisplayMessage = {
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    };

    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // Only send last few messages for context (not entire history for perf)
      const recentForContext = updatedMessages.slice(-10);
      const chatHistory: ChatMessageType[] = recentForContext.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChat(token, chatHistory);

      const assistantMsg: DisplayMessage = {
        role: "assistant",
        content: response.reply,
        searchResults: response.search_results,
        isSearch: response.is_search,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const msg = err.message ?? "Failed to get response";
      // If session expired, auto-logout
      if (msg.includes("session has expired") || msg.includes("401")) {
        handleLogout();
        return;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleClearChat() {
    if (!token) return;
    try {
      await clearChatHistory(token);
      setMessages([]);
      setError(null);
    } catch (err: any) {
      const msg = err.message ?? "Failed to clear chat";
      if (msg.includes("session has expired") || msg.includes("401")) {
        handleLogout();
        return;
      }
      setError(msg);
    }
  }

  function handleLogout() {
    if (typeof window !== "undefined") {
      localStorage.removeItem("pp_token");
      localStorage.removeItem("pp_email");
      localStorage.removeItem("pp_chat_history");
    }
    router.replace("/");
  }

  function riskColor(label: string): string {
    switch (label) {
      case "High":
        return "bg-red-500/20 text-red-300 border-red-500/30";
      case "Medium":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      default:
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    }
  }

  function riskIcon(label: string): string {
    switch (label) {
      case "High":
        return "🔴";
      case "Medium":
        return "🟡";
      default:
        return "🟢";
    }
  }

  return (
    <div className="flex flex-1 flex-col h-full max-h-[calc(100vh-120px)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-700/50">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-slate-50">
            Privacy Assistant
          </h2>
          <p className="text-[11px] text-slate-400">
            Ask questions or search for your digital footprint. I&apos;ll scan the web
            when you need it.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* User profile badge */}
          {userEmail && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-600/40 bg-slate-800/60 px-3 py-1 text-[10px] text-slate-300">
              <span className="h-5 w-5 rounded-full bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center text-[9px] font-bold text-white">
                {userEmail.charAt(0).toUpperCase()}
              </span>
              {userEmail}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Ollama Online
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearChat}
            className="text-[10px] h-7"
          >
            Clear Chat
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="text-[10px] h-7 border-red-500/30 text-red-300 hover:bg-red-500/10"
          >
            Logout
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 min-h-0">
        {/* Loading history indicator */}
        {historyLoading && (
          <div className="flex justify-center py-8">
            <div className="flex items-center gap-2 text-slate-400 text-xs">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
              Loading your chat history...
            </div>
          </div>
        )}

        {!historyLoading && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6 py-16">
            <div className="relative">
              <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 border border-cyan-400/20 flex items-center justify-center text-3xl shadow-lg shadow-cyan-500/10">
                🛡️
              </div>
              <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center text-xs">
                ✓
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-slate-100">
                How can I help protect your privacy?
              </h3>
              <p className="text-sm text-slate-400 max-w-md">
                I can search the web for your personal data, check for breaches,
                or answer any privacy-related questions.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
              {[
                "Search for my name online",
                "What is GDPR?",
                "Find websites that have my data",
                "How do I remove my info from Google?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="text-left rounded-xl border border-slate-700/60 bg-slate-900/50 px-4 py-3 text-xs text-slate-300 hover:bg-slate-800/60 hover:border-slate-600/60 transition-all duration-200"
                  onClick={() => setInput(suggestion)}
                >
                  <span className="text-slate-500">→</span> {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] space-y-3 ${
                msg.role === "user"
                  ? "bg-cyan-500/10 border border-cyan-500/20 rounded-2xl rounded-br-md px-4 py-3"
                  : "bg-slate-900/50 border border-slate-700/50 rounded-2xl rounded-bl-md px-4 py-3"
              }`}
            >
              {/* Role indicator */}
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    msg.role === "user"
                      ? "bg-cyan-500/20 text-cyan-300"
                      : "bg-emerald-500/20 text-emerald-300"
                  }`}
                >
                  {msg.role === "user" ? "U" : "AI"}
                </span>
                <span className="text-[10px] text-slate-500">
                  {msg.role === "user" ? "You" : "PrivacyProtector"}
                </span>
                {msg.isSearch && (
                  <span className="inline-flex items-center rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 px-2 py-0.5 text-[9px] font-medium text-fuchsia-300">
                    🔍 Web Search
                  </span>
                )}
              </div>

              {/* Message content */}
              <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>

              {/* Search results */}
              {msg.searchResults && msg.searchResults.length > 0 && (
                <div className="space-y-2 mt-3 pt-3 border-t border-slate-700/40">
                  <p className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                    {msg.searchResults.length} Results Found
                  </p>
                  {msg.searchResults.map((result, ridx) => (
                    <div
                      key={ridx}
                      className="rounded-xl border border-slate-700/50 bg-slate-950/60 p-3 space-y-1.5 hover:border-slate-600/60 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span
                              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${riskColor(
                                result.risk_label
                              )}`}
                            >
                              {riskIcon(result.risk_label)} {result.risk_label} Risk
                            </span>
                            <span className="text-[10px] text-slate-500">
                              Score: {(result.risk_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noreferrer"
                            className="block mt-1 text-[12px] font-medium text-cyan-300 hover:text-cyan-200 hover:underline truncate"
                          >
                            {result.title}
                          </a>
                          <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">
                            {result.snippet}
                          </p>
                          {result.url && (
                            <p className="text-[10px] text-slate-500 truncate mt-0.5">
                              {result.url}
                            </p>
                          )}
                          {result.rationale && (
                            <p className="text-[10px] text-slate-400 mt-1 italic">
                              💡 {result.rationale}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="h-5 w-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-[10px] font-bold text-emerald-300">
                  AI
                </span>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className="text-[11px] text-slate-400 ml-2">
                  Thinking...
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="px-2">
            <p className="text-xs text-red-400 bg-red-950/60 border border-red-900/70 rounded-xl px-3 py-2">
              ⚠️ {error}
            </p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="pt-4 border-t border-slate-700/50">
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <div className="flex-1 flex items-center gap-2 rounded-2xl border border-slate-700/60 bg-slate-900/60 px-4 py-2.5 shadow-lg shadow-black/20 focus-within:border-cyan-500/40 transition-colors">
            <span className="text-slate-500 text-sm">💬</span>
            <Input
              id="chat-input"
              className="border-0 bg-transparent px-1 py-0 text-sm text-slate-100 shadow-none focus-visible:ring-0 h-auto placeholder:text-slate-500"
              placeholder="Ask me anything about your privacy, or tell me to search for your data..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              autoFocus
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={loading || !input.trim()}
            className="h-10 w-10 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/30 text-cyan-300 p-0 flex items-center justify-center"
          >
            {loading ? (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-cyan-300 border-t-transparent" />
            ) : (
              <span className="text-lg">↑</span>
            )}
          </Button>
        </form>
        <p className="text-[10px] text-slate-600 text-center mt-2">
          PrivacyProtector uses Ollama AI locally and Serper for web searches. Your chat history
          is saved to your account and persists across sessions.
        </p>
      </div>
    </div>
  );
}
