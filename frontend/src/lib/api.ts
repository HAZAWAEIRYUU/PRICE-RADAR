import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "https://priceradar-api.onrender.com",
  headers: {
    "Content-Type": "application/json",
  },
  // Auth is an HttpOnly cookie set by the backend; the browser attaches it
  // only when the XHR explicitly opts in to credentials.
  withCredentials: true,
});

// Response interceptor: on 401, send the user back to /login/.
// We don't need to clear a local token anymore — the cookie is HttpOnly,
// cleared by the backend on /auth/logout (or it simply expired).
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login/";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
