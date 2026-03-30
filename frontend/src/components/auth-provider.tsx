"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { isAuthenticated as checkAuth, logout as doLogout } from "@/lib/auth";
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
    setAuthenticated(checkAuth());
    setLoading(false);
  }, []);

  useEffect(() => {
    const isPublicPath = pathname === "/login" || pathname === "/login/" || pathname === "/signup" || pathname === "/signup/";
    if (!loading && !authenticated && !isPublicPath) {
      window.location.href = "/login/";
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
