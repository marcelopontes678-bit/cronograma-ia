"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ProjetoListItem, StatusProjeto } from "@/lib/types";
import { Topbar } from "@/components/layout/Topbar";

const STATUS_LABEL: Record<StatusProjeto, string> = {
  rascunho: "Rascunho",
  aguardando_aprovacao: "Aguardando",
  em_producao: "Em Produção",
  concluido: "Concluído",
  cancelado: "Cancelado",
};
const STATUS_CLASS: Record<StatusProjeto, string> = {
  rascunho: "badge-gray",
  aguardando_aprovacao: "badge-yellow",
  em_producao: "badge-blue",
  concluido: "badge-green",
  cancelado: "badge-red",
};
const PRIO_COLOR: Record<number, string> = {
  1: "#EF4444", 2: "#F04C23", 3: "#F59E0B", 4: "#3B82F6", 5: "#9CA3AF",
};
const PRIO_LABEL: Record<number, string> = {
  1: "Urgente", 2: "Alta", 3: "Normal", 4: "Baixa", 5: "Mínima",
};

const FILTER_OPTIONS: { label: string; value: string }[] = [
  { label: "Todos", value: "" },
  { label: "Rascunho", value: "rascunho" },
  { label: "Aguardando", value: "aguardando_aprovacao" },
  { label: "Em Produção", value: "em_producao" },
  { label: "Concluído", value: "concluido" },
  { label: "Cancelado", value: "cancelado" },
];

export default function ProjetosPage() {
  const router = useRouter();
  const [projetos, setProjetos] = useState<ProjetoListItem[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (statusFilter) params.set("status", statusFilter);
    api.get(`/projetos?${params}`)
      .then(r => setProjetos(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [search, statusFilter]);

  return (
    <div>
      <Topbar title="Projetos" subtitle="Gerencie todos os projetos da fábrica" />

      <div className="card p-6">
        {/* Header da tabela */}
        <div className="flex items-center gap-3 mb-5">
          <div className="relative flex-1">
            <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#9CA3AF" strokeWidth={2}
                 className="absolute left-3.5 top-1/2 -translate-y-1/2">
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Buscar por nome, código ou cliente..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full rounded-xl py-2.5 pl-10 pr-4 text-sm outline-none"
              style={{ background: "#F5F6FA", border: "1.5px solid #E8EBF0", color: "#1C1C2E" }}
            />
          </div>

          {/* Filtros de status */}
          <div className="flex gap-1.5">
            {FILTER_OPTIONS.map(f => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className="text-xs font-medium px-3 py-2 rounded-lg transition"
                style={{
                  background: statusFilter === f.value ? "#F04C23" : "#F5F6FA",
                  color: statusFilter === f.value ? "white" : "#6B7280",
                  border: "1.5px solid " + (statusFilter === f.value ? "#F04C23" : "#E8EBF0"),
                }}
              >
                {f.label}
              </button>
            ))}
          </div>

          <Link
            href="/dashboard/projetos/novo"
            className="flex items-center gap-1.5 text-sm font-semibold px-4 py-2.5 rounded-xl text-white transition"
            style={{ background: "#F04C23", boxShadow: "0 4px 12px rgba(240,76,35,.25)" }}
          >
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.5}>
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Novo
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-sm" style={{ color: "#9CA3AF" }}>
            Carregando...
          </div>
        ) : projetos.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-3">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: "#FEF0EC" }}>
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="#F04C23" strokeWidth={1.5}>
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" /><rect x="9" y="3" width="6" height="4" rx="1" />
              </svg>
            </div>
            <p className="font-medium" style={{ color: "#1C1C2E" }}>Nenhum projeto encontrado</p>
            <p className="text-sm" style={{ color: "#9CA3AF" }}>
              {search || statusFilter ? "Tente ajustar os filtros" : "Crie o primeiro projeto da fábrica"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid #F0F2F8" }}>
                  {["Código", "Projeto", "Cliente", "Prioridade", "Entrega", "Status", ""].map(h => (
                    <th key={h} className="text-left py-2 pb-3 pr-4 text-xs font-medium"
                        style={{ color: "#9CA3AF" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {projetos.map((p, i) => (
                  <tr key={p.id}
                      onClick={() => router.push(`/dashboard/projetos/${p.id}`)}
                      className="group hover:bg-[#FAFAFA] transition-colors cursor-pointer"
                      style={{ borderBottom: i < projetos.length - 1 ? "1px solid #F0F2F8" : "none" }}>
                    <td className="py-3.5 pr-4 text-xs font-mono" style={{ color: "#9CA3AF" }}>{p.codigo}</td>
                    <td className="py-3.5 pr-4 text-sm font-medium max-w-[220px] truncate" style={{ color: "#1C1C2E" }}>{p.nome}</td>
                    <td className="py-3.5 pr-4 text-sm" style={{ color: "#6B7280" }}>{p.cliente_nome ?? "—"}</td>
                    <td className="py-3.5 pr-4">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full" style={{ background: PRIO_COLOR[p.prioridade] }} />
                        <span className="text-xs font-medium" style={{ color: PRIO_COLOR[p.prioridade] }}>
                          {PRIO_LABEL[p.prioridade]}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 pr-4 text-sm" style={{ color: "#6B7280" }}>
                      {p.data_entrega_prevista
                        ? new Date(p.data_entrega_prevista).toLocaleDateString("pt-BR")
                        : "—"}
                    </td>
                    <td className="py-3.5 pr-4">
                      <span className={`badge ${STATUS_CLASS[p.status] ?? "badge-gray"}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {STATUS_LABEL[p.status]}
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
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
