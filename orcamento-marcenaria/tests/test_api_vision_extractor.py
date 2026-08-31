from unittest.mock import MagicMock, patch

from api.schemas.preferencias import PreferenciasGlobais
from api.services.pdf_to_images import renderizar_paginas
from api.services.vision_extractor import (
    LIMIAR_CONFIANCA_REVISAO,
    _carregar_schema_ferramenta,
    _montar_system_prompt,
    extrair_de_pdf,
)


class TestRenderizarPaginas:
    def test_renderiza_paginas_reais_do_pdf(self, caminho_pdf_banheiro, tmp_path):
        paginas = renderizar_paginas(caminho_pdf_banheiro, tmp_path, paginas=[5])
        assert len(paginas) == 1
        pagina = paginas[0]
        assert pagina.numero == 5
        assert pagina.caminho_arquivo.exists()
        assert pagina.largura_px > 0 and pagina.altura_px > 0
        assert len(pagina.base64()) > 0

    def test_renderiza_todas_as_paginas_quando_nao_filtrado(self, caminho_pdf_banheiro, tmp_path):
        paginas = renderizar_paginas(caminho_pdf_banheiro, tmp_path)
        assert len(paginas) == 6


class TestSchemaEPrompt:
    def test_schema_de_ferramenta_carrega(self):
        schema = _carregar_schema_ferramenta()
        assert schema["name"] == "registrar_extracao"
        assert "ambientes" in schema["input_schema"]["properties"]

    def test_prompt_injeta_preferencias_e_regras(self):
        prefs = PreferenciasGlobais(usuario_id="teste")
        prompt = _montar_system_prompt(prefs, ["Regra ativa de teste"])
        assert "Regra ativa de teste" in prompt
        assert "espessuras" in prompt  # veio do dump json das preferencias
        assert "PREFERENCIAS_GLOBAIS_DO_USUARIO" not in prompt  # placeholder foi substituido
        assert "REGRAS_APRENDIDAS_DO_USUARIO" not in prompt

    def test_prompt_sem_regras_mostra_mensagem_padrao(self):
        prefs = PreferenciasGlobais(usuario_id="teste")
        prompt = _montar_system_prompt(prefs, [])
        assert "nenhuma regra aprendida ainda" in prompt


def _resposta_tool_use(ambientes, avisos=None):
    bloco = MagicMock()
    bloco.type = "tool_use"
    bloco.name = "registrar_extracao"
    bloco.input = {"ambientes": ambientes, "avisos": avisos or []}
    resposta = MagicMock()
    resposta.content = [bloco]
    return resposta


class TestExtrairDePdfComApiMockada:
    def _materiais(self, caixaria="MDF Cinza Cobalto Berneck"):
        return {
            "caixaria": caixaria, "frente": caixaria, "fundo": "MDF Branco",
            "metodo_uniao": "minifix", "fixacao_fundo": "encaixado_em_rebaixo", "campos_inferidos": [],
        }

    def _ambiente_banheiro(self):
        return [{
            "nome_ambiente": "Banheiro",
            "modulos": [
                {
                    "id": "MOD-001", "nome": "Armario superior", "vista_referencia": "",
                    "dimensoes": {"largura_mm": 930, "altura_mm": 1040, "profundidade_mm": 150},
                    "componentes": {"portas": 1, "gavetas": 0, "prateleiras_internas": 1},
                    "especificacoes_materiais": self._materiais(),
                    "ferragens_sugeridas": [], "itens_complementares": [],
                    "auditoria_visual": {"pagina_pdf": 5, "bounding_box": [400, 100, 700, 400]},
                    "descricao_resumida": "", "confianca": 0.9,
                },
                {
                    "id": "MOD-002", "nome": "Armario inferior", "vista_referencia": "",
                    "dimensoes": {"largura_mm": None, "altura_mm": 610, "profundidade_mm": 580},
                    "componentes": {"portas": 2, "gavetas": 4, "prateleiras_internas": 0},
                    "especificacoes_materiais": self._materiais(caixaria="MDF Verde Floresta Duratex"),
                    "ferragens_sugeridas": [], "itens_complementares": [],
                    "auditoria_visual": {"pagina_pdf": 5, "bounding_box": [700, 100, 900, 400]},
                    "descricao_resumida": "largura ilegivel", "confianca": 0.5,
                },
            ],
        }]

    def test_agrega_modulos_de_varios_lotes_com_ids_unicos(self, caminho_pdf_banheiro, tmp_path):
        with patch("api.services.vision_extractor.Anthropic") as MockAnthropic:
            MockAnthropic.return_value.messages.create.return_value = _resposta_tool_use(self._ambiente_banheiro())
            resultado = extrair_de_pdf(
                job_id="job_teste", caminho_pdf=caminho_pdf_banheiro, pasta_trabalho=tmp_path,
                preferencias=PreferenciasGlobais(usuario_id="teste"), regras_ativas=[],
                api_key="fake", paginas_por_lote=2,
            )

        # 6 paginas / 2 por lote = 3 lotes, cada um retornando os mesmos 2 modulos do mock
        modulos = [m for amb in resultado.ambientes for m in amb.modulos]
        assert len(modulos) == 6
        ids = [m.id for m in modulos]
        assert len(ids) == len(set(ids)), "IDs de modulo devem ser unicos mesmo com dados repetidos entre lotes"

    def test_status_sempre_comeca_aguardando_revisao_mesmo_com_alta_confianca(self, caminho_pdf_banheiro, tmp_path):
        ambiente_alta_confianca = [{
            "nome_ambiente": "Banheiro",
            "modulos": [{
                "id": "MOD-001", "nome": "Armario", "vista_referencia": "",
                "dimensoes": {"largura_mm": 900, "altura_mm": 1000, "profundidade_mm": 500},
                "componentes": {"portas": 1, "gavetas": 0, "prateleiras_internas": 0},
                "especificacoes_materiais": self._materiais(caixaria="MDF Branco"),
                "ferragens_sugeridas": [], "itens_complementares": [],
                "auditoria_visual": {"pagina_pdf": 1, "bounding_box": [0, 0, 100, 100]},
                "descricao_resumida": "", "confianca": 1.0,
            }],
        }]
        with patch("api.services.vision_extractor.Anthropic") as MockAnthropic:
            MockAnthropic.return_value.messages.create.return_value = _resposta_tool_use(ambiente_alta_confianca)
            resultado = extrair_de_pdf(
                job_id="job_alta_confianca", caminho_pdf=caminho_pdf_banheiro, pasta_trabalho=tmp_path,
                preferencias=PreferenciasGlobais(usuario_id="teste"), regras_ativas=[],
                api_key="fake", paginas_por_lote=6,
            )
        assert resultado.status.value == "aguardando_revisao"

    def test_falha_de_rede_vira_excecao_com_contexto(self, caminho_pdf_banheiro, tmp_path):
        from api.services.vision_extractor import ExtracaoVisionError
        import pytest

        with patch("api.services.vision_extractor.Anthropic") as MockAnthropic:
            MockAnthropic.return_value.messages.create.side_effect = RuntimeError("erro de rede simulado")
            with pytest.raises(ExtracaoVisionError):
                extrair_de_pdf(
                    job_id="job_falha", caminho_pdf=caminho_pdf_banheiro, pasta_trabalho=tmp_path,
                    preferencias=PreferenciasGlobais(usuario_id="teste"), regras_ativas=[],
                    api_key="fake",
                )

    def test_limiar_de_confianca_e_070(self):
        assert LIMIAR_CONFIANCA_REVISAO == 0.7
