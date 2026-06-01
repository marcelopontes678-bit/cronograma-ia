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
  const [showPass, setShowPass] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setError("");
    try { await login(data.email, data.password); }
    catch (e) { setError(extractErrorMessage(e)); }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1.5" style={{ color: "#374151" }}>
          E-mail
        </label>
        <input
          {...register("email")}
          type="email"
          autoComplete="email"
          placeholder="seu@email.com"
          className="w-full rounded-xl px-4 py-3 text-sm outline-none transition"
          style={{
            background: "#F9FAFB",
            border: errors.email ? "1.5px solid #EF4444" : "1.5px solid #E8EBF0",
            color: "#1C1C2E",
          }}
          onFocus={e => (e.currentTarget.style.borderColor = "#F04C23")}
          onBlur={e => (e.currentTarget.style.borderColor = errors.email ? "#EF4444" : "#E8EBF0")}
        />
        {errors.email && <p className="text-xs mt-1 text-red-500">{errors.email.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5" style={{ color: "#374151" }}>
          Senha
        </label>
        <div className="relative">
          <input
            {...register("password")}
            type={showPass ? "text" : "password"}
            autoComplete="current-password"
            placeholder="••••••••"
            className="w-full rounded-xl px-4 py-3 pr-11 text-sm outline-none transition"
            style={{
              background: "#F9FAFB",
              border: errors.password ? "1.5px solid #EF4444" : "1.5px solid #E8EBF0",
              color: "#1C1C2E",
            }}
            onFocus={e => (e.currentTarget.style.borderColor = "#F04C23")}
            onBlur={e => (e.currentTarget.style.borderColor = errors.password ? "#EF4444" : "#E8EBF0")}
          />
          <button
            type="button"
            onClick={() => setShowPass(p => !p)}
            className="absolute right-3 top-1/2 -translate-y-1/2"
            style={{ color: "#9CA3AF" }}
          >
            {showPass ? (
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>
        {errors.password && <p className="text-xs mt-1 text-red-500">{errors.password.message}</p>}
      </div>

      {error && (
        <div className="rounded-xl px-4 py-3 text-sm flex items-center gap-2"
             style={{ background: "#FEF2F2", color: "#DC2626", border: "1px solid #FECACA" }}>
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-3 rounded-xl text-sm font-semibold text-white transition"
        style={{
          background: isSubmitting ? "#F89880" : "#F04C23",
          boxShadow: "0 4px 12px rgba(240,76,35,.3)",
        }}
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
            Entrando...
          </span>
        ) : "Entrar"}
      </button>
    </form>
  );
}
