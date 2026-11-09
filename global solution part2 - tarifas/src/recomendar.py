from __future__ import annotations

import datetime
import math
import zoneinfo
from typing import Any, Callable

from src.config import (
    CAMINHADA_MAX_PADRAO_M,
    FUSO,
    RAIO_TERRA_M,
    VELOCIDADE_CAMINHADA_PADRAO_MS,
)
from src.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_SOLICITADA,
    ACESS_NAO_VERIFICADA,
    SEG_INDISPONIVEL,
    SEG_INSUFICIENTE,
    SEG_SUFICIENTE,
    Perfil,
    Rede,
    RespostaRotas,
    Restricoes,
    Rota,
)
from src.ranking import (
    gerar_motivos,
    montar_aviso,
    motivo_inviabilidade,
    selecionar,
)
from src.rotas import Navegador, buscar_rotas
from src.tarifas import calcular_tarifa


def recomendar(
    rede: Rede,
    regras_tarifa: list[dict[str, Any]],
    origem: tuple[float, float],
    destino: tuple[float, float],
    partida: datetime.datetime,
    perfil: Perfil | None = None,
    restricoes: Restricoes | None = None,
    verificar_acessibilidade: Callable[[Rota, frozenset[str]], str] | None = None,
    avaliar_exposicao: Callable[[Rota], tuple[float | None, str]] | None = None,
    nav: Navegador | None = None,
) -> RespostaRotas:
    if perfil is None:
        perfil = Perfil()
    if restricoes is None:
        restricoes = Restricoes()
    if verificar_acessibilidade is None:
        verificar_acessibilidade = lambda rota, nec: ACESS_NAO_VERIFICADA
    if avaliar_exposicao is None:
        avaliar_exposicao = lambda rota: (None, SEG_INDISPONIVEL)
    if nav is None:
        nav = Navegador(rede)

    # 2. Validar
    if not (
        isinstance(origem, (tuple, list))
        and len(origem) == 2
        and isinstance(origem[0], (int, float))
        and isinstance(origem[1], (int, float))
        and -90 <= origem[0] <= 90
        and -180 <= origem[1] <= 180
    ):
        return RespostaRotas(erro={"codigo": "origem_invalida", "mensagem": "Origem inválida."})

    if not (
        isinstance(destino, (tuple, list))
        and len(destino) == 2
        and isinstance(destino[0], (int, float))
        and isinstance(destino[1], (int, float))
        and -90 <= destino[0] <= 90
        and -180 <= destino[1] <= 180
    ):
        return RespostaRotas(erro={"codigo": "destino_invalida", "mensagem": "Destino inválido."})

    if not isinstance(partida, datetime.datetime):
        return RespostaRotas(
            erro={"codigo": "partida_invalida", "mensagem": "Horário de partida inválido."}
        )

    problemas = perfil.problemas()
    if problemas:
        return RespostaRotas(
            erro={"codigo": "preferencias_invalidas", "mensagem": "; ".join(problemas)}
        )

    # Área piloto
    lat_min, lon_min, lat_max, lon_max = rede.limites()
    m_por_deg_lat = RAIO_TERRA_M * math.pi / 180.0
    lat_media = (lat_min + lat_max) / 2.0
    m_por_deg_lon = m_por_deg_lat * math.cos(math.radians(lat_media))
    delta_lat = perfil.caminhada_max_m / m_por_deg_lat
    delta_lon = perfil.caminhada_max_m / m_por_deg_lon

    area_lat_min = lat_min - delta_lat
    area_lat_max = lat_max + delta_lat
    area_lon_min = lon_min - delta_lon
    area_lon_max = lon_max + delta_lon

    if not (area_lat_min <= origem[0] <= area_lat_max and area_lon_min <= origem[1] <= area_lon_max):
        return RespostaRotas(
            erro={"codigo": "origem_fora_da_area_piloto", "mensagem": "Origem fora da área piloto."}
        )

    if not (area_lat_min <= destino[0] <= area_lat_max and area_lon_min <= destino[1] <= area_lon_max):
        return RespostaRotas(
            erro={"codigo": "destino_fora_da_area_piloto", "mensagem": "Destino fora da área piloto."}
        )

    # 3. Candidatas
    candidatas = buscar_rotas(nav, origem, destino, partida, perfil, restricoes)
    if not candidatas:
        return RespostaRotas(
            erro={
                "codigo": "sem_trajeto",
                "mensagem": (
                    "Nenhum trajeto encontrado para esse horário e essas condições "
                    "(sem serviço, bloqueios confirmados ou paradas fora do limite de caminhada)."
                ),
            }
        )

    # 4. Avaliar custo, acessibilidade e segurança
    for r in candidatas:
        r.custo = calcular_tarifa(
            r.transportes, partida.date(), perfil.perfil_tarifario, regras_tarifa
        )
        if not perfil.acessibilidade:
            r.acessibilidade = ACESS_NAO_SOLICITADA
        else:
            acess = verificar_acessibilidade(r, perfil.acessibilidade)
            if acess not in {
                ACESS_NAO_SOLICITADA,
                ACESS_COMPATIVEL,
                ACESS_NAO_VERIFICADA,
                ACESS_INCOMPATIVEL,
            }:
                acess = ACESS_NAO_VERIFICADA
            r.acessibilidade = acess

        exp, st = avaliar_exposicao(r)
        if exp is not None and not (isinstance(exp, (int, float)) and 0.0 <= exp <= 1.0):
            exp = None
        r.exposicao = float(exp) if exp is not None else None
        r.status_seguranca = (
            st
            if st in {SEG_SUFICIENTE, SEG_INSUFICIENTE, SEG_INDISPONIVEL}
            else SEG_INDISPONIVEL
        )

    # 5. Viabilidade
    descartes: dict[str, int] = {}
    viaveis: list[Rota] = []
    for r in candidatas:
        motivo = motivo_inviabilidade(r, perfil)
        if motivo is not None:
            descartes[motivo] = descartes.get(motivo, 0) + 1
        else:
            viaveis.append(r)

    if not viaveis:
        return RespostaRotas(
            rotas=[],
            erro={
                "codigo": "nenhuma_rota_atende",
                "mensagem": (
                    "Há trajetos, mas nenhum atende às restrições informadas. "
                    "Não trocamos sua necessidade por ganho de tempo ou custo."
                ),
            },
            descartes=descartes,
        )

    # 6. Seleção
    escolhidas, usar = selecionar(viaveis, perfil)
    for idx_ord, r in enumerate(escolhidas, start=1):
        r.ordem = idx_ord
        r.motivos = gerar_motivos(r, escolhidas, usar, perfil)
        r.fontes = [
            {
                "fonte": rede.versao,
                "rotulo": "planejado",
                "origem_dados": rede.origem_dados,
                "tarifa_regra": r.custo.regra_versao,
            }
        ]

    aviso = montar_aviso(escolhidas, usar)
    return RespostaRotas(
        rotas=escolhidas,
        aviso=aviso,
        criterios_usados=usar,
        descartes=descartes,
    )


def processar_pedido(
    pedido: Any,
    rede: Rede,
    regras_tarifa: list[dict[str, Any]],
    restricoes: Restricoes | None = None,
    verificar_acessibilidade: Callable[[Rota, frozenset[str]], str] | None = None,
    avaliar_exposicao: Callable[[Rota], tuple[float | None, str]] | None = None,
    nav: Navegador | None = None,
) -> dict:
    if not isinstance(pedido, dict):
        return RespostaRotas(
            erro={"codigo": "origem_invalida", "mensagem": "Origem inválida."}
        ).para_dict()

    orig = pedido.get("origem")
    if not (
        isinstance(orig, dict)
        and isinstance(orig.get("lat"), (int, float))
        and isinstance(orig.get("lon"), (int, float))
    ):
        return RespostaRotas(
            erro={"codigo": "origem_invalida", "mensagem": "Origem inválida."}
        ).para_dict()

    dest = pedido.get("destino")
    if not (
        isinstance(dest, dict)
        and isinstance(dest.get("lat"), (int, float))
        and isinstance(dest.get("lon"), (int, float))
    ):
        return RespostaRotas(
            erro={"codigo": "destino_invalida", "mensagem": "Destino inválido."}
        ).para_dict()

    partida_raw = pedido.get("partida")
    if not isinstance(partida_raw, str):
        return RespostaRotas(
            erro={
                "codigo": "partida_invalida",
                "mensagem": "Informe 'partida' em formato ISO (ex.: 2026-11-09T08:00:00).",
            }
        ).para_dict()

    try:
        dt = datetime.datetime.fromisoformat(partida_raw)
    except Exception:
        return RespostaRotas(
            erro={
                "codigo": "partida_invalida",
                "mensagem": "Informe 'partida' em formato ISO (ex.: 2026-11-09T08:00:00).",
            }
        ).para_dict()

    if dt.tzinfo is not None:
        sp_tz = zoneinfo.ZoneInfo(FUSO)
        dt = dt.astimezone(sp_tz).replace(tzinfo=None)

    nec = pedido.get("necessidades")
    if not isinstance(nec, dict):
        nec = {}

    perfil = Perfil(
        caminhada_max_m=nec.get("caminhada_max_m", CAMINHADA_MAX_PADRAO_M),
        baldeacoes_max=nec.get("baldeacoes_max"),
        orcamento_max_centavos=nec.get("orcamento_max_centavos"),
        acessibilidade=frozenset(nec.get("acessibilidade") or []),
        velocidade_caminhada_ms=nec.get(
            "velocidade_caminhada_ms", VELOCIDADE_CAMINHADA_PADRAO_MS
        ),
        perfil_tarifario=nec.get("perfil_tarifario", "padrao"),
    )

    origem_tuple = (float(orig["lat"]), float(orig["lon"]))
    destino_tuple = (float(dest["lat"]), float(dest["lon"]))

    resposta = recomendar(
        rede=rede,
        regras_tarifa=regras_tarifa,
        origem=origem_tuple,
        destino=destino_tuple,
        partida=dt,
        perfil=perfil,
        restricoes=restricoes,
        verificar_acessibilidade=verificar_acessibilidade,
        avaliar_exposicao=avaliar_exposicao,
        nav=nav,
    )
    return resposta.para_dict()
