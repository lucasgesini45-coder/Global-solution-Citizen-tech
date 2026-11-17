"""Estimativas conservadoras de custo da viagem, sem confundir com tarifa confirmada."""
from datetime import datetime
from zoneinfo import ZoneInfo
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
            except (TypeError, ValueError, KeyError):
                pass
        elif modo in {"SUBWAY","METRO","RAIL","SUBURBAN","REGIONAL_RAIL"} and op in {"metro", "metro sp", "metro de sao paulo", "companhia do metropolitano de sao paulo", "cptm", "companhia paulista de trens metropolitanos", "viaquatro", "viamobilidade", "motiva", "tic trens", "trivia", "trivia trens"} and linha.startswith(("Linha 1 –","Linha 2 –","Linha 3 –","Linha 4 –","Linha 5 –","Linha 7 –","Linha 8 –","Linha 9 –","Linha 10 –","Linha 11 –","Linha 12 –","Linha 13 –","Linha 15 –")):
            valor = 540
        else:
            pendencias.append(f"{linha or modo}: tarifa não identificada para {e.get('operadora') or 'operadora desconhecida'}.")
            continue
        total += valor
        detalhes.append({"linha":linha or modo,"centavos":valor})
    return {"centavos":None if pendencias or not etapas else total,
            "status":"incompleto" if pendencias or not etapas else "estimativa",
            "detalhes":detalhes,"pendencias":pendencias,"fontes":FONTES,
            "data_referencia":DATA_REFERENCIA,
            "aviso":"Referência de tarifas comuns avulsas de 2026. Não pressupõe integração gratuita, meia tarifa ou benefícios. Tarifas podem mudar; não garante o valor cobrado."}
