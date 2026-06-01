"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Usuario, RoleUsuario } from "@/lib/types";
import { Topbar } from "@/components/layout/Topbar";

const ROLE_LABEL: Record<RoleUsuario, string> = {
  admin: "Admin",
  gerente: "Gerente",
  operador: "Operador",
  visualizador: "Visualizador",
};
const ROLE_COLOR: Record<RoleUsuario, string> = {
  admin: "#EF4444",
  gerente: "#F04C23",
  operador: "#3B82F6",
  visualizador: "#9CA3AF",
};
const ROLE_BG: Record<RoleUsuario, string> = {
  admin: "#FEF2F2",
  gerente: "#FEF0EC",
  operador: "#EFF6FF",
  visualizador: "#F5F6FA",
};

function getInitials(nome: string) {
  return nome.split(" ").slice(0, 2).map(p => p[0]).join("").toUpperCase();
}

const AVATAR_COLORS = ["#F04C23", "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6"];

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/usuarios")
      .then(r => setUsuarios(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = usuarios.filter(u =>
    !search ||
    u.nome.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <Topbar title="Usuários" subtitle="Gerencie os usuários do sistema" />

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="relative flex-1 max-w-sm">
            <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#9CA3AF" strokeWidth={2}
                 className="absolute left-3.5 top-1/2 -translate-y-1/2">
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Buscar por nome ou e-mail..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full rounded-xl py-2.5 pl-10 pr-4 text-sm outline-none"
              style={{ background: "#F5F6FA", border: "1.5px solid #E8EBF0", color: "#1C1C2E" }}
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-sm" style={{ color: "#9CA3AF" }}>
            Carregando...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-3">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: "#FEF0EC" }}>
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="#F04C23" strokeWidth={1.5}>
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
              </svg>
            </div>
            <p className="font-medium" style={{ color: "#1C1C2E" }}>Nenhum usuário encontrado</p>
            <p className="text-sm" style={{ color: "#9CA3AF" }}>
              {search ? "Tente ajustar a busca" : "Nenhum usuário cadastrado"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid #F0F2F8" }}>
                  {["Usuário", "E-mail", "Perfil", "Status", ""].map(h => (
                    <th key={h} className="text-left py-2 pb-3 pr-4 text-xs font-medium"
                        style={{ color: "#9CA3AF" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((u, i) => {
                  const color = AVATAR_COLORS[i % AVATAR_COLORS.length];
                  return (
                    <tr key={u.id}
                        className="group hover:bg-[#FAFAFA] transition-colors"
                        style={{ borderBottom: i < filtered.length - 1 ? "1px solid #F0F2F8" : "none" }}>
                      <td className="py-3.5 pr-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                               style={{ background: color }}>
                            {getInitials(u.nome)}
                          </div>
                          <span className="text-sm font-medium" style={{ color: "#1C1C2E" }}>{u.nome}</span>
                        </div>
                      </td>
                      <td className="py-3.5 pr-4 text-sm" style={{ color: "#6B7280" }}>{u.email}</td>
                      <td className="py-3.5 pr-4">
                        <span className="text-xs font-medium px-2.5 py-1 rounded-lg"
                              style={{ background: ROLE_BG[u.role], color: ROLE_COLOR[u.role] }}>
                          {ROLE_LABEL[u.role]}
                        </span>
                      </td>
                      <td className="py-3.5 pr-4">
                        <span className={`badge ${u.is_active ? "badge-green" : "badge-gray"}`}>
                          <span className="w-1.5 h-1.5 rounded-full bg-current" />
                          {u.is_active ? "Ativo" : "Inativo"}
                        </span>
                      </td>
                      <td className="py-3.5">
                        <button className="opacity-0 group-hover:opacity-100 transition"
                                style={{ color: "#9CA3AF" }}>
                          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <circle cx="12" cy="5" r="1" fill="currentColor" /><circle cx="12" cy="12" r="1" fill="currentColor" />
                            <circle cx="12" cy="19" r="1" fill="currentColor" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
