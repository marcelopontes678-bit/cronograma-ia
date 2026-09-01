"use client";
import { useEffect, useState } from "react";
import { api, extractErrorMessage } from "@/lib/api";
import { PreferenciasGlobaisConfig } from "@/lib/types";

const CAMPOS_TEXTUAL_JSON: Array<keyof PreferenciasGlobaisConfig> = [
  "espessuras",
  "ferragens",
  "regra_apoio_por_ambiente",
  "faixas_dobradicas_por_altura",
  "profundidade_padrao_por_tipo_mm",
];

export default function PreferenciasOrcamentoPage() {
  const [config, setConfig] = useState<PreferenciasGlobaisConfig | null>(null);
  const [jsonAvancado, setJsonAvancado] = useState("");
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState(false);

  useEffect(() => {
    api
      .get("/orcamentos/preferencias")
      .then((r) => {
        setConfig(r.data.configuracao);
        setJsonAvancado(
          JSON.stringify(pick(r.data.configuracao, CAMPOS_TEXTUAL_JSON), null, 2)
        );
      })
      .catch((e) => setErro(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  const salvar = async () => {
    if (!config) return;
    setErro("");
    setSucesso(false);

    let avancado: Record<string, unknown>;
    try {
      avancado = JSON.parse(jsonAvancado);
    } catch {
      setErro("JSON avançado inválido -- confira a sintaxe antes de salvar.");
      return;
    }

    setSalvando(true);
    try {
      const r = await api.put("/orcamentos/preferencias", { ...config, ...avancado });
      setConfig(r.data.configuracao);
      setSucesso(true);
    } catch (e) {
      setErro(extractErrorMessage(e));
    } finally {
      setSalvando(false);
    }
  };

  if (loading) return <p className="text-gray-500">Carregando...</p>;
  if (!config) return <p className="text-red-400">{erro}</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-1">Preferências de orçamento</h1>
      <p className="text-gray-500 text-sm mb-6">
        Diretrizes padrão da fábrica usadas pelo agente MARC para inferir o que o desenho não
        especifica.
      </p>

      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1 text-gray-300">Método de união</label>
            <select
              value={config.metodo_uniao}
              onChange={(e) => setConfig({ ...config, metodo_uniao: e.target.value })}
              className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
            >
              <option value="cavilha">Cavilha</option>
              <option value="minifix">Minifix</option>
              <option value="vb35">VB35</option>
              <option value="parafuso_direto">Parafuso direto</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1 text-gray-300">Fixação do fundo</label>
            <select
              value={config.fixacao_fundo}
              onChange={(e) => setConfig({ ...config, fixacao_fundo: e.target.value })}
              className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
            >
              <option value="encaixado_em_rebaixo">Encaixado em rebaixo</option>
              <option value="parafusado_por_tras">Parafusado por trás</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm mb-1 text-gray-300">Acabamento interno padrão</label>
          <input
            value={config.acabamento_interno_padrao}
            onChange={(e) => setConfig({ ...config, acabamento_interno_padrao: e.target.value })}
            className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={config.regra_fundo_exposto_forca_cor_caixaria}
            onChange={(e) =>
              setConfig({ ...config, regra_fundo_exposto_forca_cor_caixaria: e.target.checked })
            }
            className="accent-brand-500"
          />
          Em cristaleiras com vidro/nicho aberto, forçar o fundo na cor da caixaria
        </label>

        <div>
          <label className="block text-sm mb-1 text-gray-300">
            Configuração avançada (JSON){" "}
            <span className="text-gray-600">
              — espessuras, ferragens, apoio por ambiente, dobradiças por altura
            </span>
          </label>
          <textarea
            value={jsonAvancado}
            onChange={(e) => setJsonAvancado(e.target.value)}
            rows={12}
            className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg px-4 py-3 font-mono text-xs focus:outline-none focus:border-brand-500"
            spellCheck={false}
          />
        </div>

        {erro && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
            {erro}
          </div>
        )}
        {sucesso && (
          <div className="bg-green-900/20 border border-green-800 rounded-lg px-4 py-3 text-green-300 text-sm">
            Preferências salvas.
          </div>
        )}

        <button
          onClick={salvar}
          disabled={salvando}
          className="bg-brand-500 text-black font-semibold px-6 py-3 rounded-lg hover:bg-brand-600 transition disabled:opacity-50"
        >
          {salvando ? "Salvando..." : "Salvar preferências"}
        </button>
      </div>
    </div>
  );
}

function pick<T extends object, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  const out = {} as Pick<T, K>;
  for (const k of keys) out[k] = obj[k];
  return out;
}
