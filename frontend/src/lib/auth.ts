import Cookies from "js-cookie";
import api from "./api";

export async function login(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/api/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  const { access_token } = response.data;
  Cookies.set("access_token", access_token, { expires: 7, sameSite: "lax", secure: process.env.NODE_ENV === "production" });
  prewarmBackend();
  return response.data;
}

export async function register(username: string, password: string, email?: string) {
  const response = await api.post("/api/auth/register", {
    username,
    password,
    email: email || null,
  });

  const { access_token } = response.data;
  Cookies.set("access_token", access_token, { expires: 7, sameSite: "lax", secure: process.env.NODE_ENV === "production" });
  prewarmBackend();
  return response.data;
}

export async function googleLogin(code: string, redirectUri: string) {
  const response = await api.post("/api/auth/google", {
    code,
    redirect_uri: redirectUri,
  });

  const { access_token } = response.data;
  Cookies.set("access_token", access_token, { expires: 7, sameSite: "lax", secure: process.env.NODE_ENV === "production" });
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

export async function lineLogin(code: string, redirectUri: string, linkToUserId?: number) {
  const response = await api.post("/api/auth/line", {
    code,
    redirect_uri: redirectUri,
    link_to_user_id: linkToUserId ?? null,
  });

  const { access_token } = response.data;
  Cookies.set("access_token", access_token, { expires: 7, sameSite: "lax", secure: process.env.NODE_ENV === "production" });
  prewarmBackend();
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

export function logout() {
  Cookies.remove("access_token");
  window.location.href = "/login/";
}

// Pre-warm the backend after login to reduce cold-start delay on dashboard
export function prewarmBackend() {
  api.get("/api/products/count").catch(() => {});
}

export function getToken(): string | undefined {
  return Cookies.get("access_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
