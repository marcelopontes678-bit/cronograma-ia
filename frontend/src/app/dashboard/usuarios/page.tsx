"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Usuario, RoleUsuario } from "@/lib/types";

const ROLE_LABEL: Record<RoleUsuario, string> = {
  admin: "Admin",
  gerente: "Gerente",
  operador: "Operador",
  visualizador: "Visualizador",
};

const ROLE_COLOR: Record<RoleUsuario, string> = {
  admin: "text-red-300 bg-red-900/40",
  gerente: "text-orange-300 bg-orange-900/40",
  operador: "text-blue-300 bg-blue-900/40",
  visualizador: "text-gray-300 bg-gray-800",
};

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/usuarios")
      .then((r) => setUsuarios(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Usuários</h1>
      </div>

      {loading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : (
        <div className="space-y-3">
          {usuarios.map((u) => (
            <div
              key={u.id}
              className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl px-5 py-4 flex items-center justify-between"
            >
              <div>
                <p className="font-medium">{u.nome}</p>
                <p className="text-gray-500 text-sm">{u.email}</p>
              </div>
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full ${ROLE_COLOR[u.role]}`}
              >
                {ROLE_LABEL[u.role]}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
