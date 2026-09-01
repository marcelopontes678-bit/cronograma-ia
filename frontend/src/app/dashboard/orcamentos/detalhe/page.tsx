"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, extractErrorMessage } from "@/lib/api";
import { Modulo, OrcamentoJob, OrcamentoResponse } from "@/lib/types";
import { PaginaComOverlay } from "@/components/orcamento/PaginaComOverlay";

// Rota estatica (nao [jobId] dinamico de arquivo) lendo o id via
// query string (?job=...) de proposito: o @cloudflare/next-on-pages
// (adapter deprecated, ver README) nao consegue resolver em runtime o
// modulo de uma Edge Function cujo nome de arquivo tem colchetes --
// "No such module .../[jobId].func.js" mesmo o arquivo existindo no
// bundle (bug real reproduzido com wrangler dev, nao teorico). Uma
// rota estatica com query string evita depender desse caminho quebrado
// do adapter por completo.

const LIMIAR_CONFIANCA = 0.7;

const STATUS_LABEL: Record<string, string> = {
  processando: "Processando",
  aguardando_revisao: "Aguardando revisão",
  confirmado: "Confirmado",
  erro: "Erro",
};

function todosModulos(job: OrcamentoJob): { ambiente: string; modulo: Modulo }[] {
  return job.ambientes.flatMap((a) => a.modulos.map((m) => ({ ambiente: a.nome_ambiente, modulo: m })));
}

export default function OrcamentoJobPage() {
  return (
    <Suspense fallback={<p className="text-gray-500">Carregando...</p>}>
      <OrcamentoJobPageInner />
    </Suspense>
  );
}

function OrcamentoJobPageInner() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job") ?? "";

  const [job, setJob] = useState<OrcamentoJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [moduloSelecionado, setModuloSelecionado] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState(false);

  const carregarJob = () => {
    api
      .get(`/orcamentos/jobs/${jobId}`)
      .then((r) => setJob(r.data))
      .catch((e) => setErro(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!jobId) {
      setLoading(false);
      return;
    }
    carregarJob();
    // job em "processando" ainda esta sendo extraido em background --
    // faz poll ate sair desse estado.
    const interval = setInterval(() => {
      api
        .get(`/orcamentos/jobs/${jobId}`)
        .then((r) => {
          setJob(r.data);
          if (r.data.status !== "processando") clearInterval(interval);
        })
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const confirmar = async () => {
    setErro("");
    setConfirmando(true);
    try {
      const r = await api.post(`/orcamentos/jobs/${jobId}/confirmar`);
      setJob(r.data);
    } catch (e) {
      setErro(extractErrorMessage(e));
    } finally {
      setConfirmando(false);
    }
  };

  if (loading) return <p className="text-gray-500">Carregando...</p>;
  if (!job) return <p className="text-red-400">{erro || "Job não encontrado."}</p>;

  const modulos = todosModulos(job);
  const pendentes = modulos.filter(
    ({ modulo }) => modulo.origem === "vision_automatico" && modulo.confianca < LIMIAR_CONFIANCA
  );
  const selecionado = modulos.find(({ modulo }) => modulo.id === moduloSelecionado)?.modulo;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{job.arquivo_origem}</h1>
          <p className="text-gray-500 text-sm mt-1">Status: {STATUS_LABEL[job.status] ?? job.status}</p>
        </div>
        {job.status === "aguardando_revisao" && (
          <button
            onClick={confirmar}
            disabled={confirmando || pendentes.length > 0}
            title={
              pendentes.length > 0
                ? `Corrija ${pendentes.length} módulo(s) de baixa confiança antes de confirmar`
                : undefined
            }
            className="bg-brand-500 text-black text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-600 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {confirmando ? "Confirmando..." : "Confirmar orçamento"}
          </button>
        )}
      </div>

      {erro && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm mb-6">
          {erro}
        </div>
      )}

      {pendentes.length > 0 && job.status === "aguardando_revisao" && (
        <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg px-4 py-3 text-yellow-300 text-sm mb-6">
          {pendentes.length} módulo(s) com confiança abaixo de {Math.round(LIMIAR_CONFIANCA * 100)}% precisam de
          revisão antes de confirmar.
        </div>
      )}

      {job.avisos.length > 0 && (
        <details className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 mb-6">
          <summary className="text-sm text-gray-400 cursor-pointer">
            {job.avisos.length} aviso(s) da extração
          </summary>
          <ul className="mt-3 space-y-1.5 text-xs text-gray-500 list-disc list-inside">
            {job.avisos.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </details>
      )}

      {job.status === "processando" ? (
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-12 text-center text-gray-500">
          Extraindo módulos via Claude Vision... esta página atualiza sozinha.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4">
            {job.ambientes.map((ambiente) => (
              <div key={ambiente.nome_ambiente}>
                <h2 className="text-sm font-semibold text-gray-400 mb-2">{ambiente.nome_ambiente}</h2>
                <div className="space-y-2">
                  {ambiente.modulos.map((modulo) => (
                    <ModuloCard
                      key={modulo.id}
                      jobId={jobId}
                      modulo={modulo}
                      selecionado={modulo.id === moduloSelecionado}
                      onSelecionar={() => setModuloSelecionado(modulo.id)}
                      onAtualizado={(m) => {
                        setJob((prev) =>
                          prev
                            ? {
                                ...prev,
                                ambientes: prev.ambientes.map((a) => ({
                                  ...a,
                                  modulos: a.modulos.map((mm) => (mm.id === m.id ? m : mm)),
                                })),
                              }
                            : prev
                        );
                      }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="sticky top-8 self-start">
            {selecionado ? (
              <PaginaComOverlay
                jobId={jobId}
                paginaNumero={selecionado.auditoria_visual.pagina_pdf}
                boundingBox={selecionado.auditoria_visual.bounding_box}
              />
            ) : (
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-12 text-center text-gray-500 text-sm">
                Selecione um módulo para ver a posição no desenho.
              </div>
            )}
          </div>
        </div>
      )}

      {job.status === "confirmado" && <PainelOrcamento jobId={jobId} />}
    </div>
  );
}

function ModuloCard({
  jobId,
  modulo,
  selecionado,
  onSelecionar,
  onAtualizado,
}: {
  jobId: string;
  modulo: Modulo;
  selecionado: boolean;
  onSelecionar: () => void;
  onAtualizado: (m: Modulo) => void;
}) {
  const [editando, setEditando] = useState(false);
  const [largura, setLargura] = useState(modulo.dimensoes.largura_mm ?? "");
  const [altura, setAltura] = useState(modulo.dimensoes.altura_mm ?? "");
  const [profundidade, setProfundidade] = useState(modulo.dimensoes.profundidade_mm ?? "");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const baixaConfianca = modulo.origem === "vision_automatico" && modulo.confianca < LIMIAR_CONFIANCA;

  return (
    <div
      onClick={onSelecionar}
      className={`bg-[#1a1a1a] border rounded-lg px-4 py-3 cursor-pointer transition ${
        selecionado ? "border-brand-500" : "border-[#2a2a2a] hover:border-[#444]"
      }`}
    >
      <div className="flex items-center justify-between">
        <p className="font-medium text-sm">{modulo.nome}</p>
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            baixaConfianca ? "text-red-300 bg-red-900/40" : "text-green-300 bg-green-900/40"
          }`}
        >
          {Math.round(modulo.confianca * 100)}%
        </span>
      </div>
      <p className="text-gray-500 text-xs mt-1">
        {modulo.dimensoes.largura_mm ?? "?"} × {modulo.dimensoes.altura_mm ?? "?"} ×{" "}
        {modulo.dimensoes.profundidade_mm ?? "?"} mm · {modulo.especificacoes_materiais.caixaria}
      </p>

      {!editando ? (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setEditando(true);
          }}
          className="text-brand-500 text-xs mt-2 hover:underline"
        >
          Corrigir
        </button>
      ) : (
        <div onClick={(e) => e.stopPropagation()} className="mt-3 space-y-2">
          <div className="grid grid-cols-3 gap-2">
            <input
              type="number"
              value={largura}
              onChange={(e) => setLargura(e.target.value)}
              placeholder="Largura"
              className="bg-[#111] border border-[#2a2a2a] rounded px-2 py-1.5 text-xs w-full"
            />
            <input
              type="number"
              value={altura}
              onChange={(e) => setAltura(e.target.value)}
              placeholder="Altura"
              className="bg-[#111] border border-[#2a2a2a] rounded px-2 py-1.5 text-xs w-full"
            />
            <input
              type="number"
              value={profundidade}
              onChange={(e) => setProfundidade(e.target.value)}
              placeholder="Profund."
              className="bg-[#111] border border-[#2a2a2a] rounded px-2 py-1.5 text-xs w-full"
            />
          </div>
          {erro && <p className="text-red-400 text-xs">{erro}</p>}
          <div className="flex gap-2">
            <button
              disabled={salvando}
              onClick={async () => {
                setErro("");
                setSalvando(true);
                try {
                  const r = await api.patch(`/orcamentos/jobs/${jobId}/modulos/${modulo.id}`, {
                    dimensoes: {
                      largura_mm: largura === "" ? null : Number(largura),
                      altura_mm: altura === "" ? null : Number(altura),
                      profundidade_mm: profundidade === "" ? null : Number(profundidade),
                    },
                    confianca: 1.0,
                  });
                  onAtualizado(r.data);
                  setEditando(false);
                } catch (e) {
                  setErro(extractErrorMessage(e));
                } finally {
                  setSalvando(false);
                }
              }}
              className="bg-brand-500 text-black text-xs font-semibold px-3 py-1.5 rounded hover:bg-brand-600 transition disabled:opacity-50"
            >
              {salvando ? "Salvando..." : "Salvar e confirmar módulo"}
            </button>
            <button
              onClick={() => setEditando(false)}
              className="text-gray-500 text-xs px-3 py-1.5 hover:text-white transition"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PainelOrcamento({ jobId }: { jobId: string }) {
  const [faturamento, setFaturamento] = useState("100000");
  const [custoHora, setCustoHora] = useState("0");
  const [horas, setHoras] = useState("0");
  const [fatorArea, setFatorArea] = useState("");
  const [resultado, setResultado] = useState<OrcamentoResponse | null>(null);
  const [erro, setErro] = useState("");
  const [gerando, setGerando] = useState(false);

  const gerar = async () => {
    setErro("");
    setGerando(true);
    setResultado(null);
    try {
      const r = await api.post(
        `/orcamentos?job_id=${jobId}`,
        {
          faturamento_acumulado: Number(faturamento),
          custo_hora_mao_de_obra: Number(custoHora),
          horas_estimadas: Number(horas),
          fator_area_frontal_para_chapa: fatorArea === "" ? null : Number(fatorArea),
        }
      );
      setResultado(r.data);
    } catch (e) {
      setErro(extractErrorMessage(e));
    } finally {
      setGerando(false);
    }
  };

  return (
    <div className="mt-8 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Gerar orçamento</h2>
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div>
          <label className="block text-xs mb-1 text-gray-400">Faturamento acumulado</label>
          <input
            type="number"
            value={faturamento}
            onChange={(e) => setFaturamento(e.target.value)}
            className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs mb-1 text-gray-400">Custo/hora mão de obra</label>
          <input
            type="number"
            value={custoHora}
            onChange={(e) => setCustoHora(e.target.value)}
            className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs mb-1 text-gray-400">Horas estimadas</label>
          <input
            type="number"
            value={horas}
            onChange={(e) => setHoras(e.target.value)}
            className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs mb-1 text-gray-400">
            Fator área frontal→chapa <span className="text-gray-600">(opcional)</span>
          </label>
          <input
            type="number"
            value={fatorArea}
            onChange={(e) => setFatorArea(e.target.value)}
            placeholder="sem isso, custo de chapa fica pendente"
            className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm"
          />
        </div>
      </div>

      <button
        onClick={gerar}
        disabled={gerando}
        className="bg-brand-500 text-black text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-600 transition disabled:opacity-50"
      >
        {gerando ? "Calculando..." : "Calcular"}
      </button>

      {erro && <p className="text-red-400 text-sm mt-4">{erro}</p>}

      {resultado && (
        <div className="mt-6 grid grid-cols-2 gap-6">
          <div className="space-y-2 text-sm">
            <p className="flex justify-between">
              <span className="text-gray-400">Custo material</span>
              <span>R$ {resultado.custo_material_total.toFixed(2)}</span>
            </p>
            <p className="flex justify-between">
              <span className="text-gray-400">Preço de venda (material)</span>
              <span>R$ {resultado.preco_venda_material.toFixed(2)}</span>
            </p>
            <p className="flex justify-between">
              <span className="text-gray-400">Mão de obra</span>
              <span>R$ {resultado.custo_mao_de_obra.toFixed(2)}</span>
            </p>
            <p className="flex justify-between font-semibold text-brand-500 border-t border-[#2a2a2a] pt-2">
              <span>Total</span>
              <span>R$ {resultado.total.toFixed(2)}</span>
            </p>
          </div>
          {(resultado.avisos.length > 0 || resultado.itens_pendentes.length > 0) && (
            <div className="text-xs text-gray-500 space-y-1">
              {resultado.avisos.map((a, i) => (
                <p key={i}>⚠ {a}</p>
              ))}
              {resultado.itens_pendentes.map((it, i) => (
                <p key={i}>
                  ⚠ {it.descricao} — {it.motivo}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
