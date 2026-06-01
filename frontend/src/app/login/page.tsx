import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand-500">SmartFactory</h1>
          <p className="text-gray-500 mt-1">Móveis AI — ERP Industrial</p>
        </div>
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-8">
          <h2 className="text-xl font-semibold mb-6">Acesso ao sistema</h2>
          <LoginForm />
        </div>
      </div>
    </div>
  );
}
