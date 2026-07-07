"""Gera o plano de corte do projeto a partir da árvore de engenharia."""
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cutting import PecaCorte, empacotar
from app.models.material import Material, TipoMaterial
from app.models.usuario import Usuario
from app.schemas.plano_corte import (
    ChapaCorteOut,
    PecaPosicionadaOut,
    PecaSemMaterialOut,
    PlanoCorteOut,
    PlanoMaterialOut,
)
from app.services.engenharia_service import (
    _get_projeto_autorizado,
    list_ambientes,
)


async def gerar_plano_corte(
    db: AsyncSession,
    projeto_id: uuid.UUID,
    current_user: Usuario,
    kerf_mm: int = 3,
) -> PlanoCorteOut:
    projeto = await _get_projeto_autorizado(db, projeto_id, current_user)
    ambientes = await list_ambientes(db, projeto_id, current_user)

    materiais_result = await db.execute(
        select(Material).where(
            Material.empresa_id == projeto.empresa_id,
            Material.is_active.is_(True),
        )
    )
    materiais = {m.id: m for m in materiais_result.scalars().all()}

    # Agrupar peças por material, expandindo quantidades (peça × módulo)
    por_material: dict[uuid.UUID, list[PecaCorte]] = defaultdict(list)
    ignoradas: list[PecaSemMaterialOut] = []

    for amb in ambientes:
        for mod in amb.modulos:
            if not mod.is_active:
                continue
            for p in mod.pecas:
                if not p.is_active:
                    continue
                qtd = p.quantidade * mod.quantidade
                if not p.material_id:
                    ignoradas.append(PecaSemMaterialOut(
                        nome=f"{amb.nome} / {mod.nome} / {p.nome}",
                        motivo="Peça sem material definido",
                    ))
                    continue
                material = materiais.get(p.material_id)
                if not material or material.tipo != TipoMaterial.CHAPA:
                    ignoradas.append(PecaSemMaterialOut(
                        nome=f"{amb.nome} / {mod.nome} / {p.nome}",
                        motivo="Material não é chapa",
                    ))
                    continue
                if not material.comprimento_mm or not material.largura_mm:
                    ignoradas.append(PecaSemMaterialOut(
                        nome=f"{amb.nome} / {mod.nome} / {p.nome}",
                        motivo=f"Chapa '{material.nome}' sem dimensões cadastradas",
                    ))
                    continue
                for n in range(qtd):
                    por_material[material.id].append(PecaCorte(
                        ref=str(p.id),
                        nome=f"{p.nome} ({mod.nome})",
                        comprimento_mm=p.comprimento_mm,
                        largura_mm=p.largura_mm,
                        veio=p.veio,
                    ))

    planos: list[PlanoMaterialOut] = []
    total_alocadas = 0

    for material_id, pecas in por_material.items():
        material = materiais[material_id]
        resultado = empacotar(
            pecas,
            chapa_comprimento_mm=material.comprimento_mm,
            chapa_largura_mm=material.largura_mm,
            kerf_mm=kerf_mm,
        )
        area_chapa = material.comprimento_mm * material.largura_mm
        chapas_out = []
        for chapa in resultado.chapas:
            aproveitamento = chapa.area_ocupada_mm2() / area_chapa * 100
            chapas_out.append(ChapaCorteOut(
                indice=chapa.indice,
                aproveitamento_pct=round(aproveitamento, 1),
                pecas=[PecaPosicionadaOut(**p.__dict__) for p in chapa.pecas],
            ))
            total_alocadas += len(chapa.pecas)

        media = (
            sum(c.aproveitamento_pct for c in chapas_out) / len(chapas_out)
            if chapas_out else 0.0
        )
        planos.append(PlanoMaterialOut(
            material_id=material_id,
            material_nome=material.nome,
            chapa_comprimento_mm=material.comprimento_mm,
            chapa_largura_mm=material.largura_mm,
            total_chapas=len(chapas_out),
            aproveitamento_medio_pct=round(media, 1),
            chapas=chapas_out,
            nao_alocadas=[
                f"{p.nome} ({p.comprimento_mm}×{p.largura_mm}mm não cabe na chapa)"
                for p in resultado.nao_alocadas
            ],
        ))

    return PlanoCorteOut(
        projeto_id=projeto_id,
        kerf_mm=kerf_mm,
        total_pecas_alocadas=total_alocadas,
        materiais=planos,
        pecas_ignoradas=ignoradas,
    )
