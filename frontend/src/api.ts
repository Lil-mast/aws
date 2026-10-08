const API_ROOT = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

export type Tokens = { access_token: string; refresh_token: string; token_type: "bearer" };
export type Profile = {
  id: string;
  email: string;
  full_name: string | null;
  currency: string;
  monthly_income: number | null;
};
export type Transaction = {
  id: string;
  amount: number;
  currency: string;
  transaction_type: "credit" | "debit";
  category: string | null;
  description: string | null;
  transaction_date: string;
};
export type Summary = {
  total_credits: number;
  total_debits: number;
  net: number;
  count: number;
  by_category: Record<string, number>;
};
export type Budget = {
  id: string;
  name: string;
  period: string;
  total_income: number;
  currency: string;
  categories: { id: string; name: string; category_type: string; allocated_amount: number; spent_amount: number }[];
};

let accessToken = localStorage.getItem("mula_access_token");
let refreshToken = localStorage.getItem("mula_refresh_token");
let refreshInFlight: Promise<boolean> | null = null;

export function hasSession() {
  return Boolean(accessToken && refreshToken);
}

function saveTokens(tokens: Tokens) {
  accessToken = tokens.access_token;
  refreshToken = tokens.refresh_token;
  localStorage.setItem("mula_access_token", tokens.access_token);
  localStorage.setItem("mula_refresh_token", tokens.refresh_token);
}

export function clearSession() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("mula_access_token");
  localStorage.removeItem("mula_refresh_token");
}

async function renewSession(): Promise<boolean> {
  if (!refreshToken) return false;
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = fetch(`${API_ROOT}/auth/token/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
    .then(async (response) => {
      if (!response.ok) return false;
      saveTokens((await response.json()) as Tokens);
      return true;
    })
    .catch(() => false)
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

export async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  let response: Response;
  try {
    response = await fetch(`${API_ROOT}${path}`, { ...init, headers });
  } catch {
    throw new Error(`Can’t reach the Mula API at ${API_ROOT}. In a second terminal, run ./backend/run-local.sh after installing the backend requirements.`);
  }
  if (response.status === 401 && retry && refreshToken && !path.startsWith("/auth/token/refresh")) {
    if (await renewSession()) return request<T>(path, init, false);
    clearSession();
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail ?? payload);
    } catch {
      // Keep the status-based message for non-JSON responses.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function signIn(email: string, password: string) {
  const tokens = await request<Tokens>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  saveTokens(tokens);
}

export async function signUp(full_name: string, email: string, password: string) {
  await request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ full_name, email, password }),
  });
  await signIn(email, password);
}

export async function signOut() {
  const token = refreshToken;
  clearSession();
  if (!token) return;
  try {
    await request("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: token }) }, false);
  } catch {
    // Local credentials are cleared even if the network is unavailable.
  }
}
