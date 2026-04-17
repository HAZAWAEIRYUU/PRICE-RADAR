import api from "./api";

// Auth state is owned by the backend via an HttpOnly cookie. The frontend
// can't read the token; it only checks "am I logged in?" by calling
// /api/auth/me. All mutations happen via axios with withCredentials.

export async function login(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/api/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  prewarmBackend();
  return response.data;
}

export async function register(username: string, password: string, email?: string) {
  const response = await api.post("/api/auth/register", {
    username,
    password,
    email: email || null,
  });
  prewarmBackend();
  return response.data;
}

export async function googleLogin(code: string, redirectUri: string) {
  const response = await api.post("/api/auth/google", {
    code,
    redirect_uri: redirectUri,
  });
  prewarmBackend();
  return response.data;
}

export function getGoogleAuthUrl(redirectUri: string): string {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!clientId) return "";
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "consent",
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
}

export async function lineLogin(code: string, redirectUri: string) {
  const response = await api.post("/api/auth/line", {
    code,
    redirect_uri: redirectUri,
  });
  prewarmBackend();
  return response.data;
}

// 認証済みユーザーに LINE を連携する（cookie が自動で送られる）。
export async function lineLink(code: string, redirectUri: string) {
  const response = await api.post("/api/auth/line/link", {
    code,
    redirect_uri: redirectUri,
  });
  return response.data;
}

export function getLineAuthUrl(redirectUri: string, state?: string): string {
  const clientId = process.env.NEXT_PUBLIC_LINE_LOGIN_CHANNEL_ID;
  if (!clientId) return "";
  const params = new URLSearchParams({
    response_type: "code",
    client_id: clientId,
    redirect_uri: redirectUri,
    state: state || Math.random().toString(36).substring(2, 15),
    scope: "profile openid",
  });
  return `https://access.line.me/oauth2/v2.1/authorize?${params.toString()}`;
}

export async function logout() {
  try {
    await api.post("/api/auth/logout");
  } catch {
    // Even if the request fails we still want to redirect; an expired
    // cookie is effectively a logout already.
  }
  if (typeof window !== "undefined") {
    window.location.href = "/login/";
  }
}

// Pre-warm the backend after login to reduce cold-start delay on dashboard
export function prewarmBackend() {
  api.get("/api/products/count").catch(() => {});
}

// Cookie is HttpOnly, so we can't read it from JS. Probe the backend instead.
// Returns true iff /api/auth/me responds 200.
export async function isAuthenticated(): Promise<boolean> {
  try {
    await api.get("/api/auth/me");
    return true;
  } catch {
    return false;
  }
}
