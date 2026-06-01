"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#F5F6FA" }}>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 rounded-full border-2 border-[#F04C23] border-t-transparent animate-spin" />
          <span style={{ color: "#9CA3AF", fontSize: 14 }}>Carregando...</span>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex min-h-screen" style={{ background: "#F5F6FA" }}>
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto" style={{ marginLeft: 64 }}>
        {children}
      </main>
    </div>
  );
}
