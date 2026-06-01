"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Unidade, TipoUnidade } from "@/lib/types";
import { Topbar } from "@/components/layout/Topbar";

const TIPO_LABEL: Record<TipoUnidade, string> = {
  fabrica: "Fábrica",
  centro_distribuicao: "Centro de Distribuição",
  escritorio: "Escritório",
};
const TIPO_COLOR: Record<TipoUnidade, string> = {
  fabrica: "#F04C23",
  centro_distribuicao: "#3B82F6",
  escritorio: "#10B981",
};
const TIPO_BG: Record<TipoUnidade, string> = {
  fabrica: "#FEF0EC",
  centro_distribuicao: "#EFF6FF",
  escritorio: "#ECFDF5",
};

export default function UnidadesPage() {
  const { user } = useAuth();
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api.get(`/empresas/${user.empresa_id}/unidades`)
      .then(r => setUnidades(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  return (
    <div>
      <Topbar title="Unidades" subtitle="Fábricas, centros de distribuição e escritórios" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 flex items-center justify-center py-16 text-sm" style={{ color: "#9CA3AF" }}>
            Carregando...
          </div>
        ) : unidades.map(u => (
          <div key={u.id} className="card p-5">
            <div className="flex items-start justify-between mb-4">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center"
                   style={{ background: TIPO_BG[u.tipo] }}>
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24"
                     stroke={TIPO_COLOR[u.tipo]} strokeWidth={1.8}>
                  <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" />
                </svg>
              </div>
              {u.is_sede && <span className="badge badge-orange">Sede</span>}
            </div>

            <h3 className="font-semibold mb-1" style={{ color: "#1C1C2E" }}>{u.nome}</h3>

            <div className="flex items-center gap-2 mb-3">
              <span className="badge" style={{ background: TIPO_BG[u.tipo], color: TIPO_COLOR[u.tipo] }}>
                {TIPO_LABEL[u.tipo]}
              </span>
              {u.codigo && (
                <span className="badge badge-gray">{u.codigo}</span>
              )}
            </div>

            {(u.cidade || u.estado) && (
              <div className="flex items-center gap-1.5 text-xs" style={{ color: "#9CA3AF" }}>
                <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {[u.cidade, u.estado].filter(Boolean).join(" / ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
