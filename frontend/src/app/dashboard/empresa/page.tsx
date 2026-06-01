"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Empresa } from "@/lib/types";
import { Topbar } from "@/components/layout/Topbar";

const TIPO_LABEL: Record<string, string> = {
  fabrica: "Fábrica",
  centro_distribuicao: "Centro de Distribuição",
  escritorio: "Escritório",
};
const TIPO_COLOR: Record<string, string> = {
  fabrica: "#F04C23", centro_distribuicao: "#3B82F6", escritorio: "#10B981",
};
const TIPO_BG: Record<string, string> = {
  fabrica: "#FEF0EC", centro_distribuicao: "#EFF6FF", escritorio: "#ECFDF5",
};

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs mb-1" style={{ color: "#9CA3AF" }}>{label}</p>
      <p className="text-sm font-medium" style={{ color: value ? "#1C1C2E" : "#D1D5DB" }}>
        {value ?? "Não informado"}
      </p>
    </div>
  );
}

export default function EmpresaPage() {
  const { user } = useAuth();
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api.get(`/empresas/${user.empresa_id}`)
      .then(r => setEmpresa(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return (
    <div>
      <Topbar title="Empresa" />
      <div className="flex items-center justify-center py-20 text-sm" style={{ color: "#9CA3AF" }}>Carregando...</div>
    </div>
  );

  if (!empresa) return (
    <div>
      <Topbar title="Empresa" />
      <div className="card p-12 text-center text-sm" style={{ color: "#EF4444" }}>Empresa não encontrada.</div>
    </div>
  );

  return (
    <div>
      <Topbar title="Empresa" subtitle="Dados cadastrais e unidades" />

      <div className="max-w-3xl space-y-4">
        {/* Card principal */}
        <div className="card p-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold text-white"
                   style={{ background: "#F04C23" }}>
                {empresa.nome.charAt(0)}
              </div>
              <div>
                <h2 className="text-lg font-bold" style={{ color: "#1C1C2E" }}>{empresa.nome}</h2>
                {empresa.nome_fantasia && (
                  <p className="text-sm" style={{ color: "#9CA3AF" }}>{empresa.nome_fantasia}</p>
                )}
              </div>
            </div>
            <span className="badge badge-green">Ativa</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
            <InfoRow label="CNPJ" value={empresa.cnpj} />
            <InfoRow label="E-mail" value={empresa.email} />
            <InfoRow label="Telefone" value={empresa.telefone} />
            <InfoRow label="Cidade" value={empresa.cidade ? `${empresa.cidade}${empresa.estado ? ` / ${empresa.estado}` : ""}` : null} />
            <InfoRow label="CEP" value={empresa.cep} />
          </div>

          {empresa.dias_funcionamento && empresa.dias_funcionamento.length > 0 && (
            <div className="mt-5 pt-5" style={{ borderTop: "1px solid #F0F2F8" }}>
              <p className="text-xs mb-2" style={{ color: "#9CA3AF" }}>Dias de funcionamento</p>
              <div className="flex gap-2 flex-wrap">
                {empresa.dias_funcionamento.map(d => (
                  <span key={d} className="text-xs font-medium px-2.5 py-1 rounded-lg"
                        style={{ background: "#FEF0EC", color: "#F04C23" }}>{d}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Unidades */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-semibold" style={{ color: "#1C1C2E" }}>Unidades</h3>
            <span className="text-xs px-2.5 py-1 rounded-lg font-medium"
                  style={{ background: "#F5F6FA", color: "#9CA3AF" }}>
              {empresa.unidades.length} unidade{empresa.unidades.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="space-y-3">
            {empresa.unidades.map(u => (
              <div key={u.id}
                   className="flex items-center justify-between p-4 rounded-xl"
                   style={{ background: "#F9FAFB", border: "1.5px solid #F0F2F8" }}>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                       style={{ background: TIPO_BG[u.tipo] ?? "#F5F6FA" }}>
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24"
                         stroke={TIPO_COLOR[u.tipo] ?? "#9CA3AF"} strokeWidth={1.8}>
                      <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium" style={{ color: "#1C1C2E" }}>{u.nome}</p>
                    <p className="text-xs" style={{ color: "#9CA3AF" }}>
                      {TIPO_LABEL[u.tipo]}
                      {u.codigo ? ` · ${u.codigo}` : ""}
                    </p>
                  </div>
                </div>
                {u.is_sede && (
                  <span className="badge badge-orange">Sede</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
