"use client";
import { useState } from "react";
import { api, extractErrorMessage } from "@/lib/api";
import { PlanoCorte } from "@/lib/types";

const CORES = [
  "#F04C23", "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
  "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
];

function corDaPeca(ref: string): string {
  let h = 0;
  for (let i = 0; i < ref.length; i++) h = (h * 31 + ref.charCodeAt(i)) >>> 0;
  return CORES[h % CORES.length];
}

function ChapaSvg({
  chapa, comp, larg,
}: {
  chapa: PlanoCorte["materiais"][0]["chapas"][0];
  comp: number;
  larg: number;
}) {
  const W = 560;
  const escala = W / comp;
  const H = larg * escala;

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
         className="rounded-lg" style={{ background: "#FBF7F2", border: "1.5px solid #E8DFD3" }}>
      {chapa.pecas.map((p, i) => {
        const x = p.x_mm * escala;
        const y = p.y_mm * escala;
        const w = p.comprimento_mm * escala;
        const h = p.largura_mm * escala;
        const cor = corDaPeca(p.ref);
        const mostraTexto = w > 46 && h > 15;
        return (
          <g key={`${p.ref}-${i}`}>
            <rect x={x + 1} y={y + 1} width={Math.max(w - 2, 1)} height={Math.max(h - 2, 1)}
                  rx={2} fill={cor} fillOpacity={0.16} stroke={cor} strokeWidth={1.2} />
            {mostraTexto && (
              <text x={x + w / 2} y={y + h / 2} textAnchor="middle" dominantBaseline="central"
                    fontSize={Math.min(10, h * 0.4)} fill={cor} fontWeight={600}>
                {p.comprimento_mm}×{p.largura_mm}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

export function PlanoCorteViewer({ projetoId }: { projetoId: string }) {
  const [plano, setPlano] = useState<PlanoCorte | null>(null);
  const [kerf, setKerf] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const gerar = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/projetos/${projetoId}/plano-corte?kerf_mm=${kerf}`);
      setPlano(data);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-5 mt-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold" style={{ color: "#1C1C2E" }}>Plano de Corte</h3>
          <p className="text-xs mt-0.5" style={{ color: "#9CA3AF" }}>
            Otimização do aproveitamento das chapas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs" style={{ color: "#6B7280" }}>Serra (kerf)</label>
          <select value={kerf} onChange={e => setKerf(Number(e.target.value))}
                  className="rounded-lg px-2 py-1.5 text-xs outline-none"
                  style={{ background: "#F5F6FA", border: "1.5px solid #E8EBF0", color: "#1C1C2E" }}>
            {[0, 2, 3, 4, 5].map(k => <option key={k} value={k}>{k} mm</option>)}
          </select>
          <button onClick={gerar} disabled={loading}
                  className="flex items-center gap-1.5 text-sm font-semibold px-4 py-2 rounded-xl text-white"
                  style={{ background: "#F04C23", boxShadow: "0 4px 12px rgba(240,76,35,.25)", opacity: loading ? 0.7 : 1 }}>
            {loading && <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />}
            {plano ? "Recalcular" : "Gerar plano"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl px-4 py-2.5 text-sm mb-3"
             style={{ background: "#FEF2F2", color: "#DC2626", border: "1px solid #FECACA" }}>
          {error}
        </div>
      )}

      {!plano ? (
        <div className="flex flex-col items-center py-10 gap-2">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center" style={{ background: "#FEF0EC" }}>
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="#F04C23" strokeWidth={1.5}>
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="3" y1="12" x2="15" y2="12" /><line x1="15" y1="3" x2="15" y2="21" />
              <line x1="9" y1="12" x2="9" y2="21" />
            </svg>
          </div>
          <p className="text-sm" style={{ color: "#9CA3AF" }}>
            Clique em &quot;Gerar plano&quot; para calcular o corte das chapas
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {plano.pecas_ignoradas.length > 0 && (
            <div className="rounded-xl px-4 py-3 text-xs space-y-1"
                 style={{ background: "#FFFBEB", color: "#B45309", border: "1px solid #FDE68A" }}>
              <p className="font-semibold">Peças fora do plano:</p>
              {plano.pecas_ignoradas.map((p, i) => (
                <p key={i}>• {p.nome} — {p.motivo}</p>
              ))}
            </div>
          )}

          {plano.materiais.length === 0 && (
            <p className="text-sm text-center py-6" style={{ color: "#9CA3AF" }}>
              Nenhuma peça com chapa dimensionada para cortar.
            </p>
          )}

          {plano.materiais.map(mat => (
            <div key={mat.material_id}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-sm font-semibold" style={{ color: "#1C1C2E" }}>{mat.material_nome}</span>
                <span className="badge badge-orange">{mat.total_chapas} chapa{mat.total_chapas !== 1 ? "s" : ""}</span>
                <span className="badge badge-green">{mat.aproveitamento_medio_pct}% aproveitamento</span>
                <span className="text-xs" style={{ color: "#9CA3AF" }}>
                  chapa {mat.chapa_comprimento_mm}×{mat.chapa_largura_mm}mm · kerf {plano.kerf_mm}mm
                </span>
              </div>

              {mat.nao_alocadas.length > 0 && (
                <p className="text-xs mb-2" style={{ color: "#DC2626" }}>
                  Não couberam: {mat.nao_alocadas.join("; ")}
                </p>
              )}

              <div className="flex flex-wrap gap-4">
                {mat.chapas.map(chapa => (
                  <div key={chapa.indice}>
                    <p className="text-xs mb-1.5 font-medium" style={{ color: "#6B7280" }}>
                      Chapa {chapa.indice} — {chapa.aproveitamento_pct}% · {chapa.pecas.length} peça{chapa.pecas.length !== 1 ? "s" : ""}
                    </p>
                    <ChapaSvg chapa={chapa} comp={mat.chapa_comprimento_mm} larg={mat.chapa_largura_mm} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
