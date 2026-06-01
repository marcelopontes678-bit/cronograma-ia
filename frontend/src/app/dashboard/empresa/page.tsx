"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Empresa } from "@/lib/types";

const TIPO_LABEL = {
  fabrica: "Fábrica",
  centro_distribuicao: "Centro de Distribuição",
  escritorio: "Escritório",
};

export default function EmpresaPage() {
  const { user } = useAuth();
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api
      .get(`/empresas/${user.empresa_id}`)
      .then((r) => setEmpresa(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <p className="text-gray-500">Carregando...</p>;
  if (!empresa) return <p className="text-red-400">Empresa não encontrada.</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Empresa</h1>

      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6 space-y-4">
        <div>
          <p className="text-gray-500 text-xs">Razão Social</p>
          <p className="font-medium">{empresa.nome}</p>
        </div>
        {empresa.nome_fantasia && (
          <div>
            <p className="text-gray-500 text-xs">Nome Fantasia</p>
            <p className="font-medium">{empresa.nome_fantasia}</p>
          </div>
        )}
        <div>
          <p className="text-gray-500 text-xs">CNPJ</p>
          <p className="font-medium">{empresa.cnpj}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">E-mail</p>
          <p className="font-medium">{empresa.email}</p>
        </div>
        {empresa.cidade && (
          <div>
            <p className="text-gray-500 text-xs">Localização</p>
            <p className="font-medium">
              {empresa.cidade}
              {empresa.estado ? ` — ${empresa.estado}` : ""}
            </p>
          </div>
        )}
      </div>

      <h2 className="text-lg font-semibold mt-8 mb-4">Unidades</h2>
      <div className="space-y-3">
        {empresa.unidades.map((u) => (
          <div
            key={u.id}
            className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl px-5 py-4 flex items-center justify-between"
          >
            <div>
              <p className="font-medium">{u.nome}</p>
              <p className="text-gray-500 text-sm">
                {TIPO_LABEL[u.tipo as keyof typeof TIPO_LABEL]}
                {u.codigo ? ` · ${u.codigo}` : ""}
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
    </div>
  );
}
