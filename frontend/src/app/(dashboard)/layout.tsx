"use client";

import { AuthProvider } from "@/components/auth-provider";
import { Sidebar, MobileHeader } from "@/components/sidebar";
import { useAuth } from "@/components/auth-provider";

function DashboardShell({ children }: { children: React.ReactNode }) {
  const { authenticated } = useAuth();

  if (!authenticated) {
    return null;
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <MobileHeader />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <DashboardShell>{children}</DashboardShell>
    </AuthProvider>
  );
}
