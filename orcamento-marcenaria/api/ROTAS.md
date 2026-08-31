# Contratos das rotas da API

Todas as rotas sob `/api/v1`. Autenticacao (header `Authorization`) omitida
deste desenho inicial -- adicionar antes de qualquer deploy real.

---

## Upload e extracao

### `POST /api/v1/jobs`
Recebe o PDF, renderiza as paginas e dispara a extracao via Claude Vision
(assincrono -- retorna imediatamente com status `processando`).

**Request:** `multipart/form-data`
- `arquivo`: PDF (obrigatorio)
- `usuario_id`: string (obrigatorio -- define quais Preferencias Globais e Regras Aprendidas usar)

**Response `202 Accepted`:**
```json
{ "job_id": "job_8f3a1c", "status": "processando", "paginas": 16 }
```

### `GET /api/v1/jobs/{job_id}`
Consulta o status/resultado do job. Fazer polling ate `status` sair de
`processando`.

**Response `200 OK`:** corpo = `ExtracaoResultado` (ver `schemas/extracao.py`).
Quando `status == "aguardando_revisao"`, o frontend deve renderizar
`modulo.auditoria_visual.bounding_box` (`[y_min, x_min, y_max, x_max]`,
normalizado 0-1000) sobre a pagina `auditoria_visual.pagina_pdf`, e
destacar modulos com `confianca < 0.7`.

---

## Revisao humana (obrigatoria antes de precificar)

### `PATCH /api/v1/jobs/{job_id}/modulos/{modulo_id}`
Corrige um modulo especifico (dimensao, material, etc). Marca
`origem = "confirmado_humano"`.

**Request:** patch parcial (merge raso em subcampos aninhados como `dimensoes`):
```json
{ "dimensoes": { "largura_mm": 900 }, "especificacoes_materiais": { "caixaria": "MDF Branco TX" }, "confianca": 1.0 }
```
**Response `200 OK`:** o `Modulo` atualizado.

### `POST /api/v1/jobs/{job_id}/modulos`
Adiciona um modulo que a IA nao detectou. `origem = "adicionado_manual"`.

### `POST /api/v1/jobs/{job_id}/confirmar`
Marca o job inteiro como `status = "confirmado"` -- so entao ele pode ser
usado em `POST /api/v1/orcamentos`. Rejeita (`409 Conflict`) se ainda
houver modulo com `confianca < 0.7` e `origem == "vision_automatico"`.

---

## Preferencias Globais

### `GET /api/v1/usuarios/{usuario_id}/preferencias`
**Response `200 OK`:** `PreferenciasGlobais` (ver `schemas/preferencias.py`).
Se o usuario nao tiver preferencias salvas, retorna os defaults do schema.

### `PUT /api/v1/usuarios/{usuario_id}/preferencias`
Substitui as preferencias do usuario. **Request/Response:** `PreferenciasGlobais`.

---

## Auto-aprendizado / feedback

### `POST /api/v1/usuarios/{usuario_id}/feedback`
**Request:** `FeedbackRequest`
```json
{
  "usuario_id": "u_123",
  "job_id": "job_8f3a1c",
  "modulo_id": "mod_005",
  "instrucao": "Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa"
}
```
Fluxo interno: `feedback_service.py` chama a LLM para normalizar a
instrucao numa regra de sistema reusavel, persiste em
`storage/regras_aprendidas/{usuario_id}.json`.

**Response `201 Created`:** `FeedbackResponse`
```json
{
  "regra": {
    "id": "regra_007",
    "usuario_id": "u_123",
    "instrucao_original": "Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa",
    "regra_normalizada": "Quando um modulo tiver porta com vidro reflecta, defina a cor do fundo igual a cor da caixa.",
    "ativa": true,
    "criado_em": "2026-08-28T20:00:00Z"
  },
  "total_regras_ativas_usuario": 7
}
```

### `GET /api/v1/usuarios/{usuario_id}/regras`
Lista as regras aprendidas ativas do usuario (para o marceneiro poder
revisar/desativar regras erradas).

### `DELETE /api/v1/usuarios/{usuario_id}/regras/{regra_id}`
Desativa uma regra (soft delete -- `ativa = false`).

---

## Precificacao

### `POST /api/v1/orcamentos`
**Request:** `OrcamentoRequest` -- exige `job_id` com `status == "confirmado"`.

**Response `200 OK`:** `OrcamentoResponse` (ver `schemas/orcamento.py`).
Internamente delega para `pricing_service.py`, que chama
`engine/calculo_projeto.calcular_projeto` +
`engine/orcamento_engine.calcular_orcamento_projeto` -- os mesmos
modulos ja testados com o projeto Quarto Maria.

**Erros:**
- `409 Conflict` se `job_id` nao estiver `confirmado`.
- Itens sem preco na tabela NUNCA geram erro nem custo zero silencioso --
  aparecem em `itens_pendentes` e sao excluidos do total, exatamente como
  o `calculo_projeto.py` ja faz hoje.
