export type TipoUnidade = "fabrica" | "centro_distribuicao" | "escritorio";
export type RoleUsuario = "admin" | "gerente" | "operador" | "visualizador";
export type StatusProjeto =
  | "rascunho"
  | "aguardando_aprovacao"
  | "em_producao"
  | "concluido"
  | "cancelado";

export interface UnidadeSummary {
  id: string;
  nome: string;
  tipo: TipoUnidade;
  codigo: string | null;
  is_sede: boolean;
}

export interface Empresa {
  id: string;
  nome: string;
  nome_fantasia: string | null;
  cnpj: string;
  email: string;
  telefone: string | null;
  cidade: string | null;
  estado: string | null;
  is_active: boolean;
  unidades: UnidadeSummary[];
}

export interface Unidade {
  id: string;
  empresa_id: string;
  nome: string;
  tipo: TipoUnidade;
  codigo: string | null;
  is_sede: boolean;
  cidade: string | null;
  estado: string | null;
  is_active: boolean;
}

export interface UsuarioSummary {
  id: string;
  nome: string;
  email: string;
  role: RoleUsuario;
}

export interface Usuario extends UsuarioSummary {
  empresa_id: string;
  unidade_id: string | null;
  telefone: string | null;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  is_active: boolean;
}

export interface ProjetoListItem {
  id: string;
  codigo: string;
  nome: string;
  status: StatusProjeto;
  cliente_nome: string | null;
  data_entrega_prevista: string | null;
  prioridade: number;
  created_at: string;
}

export interface Projeto extends ProjetoListItem {
  empresa_id: string;
  descricao: string | null;
  cliente_contato: string | null;
  data_entrada: string | null;
  data_entrega_real: string | null;
  observacoes: string | null;
  unidade_id: string | null;
  responsavel: UsuarioSummary | null;
  criado_por: UsuarioSummary | null;
  updated_at: string;
  is_active: boolean;
}

// --- Orcamento (Claude Vision, persona MARC) ---

export type StatusOrcamentoJob = "processando" | "aguardando_revisao" | "confirmado" | "erro";
export type OrigemModulo = "vision_automatico" | "confirmado_humano" | "adicionado_manual";

export interface Dimensoes {
  largura_mm: number | null;
  altura_mm: number | null;
  profundidade_mm: number | null;
}

export interface Componentes {
  portas: number;
  gavetas: number;
  prateleiras_internas: number;
}

export interface EspecificacoesMateriais {
  caixaria: string;
  frente: string;
  fundo: string;
  metodo_uniao: string;
  fixacao_fundo: string;
  campos_inferidos: string[];
}

export interface FerragemSugerida {
  nome: string;
  quantidade: number;
}

export interface ItemComplementar {
  nome: string;
  tipo: string;
}

export interface AuditoriaVisual {
  pagina_pdf: number;
  arquivo_indice?: number; // indice (0-indexed) do arquivo de origem dentro do job
  bounding_box: [number, number, number, number]; // [y_min, x_min, y_max, x_max], 0-1000
}

export interface Modulo {
  id: string;
  nome: string;
  vista_referencia: string;
  dimensoes: Dimensoes;
  componentes: Componentes;
  especificacoes_materiais: EspecificacoesMateriais;
  ferragens_sugeridas: FerragemSugerida[];
  itens_complementares: ItemComplementar[];
  auditoria_visual: AuditoriaVisual;
  descricao_resumida: string;
  confianca: number;
  origem: OrigemModulo;
}

export interface Ambiente {
  nome_ambiente: string;
  modulos: Modulo[];
}

export interface OrcamentoJobListItem {
  id: string;
  empresa_id: string;
  usuario_id: string | null;
  projeto_id: string | null;
  arquivo_origem: string;
  status: StatusOrcamentoJob;
  ambientes: Ambiente[];
  avisos: string[];
  created_at: string;
  updated_at: string;
}

export type OrcamentoJob = OrcamentoJobListItem;

export interface FaixaDobradicasPorAltura {
  altura_maxima_mm: number;
  quantidade_dobradicas: number;
}

export interface RegraApoioPorAmbiente {
  ambientes_molhados: string[];
  apoio_area_molhada: string;
  apoio_area_seca: string;
}

export interface PreferenciasGlobaisConfig {
  espessuras: {
    caixa_mm: number;
    porta_mm: number;
    fundo_mm: number;
    prateleira_mm: number;
    sarrafo_superior_mm: number;
  };
  ferragens: {
    marca_corredicas: string;
    marca_dobradicas: string;
    tipo_corredica_padrao: string;
    dobradica_com_amortecimento: boolean;
  };
  metodo_uniao: string;
  fixacao_fundo: string;
  acabamento_interno_padrao: string;
  regra_fundo_exposto_forca_cor_caixaria: boolean;
  regra_apoio_por_ambiente: RegraApoioPorAmbiente;
  faixas_dobradicas_por_altura: FaixaDobradicasPorAltura[];
  profundidade_padrao_por_tipo_mm: Record<string, number>;
}

export interface PreferenciasGlobaisResponse {
  empresa_id: string;
  configuracao: PreferenciasGlobaisConfig;
  created_at: string;
  updated_at: string;
}

export interface RegraAprendida {
  id: string;
  empresa_id: string;
  usuario_id: string | null;
  instrucao_original: string;
  regra_normalizada: string;
  origem_job_id: string | null;
  origem_modulo_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ItemPendente {
  reference_ou_acabamento: string;
  descricao: string;
  motivo: string;
}

export interface OrcamentoResponse {
  job_id: string;
  divisor_markup: number;
  custo_material_total: number;
  preco_venda_material: number;
  custo_mao_de_obra: number;
  total: number;
  itens_pendentes: ItemPendente[];
  avisos: string[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
}
