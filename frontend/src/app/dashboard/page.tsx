"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

interface Counters {
  projetos: number;
  usuarios: number;
  unidades: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [counters, setCounters] = useState<Counters>({
    projetos: 0,
    usuarios: 0,
    unidades: 0,
  });

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get(`/projetos?limit=1`),
      api.get(`/usuarios?limit=1`),
      api.get(`/empresas/${user.empresa_id}/unidades`),
    ])
      .then(([p, u, un]) => {
        setCounters({
          projetos: p.data.length,
          usuarios: u.data.length,
          unidades: un.data.length,
        });
      })
      .catch(() => {});
  }, [user]);

  const cards = [
    { label: "Projetos ativos", value: counters.projetos, color: "text-brand-500" },
    { label: "Usuários", value: counters.usuarios, color: "text-blue-400" },
    { label: "Unidades", value: counters.unidades, color: "text-green-400" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-500 mb-8">Bem-vindo, {user?.nome}</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {cards.map((c) => (
          <div
            key={c.label}
            className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6"
          >
            <p className="text-gray-500 text-sm">{c.label}</p>
            <p className={`text-4xl font-bold mt-2 ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {user?.must_change_password && (
        <div className="mt-6 bg-yellow-900/30 border border-yellow-700 rounded-xl px-5 py-4 text-yellow-300 text-sm">
          Por segurança, altere sua senha no primeiro acesso em Usuários → seu perfil.
        </div>
      )}
    </div>
  );
}
