"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { extractErrorMessage } from "@/lib/api";

const schema = z.object({
  email: z.string().email("E-mail inválido"),
  password: z.string().min(1, "Informe a senha"),
});
type FormData = z.infer<typeof schema>;

export function LoginForm() {
  const { login } = useAuth();
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      await login(data.email, data.password);
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div>
        <label className="block text-sm mb-1 text-gray-300">E-mail</label>
        <input
          {...register("email")}
          type="email"
          autoComplete="email"
          className="w-full bg-[#222] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500"
          placeholder="seu@email.com"
        />
        {errors.email && (
          <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm mb-1 text-gray-300">Senha</label>
        <input
          {...register("password")}
          type="password"
          autoComplete="current-password"
          className="w-full bg-[#222] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500"
          placeholder="••••••••"
        />
        {errors.password && (
          <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>
        )}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-brand-500 text-black font-semibold py-3 rounded-lg hover:bg-brand-600 transition disabled:opacity-50"
      >
        {isSubmitting ? "Entrando..." : "Entrar"}
      </button>
    </form>
  );
}
