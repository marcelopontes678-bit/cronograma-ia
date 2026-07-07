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
  cep: string | null;
  dias_funcionamento: string[] | null;
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

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
}

// ── Sprint 2: Engenharia manual ──────────────────────────────────────────────

export type TipoMaterial = "chapa" | "fita_borda" | "ferragem" | "outro";

export interface Material {
  id: string;
  empresa_id: string;
  nome: string;
  codigo: string | null;
  tipo: TipoMaterial;
  espessura_mm: number | null;
  largura_mm: number | null;
  comprimento_mm: number | null;
  cor: string | null;
  unidade_medida: string;
  preco_unitario: string | null;
  observacoes: string | null;
  is_active: boolean;
}

export interface Peca {
  id: string;
  modulo_id: string;
  material_id: string | null;
  nome: string;
  comprimento_mm: number;
  largura_mm: number;
  quantidade: number;
  veio: boolean;
  fita_c1: boolean;
  fita_c2: boolean;
  fita_l1: boolean;
  fita_l2: boolean;
  observacoes: string | null;
}

export interface Modulo {
  id: string;
  ambiente_id: string;
  nome: string;
  codigo: string | null;
  largura_mm: number | null;
  altura_mm: number | null;
  profundidade_mm: number | null;
  quantidade: number;
  descricao: string | null;
  ordem: number;
  pecas: Peca[];
}

export interface Ambiente {
  id: string;
  projeto_id: string;
  nome: string;
  descricao: string | null;
  ordem: number;
  modulos: Modulo[];
}

export interface ResumoMaterial {
  material_id: string | null;
  material_nome: string;
  total_pecas: number;
  area_m2: number;
  fita_borda_m: number;
}

export interface EngenhariaResumo {
  projeto_id: string;
  total_ambientes: number;
  total_modulos: number;
  total_pecas: number;
  materiais: ResumoMaterial[];
  ambientes: Ambiente[];
}
