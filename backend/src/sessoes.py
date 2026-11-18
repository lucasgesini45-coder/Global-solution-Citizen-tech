# encoding: utf-8
"""Sessão colaborativa básica (parte 5 - Servidor e integração).

Duas ou mais pessoas (por exemplo, uma pessoa com mobilidade reduzida e quem a
acompanha) compartilham o MESMO planejamento: origem, destino, modal,
preferências e a alternativa de rota escolhida.

Decisões de projeto
-------------------
* Tudo fica em memória do servidor local. Nada é gravado em disco ou no SQLite.
* A sessão expira após TTL_SESSAO_S segundos sem atividade (padrão: 2 h).
* Não há conta, e-mail, telefone ou GPS contínuo: só um apelido por pessoa.
* Quem cria a sessão recebe um código curto para convidar os outros; cada
  participante recebe um token secreto, exigido em toda operação posterior.
* Só usa GET/POST e o cabeçalho Content-Type, para continuar compatível com a
  política de CORS definida em backend/src/api.py (o token vai no corpo JSON).
* O estado compartilhado é versionado. Os clientes consultam por polling
  (POST /sessoes/{codigo}/sincronizar com "desde") e recebem só o que mudou.
* Conflitos: quem envia "versao_base" diferente da versão atual recebe 409 com o
  estado vigente, evitando que uma edição apague a outra sem querer.

Este módulo não calcula rotas nem afirma acessibilidade: apenas guarda o que os
participantes escolheram. Os cálculos continuam nos módulos de rotas e
acessibilidade e seus avisos de incerteza não são alterados aqui.
"""
from __future__ import annotations

import re
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enderecos_api import Coordenadas

# ---------------------------------------------------------------- constantes
CODIGO_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sem I, L, O, 0 e 1
CODIGO_TAMANHO = 6
TTL_SESSAO_S = 2 * 60 * 60
MAX_PARTICIPANTES = 6
MAX_SESSOES_ATIVAS = 200
MAX_EVENTOS = 100
APELIDO_MAX = 30
ROTULO_MAX = 120
MAX_ALTERNATIVAS = 3  # o planejador exibe até três opções de rota
MODAIS_VALIDOS = ("todos", "onibus", "ferroviario", "ape")
CAMPOS_PLANEJAMENTO = (
    "origem", "destino", "modal", "priorizar_menos_caminhada", "evitar_escadas",
)
AVISO_PRIVACIDADE = (
    "Sessão temporária guardada apenas na memória do servidor. Expira após 2 horas "
    "sem atividade e não guarda histórico nem localização contínua. Não escreva "
    "dados pessoais. Não é um canal oficial de operadores de transporte."
)

_PADRAO_CODIGO = re.compile(rf"^[{CODIGO_ALFABETO}]{{{CODIGO_TAMANHO}}}$")
_PADRAO_EMAIL = re.compile(r"\S+@\S+")
_PADRAO_TELEFONE = re.compile(r"(?:\d[\s().-]*){8,}")


# ------------------------------------------------------------------- erros
class ErroSessao(Exception):
    """Erro de regra de negócio, convertido em HTTPException pela camada HTTP."""

    def __init__(self, status: int, mensagem: str, extra: dict | None = None):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem
        self.extra = extra or {}


def validar_apelido(valor: str | None, padrao: str) -> str:
    """Normaliza o apelido e recusa o que parece dado pessoal sensível."""
    if valor is None or not valor.strip():
        return padrao
    apelido = " ".join(valor.split())
    if len(apelido) > APELIDO_MAX:
        raise ErroSessao(422, f"O apelido deve ter no máximo {APELIDO_MAX} caracteres.")
    if any(ord(c) < 32 for c in apelido):
        raise ErroSessao(422, "O apelido contém caracteres inválidos.")
    if _PADRAO_EMAIL.search(apelido) or _PADRAO_TELEFONE.search(apelido):
        raise ErroSessao(
            422, "Use apenas um apelido, sem e-mail, telefone ou outros dados pessoais.")
    return apelido


# ------------------------------------------------------------- gerenciador
class _Participante:
    __slots__ = ("id", "apelido", "token")

    def __init__(self, id_: int, apelido: str):
        self.id = id_
        self.apelido = apelido
        self.token = secrets.token_urlsafe(16)


class _Sessao:
    def __init__(self, codigo: str, agora: float):
        self.codigo = codigo
        self.criada_em = agora
        self.atividade_em = agora
        self.versao = 0
        self.participantes: dict[int, _Participante] = {}
        self.criador_id: int | None = None
        self.proximo_id = 1
        self.estado = estado_inicial()
        self.eventos: list[dict] = []


def estado_inicial() -> dict:
    return {
        "origem": None,
        "destino": None,
        "modal": "todos",
        "priorizar_menos_caminhada": False,
        "evitar_escadas": False,
        "rota_selecionada": None,
    }


def _iso(instante: float) -> str:
    return datetime.fromtimestamp(instante, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class GerenciadorSessoes:
    """Armazena as sessões em memória, com trava para uso por várias threads."""

    def __init__(self, relogio: Callable[[], float] = time.time,
                 ttl_s: int = TTL_SESSAO_S, max_sessoes: int = MAX_SESSOES_ATIVAS,
                 max_participantes: int = MAX_PARTICIPANTES):
        self._relogio = relogio
        self._ttl_s = ttl_s
        self._max_sessoes = max_sessoes
        self._max_participantes = max_participantes
        self._sessoes: dict[str, _Sessao] = {}
        self._trava = threading.RLock()

    # -- utilidades internas
    def _expirar(self) -> None:
        agora = self._relogio()
        vencidas = [c for c, s in self._sessoes.items() if agora - s.atividade_em > self._ttl_s]
        for codigo in vencidas:
            del self._sessoes[codigo]

    def _obter(self, codigo: str) -> _Sessao:
        self._expirar()
        chave = (codigo or "").strip().upper()
        sessao = self._sessoes.get(chave) if _PADRAO_CODIGO.match(chave) else None
        if sessao is None:
            raise ErroSessao(404, "Sessão não encontrada ou expirada.")
        return sessao

    @staticmethod
    def _participante(sessao: _Sessao, token: str) -> _Participante:
        # Compara em tempo constante para não vazar informação sobre o token.
        encontrado = None
        for p in sessao.participantes.values():
            if secrets.compare_digest(p.token, token or ""):
                encontrado = p
        if encontrado is None:
            raise ErroSessao(403, "Token da sessão inválido.")
        return encontrado

    def _registrar(self, sessao: _Sessao, tipo: str, participante: _Participante,
                   campos: list[str] | None = None) -> None:
        agora = self._relogio()
        sessao.versao += 1
        sessao.atividade_em = agora
        sessao.eventos.append({
            "versao": sessao.versao, "tipo": tipo,
            "participante": participante.apelido, "campos": campos or [],
            "em": _iso(agora),
        })
        del sessao.eventos[:-MAX_EVENTOS]

    def _adicionar(self, sessao: _Sessao, apelido: str | None) -> _Participante:
        if len(sessao.participantes) >= self._max_participantes:
            raise ErroSessao(409, f"A sessão já tem o máximo de {self._max_participantes} participantes.")
        base = validar_apelido(apelido, f"Participante {sessao.proximo_id}")
        usados = {p.apelido.casefold() for p in sessao.participantes.values()}
        final, n = base, 2
        while final.casefold() in usados:
            sufixo = f" ({n})"
            final = base[: APELIDO_MAX - len(sufixo)] + sufixo
            n += 1
        participante = _Participante(sessao.proximo_id, final)
        sessao.proximo_id += 1
        sessao.participantes[participante.id] = participante
        return participante

    def _visao(self, sessao: _Sessao, desde: int | None = None) -> dict:
        eventos = [e for e in sessao.eventos if desde is None or e["versao"] > desde]
        return {
            "codigo": sessao.codigo,
            "versao": sessao.versao,
            "estado": dict(sessao.estado),
            "participantes": [
                {"id": p.id, "apelido": p.apelido, "criador": p.id == sessao.criador_id}
                for p in sessao.participantes.values()
            ],
            "eventos": [dict(e) for e in eventos],
            "expira_em": _iso(sessao.atividade_em + self._ttl_s),
        }

    # -- operações públicas
    def total_ativas(self) -> int:
        with self._trava:
            self._expirar()
            return len(self._sessoes)

    def limpar(self) -> None:
        with self._trava:
            self._sessoes.clear()

    def criar(self, apelido: str | None = None) -> dict:
        with self._trava:
            self._expirar()
            if len(self._sessoes) >= self._max_sessoes:
                raise ErroSessao(503, "Limite de sessões ativas atingido. Tente novamente mais tarde.")
            codigo = ""
            while not codigo or codigo in self._sessoes:
                codigo = "".join(secrets.choice(CODIGO_ALFABETO) for _ in range(CODIGO_TAMANHO))
            sessao = _Sessao(codigo, self._relogio())
            participante = self._adicionar(sessao, apelido)
            sessao.criador_id = participante.id
            self._sessoes[codigo] = sessao
            self._registrar(sessao, "criada", participante)
            return {**self._visao(sessao), "token": participante.token,
                    "participante_id": participante.id}

    def entrar(self, codigo: str, apelido: str | None = None) -> dict:
        with self._trava:
            sessao = self._obter(codigo)
            participante = self._adicionar(sessao, apelido)
            self._registrar(sessao, "entrou", participante)
            return {**self._visao(sessao), "token": participante.token,
                    "participante_id": participante.id}

    def sincronizar(self, codigo: str, token: str, desde: int | None = None) -> dict:
        with self._trava:
            sessao = self._obter(codigo)
            self._participante(sessao, token)
            return self._visao(sessao, desde)

    def atualizar_estado(self, codigo: str, token: str, mudancas: dict,
                         versao_base: int | None = None) -> dict:
        """Aplica mudanças parciais. Chave presente com None limpa o campo permitido."""
        with self._trava:
            sessao = self._obter(codigo)
            participante = self._participante(sessao, token)
            if not mudancas:
                raise ErroSessao(422, "Nenhuma alteração informada.")
            if versao_base is not None and versao_base != sessao.versao:
                raise ErroSessao(
                    409, "O planejamento foi alterado por outra pessoa. Revise e envie novamente.",
                    {"versao_atual": sessao.versao, "estado": dict(sessao.estado)})
            alterados = [c for c, v in mudancas.items() if sessao.estado.get(c) != v]
            if not alterados:
                return {**self._visao(sessao), "alterado": False}
            sessao.estado.update({c: mudancas[c] for c in alterados})
            # Mudar o planejamento invalida a alternativa escolhida antes.
            if "rota_selecionada" not in mudancas and any(c in CAMPOS_PLANEJAMENTO for c in alterados):
                if sessao.estado["rota_selecionada"] is not None:
                    sessao.estado["rota_selecionada"] = None
                    alterados.append("rota_selecionada")
            self._registrar(sessao, "estado", participante, alterados)
            return {**self._visao(sessao), "alterado": True}

    def sair(self, codigo: str, token: str) -> dict:
        with self._trava:
            sessao = self._obter(codigo)
            participante = self._participante(sessao, token)
            del sessao.participantes[participante.id]
            if not sessao.participantes:
                del self._sessoes[sessao.codigo]
                return {"encerrada": True, "codigo": sessao.codigo}
            if sessao.criador_id == participante.id:
                sessao.criador_id = next(iter(sessao.participantes))
            self._registrar(sessao, "saiu", participante)
            return {"encerrada": False, "codigo": sessao.codigo, "versao": sessao.versao}

    def encerrar(self, codigo: str, token: str) -> dict:
        with self._trava:
            sessao = self._obter(codigo)
            participante = self._participante(sessao, token)
            if participante.id != sessao.criador_id:
                raise ErroSessao(403, "Somente quem criou a sessão pode encerrá-la.")
            del self._sessoes[sessao.codigo]
            return {"encerrada": True, "codigo": sessao.codigo}


# --------------------------------------------------------------- camada HTTP
router = APIRouter(prefix="/sessoes", tags=["Sessão colaborativa"])
_gerenciador = GerenciadorSessoes()


def obter_gerenciador() -> GerenciadorSessoes:
    return _gerenciador


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PontoSessao(Coordenadas):
    rotulo: str | None = Field(default=None, max_length=ROTULO_MAX)

    @field_validator("rotulo")
    @classmethod
    def _limpar(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpo = " ".join(valor.split())
        return limpo or None


class NovaSessao(_Base):
    apelido: str | None = None


class EntradaSessao(_Base):
    apelido: str | None = None


class SincronizarPedido(_Base):
    token: str = Field(min_length=1, max_length=100)
    desde: int | None = Field(default=None, ge=0)


class TokenPedido(_Base):
    token: str = Field(min_length=1, max_length=100)


class AtualizacaoEstado(_Base):
    token: str = Field(min_length=1, max_length=100)
    versao_base: int | None = Field(default=None, ge=0)
    origem: PontoSessao | None = None
    destino: PontoSessao | None = None
    modal: Literal["todos", "onibus", "ferroviario", "ape"] | None = None
    priorizar_menos_caminhada: bool | None = None
    evitar_escadas: bool | None = None
    rota_selecionada: int | None = Field(default=None, ge=0, lt=MAX_ALTERNATIVAS)

    @model_validator(mode="after")
    def _campos_obrigatorios_nao_nulos(self):
        # Só origem, destino e rota_selecionada podem ser limpos com null.
        for campo in ("modal", "priorizar_menos_caminhada", "evitar_escadas"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"'{campo}' não pode ser nulo.")
        return self

    def mudancas(self) -> dict:
        saida = {}
        for campo in CAMPOS_PLANEJAMENTO + ("rota_selecionada",):
            if campo in self.model_fields_set:
                valor = getattr(self, campo)
                saida[campo] = valor.model_dump() if isinstance(valor, BaseModel) else valor
        return saida


def _responder(chamada: Callable[[], dict]) -> dict:
    try:
        return {**chamada(), "aviso": AVISO_PRIVACIDADE}
    except ErroSessao as exc:
        detalhe = {"mensagem": exc.mensagem, **exc.extra} if exc.extra else exc.mensagem
        raise HTTPException(status_code=exc.status, detail=detalhe) from exc


@router.post("", status_code=201)
def criar_sessao(corpo: NovaSessao, g: GerenciadorSessoes = Depends(obter_gerenciador)):
    """Cria a sessão e devolve o código para convidar e o token de quem criou."""
    return _responder(lambda: g.criar(corpo.apelido))


@router.post("/{codigo}/entrar")
def entrar_na_sessao(codigo: str, corpo: EntradaSessao,
                     g: GerenciadorSessoes = Depends(obter_gerenciador)):
    return _responder(lambda: g.entrar(codigo, corpo.apelido))


@router.post("/{codigo}/sincronizar")
def sincronizar_sessao(codigo: str, corpo: SincronizarPedido,
                       g: GerenciadorSessoes = Depends(obter_gerenciador)):
    """Estado atual e eventos posteriores à versão 'desde' (polling)."""
    return _responder(lambda: g.sincronizar(codigo, corpo.token, corpo.desde))


@router.post("/{codigo}/estado")
def atualizar_estado_sessao(codigo: str, corpo: AtualizacaoEstado,
                            g: GerenciadorSessoes = Depends(obter_gerenciador)):
    """Atualiza só os campos enviados. 'versao_base' ativa a detecção de conflito."""
    return _responder(
        lambda: g.atualizar_estado(codigo, corpo.token, corpo.mudancas(), corpo.versao_base))


@router.post("/{codigo}/sair")
def sair_da_sessao(codigo: str, corpo: TokenPedido,
                   g: GerenciadorSessoes = Depends(obter_gerenciador)):
    return _responder(lambda: g.sair(codigo, corpo.token))


@router.post("/{codigo}/encerrar")
def encerrar_sessao(codigo: str, corpo: TokenPedido,
                    g: GerenciadorSessoes = Depends(obter_gerenciador)):
    """Apaga a sessão para todos. Somente quem a criou (ou herdou a criação) pode."""
    return _responder(lambda: g.encerrar(codigo, corpo.token))
