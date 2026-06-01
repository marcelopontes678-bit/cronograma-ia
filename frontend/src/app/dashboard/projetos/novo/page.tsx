"use client";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { extractErrorMessage } from "@/lib/api";

const schema = z.object({
  codigo: z.string().min(1, "Código obrigatório"),
  nome: z.string().min(1, "Nome obrigatório"),
  cliente_nome: z.string().optional(),
  data_entrega_prevista: z.string().optional(),
  prioridade: z.coerce.number().min(1).max(5),
  descricao: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export default function NovoProjetoPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
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
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Novo Projeto</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1 text-gray-300">Código *</label>
            <input
              {...register("codigo")}
              className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
              placeholder="OP-2024-001"
            />
            {errors.codigo && (
              <p className="text-red-400 text-xs mt-1">{errors.codigo.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm mb-1 text-gray-300">Prioridade</label>
            <select
              {...register("prioridade")}
              className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
            >
              <option value={1}>1 — Urgente</option>
              <option value={2}>2 — Alta</option>
              <option value={3}>3 — Normal</option>
              <option value={4}>4 — Baixa</option>
              <option value={5}>5 — Mínima</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm mb-1 text-gray-300">Nome *</label>
          <input
            {...register("nome")}
            className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
            placeholder="Quarto casal — Cozinha planejada"
          />
          {errors.nome && (
            <p className="text-red-400 text-xs mt-1">{errors.nome.message}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1 text-gray-300">Cliente</label>
            <input
              {...register("cliente_nome")}
              className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
              placeholder="Nome do cliente"
            />
          </div>
          <div>
            <label className="block text-sm mb-1 text-gray-300">Previsão de entrega</label>
            <input
              {...register("data_entrega_prevista")}
              type="date"
              className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm mb-1 text-gray-300">Descrição</label>
          <textarea
            {...register("descricao")}
            rows={3}
            className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-4 py-3 focus:outline-none focus:border-brand-500 resize-none"
            placeholder="Detalhes do projeto..."
          />
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-brand-500 text-black font-semibold px-6 py-3 rounded-lg hover:bg-brand-600 transition disabled:opacity-50"
          >
            {isSubmitting ? "Salvando..." : "Criar Projeto"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="border border-[#2a2a2a] text-gray-400 px-6 py-3 rounded-lg hover:border-[#444] hover:text-white transition"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
