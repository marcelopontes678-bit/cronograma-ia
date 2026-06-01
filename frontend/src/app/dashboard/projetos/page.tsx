"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ProjetoListItem, StatusProjeto } from "@/lib/types";

const STATUS_LABEL: Record<StatusProjeto, string> = {
  rascunho: "Rascunho",
  aguardando_aprovacao: "Aguardando",
  em_producao: "Em Produção",
  concluido: "Concluído",
  cancelado: "Cancelado",
};

const STATUS_COLOR: Record<StatusProjeto, string> = {
  rascunho: "text-gray-400 bg-gray-800",
  aguardando_aprovacao: "text-yellow-300 bg-yellow-900/40",
  em_producao: "text-blue-300 bg-blue-900/40",
  concluido: "text-green-300 bg-green-900/40",
  cancelado: "text-red-300 bg-red-900/40",
};

export default function ProjetosPage() {
  const [projetos, setProjetos] = useState<ProjetoListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = search ? `?search=${encodeURIComponent(search)}` : "";
    api
      .get(`/projetos${params}`)
      .then((r) => setProjetos(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [search]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projetos</h1>
        <Link
          href="/dashboard/projetos/novo"
          className="bg-brand-500 text-black text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-600 transition"
        >
          + Novo Projeto
        </Link>
      </div>

      <input
        type="text"
        placeholder="Buscar por nome, código ou cliente..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 mb-6 text-white focus:outline-none focus:border-brand-500"
      />

      {loading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : projetos.length === 0 ? (
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-12 text-center text-gray-500">
          Nenhum projeto encontrado.
        </div>
      ) : (
        <div className="space-y-3">
          {projetos.map((p) => (
            <div
              key={p.id}
              className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl px-5 py-4 flex items-center justify-between"
            >
              <div>
                <p className="font-medium">
                  <span className="text-gray-500 text-sm mr-2">{p.codigo}</span>
                  {p.nome}
                </p>
                {p.cliente_nome && (
                  <p className="text-gray-500 text-sm mt-0.5">{p.cliente_nome}</p>
                )}
              </div>
              <div className="flex items-center gap-4">
                {p.data_entrega_prevista && (
                  <span className="text-gray-500 text-sm hidden sm:block">
                    Entrega: {new Date(p.data_entrega_prevista).toLocaleDateString("pt-BR")}
                  </span>
                )}
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_COLOR[p.status]}`}
                >
                  {STATUS_LABEL[p.status]}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
