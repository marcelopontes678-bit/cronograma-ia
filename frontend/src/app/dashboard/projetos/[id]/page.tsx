"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, extractErrorMessage } from "@/lib/api";
import { Ambiente, EngenhariaResumo, Material, Modulo, Projeto } from "@/lib/types";
import { Topbar } from "@/components/layout/Topbar";
import { PlanoCorteViewer } from "@/components/engenharia/PlanoCorteViewer";

const inputClass = "rounded-lg px-3 py-2 text-sm outline-none";
const inputStyle = { background: "#FFFFFF", border: "1.5px solid #E8EBF0", color: "#1C1C2E" };

function BotaoMini({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
            className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg"
            style={{ background: "#FEF0EC", color: "#F04C23" }}>
      <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
      </svg>
      {children}
    </button>
  );
}

export default function ProjetoDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const [projeto, setProjeto] = useState<Projeto | null>(null);
  const [resumo, setResumo] = useState<EngenhariaResumo | null>(null);
  const [materiais, setMateriais] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Forms inline
  const [novoAmbiente, setNovoAmbiente] = useState("");
  const [moduloForm, setModuloForm] = useState<{ ambienteId: string; nome: string } | null>(null);
  const [pecaForm, setPecaForm] = useState<{
    moduloId: string; nome: string; comprimento: string; largura: string;
    quantidade: string; materialId: string;
  } | null>(null);

  const carregar = useCallback(() => {
    Promise.all([
      api.get(`/projetos/${id}`),
      api.get(`/projetos/${id}/engenharia`),
      api.get("/materiais"),
    ])
      .then(([p, e, m]) => { setProjeto(p.data); setResumo(e.data); setMateriais(m.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => { carregar(); }, [carregar]);

  const acao = async (fn: () => Promise<unknown>) => {
    setError("");
    try { await fn(); carregar(); }
    catch (e) { setError(extractErrorMessage(e)); }
  };

  const criarAmbiente = () => acao(async () => {
    await api.post(`/projetos/${id}/ambientes`, { nome: novoAmbiente });
    setNovoAmbiente("");
  });

  const criarModulo = () => moduloForm && acao(async () => {
    await api.post(`/ambientes/${moduloForm.ambienteId}/modulos`, { nome: moduloForm.nome });
    setModuloForm(null);
  });

  const criarPeca = () => pecaForm && acao(async () => {
    await api.post(`/modulos/${pecaForm.moduloId}/pecas`, {
      nome: pecaForm.nome,
      comprimento_mm: Number(pecaForm.comprimento),
      largura_mm: Number(pecaForm.largura),
      quantidade: Number(pecaForm.quantidade) || 1,
      material_id: pecaForm.materialId || null,
    });
    setPecaForm(null);
  });

  if (loading) return (
    <div>
      <Topbar title="Projeto" />
      <div className="flex items-center justify-center py-20 text-sm" style={{ color: "#9CA3AF" }}>Carregando...</div>
    </div>
  );

  if (!projeto) return (
    <div>
      <Topbar title="Projeto" />
      <div className="card p-12 text-center text-sm" style={{ color: "#EF4444" }}>Projeto não encontrado.</div>
    </div>
  );

  return (
    <div>
      <Topbar title={projeto.nome} subtitle={`${projeto.codigo}${projeto.cliente_nome ? ` · ${projeto.cliente_nome}` : ""}`} />

      {/* Resumo de engenharia */}
      {resumo && (
        <div className="grid grid-cols-4 gap-4 mb-5">
          <div className="card p-4">
            <p className="text-xs mb-1" style={{ color: "#9CA3AF" }}>Ambientes</p>
            <p className="text-2xl font-bold" style={{ color: "#1C1C2E" }}>{resumo.total_ambientes}</p>
          </div>
          <div className="card p-4">
            <p className="text-xs mb-1" style={{ color: "#9CA3AF" }}>Módulos</p>
            <p className="text-2xl font-bold" style={{ color: "#1C1C2E" }}>{resumo.total_modulos}</p>
          </div>
          <div className="card p-4">
            <p className="text-xs mb-1" style={{ color: "#9CA3AF" }}>Peças</p>
            <p className="text-2xl font-bold" style={{ color: "#1C1C2E" }}>{resumo.total_pecas}</p>
          </div>
          <div className="card p-4" style={{ background: "#F04C23", borderColor: "#F04C23" }}>
            <p className="text-xs mb-1 text-white/70">Área de chapa</p>
            <p className="text-2xl font-bold text-white">
              {resumo.materiais.reduce((s, m) => s + m.area_m2, 0).toFixed(2)} m²
            </p>
          </div>
        </div>
      )}

      {/* Consumo por material */}
      {resumo && resumo.materiais.length > 0 && (
        <div className="card p-5 mb-5">
          <h3 className="text-sm font-bold mb-3" style={{ color: "#1C1C2E" }}>Consumo por material</h3>
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: "1px solid #F0F2F8" }}>
                {["Material", "Peças", "Área (m²)", "Fita de borda (m)"].map(h => (
                  <th key={h} className="text-left py-1.5 pb-2.5 pr-4 text-xs font-medium" style={{ color: "#9CA3AF" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {resumo.materiais.map((m, i) => (
                <tr key={m.material_id ?? "sem"} style={{ borderBottom: i < resumo.materiais.length - 1 ? "1px solid #F0F2F8" : "none" }}>
                  <td className="py-2.5 pr-4 text-sm font-medium" style={{ color: "#1C1C2E" }}>{m.material_nome}</td>
                  <td className="py-2.5 pr-4 text-sm" style={{ color: "#6B7280" }}>{m.total_pecas}</td>
                  <td className="py-2.5 pr-4 text-sm" style={{ color: "#6B7280" }}>{m.area_m2.toFixed(3)}</td>
                  <td className="py-2.5 pr-4 text-sm" style={{ color: "#6B7280" }}>{m.fita_borda_m.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Árvore de engenharia */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold" style={{ color: "#1C1C2E" }}>Engenharia</h3>
          <div className="flex items-center gap-2">
            <input placeholder="Nome do ambiente (ex: Cozinha)" value={novoAmbiente}
                   onChange={e => setNovoAmbiente(e.target.value)}
                   className={inputClass} style={{ ...inputStyle, width: 240 }} />
            <BotaoMini onClick={criarAmbiente}>Ambiente</BotaoMini>
          </div>
        </div>

        {error && (
          <div className="rounded-xl px-4 py-2.5 text-sm mb-3"
               style={{ background: "#FEF2F2", color: "#DC2626", border: "1px solid #FECACA" }}>
            {error}
          </div>
        )}

        {(!resumo || resumo.ambientes.length === 0) ? (
          <div className="flex flex-col items-center py-12 gap-2">
            <p className="font-medium" style={{ color: "#1C1C2E" }}>Nenhum ambiente ainda</p>
            <p className="text-sm" style={{ color: "#9CA3AF" }}>Comece adicionando um ambiente (Cozinha, Quarto...)</p>
          </div>
        ) : (
          <div className="space-y-4">
            {resumo.ambientes.map((amb: Ambiente) => (
              <div key={amb.id} className="rounded-xl p-4" style={{ background: "#F9FAFB", border: "1.5px solid #F0F2F8" }}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "#FEF0EC" }}>
                      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#F04C23" strokeWidth={2}>
                        <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <span className="font-semibold text-sm" style={{ color: "#1C1C2E" }}>{amb.nome}</span>
                    <span className="text-xs" style={{ color: "#9CA3AF" }}>
                      {amb.modulos.length} módulo{amb.modulos.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <BotaoMini onClick={() => setModuloForm({ ambienteId: amb.id, nome: "" })}>Módulo</BotaoMini>
                </div>

                {moduloForm?.ambienteId === amb.id && (
                  <div className="flex items-center gap-2 mb-3">
                    <input autoFocus placeholder="Nome do módulo (ex: Armário superior 800mm)"
                           value={moduloForm.nome}
                           onChange={e => setModuloForm({ ...moduloForm, nome: e.target.value })}
                           onKeyDown={e => e.key === "Enter" && criarModulo()}
                           className={inputClass} style={{ ...inputStyle, flex: 1 }} />
                    <button onClick={criarModulo} className="text-xs font-semibold px-3 py-2 rounded-lg text-white" style={{ background: "#F04C23" }}>OK</button>
                    <button onClick={() => setModuloForm(null)} className="text-xs px-3 py-2 rounded-lg" style={{ color: "#6B7280" }}>Cancelar</button>
                  </div>
                )}

                <div className="space-y-2">
                  {amb.modulos.map((mod: Modulo) => (
                    <div key={mod.id} className="rounded-lg p-3 bg-white" style={{ border: "1px solid #F0F2F8" }}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium" style={{ color: "#1C1C2E" }}>{mod.nome}</span>
                          {mod.quantidade > 1 && (
                            <span className="badge badge-blue">×{mod.quantidade}</span>
                          )}
                          <span className="text-xs" style={{ color: "#9CA3AF" }}>
                            {mod.pecas.length} peça{mod.pecas.length !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <BotaoMini onClick={() => setPecaForm({
                          moduloId: mod.id, nome: "", comprimento: "", largura: "", quantidade: "1", materialId: "",
                        })}>Peça</BotaoMini>
                      </div>

                      {pecaForm?.moduloId === mod.id && (
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <input autoFocus placeholder="Nome (ex: Lateral)" value={pecaForm.nome}
                                 onChange={e => setPecaForm({ ...pecaForm, nome: e.target.value })}
                                 className={inputClass} style={{ ...inputStyle, width: 160 }} />
                          <input placeholder="Comp. (mm)" type="number" value={pecaForm.comprimento}
                                 onChange={e => setPecaForm({ ...pecaForm, comprimento: e.target.value })}
                                 className={inputClass} style={{ ...inputStyle, width: 110 }} />
                          <input placeholder="Larg. (mm)" type="number" value={pecaForm.largura}
                                 onChange={e => setPecaForm({ ...pecaForm, largura: e.target.value })}
                                 className={inputClass} style={{ ...inputStyle, width: 110 }} />
                          <input placeholder="Qtd" type="number" value={pecaForm.quantidade}
                                 onChange={e => setPecaForm({ ...pecaForm, quantidade: e.target.value })}
                                 className={inputClass} style={{ ...inputStyle, width: 70 }} />
                          <select value={pecaForm.materialId}
                                  onChange={e => setPecaForm({ ...pecaForm, materialId: e.target.value })}
                                  className={inputClass} style={{ ...inputStyle, width: 180 }}>
                            <option value="">Sem material</option>
                            {materiais.map(m => <option key={m.id} value={m.id}>{m.nome}</option>)}
                          </select>
                          <button onClick={criarPeca} className="text-xs font-semibold px-3 py-2 rounded-lg text-white" style={{ background: "#F04C23" }}>OK</button>
                          <button onClick={() => setPecaForm(null)} className="text-xs px-3 py-2 rounded-lg" style={{ color: "#6B7280" }}>Cancelar</button>
                        </div>
                      )}

                      {mod.pecas.length > 0 && (
                        <table className="w-full">
                          <tbody>
                            {mod.pecas.map(p => (
                              <tr key={p.id} style={{ borderTop: "1px solid #F7F8FB" }}>
                                <td className="py-1.5 pr-3 text-xs" style={{ color: "#1C1C2E" }}>{p.nome}</td>
                                <td className="py-1.5 pr-3 text-xs font-mono" style={{ color: "#6B7280" }}>
                                  {p.comprimento_mm}×{p.largura_mm}mm
                                </td>
                                <td className="py-1.5 pr-3 text-xs" style={{ color: "#9CA3AF" }}>×{p.quantidade}</td>
                                <td className="py-1.5 text-xs" style={{ color: "#9CA3AF" }}>
                                  {materiais.find(m => m.id === p.material_id)?.nome ?? "—"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <PlanoCorteViewer projetoId={id} />
    </div>
  );
}
