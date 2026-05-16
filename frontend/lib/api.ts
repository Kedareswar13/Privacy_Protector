const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch (err: any) {
    // Network errors: backend is down, DNS failure, CORS blocked, etc.
    if (err.name === "TypeError" && err.message?.includes("fetch")) {
      throw new Error(
        "Cannot connect to the server. Please make sure the backend is running on port 8000."
      );
    }
    throw new Error(
      `Network error: ${err.message || "Unable to reach the server. Check your connection."}`
    );
  }

  if (!res.ok) {
    let errorDetail: string;
    try {
      const body = await res.json();
      errorDetail = body.detail || JSON.stringify(body);
    } catch {
      errorDetail = await res.text().catch(() => "Unknown error");
    }

    // Provide user-friendly messages for common HTTP errors
    switch (res.status) {
      case 401:
        throw new Error("Your session has expired. Please log in again.");
      case 403:
        throw new Error("You do not have permission to perform this action.");
      case 404:
        throw new Error(`Resource not found: ${errorDetail}`);
      case 422:
        throw new Error(`Invalid input: ${errorDetail}`);
      case 429:
        throw new Error("Too many requests. Please wait a moment and try again.");
      case 500:
        throw new Error(`Server error: ${errorDetail}`);
      case 502:
      case 503:
      case 504:
        throw new Error("The server is temporarily unavailable. Please try again later.");
      default:
        throw new Error(`Error ${res.status}: ${errorDetail}`);
    }
  }

  return (await res.json()) as T;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string) {
  return apiRequest<{ user_id: number; email: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function createConsent(token: string) {
  return apiRequest<{ consent_id: number; user_id: number }>("/consent", {
    method: "POST",
    token,
    body: JSON.stringify({
      scopes: { scan_web: true, scan_social: true, check_breach: true, reverse_image: true },
    }),
  });
}

export async function createScan(token: string | null, payload: any) {
  return apiRequest<{ scan_id: number }>("/scans", {
    method: "POST",
    body: JSON.stringify(payload),
    ...(token ? { token } : {}),
  });
}

export async function getScan(scanId: number) {
  return apiRequest(`/scans/${scanId}`);
}

export async function runScan(scanId: number) {
  return apiRequest(`/scans/${scanId}/run`, { method: "POST" });
}

export async function getScanItems(scanId: number) {
  return apiRequest(`/scans/${scanId}/items`);
}

export async function getItem(itemId: number) {
  return apiRequest(`/scans/items/${itemId}`);
}

export interface ChatMessageType {
  role: "user" | "assistant";
  content: string;
}

export interface SearchResultType {
  title: string;
  snippet: string;
  url: string;
  date: string;
  risk_label: string;
  risk_score: number;
  rationale: string;
}

export interface ChatResponseType {
  reply: string;
  search_results: SearchResultType[] | null;
  is_search: boolean;
}

export interface HistoryMessageType {
  id: number;
  role: "user" | "assistant";
  content: string;
  search_results: SearchResultType[] | null;
  is_search: boolean;
  created_at: string;
}

export async function sendChat(token: string, messages: ChatMessageType[]): Promise<ChatResponseType> {
  return apiRequest<ChatResponseType>("/chat", {
    method: "POST",
    token,
    body: JSON.stringify({ messages }),
  });
}

export async function getChatHistory(token: string): Promise<HistoryMessageType[]> {
  return apiRequest<HistoryMessageType[]>("/chat/history", {
    method: "GET",
    token,
  });
}

export async function clearChatHistory(token: string): Promise<{ deleted: number }> {
  return apiRequest<{ deleted: number }>("/chat/history", {
    method: "DELETE",
    token,
  });
}
