// Derive API base. Prefer explicit VITE_API_BASE; fall back to same-origin '/api'.
// If an explicit base is provided, strip trailing slash for consistent concatenation.
const rawBase = (import.meta as any).env?.VITE_API_BASE as string | undefined;
const API_BASE = (() => {
  const fallback = "/api"; // served through reverse proxy -> backend API
  if (!rawBase || rawBase.trim() === "") return fallback;
  return rawBase.endsWith("/") ? rawBase.slice(0, -1) : rawBase;
})();

async function request<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    },
    ...options
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof body === "string" ? body : JSON.stringify(body);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return body as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function apiPost<T>(path: string, payload: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(payload ?? {})
  });
}

export { API_BASE };
