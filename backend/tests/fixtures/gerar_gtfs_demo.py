# encoding: utf-8
"""Gera a fixture gtfs_mini (.zip) a partir da rede demo."""

import io
import math
from pathlib import Path
import zipfile

from backend.src.rotas.config import RAIO_TERRA_M
from backend.tests.fixtures.rede_demo import criar_rede_demo, ponto


def segundos_para_hhmmss(seg: int) -> str:
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def gerar_gtfs_mini_zip(destino_zip: Path | str | None = None) -> bytes:
    rede = criar_rede_demo()
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # agency.txt
        z.writestr(
            "agency.txt",
            "agency_id,agency_name,agency_url,agency_timezone\n"
            "sptrans,SPTrans,https://www.sptrans.com.br,America/Sao_Paulo\n",
        )
        
        # stops.txt
        linhas_stops = ["stop_id,stop_name,stop_lat,stop_lon"]
        for p in rede.paradas.values():
            linhas_stops.append(f"{p.id},{p.nome},{p.lat:.6f},{p.lon:.6f}")
        z.writestr("stops.txt", "\n".join(linhas_stops) + "\n")
        
        # routes.txt
        # M1 -> route_type 1 (metro), L100/L200/L300 -> route_type 3 (onibus)
        linhas_routes = [
            "route_id,agency_id,route_short_name,route_long_name,route_type",
            "M1,sptrans,M1,Metrô Linha 1,1",
            "L100,sptrans,100,Ônibus 100,3",
            "L200,sptrans,200,Ônibus 200,3",
            "L300,sptrans,300,Ônibus 300,3",
        ]
        z.writestr("routes.txt", "\n".join(linhas_routes) + "\n")
        
        # calendar.txt e calendar_dates.txt
        # Servico U: todos os dias (M1, L200, L300)
        # Servico DU: dias uteis 0,1,2,3,4 (L100)
        linhas_calendar = [
            "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
            "SERV_TODOS,1,1,1,1,1,1,1,20260101,20261231",
            "SERV_UTEIS,1,1,1,1,1,0,0,20260101,20261231",
        ]
        z.writestr("calendar.txt", "\n".join(linhas_calendar) + "\n")
        
        linhas_calendar_dates = [
            "service_id,date,exception_type",
            "SERV_UTEIS,20261120,2",  # 2 = removido
        ]
        z.writestr("calendar_dates.txt", "\n".join(linhas_calendar_dates) + "\n")
        
        # trips.txt e stop_times.txt
        linhas_trips = ["route_id,service_id,trip_id,trip_headsign,direction_id"]
        linhas_stop_times = ["trip_id,arrival_time,departure_time,stop_id,stop_sequence"]
        
        for v in rede.viagens:
            serv = "SERV_UTEIS" if v.linha_id == "L100" else "SERV_TODOS"
            linhas_trips.append(f"{v.linha_id},{serv},{v.id},{v.nome_linha},0")
            for seq, (p_id, t) in enumerate(zip(v.paradas, v.horarios), start=1):
                hora_str = segundos_para_hhmmss(t)
                linhas_stop_times.append(f"{v.id},{hora_str},{hora_str},{p_id},{seq}")
                
        z.writestr("trips.txt", "\n".join(linhas_trips) + "\n")
        z.writestr("stop_times.txt", "\n".join(linhas_stop_times) + "\n")
        
        # feed_info.txt
        z.writestr(
            "feed_info.txt",
            "feed_publisher_name,feed_publisher_url,feed_lang,feed_version,feed_start_date,feed_end_date\n"
            "SPTrans,https://www.sptrans.com.br,pt,gtfs-mini-1.0,20260101,20261231\n",
        )
        
    conteudo = buffer.getvalue()
    if destino_zip is not None:
        caminho = Path(destino_zip)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "wb") as fp:
            fp.write(conteudo)
    return conteudo


if __name__ == "__main__":
    destino = Path(__file__).resolve().parent / "gtfs_mini.zip"
    gerar_gtfs_mini_zip(destino)
    print(f"gtfs_mini.zip gerado em: {destino}")
