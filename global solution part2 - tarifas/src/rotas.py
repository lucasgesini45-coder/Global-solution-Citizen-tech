from __future__ import annotations

import bisect
import datetime
import math
from datetime import date
from typing import TYPE_CHECKING

from src.config import (
    CAMINHADA_BALDEACAO_MAX_M,
    ESPERA_MAX_S,
    FOLGA_BALDEACAO_S,
    MAX_EXECUCOES,
    MAX_RODADAS_PADRAO,
    RAIO_TERRA_M,
    TAMANHO_CELULA_M,
)
from src.contratos import Perfil, Rede, Restricoes, Rota, Trecho, Viagem


def haversine(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    lat1, lon1 = p1
    lat2, lon2 = p2
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return RAIO_TERRA_M * c


def seg_a_pe(distancia_m: float, velocidade_ms: float) -> int:
    if distancia_m < 1.0:
        return 0
    return round(distancia_m / velocidade_ms)


class IndiceHorarios:
    def __init__(self, rede: Rede, dia: date) -> None:
        self.rede = rede
        self.dia = dia
        self.tabela: dict[
            tuple[str, tuple[str, tuple[str, ...]]],
            list[tuple[int, str, int, Viagem, int]],
        ] = {}
        self.padroes_por_parada: dict[
            str, set[tuple[str, tuple[str, ...]]]
        ] = {}

        for k in (-1, 0, 1):
            dia_servico = dia + datetime.timedelta(days=k)
            deslocamento = k * 86400
            for viagem in rede.viagens:
                if viagem.opera_em(dia_servico):
                    padrao = viagem.padrao
                    n_paradas = len(viagem.paradas)
                    for i in range(n_paradas - 1):
                        p_id = viagem.paradas[i]
                        dep_horario = viagem.horarios[i] + deslocamento
                        chave = (p_id, padrao)
                        if chave not in self.tabela:
                            self.tabela[chave] = []
                        self.tabela[chave].append(
                            (dep_horario, viagem.id, deslocamento, viagem, i)
                        )
                        if p_id not in self.padroes_por_parada:
                            self.padroes_por_parada[p_id] = set()
                        self.padroes_por_parada[p_id].add(padrao)

        for chave in self.tabela:
            self.tabela[chave].sort(key=lambda item: (item[0], item[1], item[2]))

    def padroes_na_parada(
        self, parada_id: str
    ) -> list[tuple[str, tuple[str, ...]]]:
        padroes = self.padroes_por_parada.get(parada_id, set())
        return sorted(padroes, key=lambda p: (p[0], p[1]))

    def primeira_saida(
        self, parada_id: str, padrao: tuple[str, tuple[str, ...]], t_min: int
    ) -> tuple[int, Viagem, int, int] | None:
        chave = (parada_id, padrao)
        ocorrencias = self.tabela.get(chave)
        if not ocorrencias:
            return None

        idx = bisect.bisect_left(ocorrencias, (t_min, "", -100000))
        if idx >= len(ocorrencias):
            return None

        horario, _v_id, deslocamento, viagem, i = ocorrencias[idx]
        if horario - t_min > ESPERA_MAX_S:
            return None

        return (horario, viagem, i, deslocamento)


class Navegador:
    def __init__(self, rede: Rede) -> None:
        self.rede = rede
        self._cache_indices: dict[date, IndiceHorarios] = {}
        self._cache_vizinhas: dict[tuple[str, float], list[tuple[str, float]]] = {}
        self._grade: dict[tuple[int, int], list] = {}

        m_por_deg_lat = RAIO_TERRA_M * math.pi / 180.0
        for p in rede.paradas.values():
            m_por_deg_lon = m_por_deg_lat * math.cos(math.radians(p.lat))
            gx = int(math.floor((p.lon * m_por_deg_lon) / TAMANHO_CELULA_M))
            gy = int(math.floor((p.lat * m_por_deg_lat) / TAMANHO_CELULA_M))
            chave = (gx, gy)
            if chave not in self._grade:
                self._grade[chave] = []
            self._grade[chave].append(p)

    def indice(self, dia: date) -> IndiceHorarios:
        if dia not in self._cache_indices:
            self._cache_indices[dia] = IndiceHorarios(self.rede, dia)
        return self._cache_indices[dia]

    def proximas(
        self, lat: float, lon: float, raio_m: float
    ) -> list[tuple[str, float]]:
        m_por_deg_lat = RAIO_TERRA_M * math.pi / 180.0
        m_por_deg_lon = m_por_deg_lat * math.cos(math.radians(lat))
        gx_centro = int(math.floor((lon * m_por_deg_lon) / TAMANHO_CELULA_M))
        gy_centro = int(math.floor((lat * m_por_deg_lat) / TAMANHO_CELULA_M))

        delta_x = int(math.ceil(raio_m / TAMANHO_CELULA_M)) + 1
        delta_y = int(math.ceil(raio_m / TAMANHO_CELULA_M)) + 1

        resultado: list[tuple[str, float]] = []
        for gx in range(gx_centro - delta_x, gx_centro + delta_x + 1):
            for gy in range(gy_centro - delta_y, gy_centro + delta_y + 1):
                paradas_celula = self._grade.get((gx, gy))
                if paradas_celula:
                    for p in paradas_celula:
                        d = haversine((lat, lon), (p.lat, p.lon))
                        if d <= raio_m:
                            resultado.append((p.id, d))

        resultado.sort(key=lambda item: (item[1], item[0]))
        return resultado

    def vizinhas(self, parada_id: str, raio_m: float) -> list[tuple[str, float]]:
        chave = (parada_id, raio_m)
        if chave not in self._cache_vizinhas:
            p = self.rede.paradas[parada_id]
            res = [
                (pid, d)
                for pid, d in self.proximas(p.lat, p.lon, raio_m)
                if pid != parada_id
            ]
            self._cache_vizinhas[chave] = res
        return self._cache_vizinhas[chave]


def _montar_rota(
    nav: Navegador,
    origem: tuple[float, float],
    destino: tuple[float, float],
    t0: int,
    perfil: Perfil,
    k: int,
    p_dest_stop: str,
    destino_prox: dict[str, float],
    chegada: dict[int, dict],
) -> Rota:
    d_dest_walk = destino_prox[p_dest_stop]
    percurso = []
    curr_stop = p_dest_stop
    for r in range(k, 0, -1):
        _t_arr, pred = chegada[r][curr_stop]
        if pred[0] == "caminhada":
            _, p_from, d_walk, pred_veiculo = pred
            percurso.append(("caminhada", p_from, curr_stop, d_walk))
            _, viagem, i, j, deslocamento, p_board = pred_veiculo
            percurso.append(("veiculo", viagem, i, j, deslocamento, p_board, p_from))
            curr_stop = p_board
        elif pred[0] == "veiculo":
            _, viagem, i, j, deslocamento, p_board = pred
            percurso.append(("veiculo", viagem, i, j, deslocamento, p_board, curr_stop))
            curr_stop = p_board

    _t0_arr, pred_orig = chegada[0][curr_stop]
    _, d_orig = pred_orig
    percurso.reverse()

    agora = t0
    trechos: list[Trecho] = []
    v = perfil.velocidade_caminhada_ms

    # 1. Origem
    if d_orig >= 1.0:
        dur = seg_a_pe(d_orig, v)
        trechos.append(
            Trecho(
                tipo="caminhada",
                inicio_s=agora,
                fim_s=agora + dur,
                de="Origem",
                para=nav.rede.paradas[curr_stop].nome,
                distancia_m=d_orig,
                geometria=[origem, (nav.rede.paradas[curr_stop].lat, nav.rede.paradas[curr_stop].lon)],
            )
        )
    agora += seg_a_pe(d_orig, v)

    # 2. Trechos intermediários
    for step in percurso:
        if step[0] == "veiculo":
            _, viagem, i, j, deslocamento, p_board, p_alight = step
            dep = viagem.horarios[i] + deslocamento
            arr = viagem.horarios[j] + deslocamento
            nome_board = nav.rede.paradas[p_board].nome
            nome_alight = nav.rede.paradas[p_alight].nome
            if dep > agora:
                trechos.append(
                    Trecho(
                        tipo="espera",
                        inicio_s=agora,
                        fim_s=dep,
                        de=nome_board,
                        para=nome_board,
                        distancia_m=0.0,
                        geometria=[(nav.rede.paradas[p_board].lat, nav.rede.paradas[p_board].lon)],
                    )
                )
            geom = [
                (
                    nav.rede.paradas[viagem.paradas[idx_p]].lat,
                    nav.rede.paradas[viagem.paradas[idx_p]].lon,
                )
                for idx_p in range(i, j + 1)
            ]
            trechos.append(
                Trecho(
                    tipo="transporte",
                    inicio_s=dep,
                    fim_s=arr,
                    de=nome_board,
                    para=nome_alight,
                    distancia_m=0.0,
                    modal=viagem.modal,
                    operador=viagem.operador,
                    linha_id=viagem.linha_id,
                    nome_linha=viagem.nome_linha,
                    viagem_id=viagem.id,
                    parada_de=p_board,
                    parada_para=p_alight,
                    geometria=geom,
                )
            )
            agora = arr
        elif step[0] == "caminhada":
            _, p_from, p_to, d_walk = step
            if d_walk >= 1.0:
                dur = seg_a_pe(d_walk, v)
                trechos.append(
                    Trecho(
                        tipo="caminhada",
                        inicio_s=agora,
                        fim_s=agora + dur,
                        de=nav.rede.paradas[p_from].nome,
                        para=nav.rede.paradas[p_to].nome,
                        distancia_m=d_walk,
                        geometria=[
                            (nav.rede.paradas[p_from].lat, nav.rede.paradas[p_from].lon),
                            (nav.rede.paradas[p_to].lat, nav.rede.paradas[p_to].lon),
                        ],
                    )
                )
            agora += seg_a_pe(d_walk, v)

    # 3. Final
    if d_dest_walk >= 1.0:
        dur = seg_a_pe(d_dest_walk, v)
        trechos.append(
            Trecho(
                tipo="caminhada",
                inicio_s=agora,
                fim_s=agora + dur,
                de=nav.rede.paradas[p_dest_stop].nome,
                para="Destino",
                distancia_m=d_dest_walk,
                geometria=[(nav.rede.paradas[p_dest_stop].lat, nav.rede.paradas[p_dest_stop].lon), destino],
            )
        )
    agora += seg_a_pe(d_dest_walk, v)

    return Rota(trechos=trechos, saida_s=t0, chegada_s=agora)


def _busca(
    nav: Navegador,
    idx: IndiceHorarios,
    origem: tuple[float, float],
    destino: tuple[float, float],
    t0: int,
    perfil: Perfil,
    restricoes: Restricoes,
    max_rodadas: int,
) -> list[Rota]:
    origem_prox_lista = [
        (p, d)
        for p, d in nav.proximas(origem[0], origem[1], perfil.caminhada_max_m)
        if p not in restricoes.paradas_bloqueadas
    ]
    destino_prox = {
        p: d
        for p, d in nav.proximas(destino[0], destino[1], perfil.caminhada_max_m)
        if p not in restricoes.paradas_bloqueadas
    }

    if not origem_prox_lista or not destino_prox:
        return []

    chegada: dict[int, dict] = {}
    chegada[0] = {}
    melhor: dict[str, int] = {}

    for p, d in origem_prox_lista:
        t_arr = t0 + seg_a_pe(d, perfil.velocidade_caminhada_ms)
        chegada[0][p] = (t_arr, ("origem", d))
        melhor[p] = t_arr

    marcadas = sorted(chegada[0].keys())
    melhor_ch_aceito = float("inf")
    achados: list[Rota] = []

    for k in range(1, max_rodadas + 1):
        folga = FOLGA_BALDEACAO_S if k >= 2 else 0

        # Passo de veículo
        atual: dict[str, tuple[int, tuple]] = {}
        for p in marcadas:
            t = chegada[k - 1][p][0]
            padroes = idx.padroes_na_parada(p)
            for padrao in padroes:
                linha_id = padrao[0]
                if linha_id in restricoes.linhas_bloqueadas:
                    continue
                saida = idx.primeira_saida(p, padrao, t + folga)
                if saida is None:
                    continue
                horario, viagem, i, deslocamento = saida
                for j in range(i + 1, len(viagem.paradas)):
                    p2 = viagem.paradas[j]
                    if p2 in restricoes.paradas_bloqueadas:
                        continue
                    arr = viagem.horarios[j] + deslocamento
                    if arr < melhor.get(p2, float("inf")) and (
                        p2 not in atual or arr < atual[p2][0]
                    ):
                        atual[p2] = (
                            arr,
                            ("veiculo", viagem, i, j, deslocamento, p),
                        )

        # Passo a pé (uma perna por rodada)
        novos = dict(atual)
        raio_baldeacao = min(perfil.caminhada_max_m, CAMINHADA_BALDEACAO_MAX_M)
        for p2 in sorted(atual.keys()):
            arr, pred_veiculo = atual[p2]
            for p3, d in nav.vizinhas(p2, raio_baldeacao):
                if p3 in restricoes.paradas_bloqueadas or (p2, p3) in restricoes.trocas_bloqueadas:
                    continue
                t3 = arr + seg_a_pe(d, perfil.velocidade_caminhada_ms)
                if t3 < melhor.get(p3, float("inf")) and (
                    p3 not in novos or t3 < novos[p3][0]
                ):
                    novos[p3] = (t3, ("caminhada", p2, d, pred_veiculo))

        if not novos:
            break

        for p, (t_val, _) in novos.items():
            melhor[p] = min(melhor.get(p, float("inf")), t_val)

        chegada[k] = novos
        marcadas = sorted(novos.keys())

        # Candidata da rodada
        candidatos: list[tuple[int, str]] = []
        for p in novos:
            if p in destino_prox:
                ch = novos[p][0] + seg_a_pe(
                    destino_prox[p], perfil.velocidade_caminhada_ms
                )
                candidatos.append((ch, p))

        if candidatos:
            ch, p_escolhida = min(candidatos)
            if ch < melhor_ch_aceito:
                melhor_ch_aceito = ch
                rota = _montar_rota(
                    nav=nav,
                    origem=origem,
                    destino=destino,
                    t0=t0,
                    perfil=perfil,
                    k=k,
                    p_dest_stop=p_escolhida,
                    destino_prox=destino_prox,
                    chegada=chegada,
                )
                achados.append(rota)

    return achados


def buscar_rotas(
    nav: Navegador,
    origem: tuple[float, float],
    destino: tuple[float, float],
    partida: datetime.datetime,
    perfil: Perfil,
    restricoes: Restricoes | None = None,
    max_execucoes: int = MAX_EXECUCOES,
) -> list[Rota]:
    t0 = partida.hour * 3600 + partida.minute * 60 + partida.second
    idx = nav.indice(partida.date())
    if restricoes is None:
        restricoes = Restricoes()

    fila: list[Restricoes] = [restricoes]
    vistos: set[frozenset[str]] = {restricoes.linhas_bloqueadas}
    execucoes = 0
    rotas_por_assinatura: dict[tuple, Rota] = {}

    max_rodadas = (
        perfil.baldeacoes_max + 1
        if perfil.baldeacoes_max is not None
        else MAX_RODADAS_PADRAO
    )

    while fila and execucoes < max_execucoes:
        r = fila.pop(0)
        achadas = _busca(nav, idx, origem, destino, t0, perfil, r, max_rodadas)
        execucoes += 1
        for rota in achadas:
            if rota.assinatura not in rotas_por_assinatura:
                rotas_por_assinatura[rota.assinatura] = rota
            for t in rota.transportes:
                if t.linha_id:
                    novo = r.linhas_bloqueadas | {t.linha_id}
                    if novo not in vistos:
                        vistos.add(novo)
                        fila.append(
                            Restricoes(
                                paradas_bloqueadas=r.paradas_bloqueadas,
                                linhas_bloqueadas=novo,
                                trocas_bloqueadas=r.trocas_bloqueadas,
                            )
                        )

    # 4. Rota só a pé
    d_a_pe = haversine(origem, destino)
    if d_a_pe <= perfil.caminhada_max_m:
        dur_a_pe = seg_a_pe(d_a_pe, perfil.velocidade_caminhada_ms)
        trecho_a_pe = Trecho(
            tipo="caminhada",
            inicio_s=t0,
            fim_s=t0 + dur_a_pe,
            de="Origem",
            para="Destino",
            distancia_m=d_a_pe,
            geometria=[origem, destino],
        )
        rota_a_pe = Rota(
            trechos=[trecho_a_pe],
            saida_s=t0,
            chegada_s=t0 + dur_a_pe,
        )
        if rota_a_pe.assinatura not in rotas_por_assinatura:
            rotas_por_assinatura[rota_a_pe.assinatura] = rota_a_pe

    return list(rotas_por_assinatura.values())
