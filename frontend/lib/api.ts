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
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
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
