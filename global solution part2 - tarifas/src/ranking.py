from __future__ import annotations

import re
from typing import TYPE_CHECKING

from src.config import LIMIAR_SIMILARIDADE, MAX_ROTAS, PESOS, REF
from src.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_SOLICITADA,
    ACESS_NAO_VERIFICADA,
    Perfil,
    Rota,
)

PALAVRAS_PROIBIDAS = re.compile(
    r"\b(segura|seguro|garantida|garantido|pontual|sem risco)\b", re.IGNORECASE
)


def motivo_inviabilidade(rota: Rota, perfil: Perfil) -> str | None:
    if rota.caminhada_m > perfil.caminhada_max_m:
        return "caminhada_acima_do_limite"
    if perfil.baldeacoes_max is not None and rota.baldeacoes > perfil.baldeacoes_max:
        return "baldeacoes_acima_do_limite"
    if (
        perfil.orcamento_max_centavos is not None
        and rota.custo.centavos is not None
        and rota.custo.centavos > perfil.orcamento_max_centavos
    ):
        return "orcamento_excedido"
    if rota.acessibilidade == ACESS_INCOMPATIVEL:
        return "acessibilidade_incompativel"
    return None


def criterios_usaveis(candidatas: list[Rota]) -> list[str]:
    usar = ["tempo"]
    if candidatas and all(r.custo.centavos is not None for r in candidatas):
        usar.append("custo")
    if candidatas and all(r.exposicao is not None for r in candidatas):
        usar.append("exposicao")
    return usar


def valor_criterio(rota: Rota, criterio: str) -> float:
    if criterio == "tempo":
        return rota.tempo_total_s / 60.0
    if criterio == "custo":
        return float(rota.custo.centavos or 0)
    if criterio == "exposicao":
        return float(rota.exposicao or 0.0)
    if criterio == "baldeacoes":
        return float(rota.baldeacoes)
    if criterio == "caminhada":
        return float(rota.caminhada_m)
    if criterio == "acess":
        return 0.0 if rota.acessibilidade == ACESS_COMPATIVEL else 1.0
    return 0.0


def escore(rota: Rota, usar: list[str]) -> float:
    numerador = sum(
        PESOS[c] * (valor_criterio(rota, c) / REF[c]) for c in usar
    )
    denominador = sum(PESOS[c] for c in usar)
    return numerador / denominador


def similares(a: Rota, b: Rota) -> bool:
    set_a = set(a.linhas)
    set_b = set(b.linhas)
    if not set_a and not set_b:
        return True
    if not set_a or not set_b:
        return False
    inter = len(set_a & set_b)
    uniao = len(set_a | set_b)
    return (inter / uniao) >= LIMIAR_SIMILARIDADE


def selecionar(
    candidatas: list[Rota], perfil: Perfil
) -> tuple[list[Rota], list[str]]:
    if not candidatas:
        return ([], [])

    usar = criterios_usaveis(candidatas)

    dimensoes = list(usar) + ["baldeacoes", "caminhada"]
    if bool(perfil.acessibilidade):
        dimensoes.append("acess")

    # Remover dominadas
    nao_dominadas: list[Rota] = []
    for a in candidatas:
        dominada = False
        for b in candidatas:
            if a is b:
                continue
            # b domina a se b <= a em todas as dimensoes e b < a em pelo menos uma
            menor_ou_igual = all(
                valor_criterio(b, d) <= valor_criterio(a, d) for d in dimensoes
            )
            estritamente_menor = any(
                valor_criterio(b, d) < valor_criterio(a, d) for d in dimensoes
            )
            if menor_ou_igual and estritamente_menor:
                dominada = True
                break
        if not dominada:
            nao_dominadas.append(a)

    exige_acess = bool(perfil.acessibilidade)

    def chave_ordenacao(r: Rota) -> tuple:
        acess_val = valor_criterio(r, "acess") if exige_acess else 0.0
        return (
            acess_val,
            escore(r, usar),
            r.tempo_total_s,
            r.baldeacoes,
            str(r.assinatura),
        )

    nao_dominadas.sort(key=chave_ordenacao)

    escolhidas: list[Rota] = []
    for r in nao_dominadas:
        if not any(similares(r, esc) for esc in escolhidas):
            escolhidas.append(r)
            if len(escolhidas) >= MAX_ROTAS:
                break

    return (escolhidas, usar)


def montar_aviso(escolhidas: list[Rota], usar: list[str]) -> str | None:
    frases: list[str] = []
    if "exposicao" not in usar:
        frases.append(
            "O equilíbrio entre os três critérios não pôde ser confirmado: dados de segurança insuficientes."
        )
    if "custo" not in usar:
        frases.append(
            "Há alternativa com tarifa não confirmada; o custo ficou fora da ordenação."
        )
    if 0 < len(escolhidas) < MAX_ROTAS:
        frases.append(
            f"Apenas {len(escolhidas)} alternativa(s) viável(is) e distinta(s) encontrada(s)."
        )

    if not frases:
        return None
    res = " ".join(frases)
    assert not PALAVRAS_PROIBIDAS.search(res), f"Texto contém palavra proibida: {res}"
    return res


def gerar_motivos(
    rota: Rota, escolhidas: list[Rota], usar: list[str], perfil: Perfil
) -> list[str]:
    motivos: list[str] = []
    n = len(escolhidas)
    menor_tempo = min(r.tempo_total_s for r in escolhidas)

    # 1
    if n == 1:
        motivos.append("Única alternativa viável e distinta encontrada.")
    # 2
    if n > 1 and rota.tempo_total_s == menor_tempo:
        motivos.append("Menor tempo total entre as opções.")
    # 3
    if n > 1 and rota.tempo_total_s != menor_tempo:
        dif = rota.tempo_total_s - menor_tempo
        if dif <= 300:
            motivos.append(f"Só {round(dif / 60)} min mais lenta que a mais rápida.")
    # 4
    if n > 1 and "custo" in usar:
        menor_custo = min(
            r.custo.centavos for r in escolhidas if r.custo.centavos is not None
        )
        if rota.custo.centavos == menor_custo:
            motivos.append("Menor custo entre as opções.")
    # 5
    if n > 1:
        menor_caminhada = min(r.caminhada_m for r in escolhidas)
        if (
            rota.caminhada_m == menor_caminhada
            and len({r.caminhada_m for r in escolhidas}) > 1
        ):
            motivos.append("Menor caminhada entre as opções.")
    # 6
    if len(rota.transportes) == 0:
        motivos.append("Percurso inteiro a pé.")
    # 7
    if len(rota.transportes) > 0 and rota.baldeacoes == 0:
        motivos.append("Sem baldeações.")
    # 8
    if rota.custo.centavos is None:
        motivos.append("Tarifa não confirmada para esta combinação.")
    # 9
    if "exposicao" not in usar:
        motivos.append(
            "Dados de segurança insuficientes para comparar este trajeto."
        )
    # 10, 11, 12
    if bool(perfil.acessibilidade):
        if rota.acessibilidade == ACESS_COMPATIVEL:
            motivos.append(
                "Compatível com a necessidade informada, segundo os dados disponíveis (não é garantia)."
            )
        elif rota.acessibilidade == ACESS_NAO_VERIFICADA:
            motivos.append("Acessibilidade NÃO verificada para este percurso.")
        else:
            motivos.append("Acessibilidade sem informação.")
    # 13
    motivos.append("Horários planejados (sem previsão em tempo real).")

    for m in motivos:
        assert not PALAVRAS_PROIBIDAS.search(m), f"Texto contém palavra proibida: {m}"

    return motivos
