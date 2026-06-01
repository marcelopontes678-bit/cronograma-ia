"use client";
import { useAuth } from "@/hooks/useAuth";

interface TopbarProps {
  title: string;
  subtitle?: string;
}

export function Topbar({ title, subtitle }: TopbarProps) {
  const { user } = useAuth();

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bom dia" : hour < 18 ? "Boa tarde" : "Boa noite";

  return (
    <header className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "#1C1C2E" }}>
          {title === "Dashboard" ? `${greeting}, ${user?.nome?.split(" ")[0]}` : title}
        </h1>
        <p className="text-sm mt-0.5" style={{ color: "#9CA3AF" }}>
          {subtitle ?? "Gerencie sua fábrica com inteligência"}
        </p>
      </div>

      <div className="flex items-center gap-3">
        {/* Notificação */}
        <button className="w-9 h-9 rounded-xl bg-white border border-[#E8EBF0] flex items-center justify-center hover:bg-gray-50 transition relative">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#6B7280" strokeWidth={1.8}>
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" />
          </svg>
        </button>

        {/* Avatar */}
        <div className="flex items-center gap-2 bg-white border border-[#E8EBF0] rounded-xl px-3 py-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
               style={{ background: "#F04C23" }}>
            {user?.nome?.charAt(0).toUpperCase() ?? "A"}
          </div>
          <div>
            <p className="text-xs font-600 leading-tight" style={{ color: "#1C1C2E" }}>
              {user?.nome?.split(" ")[0]}
            </p>
            <p className="text-[10px] leading-tight" style={{ color: "#9CA3AF" }}>
              {user?.role}
            </p>
          </div>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth={2}>
            <path d="M6 9l6 6 6-6" />
          </svg>
        </div>
      </div>
    </header>
  );
}
