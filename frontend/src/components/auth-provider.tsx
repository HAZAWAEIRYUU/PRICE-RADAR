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
    const isAuth = checkAuth();
    setAuthenticated(isAuth);
    if (isAuth) prewarmBackend();
    setLoading(false);
  }, []);

  useEffect(() => {
    // Exact or trailing slash matches for public pages
    const publicPaths = ["/login", "/login/", "/signup", "/signup/", "/plans", "/plans/", "/privacy", "/privacy/", "/terms", "/terms/"];
    const authPaths = ["/login", "/login/", "/signup", "/signup/"];
    
    const isPublicPath = publicPaths.includes(pathname);
    const isAuthPath = authPaths.includes(pathname);

    if (!loading) {
      if (!authenticated && !isPublicPath) {
        // Redirect unauthenticated users trying to access protected routes
        window.location.href = "/login/";
      } else if (authenticated && isAuthPath) {
        // Redirect authenticated users away from auth pages
        window.location.href = "/";
      }
    }
  }, [authenticated, loading, pathname]);

  const logout = () => {
    doLogout();
    setAuthenticated(false);
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
