"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { isAuthenticated as checkAuth, logout as doLogout, prewarmBackend } from "@/lib/auth";
import { usePathname } from "next/navigation";

interface AuthContextType {
  authenticated: boolean;
  setAuthenticated: (v: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  authenticated: false,
  setAuthenticated: () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const isAuth = await checkAuth();
      if (cancelled) return;
      setAuthenticated(isAuth);
      if (isAuth) prewarmBackend();
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const publicPaths = ["/", "/login", "/login/", "/signup", "/signup/", "/plans", "/plans/", "/privacy", "/privacy/", "/terms", "/terms/"];
    const authPaths = ["/login", "/login/", "/signup", "/signup/"];

    const isPublicPath = publicPaths.includes(pathname);
    const isAuthPath = authPaths.includes(pathname);

    // Skip redirects while Google/LINE OAuth callback is being processed
    const hasOAuthCode = typeof window !== "undefined" && window.location.search.includes("code=");

    if (!loading && !hasOAuthCode) {
      if (!authenticated && !isPublicPath) {
        window.location.href = "/login/";
      } else if (authenticated && isAuthPath) {
        window.location.href = "/dashboard/";
      } else if (authenticated && (pathname === "/" || pathname === "")) {
        window.location.href = "/dashboard/";
      }
    }
  }, [authenticated, loading, pathname]);

  const logout = () => {
    setAuthenticated(false);
    void doLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ authenticated, setAuthenticated, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
