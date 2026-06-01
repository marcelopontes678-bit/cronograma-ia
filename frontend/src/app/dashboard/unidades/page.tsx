"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Unidade, TipoUnidade } from "@/lib/types";

const TIPO_LABEL: Record<TipoUnidade, string> = {
  fabrica: "Fábrica",
  centro_distribuicao: "Centro de Distribuição",
  escritorio: "Escritório",
};

export default function UnidadesPage() {
  const { user } = useAuth();
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api
      .get(`/empresas/${user.empresa_id}/unidades`)
      .then((r) => setUnidades(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Unidades</h1>

      {loading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : (
        <div className="space-y-3">
          {unidades.map((u) => (
            <div
              key={u.id}
              className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl px-5 py-4 flex items-center justify-between"
            >
              <div>
                <p className="font-medium">{u.nome}</p>
                <p className="text-gray-500 text-sm">
                  {TIPO_LABEL[u.tipo]}
                  {u.codigo ? ` · ${u.codigo}` : ""}
                  {u.cidade ? ` · ${u.cidade}${u.estado ? `/${u.estado}` : ""}` : ""}
                </p>
              </div>
              {u.is_sede && (
                <span className="text-xs bg-brand-500/10 text-brand-500 px-2.5 py-1 rounded-full">
                  Sede
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
