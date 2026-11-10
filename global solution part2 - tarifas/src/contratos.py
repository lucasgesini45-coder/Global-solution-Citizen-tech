from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from src.config import (
    BALDEACOES_MAX_LIMITE,
    CAMINHADA_MAX_LIMITE_M,
    CAMINHADA_MAX_PADRAO_M,
    VELOCIDADE_CAMINHADA_PADRAO_MS,
)

# 4.1 Constantes de estado
ACESS_NAO_SOLICITADA = "NAO_SOLICITADA"
ACESS_COMPATIVEL = "COMPATIVEL_COM_DADOS_DISPONIVEIS"
ACESS_NAO_VERIFICADA = "NAO_VERIFICADA"
ACESS_INCOMPATIVEL = "INCOMPATIVEL"

SEG_SUFICIENTE = "dados_suficientes"
SEG_INSUFICIENTE = "dados_insuficientes"
SEG_INDISPONIVEL = "indisponivel"


# 4.2 Entrada de dados
@dataclass(frozen=True)
class Parada:
    id: str
    nome: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Viagem:
    id: str
    linha_id: str
    nome_linha: str
    operador: str
    modal: str  # "onibus", "metro" ou "trem"
    sentido: str
    paradas: tuple[str, ...]
    horarios: tuple[int, ...]
    dias_semana: frozenset[int] = frozenset(range(7))
    excecoes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if len(self.paradas) != len(self.horarios):
            raise ValueError("len(paradas) deve ser igual a len(horarios)")
        for i in range(len(self.horarios) - 1):
            if self.horarios[i] > self.horarios[i + 1]:
                raise ValueError("horarios não pode ser decrescente")

    @property
    def padrao(self) -> tuple[str, tuple[str, ...]]:
        return (self.linha_id, self.paradas)

    def opera_em(self, dia: date) -> bool:
        return dia.weekday() in self.dias_semana and dia.isoformat() not in self.excecoes


@dataclass
class Rede:
    paradas: dict[str, Parada]
    viagens: list[Viagem]
    versao: str = "sem_versao"
    origem_dados: str = "simulado"

    def validar(self) -> list[str]:
        mensagens: list[str] = []
        for v in self.viagens:
            for p in v.paradas:
                if p not in self.paradas:
                    mensagens.append(f"viagem {v.id} usa parada inexistente '{p}'")
        return mensagens

    def limites(self) -> tuple[float, float, float, float]:
        if not self.paradas:
            return (0.0, 0.0, 0.0, 0.0)
        lat_min = min(p.lat for p in self.paradas.values())
        lon_min = min(p.lon for p in self.paradas.values())
        lat_max = max(p.lat for p in self.paradas.values())
        lon_max = max(p.lon for p in self.paradas.values())
        return (lat_min, lon_min, lat_max, lon_max)


# 4.3 Pedido do passageiro
@dataclass
class Perfil:
    caminhada_max_m: int = CAMINHADA_MAX_PADRAO_M
    baldeacoes_max: int | None = None
    orcamento_max_centavos: int | None = None
    acessibilidade: frozenset[str] = frozenset()
    velocidade_caminhada_ms: float = VELOCIDADE_CAMINHADA_PADRAO_MS
    perfil_tarifario: str = "padrao"

    def problemas(self) -> list[str]:
        erros: list[str] = []
        if not (0 <= self.caminhada_max_m <= CAMINHADA_MAX_LIMITE_M):
            erros.append(f"caminhada_max_m deve estar entre 0 e {CAMINHADA_MAX_LIMITE_M}")
        if self.baldeacoes_max is not None and not (0 <= self.baldeacoes_max <= BALDEACOES_MAX_LIMITE):
            erros.append(f"baldeacoes_max deve estar entre 0 e {BALDEACOES_MAX_LIMITE}")
        if self.orcamento_max_centavos is not None and self.orcamento_max_centavos < 0:
            erros.append("orcamento_max_centavos não pode ser negativo")
        if not (0.5 <= self.velocidade_caminhada_ms <= 2.0):
            erros.append("velocidade_caminhada_ms deve estar entre 0.5 e 2.0")
        return erros


@dataclass(frozen=True)
class Restricoes:
    paradas_bloqueadas: frozenset[str] = frozenset()
    linhas_bloqueadas: frozenset[str] = frozenset()
    trocas_bloqueadas: frozenset[tuple[str, str]] = frozenset()


# 4.4 Saída
@dataclass
class Trecho:
    tipo: str  # "caminhada", "espera" ou "transporte"
    inicio_s: int
    fim_s: int
    de: str
    para: str
    distancia_m: float = 0.0
    modal: str | None = None
    operador: str | None = None
    linha_id: str | None = None
    nome_linha: str | None = None
    viagem_id: str | None = None
    parada_de: str | None = None
    parada_para: str | None = None
    geometria: list[tuple[float, float]] = field(default_factory=list)

    @property
    def duracao_s(self) -> int:
        return self.fim_s - self.inicio_s


@dataclass
class Custo:
    centavos: int | None = None
    confirmado: bool = False
    detalhe: list[str] = field(default_factory=list)
    regra_versao: str | None = None


@dataclass
class Rota:
    trechos: list[Trecho]
    saida_s: int
    chegada_s: int
    custo: Custo = field(default_factory=Custo)
    exposicao: float | None = None
    status_seguranca: str = SEG_INDISPONIVEL
    acessibilidade: str = ACESS_NAO_SOLICITADA
    ordem: int = 0
    motivos: list[str] = field(default_factory=list)
    fontes: list[dict] = field(default_factory=list)

    @property
    def transportes(self) -> list[Trecho]:
        return [t for t in self.trechos if t.tipo == "transporte"]

    @property
    def tempo_total_s(self) -> int:
        return self.chegada_s - self.saida_s

    @property
    def espera_s(self) -> int:
        return sum(t.duracao_s for t in self.trechos if t.tipo == "espera")

    @property
    def caminhada_s(self) -> int:
        return sum(t.duracao_s for t in self.trechos if t.tipo == "caminhada")

    @property
    def caminhada_m(self) -> int:
        return round(sum(t.distancia_m for t in self.trechos if t.tipo == "caminhada"))

    @property
    def baldeacoes(self) -> int:
        return max(len(self.transportes) - 1, 0)

    @property
    def linhas(self) -> tuple[str, ...]:
        return tuple(t.linha_id for t in self.transportes if t.linha_id is not None)

    @property
    def assinatura(self) -> tuple:
        if not self.transportes:
            return ("a_pe",)
        return tuple((t.linha_id, t.parada_de, t.parada_para) for t in self.transportes)

    def componentes_somam(self) -> bool:
        return (
            self.caminhada_s + self.espera_s + sum(t.duracao_s for t in self.transportes)
        ) == self.tempo_total_s

    def para_dict(self) -> dict:
        return {
            "ordem": self.ordem,
            "saida": fmt_hora(self.saida_s),
            "chegada": fmt_hora(self.chegada_s),
            "tempo_total_s": self.tempo_total_s,
            "tempo_total_min": round(self.tempo_total_s / 60),
            "espera_min": round(self.espera_s / 60),
            "caminhada_m": self.caminhada_m,
            "baldeacoes": self.baldeacoes,
            "custo": {
                "centavos": self.custo.centavos,
                "confirmado": self.custo.confirmado,
                "detalhe": list(self.custo.detalhe),
                "regra_versao": self.custo.regra_versao,
            },
            "seguranca": {
                "status": self.status_seguranca,
                "exposicao": self.exposicao,
            },
            "acessibilidade": self.acessibilidade,
            "motivos": list(self.motivos),
            "fontes": [dict(f) for f in self.fontes],
            "trechos": [
                {
                    "tipo": t.tipo,
                    "inicio": fmt_hora(t.inicio_s),
                    "fim": fmt_hora(t.fim_s),
                    "duracao_s": t.duracao_s,
                    "de": t.de,
                    "para": t.para,
                    "distancia_m": round(t.distancia_m),
                    "modal": t.modal,
                    "linha": t.nome_linha,
                    "linha_id": t.linha_id,
                    "geometria": [[float(lat), float(lon)] for lat, lon in t.geometria],
                }
                for t in self.trechos
            ],
        }


@dataclass
class RespostaRotas:
    rotas: list[Rota] = field(default_factory=list)
    aviso: str | None = None
    erro: dict | None = None
    criterios_usados: list[str] = field(default_factory=list)
    descartes: dict[str, int] = field(default_factory=dict)

    def para_dict(self) -> dict:
        return {
            "rotas": [r.para_dict() for r in self.rotas],
            "n_rotas": len(self.rotas),
            "aviso": self.aviso,
            "erro": self.erro,
            "criterios_usados": list(self.criterios_usados),
            "descartes": dict(self.descartes),
        }


# 4.5 Formatação
def fmt_hora(seg: int) -> str:
    dias, resto = divmod(int(seg), 86400)
    horas, resto_seg = divmod(resto, 3600)
    minutos = resto_seg // 60
    res = f"{horas:02d}:{minutos:02d}"
    if dias != 0:
        res += f" ({dias:+d}d)"
    return res
