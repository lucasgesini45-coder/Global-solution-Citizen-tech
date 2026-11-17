"""Estimativas conservadoras de custo da viagem, sem confundir com tarifa confirmada."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import unicodedata

FONTES = ["https://www.sptrans.com.br/tarifas", "https://www.metro.sp.gov.br/sua-viagem/bilhetes-cartoes/",
          "https://www.sptrans.com.br/perguntas-e-respostas/?sobre=tarifa-zero"]
DATA_REFERENCIA = "2026-11-17"


def normalizar(txt):
    return " ".join(unicodedata.normalize("NFKD", str(txt or "")).encode("ascii","ignore").decode().lower().split())


def estimar(etapas):
    """Soma embarques avulsos conhecidos, sem presumir integrações ou benefícios.
    Uma linha/operadora desconhecida invalida a estimativa do total."""
    total, detalhes, pendencias = 0, [], []
    for e in etapas:
        modo = e.get("modal")
        if modo == "WALK":
            continue
        op = normalizar(e.get("operadora"))
        linha = str(e.get("linha") or "")
        if modo == "BUS" and op in {"sptrans", "sao paulo transporte s/a", "sao paulo transporte s.a.", "sao paulo transporte sa", "sao paulo transporte"}:
            valor = 530
            try:
                partida = datetime.fromisoformat(e["partida"]).astimezone(ZoneInfo("America/Sao_Paulo"))
                if partida.weekday() == 6:
                    valor = 0
            except (TypeError, ValueError, KeyError, ZoneInfoNotFoundError):
                pass
        elif modo in {"SUBWAY","METRO","RAIL","SUBURBAN","REGIONAL_RAIL"} and op in {"metro", "metro sp", "metro de sao paulo", "companhia do metropolitano de sao paulo", "cptm", "companhia paulista de trens metropolitanos", "viaquatro", "viamobilidade", "motiva", "tic trens", "trivia", "trivia trens"} and linha.startswith(("Linha 1 –","Linha 2 –","Linha 3 –","Linha 4 –","Linha 5 –","Linha 7 –","Linha 8 –","Linha 9 –","Linha 10 –","Linha 11 –","Linha 12 –","Linha 13 –","Linha 15 –")):
            valor = 540
        else:
            pendencias.append(f"{linha or modo}: tarifa não identificada para {e.get('operadora') or 'operadora desconhecida'}.")
            continue
        total += valor
        detalhes.append({"linha":linha or modo,"centavos":valor})
    # Cenário opcional: crédito eletrônico COMUM do Bilhete Único,
    # somente quando os horários, operadores e linhas sustentam as condições.
    integrada = None
    condicao = None
    pagos = [e for e in etapas if e.get("modal") != "WALK"]
    if pagos and not pendencias:
        try:
            horarios = [datetime.fromisoformat(e["partida"]).astimezone(ZoneInfo("America/Sao_Paulo")) for e in pagos]
            if any(datetime.fromisoformat(e["partida"]).tzinfo is None for e in pagos):
                raise ValueError("horário sem fuso")
            primeiro = min(horarios)
            mesmos_dias = all(h.date() == primeiro.date() and h.weekday() != 6 for h in horarios)
            buses = [e for e in pagos if e["modal"] == "BUS"]
            trilhos = [e for e in pagos if e["modal"] != "BUS"]
            linhas_bus = [e.get("linha") for e in buses]
            distintas = all(linhas_bus) and len(set(linhas_bus)) == len(buses)
            if mesmos_dias and distintas and max(horarios) - primeiro <= timedelta(hours=3):
                if len(trilhos) == 0 and 1 <= len(buses) <= 4:
                    integrada = 530
                    condicao = "Cenário Bilhete Único Comum: até quatro ônibus municipais diferentes em três horas."
                elif len(trilhos) == 1 and 1 <= len(buses) <= 3 and all(h-primeiro <= timedelta(hours=2) for e,h in zip(pagos,horarios) if e["modal"] != "BUS"):
                    integrada = 938
                    condicao = "Cenário Bilhete Único Comum: até três ônibus municipais diferentes em três horas e um embarque ferroviário nas duas primeiras horas."
        except (TypeError, ValueError, KeyError, ZoneInfoNotFoundError):
            pass
    return {"centavos":None if pendencias or not etapas else total,
            "integracao_centavos": integrada, "integracao_condicao": condicao,
            "status":"incompleto" if pendencias or not etapas else "estimativa",
            "detalhes":detalhes,"pendencias":pendencias,"fontes":FONTES,
            "data_referencia":DATA_REFERENCIA,
            "aviso":"Referência de tarifas comuns avulsas de 2026. Não pressupõe integração gratuita, meia tarifa ou benefícios. Tarifas podem mudar; não garante o valor cobrado."}
