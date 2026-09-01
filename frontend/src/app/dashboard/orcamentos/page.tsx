"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, extractErrorMessage } from "@/lib/api";
import { OrcamentoJobListItem, StatusOrcamentoJob } from "@/lib/types";

const STATUS_LABEL: Record<StatusOrcamentoJob, string> = {
  processando: "Processando",
  aguardando_revisao: "Aguardando revisão",
  confirmado: "Confirmado",
  erro: "Erro",
};

const STATUS_COLOR: Record<StatusOrcamentoJob, string> = {
  processando: "text-yellow-300 bg-yellow-900/40",
  aguardando_revisao: "text-blue-300 bg-blue-900/40",
  confirmado: "text-green-300 bg-green-900/40",
  erro: "text-red-300 bg-red-900/40",
};

function contarModulos(job: OrcamentoJobListItem): number {
  return job.ambientes.reduce((acc, a) => acc + a.modulos.length, 0);
}

export default function OrcamentosPage() {
  const [jobs, setJobs] = useState<OrcamentoJobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const carregarJobs = () => {
    setLoading(true);
    api
      .get("/orcamentos/jobs")
      .then((r) => setJobs(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(carregarJobs, []);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const arquivo = e.target.files?.[0];
    if (!arquivo) return;
    setError("");
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("arquivo", arquivo);
      // sobrescreve o Content-Type padrao (application/json) do client --
      // o axios monta o multipart/form-data + boundary sozinho quando o
      // body e um FormData e o header nao esta fixado antes.
      await api.post("/orcamentos/jobs", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      carregarJobs();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Orçamentos</h1>
          <p className="text-gray-500 text-sm mt-1">
            Extração automática de módulos via Claude Vision (agente MARC)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/orcamentos/regras"
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Regras aprendidas
          </Link>
          <Link
            href="/dashboard/orcamentos/preferencias"
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Preferências
          </Link>
          <label className="bg-brand-500 text-black text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-600 transition cursor-pointer">
            {uploading ? "Enviando..." : "+ Enviar PDF"}
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={uploading}
              onChange={onUpload}
            />
          </label>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : jobs.length === 0 ? (
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-12 text-center text-gray-500">
          Nenhum orçamento ainda. Envie um PDF de projeto para começar.
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/dashboard/orcamentos/${job.id}`}
              className="block bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl px-5 py-4 hover:border-[#444] transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{job.arquivo_origem}</p>
                  <p className="text-gray-500 text-sm mt-0.5">
                    {contarModulos(job)} módulo(s) ·{" "}
                    {new Date(job.created_at).toLocaleString("pt-BR")}
                  </p>
                </div>
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_COLOR[job.status]}`}
                >
                  {STATUS_LABEL[job.status]}
                </span>
              </div>
              {job.avisos.length > 0 && (
                <p className="text-yellow-500/80 text-xs mt-2">
                  {job.avisos.length} aviso(s) para revisar
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
