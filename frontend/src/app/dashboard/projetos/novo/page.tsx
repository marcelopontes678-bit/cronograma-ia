"use client";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { api, extractErrorMessage } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Topbar } from "@/components/layout/Topbar";

const schema = z.object({
  codigo: z.string().min(1, "Código obrigatório"),
  nome: z.string().min(1, "Nome obrigatório"),
  cliente_nome: z.string().optional(),
  data_entrega_prevista: z.string().optional(),
  prioridade: z.coerce.number().min(1).max(5),
  descricao: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1.5" style={{ color: "#374151" }}>{label}</label>
      {children}
      {error && <p className="text-xs mt-1 text-red-500">{error}</p>}
    </div>
  );
}

const inputClass = "w-full rounded-xl px-4 py-3 text-sm outline-none transition";
const inputStyle = { background: "#F9FAFB", border: "1.5px solid #E8EBF0", color: "#1C1C2E" };

export default function NovoProjetoPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { prioridade: 3 },
  });

  const onSubmit = async (data: FormData) => {
    if (!user) return;
    setError("");
    try {
      await api.post("/projetos", {
        ...data,
        empresa_id: user.empresa_id,
        data_entrega_prevista: data.data_entrega_prevista || null,
      });
      router.push("/dashboard/projetos");
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  return (
    <div>
      <Topbar title="Novo Projeto" subtitle="Preencha os dados do projeto" />

      <div className="max-w-2xl">
        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Código *" error={errors.codigo?.message}>
                <input {...register("codigo")} className={inputClass} style={inputStyle}
                       placeholder="OP-2026-001" />
              </Field>
              <Field label="Prioridade">
                <select {...register("prioridade")} className={inputClass} style={inputStyle}>
                  <option value={1}>1 — Urgente</option>
                  <option value={2}>2 — Alta</option>
                  <option value={3}>3 — Normal</option>
                  <option value={4}>4 — Baixa</option>
                  <option value={5}>5 — Mínima</option>
                </select>
              </Field>
            </div>

            <Field label="Nome *" error={errors.nome?.message}>
              <input {...register("nome")} className={inputClass} style={inputStyle}
                     placeholder="Ex: Cozinha planejada — Residência Alves" />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Cliente">
                <input {...register("cliente_nome")} className={inputClass} style={inputStyle}
                       placeholder="Nome do cliente" />
              </Field>
              <Field label="Previsão de entrega">
                <input {...register("data_entrega_prevista")} type="date"
                       className={inputClass} style={inputStyle} />
              </Field>
            </div>

            <Field label="Descrição">
              <textarea {...register("descricao")} rows={3}
                        className={inputClass} style={{ ...inputStyle, resize: "none" }}
                        placeholder="Detalhes adicionais do projeto..." />
            </Field>

            {error && (
              <div className="rounded-xl px-4 py-3 text-sm flex items-center gap-2"
                   style={{ background: "#FEF2F2", color: "#DC2626", border: "1px solid #FECACA" }}>
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 text-sm font-semibold px-6 py-3 rounded-xl text-white transition"
                style={{ background: "#F04C23", boxShadow: "0 4px 12px rgba(240,76,35,.25)", opacity: isSubmitting ? 0.7 : 1 }}
              >
                {isSubmitting && (
                  <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                )}
                {isSubmitting ? "Salvando..." : "Criar Projeto"}
              </button>
              <button
                type="button"
                onClick={() => router.back()}
                className="text-sm font-medium px-6 py-3 rounded-xl transition"
                style={{ background: "#F5F6FA", color: "#6B7280", border: "1.5px solid #E8EBF0" }}
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
