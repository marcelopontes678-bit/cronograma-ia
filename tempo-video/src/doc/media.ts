/**
 * RECURSOS SUBSTITUÍVEIS do documentário.
 *
 * Fotos de arquivo: NÃO estão incluídas (o ambiente de produção não tinha acesso a bancos de imagem).
 * Para usar fotos oficiais licenciadas (ex.: Agência Brasil, Agência Senado, Planalto — verifique a licença,
 * geralmente CC BY): salve em public/doc/fotos/ e preencha `file` e `credit`. Enquanto `file` for null,
 * o vídeo mostra um espaço identificado como "foto de arquivo pendente" (nunca uma imagem inventada).
 */
export const PHOTOS: Record<"flavio" | "lula", { file: string | null; credit: string }> = {
  flavio: { file: null, credit: "" },
  lula: { file: null, credit: "" },
};

/** Áudio gerado por audio/build_doc.py. Troque por narração humana ou trilha licenciada mantendo os caminhos. */
export const AUDIO = {
  narration: "doc/narration.wav",
  music: "doc/bed.mp3",
  sfx: "doc/sfx.mp3",
  musicLevel: 0.55,
  duckDepth: 0.62, // quanto a música baixa durante a fala
};
