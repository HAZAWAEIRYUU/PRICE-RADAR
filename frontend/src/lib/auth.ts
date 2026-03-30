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
  Cookies.set("access_token", access_token, { expires: 7, sameSite: "lax" });
  return response.data;
}

export async function register(username: string, password: string, email?: string) {
  const response = await api.post("/api/auth/register", {
    username,
    password,
    email: email || null,
  });

  const { access_token } = response.data;
  Cookies.set("access_token", access_token, { expires: 7, sameSite: "lax" });
  return response.data;
}

export function logout() {
  Cookies.remove("access_token");
  window.location.href = "/login/";
}

export function getToken(): string | undefined {
  return Cookies.get("access_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
