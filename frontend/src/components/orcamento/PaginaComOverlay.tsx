"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Props {
  jobId: string;
  paginaNumero: number;
  /** [y_min, x_min, y_max, x_max], normalizado 0-1000 -- mesmo formato de
   * Modulo.auditoria_visual.bounding_box em src/lib/types.ts */
  boundingBox: [number, number, number, number];
  destaque?: boolean;
}

/**
 * Renderiza a pagina do PDF (servida por
 * GET /orcamentos/jobs/{jobId}/paginas/{numero}, autenticada -- por isso
 * busca como blob via a instancia `api` em vez de um <img src> direto,
 * que não mandaria o Bearer token) com o bounding_box do modulo destacado
 * por cima, usando posicionamento em % (o bounding_box ja vem normalizado
 * 0-1000 relativo a pagina, entao não precisa saber o tamanho real da
 * imagem em pixels).
 */
export function PaginaComOverlay({ jobId, paginaNumero, boundingBox, destaque = true }: Props) {
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    let urlCriada: string | null = null;
    let cancelado = false;

    api
      .get(`/orcamentos/jobs/${jobId}/paginas/${paginaNumero}`, { responseType: "blob" })
      .then((r) => {
        if (cancelado) return;
        urlCriada = URL.createObjectURL(r.data);
        setImgUrl(urlCriada);
      })
      .catch(() => {
        if (!cancelado) setErro(true);
      });

    return () => {
      cancelado = true;
      if (urlCriada) URL.revokeObjectURL(urlCriada);
    };
  }, [jobId, paginaNumero]);

  if (erro) {
    return (
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-8 text-center text-gray-500 text-sm">
        Não foi possível carregar a página {paginaNumero} do PDF.
      </div>
    );
  }

  if (!imgUrl) {
    return (
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-8 text-center text-gray-500 text-sm">
        Carregando página {paginaNumero}...
      </div>
    );
  }

  const [yMin, xMin, yMax, xMax] = boundingBox;

  return (
    <div className="relative inline-block w-full">
      {/* eslint-disable-next-line @next/next/no-img-element -- vem de um blob URL local, nao de um dominio otimizavel pelo next/image */}
      <img src={imgUrl} alt={`Página ${paginaNumero}`} className="w-full h-auto rounded-lg border border-[#2a2a2a]" />
      {destaque && (
        <div
          className="absolute border-2 border-brand-500 bg-brand-500/10 pointer-events-none"
          style={{
            top: `${yMin / 10}%`,
            left: `${xMin / 10}%`,
            width: `${(xMax - xMin) / 10}%`,
            height: `${(yMax - yMin) / 10}%`,
          }}
        />
      )}
    </div>
  );
}
