"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Topbar } from "@/components/layout/Topbar";
import { ProjetoListItem } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  rascunho: "Rascunho",
  aguardando_aprovacao: "Aguardando",
  em_producao: "Em Produção",
  concluido: "Concluído",
  cancelado: "Cancelado",
};
const STATUS_CLASS: Record<string, string> = {
  rascunho: "badge-gray",
  aguardando_aprovacao: "badge-yellow",
  em_producao: "badge-blue",
  concluido: "badge-green",
  cancelado: "badge-red",
};

const PRIO_COLOR: Record<number, string> = {
  1: "#EF4444", 2: "#F04C23", 3: "#F59E0B", 4: "#3B82F6", 5: "#9CA3AF",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [projetos, setProjetos] = useState<ProjetoListItem[]>([]);
  const [totals, setTotals] = useState({ total: 0, producao: 0, concluidos: 0, usuarios: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get("/projetos?limit=100"),
      api.get("/usuarios?limit=100"),
    ]).then(([p, u]) => {
      const all: ProjetoListItem[] = p.data;
      setTotals({
        total: all.length,
        producao: all.filter(x => x.status === "em_producao").length,
        concluidos: all.filter(x => x.status === "concluido").length,
        usuarios: u.data.length,
      });
      setProjetos(all.slice(0, 6));
    }).catch(() => {}).finally(() => setLoading(false));
  }, [user]);

  const metricCards = [
    {
      label: "Total de Projetos",
      value: totals.total,
      change: "+12% este mês",
      up: true,
      primary: false,
      icon: (
        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
        </svg>
      ),
    },
    {
      label: "Em Produção",
      value: totals.producao,
      change: "Projetos ativos",
      up: true,
      primary: true,
      icon: (
        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={1.8}>
          <path d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      label: "Concluídos",
      value: totals.concluidos,
      change: "Entregues",
      up: true,
      primary: false,
      icon: (
        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
        </svg>
      ),
    },
    {
      label: "Usuários",
      value: totals.usuarios,
      change: "Equipe ativa",
      up: true,
      primary: false,
      icon: (
        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
        </svg>
      ),
    },
  ];

  return (
    <div>
      <Topbar title="Dashboard" subtitle="Acompanhe o andamento da sua fábrica" />

      {user?.must_change_password && (
        <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
             style={{ background: "#FEF0EC", color: "#C93A18", border: "1px solid #FDDDD5" }}>
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          Por segurança, altere sua senha no primeiro acesso em Usuários.
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {metricCards.map((c) => (
          <div
            key={c.label}
            className="rounded-2xl p-5"
            style={{
              background: c.primary ? "#F04C23" : "#FFFFFF",
              border: c.primary ? "none" : "1px solid #E8EBF0",
              boxShadow: c.primary
                ? "0 8px 24px rgba(240,76,35,0.25)"
                : "0 1px 4px rgba(0,0,0,.04)",
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-medium" style={{ color: c.primary ? "rgba(255,255,255,.8)" : "#9CA3AF" }}>
                {c.label}
              </p>
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{
                  background: c.primary ? "rgba(255,255,255,.2)" : "#FEF0EC",
                  color: c.primary ? "white" : "#F04C23",
                }}
              >
                {c.icon}
              </div>
            </div>
            <p className="text-3xl font-bold mb-1" style={{ color: c.primary ? "white" : "#1C1C2E" }}>
              {loading ? "—" : c.value}
            </p>
            <p className="text-xs" style={{ color: c.primary ? "rgba(255,255,255,.7)" : "#10B981" }}>
              {c.change}
            </p>
          </div>
        ))}
      </div>

      {/* Recent Projects Table */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold" style={{ color: "#1C1C2E" }}>Projetos Recentes</h2>
          <a href="/dashboard/projetos" className="text-sm font-medium" style={{ color: "#F04C23" }}>
            Ver todos →
          </a>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10 text-sm" style={{ color: "#9CA3AF" }}>
            Carregando...
          </div>
        ) : projetos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: "#FEF0EC" }}>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="#F04C23" strokeWidth={1.5}>
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" /><rect x="9" y="3" width="6" height="4" rx="1" />
              </svg>
            </div>
            <p className="text-sm" style={{ color: "#9CA3AF" }}>Nenhum projeto cadastrado ainda</p>
            <a href="/dashboard/projetos/novo"
               className="text-sm font-medium px-4 py-2 rounded-lg"
               style={{ background: "#FEF0EC", color: "#F04C23" }}>
              + Criar primeiro projeto
            </a>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid #F0F2F8" }}>
                  {["Código", "Projeto", "Cliente", "Prioridade", "Entrega", "Status"].map(h => (
                    <th key={h} className="text-left py-2 pb-3 text-xs font-medium pr-4"
                        style={{ color: "#9CA3AF" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {projetos.map((p, i) => (
                  <tr key={p.id}
                      className="group hover:bg-[#FAFAFA] transition-colors cursor-pointer"
                      style={{ borderBottom: i < projetos.length - 1 ? "1px solid #F0F2F8" : "none" }}>
                    <td className="py-3 pr-4 text-xs font-mono" style={{ color: "#9CA3AF" }}>{p.codigo}</td>
                    <td className="py-3 pr-4 text-sm font-medium" style={{ color: "#1C1C2E" }}>{p.nome}</td>
                    <td className="py-3 pr-4 text-sm" style={{ color: "#6B7280" }}>{p.cliente_nome ?? "—"}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full" style={{ background: PRIO_COLOR[p.prioridade] ?? "#9CA3AF" }} />
                        <span className="text-xs" style={{ color: PRIO_COLOR[p.prioridade] }}>{p.prioridade}</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-sm" style={{ color: "#6B7280" }}>
                      {p.data_entrega_prevista
                        ? new Date(p.data_entrega_prevista).toLocaleDateString("pt-BR")
                        : "—"}
                    </td>
                    <td className="py-3">
                      <span className={`badge ${STATUS_CLASS[p.status] ?? "badge-gray"}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {STATUS_LABEL[p.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
