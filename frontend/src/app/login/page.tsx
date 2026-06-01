import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex" style={{ background: "#F5F6FA" }}>
      {/* Painel esquerdo */}
      <div className="hidden lg:flex flex-col justify-between w-[420px] p-10"
           style={{ background: "#F04C23" }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2.2}>
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </div>
          <span className="text-white font-bold text-lg">SmartFactory</span>
        </div>

        <div>
          <h2 className="text-3xl font-bold text-white leading-snug mb-4">
            Sua fábrica<br />mais inteligente
          </h2>
          <p className="text-white/70 text-sm leading-relaxed mb-8">
            ERP vertical para marcenarias e fábricas de móveis planejados.
            Engenharia, PCP, logística e IA em um só lugar.
          </p>

          {/* Feature pills */}
          {["Plano de corte automático", "Cronograma inteligente", "IA operacional"].map(f => (
            <div key={f} className="flex items-center gap-2 mb-3">
              <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={3}>
                  <path d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-white/90 text-sm">{f}</span>
            </div>
          ))}
        </div>

        <p className="text-white/40 text-xs">© 2026 SmartFactory Móveis AI</p>
      </div>

      {/* Painel direito */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                 style={{ background: "#F04C23" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2.2}>
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <h1 className="text-xl font-bold" style={{ color: "#1C1C2E" }}>SmartFactory Móveis AI</h1>
          </div>

          <h2 className="text-2xl font-bold mb-1" style={{ color: "#1C1C2E" }}>Bem-vindo de volta</h2>
          <p className="text-sm mb-8" style={{ color: "#9CA3AF" }}>
            Entre com suas credenciais para acessar o sistema
          </p>

          <LoginForm />

          <p className="text-center text-xs mt-8" style={{ color: "#9CA3AF" }}>
            Problemas de acesso? Contate o administrador da sua empresa.
          </p>
        </div>
      </div>
    </div>
  );
}
