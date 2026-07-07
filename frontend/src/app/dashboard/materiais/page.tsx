"use client";
import { useCallback, useEffect, useState } from "react";
import { api, extractErrorMessage } from "@/lib/api";
import { Material, TipoMaterial } from "@/lib/types";
import { Topbar } from "@/components/layout/Topbar";

const TIPO_LABEL: Record<TipoMaterial, string> = {
  chapa: "Chapa",
  fita_borda: "Fita de borda",
  ferragem: "Ferragem",
  outro: "Outro",
};
const TIPO_COLOR: Record<TipoMaterial, string> = {
  chapa: "#F04C23",
  fita_borda: "#3B82F6",
  ferragem: "#10B981",
  outro: "#9CA3AF",
};
const TIPO_BG: Record<TipoMaterial, string> = {
  chapa: "#FEF0EC",
  fita_borda: "#EFF6FF",
  ferragem: "#ECFDF5",
  outro: "#F5F6FA",
};

const inputClass = "w-full rounded-xl px-3 py-2.5 text-sm outline-none";
const inputStyle = { background: "#F9FAFB", border: "1.5px solid #E8EBF0", color: "#1C1C2E" };

export default function MateriaisPage() {
  const [materiais, setMateriais] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    nome: "", codigo: "", tipo: "chapa" as TipoMaterial,
    espessura_mm: "", largura_mm: "", comprimento_mm: "", cor: "", preco_unitario: "",
  });

  const carregar = useCallback(() => {
    api.get("/materiais")
      .then(r => setMateriais(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { carregar(); }, [carregar]);

  const salvar = async () => {
    setError("");
    try {
      await api.post("/materiais", {
        nome: form.nome,
        codigo: form.codigo || null,
        tipo: form.tipo,
        espessura_mm: form.espessura_mm ? Number(form.espessura_mm) : null,
        largura_mm: form.largura_mm ? Number(form.largura_mm) : null,
        comprimento_mm: form.comprimento_mm ? Number(form.comprimento_mm) : null,
        cor: form.cor || null,
        preco_unitario: form.preco_unitario || null,
      });
      setShowForm(false);
      setForm({ nome: "", codigo: "", tipo: "chapa", espessura_mm: "", largura_mm: "", comprimento_mm: "", cor: "", preco_unitario: "" });
      carregar();
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  return (
    <div>
      <Topbar title="Materiais" subtitle="Biblioteca de chapas, fitas e ferragens" />

      <div className="card p-6">
        <div className="flex items-center justify-between mb-5">
          <span className="text-xs px-2.5 py-1 rounded-lg font-medium"
                style={{ background: "#F5F6FA", color: "#9CA3AF" }}>
            {materiais.length} materia{materiais.length !== 1 ? "is" : "l"}
          </span>
          <button
            onClick={() => setShowForm(v => !v)}
            className="flex items-center gap-1.5 text-sm font-semibold px-4 py-2.5 rounded-xl text-white"
            style={{ background: "#F04C23", boxShadow: "0 4px 12px rgba(240,76,35,.25)" }}
          >
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.5}>
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Novo Material
          </button>
        </div>

        {showForm && (
          <div className="rounded-xl p-4 mb-5" style={{ background: "#F9FAFB", border: "1.5px solid #F0F2F8" }}>
            <div className="grid grid-cols-4 gap-3 mb-3">
              <div className="col-span-2">
                <input placeholder="Nome do material *" value={form.nome}
                       onChange={e => setForm(f => ({ ...f, nome: e.target.value }))}
                       className={inputClass} style={inputStyle} />
              </div>
              <input placeholder="Código" value={form.codigo}
                     onChange={e => setForm(f => ({ ...f, codigo: e.target.value }))}
                     className={inputClass} style={inputStyle} />
              <select value={form.tipo}
                      onChange={e => setForm(f => ({ ...f, tipo: e.target.value as TipoMaterial }))}
                      className={inputClass} style={inputStyle}>
                {Object.entries(TIPO_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-5 gap-3 mb-3">
              <input placeholder="Espessura (mm)" type="number" value={form.espessura_mm}
                     onChange={e => setForm(f => ({ ...f, espessura_mm: e.target.value }))}
                     className={inputClass} style={inputStyle} />
              <input placeholder="Largura (mm)" type="number" value={form.largura_mm}
                     onChange={e => setForm(f => ({ ...f, largura_mm: e.target.value }))}
                     className={inputClass} style={inputStyle} />
              <input placeholder="Comprimento (mm)" type="number" value={form.comprimento_mm}
                     onChange={e => setForm(f => ({ ...f, comprimento_mm: e.target.value }))}
                     className={inputClass} style={inputStyle} />
              <input placeholder="Cor" value={form.cor}
                     onChange={e => setForm(f => ({ ...f, cor: e.target.value }))}
                     className={inputClass} style={inputStyle} />
              <input placeholder="Preço (R$)" type="number" step="0.01" value={form.preco_unitario}
                     onChange={e => setForm(f => ({ ...f, preco_unitario: e.target.value }))}
                     className={inputClass} style={inputStyle} />
            </div>
            {error && <p className="text-xs text-red-500 mb-2">{error}</p>}
            <div className="flex gap-2">
              <button onClick={salvar} disabled={!form.nome}
                      className="text-sm font-semibold px-4 py-2 rounded-lg text-white"
                      style={{ background: form.nome ? "#F04C23" : "#F8A78F" }}>
                Salvar
              </button>
              <button onClick={() => setShowForm(false)}
                      className="text-sm font-medium px-4 py-2 rounded-lg"
                      style={{ background: "#F5F6FA", color: "#6B7280", border: "1.5px solid #E8EBF0" }}>
                Cancelar
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-16 text-sm" style={{ color: "#9CA3AF" }}>
            Carregando...
          </div>
        ) : materiais.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-3">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: "#FEF0EC" }}>
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="#F04C23" strokeWidth={1.5}>
                <path d="M12 2l9 4.9v10.2L12 22l-9-4.9V6.9L12 2z" /><path d="M12 22V12M3 6.9l9 5.1 9-5.1" />
              </svg>
            </div>
            <p className="font-medium" style={{ color: "#1C1C2E" }}>Nenhum material cadastrado</p>
            <p className="text-sm" style={{ color: "#9CA3AF" }}>Cadastre chapas, fitas de borda e ferragens</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid #F0F2F8" }}>
                  {["Material", "Código", "Tipo", "Dimensões", "Cor", "Preço", ""].map(h => (
                    <th key={h} className="text-left py-2 pb-3 pr-4 text-xs font-medium" style={{ color: "#9CA3AF" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {materiais.map((m, i) => (
                  <tr key={m.id} style={{ borderBottom: i < materiais.length - 1 ? "1px solid #F0F2F8" : "none" }}>
                    <td className="py-3.5 pr-4 text-sm font-medium" style={{ color: "#1C1C2E" }}>{m.nome}</td>
                    <td className="py-3.5 pr-4 text-xs font-mono" style={{ color: "#9CA3AF" }}>{m.codigo ?? "—"}</td>
                    <td className="py-3.5 pr-4">
                      <span className="badge" style={{ background: TIPO_BG[m.tipo], color: TIPO_COLOR[m.tipo] }}>
                        {TIPO_LABEL[m.tipo]}
                      </span>
                    </td>
                    <td className="py-3.5 pr-4 text-sm" style={{ color: "#6B7280" }}>
                      {[m.espessura_mm && `${m.espessura_mm}mm`,
                        m.largura_mm && m.comprimento_mm && `${m.largura_mm}×${m.comprimento_mm}mm`]
                        .filter(Boolean).join(" · ") || "—"}
                    </td>
                    <td className="py-3.5 pr-4 text-sm" style={{ color: "#6B7280" }}>{m.cor ?? "—"}</td>
                    <td className="py-3.5 pr-4 text-sm font-medium" style={{ color: "#1C1C2E" }}>
                      {m.preco_unitario ? `R$ ${Number(m.preco_unitario).toFixed(2)}` : "—"}
                    </td>
                    <td className="py-3.5" />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
