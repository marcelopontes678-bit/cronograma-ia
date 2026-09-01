"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: "▤" },
  { href: "/dashboard/projetos", label: "Projetos", icon: "◈" },
  { href: "/dashboard/orcamentos", label: "Orçamentos", icon: "⌘" },
  { href: "/dashboard/empresa", label: "Empresa", icon: "⊞" },
  { href: "/dashboard/unidades", label: "Unidades", icon: "⊟" },
  { href: "/dashboard/usuarios", label: "Usuários", icon: "◉" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-60 min-h-screen bg-[#111] border-r border-[#222] flex flex-col">
      <div className="p-6 border-b border-[#222]">
        <span className="text-brand-500 font-bold text-lg">SmartFactory</span>
        <p className="text-gray-600 text-xs mt-0.5">Móveis AI</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {nav.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                active
                  ? "bg-brand-500/10 text-brand-500 font-medium"
                  : "text-gray-400 hover:bg-[#1a1a1a] hover:text-white"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[#222]">
        <p className="text-xs text-gray-500 truncate mb-2">{user?.email}</p>
        <button
          onClick={logout}
          className="w-full text-left text-xs text-gray-500 hover:text-red-400 transition"
        >
          Sair
        </button>
      </div>
    </aside>
  );
}
