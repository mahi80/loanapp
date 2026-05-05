const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiClient(path: string, options: RequestInit & { token?: string } = {}) {
  const { token, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const res = await fetch(`${API_URL}${path}`, { ...fetchOptions, headers });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export { API_URL };
