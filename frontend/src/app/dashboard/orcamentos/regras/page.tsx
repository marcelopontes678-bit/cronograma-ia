"use client";
import { useEffect, useState } from "react";
import { api, extractErrorMessage } from "@/lib/api";
import { RegraAprendida } from "@/lib/types";

export default function RegrasAprendidasPage() {
  const [regras, setRegras] = useState<RegraAprendida[]>([]);
  const [loading, setLoading] = useState(true);
  const [instrucao, setInstrucao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  const carregar = () => {
    api
      .get("/orcamentos/regras")
      .then((r) => setRegras(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(carregar, []);

  const enviarFeedback = async () => {
    if (!instrucao.trim()) return;
    setErro("");
    setEnviando(true);
    try {
      await api.post("/orcamentos/feedback", { instrucao });
      setInstrucao("");
      carregar();
    } catch (e) {
      setErro(extractErrorMessage(e));
    } finally {
      setEnviando(false);
    }
  };

  const desativar = async (id: string) => {
    try {
      await api.delete(`/orcamentos/regras/${id}`);
      carregar();
    } catch (e) {
      setErro(extractErrorMessage(e));
    }
  };

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-1">Regras aprendidas</h1>
      <p className="text-gray-500 text-sm mb-6">
        Corrija o MARC em linguagem natural — a instrução é normalizada e passa a ser aplicada
        automaticamente nas próximas extrações.
      </p>

      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-5 mb-8">
        <textarea
          value={instrucao}
          onChange={(e) => setInstrucao(e.target.value)}
          rows={3}
          placeholder='Ex: "Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa"'
          className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-brand-500 resize-none"
        />
        {erro && <p className="text-red-400 text-xs mt-2">{erro}</p>}
        <button
          onClick={enviarFeedback}
          disabled={enviando || !instrucao.trim()}
          className="mt-3 bg-brand-500 text-black text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-600 transition disabled:opacity-50"
        >
          {enviando ? "Enviando..." : "Registrar correção"}
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : regras.length === 0 ? (
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-12 text-center text-gray-500">
          Nenhuma regra aprendida ainda.
        </div>
      ) : (
        <div className="space-y-3">
          {regras.map((r) => (
            <div
              key={r.id}
              className={`bg-[#1a1a1a] border rounded-xl px-5 py-4 ${
                r.is_active ? "border-[#2a2a2a]" : "border-[#2a2a2a] opacity-50"
              }`}
            >
              <p className="text-sm">{r.regra_normalizada}</p>
              <p className="text-gray-500 text-xs mt-1">Original: "{r.instrucao_original}"</p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-gray-600 text-xs">
                  {new Date(r.created_at).toLocaleDateString("pt-BR")}
                </span>
                {r.is_active ? (
                  <button
                    onClick={() => desativar(r.id)}
                    className="text-red-400 text-xs hover:underline"
                  >
                    Desativar
                  </button>
                ) : (
                  <span className="text-gray-600 text-xs">Inativa</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
