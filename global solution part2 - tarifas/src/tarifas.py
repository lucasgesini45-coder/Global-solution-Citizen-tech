from __future__ import annotations

import json
from datetime import date
from typing import Any

from src.contratos import Custo, fmt_hora


def carregar_regras(caminho: str) -> list[dict[str, Any]]:
    with open(caminho, mode="r", encoding="utf-8") as f:
        return json.load(f)


def regra_vigente(regras: list[dict[str, Any]], dia: date) -> dict[str, Any] | None:
    dia_iso = dia.isoformat()
    candidatas = []
    for r in regras:
        v_inicio = r.get("vigencia_inicio", "")
        v_fim = r.get("vigencia_fim") or "9999-12-31"
        if v_inicio <= dia_iso <= v_fim:
            candidatas.append(r)

    if not candidatas:
        return None

    # Se houver mais de uma, a de maior vigencia_inicio
    return max(candidatas, key=lambda r: r.get("vigencia_inicio", ""))


def calcular_tarifa(
    embarques: list[Any],
    dia: date,
    perfil_tarifario: str,
    regras: list[dict[str, Any]],
) -> Custo:
    if not embarques:
        return Custo(
            centavos=0,
            confirmado=True,
            detalhe=["Sem embarque em transporte público."],
            regra_versao=None,
        )

    regra = regra_vigente(regras, dia)
    if regra is None:
        return Custo(
            centavos=None,
            confirmado=False,
            detalhe=["Tarifa não confirmada: nenhuma regra vigente para a data"],
            regra_versao=None,
        )

    regra_versao = regra.get("versao")

    if not regra.get("confirmada", False):
        return Custo(
            centavos=None,
            confirmado=False,
            detalhe=["Tarifa não confirmada: regra ainda não validada"],
            regra_versao=regra_versao,
        )

    perfis_pct = regra.get("perfis_percentual", {})
    if perfil_tarifario not in perfis_pct:
        return Custo(
            centavos=None,
            confirmado=False,
            detalhe=[f"Tarifa não confirmada: perfil '{perfil_tarifario}' sem regra"],
            regra_versao=regra_versao,
        )

    pct = perfis_pct[perfil_tarifario]

    # Normalizar embarques para ordenação
    # Cada item: (inicio_s, modal, nome_linha)
    embarques_norm: list[tuple[int, str, str]] = []
    for e in embarques:
        if isinstance(e, tuple):
            modal = e[0]
            inicio_s = e[1]
            nome_linha = e[2] if len(e) > 2 else modal
        else:
            modal = e.modal
            inicio_s = e.inicio_s
            nome_linha = getattr(e, "nome_linha", None) or modal
        embarques_norm.append((inicio_s, modal, nome_linha))

    embarques_norm.sort(key=lambda item: item[0])

    tarifa_base = regra.get("tarifa_base", {})
    integracao_adicional = regra.get("integracao_adicional", {})
    janela_s = regra.get("janela_s", 0)
    max_embarques = regra.get("max_embarques_por_janela", 0)

    inicio_cadeia: int | None = None
    n_cadeia = 0
    modal_anterior: str | None = None
    total = 0
    detalhes: list[str] = []

    for inicio_s, modal, nome_linha in embarques_norm:
        base = tarifa_base.get(modal)
        if base is None:
            return Custo(
                centavos=None,
                confirmado=False,
                detalhe=[f"Tarifa não confirmada: modal '{modal}' sem tarifa"],
                regra_versao=regra_versao,
            )

        eh_nova_cadeia = (
            inicio_cadeia is None
            or (inicio_s - inicio_cadeia > janela_s)
            or (n_cadeia >= max_embarques)
        )

        if eh_nova_cadeia:
            valor = base
            rotulo = "tarifa cheia"
            inicio_cadeia = inicio_s
            n_cadeia = 1
        else:
            chave = f"{modal_anterior}>{modal}"
            if chave not in integracao_adicional:
                return Custo(
                    centavos=None,
                    confirmado=False,
                    detalhe=[f"Tarifa não confirmada: integração '{chave}' sem regra confirmada"],
                    regra_versao=regra_versao,
                )
            valor = integracao_adicional[chave]
            rotulo = f"integração {chave}"
            n_cadeia += 1

        cobrado = (valor * pct + 50) // 100
        total += cobrado
        modal_anterior = modal
        detalhes.append(
            f"{fmt_hora(inicio_s)} {nome_linha}: R$ {cobrado / 100:.2f} ({rotulo})"
        )

    return Custo(
        centavos=total,
        confirmado=True,
        detalhe=detalhes,
        regra_versao=regra_versao,
    )
