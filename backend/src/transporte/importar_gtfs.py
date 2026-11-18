# encoding: utf-8
"""Importador oficial de dados GTFS para o banco SQLite único (Seção 7)."""

import argparse
import csv
import hashlib
import io
import math
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
import zipfile

from backend.src.config_app import RAIZ_REPOSITORIO
from backend.src.db.conexao import iniciar_banco
from backend.src.rotas.config import LOTE_IMPORTACAO, RAIO_TERRA_M, TAMANHO_CELULA_M
from .validacao import mapear_modal, parse_hhmmss_para_segundos, ponto_em_sp_limites


def calcular_sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def calcular_celula(lat: float, lon: float) -> tuple[int, int]:
    m_por_deg_lat = RAIO_TERRA_M * math.pi / 180.0
    m_por_deg_lon = m_por_deg_lat * math.cos(math.radians(lat))
    gx = int(math.floor((lon * m_por_deg_lon) / TAMANHO_CELULA_M))
    gy = int(math.floor((lat * m_por_deg_lat) / TAMANHO_CELULA_M))
    return gx, gy


def formatar_data_iso(data_str: str) -> str:
    """Converte YYYYMMDD ou YYYY-MM-DD para YYYY-MM-DD."""
    s = data_str.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s


def importar_gtfs(
    sistema: str,
    caminho_zip: str | Path,
    fonte_url: str,
    origem_dados: str = "real",
    caminho_banco: str | Path | None = None,
    hoje: datetime | None = None,
) -> dict:
    inicio_tempo = datetime.now()
    if sistema not in ("sptrans", "metroferroviario", "emtu"):
        raise ValueError(f"Sistema inválido: '{sistema}'. Deve ser sptrans, metroferroviario ou emtu.")
    if origem_dados not in ("real", "historico", "teste"):
        raise ValueError(f"origem_dados inválida: '{origem_dados}'. Deve ser real, historico ou teste.")

    zip_path = Path(caminho_zip)
    if not zip_path.is_file():
        raise FileNotFoundError(f"Arquivo GTFS não encontrado: {zip_path}")

    arquivo_sha256 = calcular_sha256(zip_path)
    
    # Conectar ao banco
    con = iniciar_banco(caminho_banco)
    
    # GT-08: Idempotência
    cur = con.cursor()
    cur.execute(
        "SELECT id, versao FROM feeds WHERE sistema = ? AND arquivo_sha256 = ?",
        (sistema, arquivo_sha256),
    )
    ja_existe = cur.fetchone()
    if ja_existe:
        print("Feed já importado.")
        con.close()
        return {
            "status": "ja_importado",
            "feed_id": ja_existe["id"],
            "versao": ja_existe["versao"],
        }

    # GT-01: Ler o zip sem extrair em disco
    with zipfile.ZipFile(zip_path, "r") as z:
        arquivos_no_zip = set(z.namelist())
        obrigatorios = {"stops.txt", "routes.txt", "trips.txt", "stop_times.txt"}
        faltantes = obrigatorios - arquivos_no_zip
        if faltantes:
            con.close()
            raise ValueError(f"Arquivos obrigatórios ausentes no GTFS: {sorted(faltantes)}")
        if "calendar.txt" not in arquivos_no_zip and "calendar_dates.txt" not in arquivos_no_zip:
            con.close()
            raise ValueError("O GTFS deve conter ao menos calendar.txt ou calendar_dates.txt")

        # 1. agency.txt (opcional)
        operador_padrao = sistema.upper()
        agency_map = {}
        if "agency.txt" in arquivos_no_zip:
            with z.open("agency.txt") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                for row in reader:
                    aid = row.get("agency_id") or "default"
                    name = row.get("agency_name") or operador_padrao
                    agency_map[aid] = name
                    if not operador_padrao or operador_padrao == sistema.upper():
                        operador_padrao = name

        # 2. stops.txt
        paradas_raw = {}
        paradas_fora_limite = {}
        with z.open("stops.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                sid = row["stop_id"].strip()
                nome = row.get("stop_name", "").strip()
                lat = float(row["stop_lat"])
                lon = float(row["stop_lon"])
                if ponto_em_sp_limites(lat, lon):
                    gx, gy = calcular_celula(lat, lon)
                    paradas_raw[sid] = {
                        "nome": nome,
                        "lat": lat,
                        "lon": lon,
                        "celula_x": gx,
                        "celula_y": gy,
                    }
                else:
                    paradas_fora_limite[sid] = {"nome": nome, "lat": lat, "lon": lon}

        # 3. routes.txt
        linhas_raw = {}
        linhas_ignoradas_motivo = {}
        with z.open("routes.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                rid = row["route_id"].strip()
                modal = mapear_modal(sistema, row.get("route_type"))
                if modal is None:
                    linhas_ignoradas_motivo[rid] = f"route_type não suportado ({row.get('route_type')})"
                    continue
                operador = agency_map.get(row.get("agency_id"), operador_padrao)
                linhas_raw[rid] = {
                    "nome_curto": (row.get("route_short_name") or row.get("route_long_name") or rid).strip(),
                    "nome_longo": (row.get("route_long_name") or "").strip() or None,
                    "operador": operador,
                    "modal": modal,
                }

        # 4. calendar.txt e calendar_dates.txt
        servicos_raw = {}
        validade_inicio_cand = []
        validade_fim_cand = []
        if "calendar.txt" in arquivos_no_zip:
            with z.open("calendar.txt") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                for row in reader:
                    svid = row["service_id"].strip()
                    ini = formatar_data_iso(row["start_date"])
                    fim = formatar_data_iso(row["end_date"])
                    validade_inicio_cand.append(ini)
                    validade_fim_cand.append(fim)
                    servicos_raw[svid] = {
                        "dia0": int(row["monday"]),
                        "dia1": int(row["tuesday"]),
                        "dia2": int(row["wednesday"]),
                        "dia3": int(row["thursday"]),
                        "dia4": int(row["friday"]),
                        "dia5": int(row["saturday"]),
                        "dia6": int(row["sunday"]),
                        "inicio": ini,
                        "fim": fim,
                    }

        servicos_excecoes_raw = []
        if "calendar_dates.txt" in arquivos_no_zip:
            with z.open("calendar_dates.txt") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                for row in reader:
                    svid = row["service_id"].strip()
                    data = formatar_data_iso(row["date"])
                    tipo = int(row["exception_type"])
                    validade_inicio_cand.append(data)
                    validade_fim_cand.append(data)
                    servicos_excecoes_raw.append({
                        "servico_id": svid,
                        "data": data,
                        "tipo": tipo,
                    })
                    if svid not in servicos_raw:
                        servicos_raw[svid] = {
                            "dia0": 0, "dia1": 0, "dia2": 0, "dia3": 0,
                            "dia4": 0, "dia5": 0, "dia6": 0,
                            "inicio": data,
                            "fim": data,
                        }

        # 5. trips.txt
        trips_info = {}
        with z.open("trips.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                tid = row["trip_id"].strip()
                rid = row["route_id"].strip()
                if rid not in linhas_raw:
                    continue
                svid = row["service_id"].strip()
                sentido = row.get("direction_id", "0").strip() or "0"
                trips_info[tid] = {
                    "linha_id": rid,
                    "servico_id": svid,
                    "sentido": sentido,
                }

        # 6. stop_times.txt
        trip_stop_times = {}
        interpolacoes_feitas = 0
        with z.open("stop_times.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                tid = row["trip_id"].strip()
                if tid not in trips_info:
                    continue
                sid = row["stop_id"].strip()
                seq = int(row["stop_sequence"])
                arr = row.get("arrival_time", "").strip()
                dep = row.get("departure_time", "").strip()
                
                # Checar existência da parada no arquivo stops.txt
                if sid not in paradas_raw and sid not in paradas_fora_limite:
                    con.close()
                    raise ValueError(f"stop_times referencia parada inexistente: {sid}")
                    
                arr_s = parse_hhmmss_para_segundos(arr) if arr else None
                dep_s = parse_hhmmss_para_segundos(dep) if dep else None
                hora_s = dep_s if dep_s is not None else arr_s
                
                if tid not in trip_stop_times:
                    trip_stop_times[tid] = []
                trip_stop_times[tid].append((seq, sid, hora_s))

        # 7. Interpolação e validação de horários de cada viagem
        viagens_processadas = {}
        viagens_ignoradas_menos_de_2_paradas = 0
        paradas_referenciadas_usadas = set()
        
        for tid, st_list in trip_stop_times.items():
            st_list.sort(key=lambda x: x[0])
            
            # Interpolação linear se houver horários vazios
            horarios = [item[2] for item in st_list]
            if None in horarios:
                n = len(horarios)
                # Encontrar trechos vazios entre conhecidos
                i = 0
                while i < n:
                    if horarios[i] is None:
                        # Buscar proximo conhecido
                        j = i
                        while j < n and horarios[j] is None:
                            j += 1
                        if i == 0 or j == n:
                            con.close()
                            raise ValueError(f"Não é possível interpolar horários nas extremidades da viagem {tid}")
                        t_ini = horarios[i - 1]
                        t_fim = horarios[j]
                        passo = (t_fim - t_ini) / (j - (i - 1))
                        for k in range(i, j):
                            horarios[k] = int(round(t_ini + passo * (k - (i - 1))))
                            interpolacoes_feitas += 1
                        i = j
                    else:
                        i += 1
                        
            # Verificar monotonicidade
            for idx in range(1, len(horarios)):
                if horarios[idx] < horarios[idx - 1]:
                    con.close()
                    raise ValueError(f"Horários não monotônicos após interpolação na viagem {tid}")
                    
            paradas_da_viagem = [item[1] for item in st_list]
            for p_id in paradas_da_viagem:
                paradas_referenciadas_usadas.add(p_id)
                
            # Descartar viagem se alguma parada estiver fora dos limites
            if any(p_id in paradas_fora_limite for p_id in paradas_da_viagem):
                continue
                
            if len(paradas_da_viagem) < 2:
                viagens_ignoradas_menos_de_2_paradas += 1
                continue
                
            t0 = horarios[0]
            deslocamentos = tuple(h - t0 for h in horarios)
            duracao_s = deslocamentos[-1]
            
            viagens_processadas[tid] = {
                "linha_id": trips_info[tid]["linha_id"],
                "servico_id": trips_info[tid]["servico_id"],
                "sentido": trips_info[tid]["sentido"],
                "inicio_s": t0,
                "paradas": tuple(paradas_da_viagem),
                "deslocamentos": deslocamentos,
                "duracao_s": duracao_s,
            }

        # GT-06: Verificar porcentagem de paradas descartadas entre as referenciadas
        if paradas_referenciadas_usadas:
            descartadas_usadas = paradas_referenciadas_usadas.intersection(paradas_fora_limite.keys())
            pct_descartadas = len(descartadas_usadas) / len(paradas_referenciadas_usadas)
            if pct_descartadas > 0.01:
                con.close()
                raise ValueError(
                    f"Mais de 1% das paradas referenciadas estão fora de SP_LIMITES ({pct_descartadas:.2%}). Feed rejeitado."
                )

        # 8. frequencies.txt (GT-04)
        viagens_finais = []
        if "frequencies.txt" in arquivos_no_zip:
            with z.open("frequencies.txt") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                for row in reader:
                    tid = row["trip_id"].strip()
                    if tid not in viagens_processadas:
                        continue
                    v_base = viagens_processadas[tid]
                    start_s = parse_hhmmss_para_segundos(row["start_time"])
                    end_s = parse_hhmmss_para_segundos(row["end_time"])
                    headway = int(row["headway_secs"])
                    
                    t = start_s
                    seq_freq = 0
                    while t < end_s:
                        viagens_finais.append({
                            "id": f"{tid}_freq_{seq_freq}",
                            "linha_id": v_base["linha_id"],
                            "servico_id": v_base["servico_id"],
                            "sentido": v_base["sentido"],
                            "inicio_s": t,
                            "paradas": v_base["paradas"],
                            "deslocamentos": v_base["deslocamentos"],
                            "duracao_s": v_base["duracao_s"],
                        })
                        t += headway
                        seq_freq += 1
        else:
            for tid, v in viagens_processadas.items():
                viagens_finais.append({
                    "id": tid,
                    "linha_id": v["linha_id"],
                    "servico_id": v["servico_id"],
                    "sentido": v["sentido"],
                    "inicio_s": v["inicio_s"],
                    "paradas": v["paradas"],
                    "deslocamentos": v["deslocamentos"],
                    "duracao_s": v["duracao_s"],
                })

        # 9. Padrões de viagem (GT-03)
        padroes_map = {}
        padroes_lista = []
        padrao_paradas_lista = []
        viagens_db = []
        
        padrao_id_counter = 1
        for v in viagens_finais:
            chave_padrao = (v["linha_id"], v["sentido"], v["paradas"], v["deslocamentos"])
            if chave_padrao not in padroes_map:
                pid = padrao_id_counter
                padrao_id_counter += 1
                padroes_map[chave_padrao] = pid
                padroes_lista.append({
                    "id": pid,
                    "linha_id": f"{sistema}:{v['linha_id']}",
                    "sentido": v["sentido"],
                    "n_paradas": len(v["paradas"]),
                    "duracao_s": v["duracao_s"],
                })
                for pos, (p_id, desloc) in enumerate(zip(v["paradas"], v["deslocamentos"])):
                    padrao_paradas_lista.append({
                        "padrao_id": pid,
                        "posicao": pos,
                        "parada_id": f"{sistema}:{p_id}",
                        "deslocamento_s": desloc,
                    })
            else:
                pid = padroes_map[chave_padrao]
                
            viagens_db.append({
                "id": f"{sistema}:{v['id']}",
                "padrao_id": pid,
                "servico_id": f"{sistema}:{v['servico_id']}",
                "inicio_s": v["inicio_s"],
            })

        # 10. feed_info.txt
        feed_version = None
        feed_validade_ini = None
        feed_validade_fim = None
        if "feed_info.txt" in arquivos_no_zip:
            with z.open("feed_info.txt") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                for row in reader:
                    feed_version = (row.get("feed_version") or "").strip() or None
                    if row.get("feed_start_date"):
                        feed_validade_ini = formatar_data_iso(row["feed_start_date"])
                    if row.get("feed_end_date"):
                        feed_validade_fim = formatar_data_iso(row["feed_end_date"])
                    break
                    
        versao = feed_version or arquivo_sha256[:12]
        validade_inicio = feed_validade_ini or (min(validade_inicio_cand) if validade_inicio_cand else None)
        validade_fim = feed_validade_fim or (max(validade_fim_cand) if validade_fim_cand else None)

    # 11. Gravação no banco SQLite com troca atômica (GT-09, GT-10)
    agora_iso = datetime.now().isoformat()
    n_paradas_final = len(paradas_raw)
    n_linhas_final = len(linhas_raw)
    n_padroes_final = len(padroes_lista)
    n_viagens_final = len(viagens_db)

    # Salva com ativo = 0
    with con:
        con.execute("PRAGMA synchronous = NORMAL;")
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO feeds (
                sistema, fonte_url, arquivo_nome, arquivo_sha256, versao,
                validade_inicio, validade_fim, origem_dados, importado_em,
                ativo, n_paradas, n_linhas, n_padroes, n_viagens
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                sistema,
                fonte_url,
                zip_path.name,
                arquivo_sha256,
                versao,
                validade_inicio,
                validade_fim,
                origem_dados,
                agora_iso,
                n_paradas_final,
                n_linhas_final,
                n_padroes_final,
                n_viagens_final,
            ),
        )
        novo_feed_id = cur.lastrowid

        # Inserir paradas
        dados_paradas = [
            (novo_feed_id, f"{sistema}:{sid}", p["nome"], p["lat"], p["lon"], p["celula_x"], p["celula_y"])
            for sid, p in paradas_raw.items()
        ]
        for i in range(0, len(dados_paradas), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO paradas (feed_id, id, nome, lat, lon, celula_x, celula_y) VALUES (?, ?, ?, ?, ?, ?, ?)",
                dados_paradas[i:i + LOTE_IMPORTACAO],
            )

        # Inserir linhas
        dados_linhas = [
            (novo_feed_id, f"{sistema}:{rid}", l["nome_curto"], l["nome_longo"], l["operador"], l["modal"])
            for rid, l in linhas_raw.items()
        ]
        for i in range(0, len(dados_linhas), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO linhas (feed_id, id, nome_curto, nome_longo, operador, modal) VALUES (?, ?, ?, ?, ?, ?)",
                dados_linhas[i:i + LOTE_IMPORTACAO],
            )

        # Inserir servicos
        dados_servicos = [
            (novo_feed_id, f"{sistema}:{svid}", s["dia0"], s["dia1"], s["dia2"], s["dia3"], s["dia4"], s["dia5"], s["dia6"], s["inicio"], s["fim"])
            for svid, s in servicos_raw.items()
        ]
        for i in range(0, len(dados_servicos), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO servicos (feed_id, id, dia0, dia1, dia2, dia3, dia4, dia5, dia6, inicio, fim) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                dados_servicos[i:i + LOTE_IMPORTACAO],
            )

        # Inserir exceções
        dados_excecoes = [
            (novo_feed_id, f"{sistema}:{ex['servico_id']}", ex["data"], ex["tipo"])
            for ex in servicos_excecoes_raw
        ]
        for i in range(0, len(dados_excecoes), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO servicos_excecoes (feed_id, servico_id, data, tipo) VALUES (?, ?, ?, ?)",
                dados_excecoes[i:i + LOTE_IMPORTACAO],
            )

        # Inserir padroes
        dados_padroes = [
            (novo_feed_id, pad["id"], pad["linha_id"], pad["sentido"], pad["n_paradas"], pad["duracao_s"])
            for pad in padroes_lista
        ]
        for i in range(0, len(dados_padroes), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO padroes (feed_id, id, linha_id, sentido, n_paradas, duracao_s) VALUES (?, ?, ?, ?, ?, ?)",
                dados_padroes[i:i + LOTE_IMPORTACAO],
            )

        # Inserir padrao_paradas
        dados_pp = [
            (novo_feed_id, pp["padrao_id"], pp["posicao"], pp["parada_id"], pp["deslocamento_s"])
            for pp in padrao_paradas_lista
        ]
        for i in range(0, len(dados_pp), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO padrao_paradas (feed_id, padrao_id, posicao, parada_id, deslocamento_s) VALUES (?, ?, ?, ?, ?)",
                dados_pp[i:i + LOTE_IMPORTACAO],
            )

        # Inserir viagens
        dados_viagens = [
            (novo_feed_id, v["id"], v["padrao_id"], v["servico_id"], v["inicio_s"])
            for v in viagens_db
        ]
        for i in range(0, len(dados_viagens), LOTE_IMPORTACAO):
            cur.executemany(
                "INSERT INTO viagens (feed_id, id, padrao_id, servico_id, inicio_s) VALUES (?, ?, ?, ?, ?)",
                dados_viagens[i:i + LOTE_IMPORTACAO],
            )

    # Troca atômica (GT-09): desativa anterior, ativa novo, e deleta anterior
    with con:
        con.execute("UPDATE feeds SET ativo = 0 WHERE sistema = ? AND id <> ?", (sistema, novo_feed_id))
        con.execute("UPDATE feeds SET ativo = 1 WHERE id = ?", (novo_feed_id,))
        con.execute("DELETE FROM feeds WHERE sistema = ? AND id <> ?", (sistema, novo_feed_id))

    con.close()
    fim_tempo = datetime.now()
    duracao_total_s = (fim_tempo - inicio_tempo).total_seconds()

    # GT-11: Gerar relatório de importação
    relatorio_md = [
        f"# Relatório de Importação GTFS - {sistema.upper()}",
        "",
        f"- **Data e Hora:** {agora_iso}",
        f"- **Arquivo:** `{zip_path.name}`",
        f"- **SHA-256:** `{arquivo_sha256}`",
        f"- **Versão do Feed:** `{versao}`",
        f"- **Período de Validade:** `{validade_inicio}` a `{validade_fim}`",
        f"- **Origem dos Dados:** `{origem_dados}`",
        f"- **Tempo Total de Importação:** {duracao_total_s:.2f} s",
        "",
        "## Contagens Importadas",
        f"- **Paradas válidas:** {n_paradas_final}",
        f"- **Linhas válidas:** {n_linhas_final}",
        f"- **Padrões operacionais:** {n_padroes_final}",
        f"- **Viagens ativas:** {n_viagens_final}",
        "",
        "## Itens Ignorados / Interpolações",
        f"- **Paradas descartadas fora de SP_LIMITES:** {len(paradas_fora_limite)}",
        f"- **Linhas ignoradas por route_type:** {len(linhas_ignoradas_motivo)}",
        f"- **Viagens ignoradas (< 2 paradas):** {viagens_ignoradas_menos_de_2_paradas}",
        f"- **Interpolações lineares de horários realizadas:** {interpolacoes_feitas}",
        "",
        "## Comando de Execução",
        f"`python -m backend.src.transporte.importar_gtfs --sistema {sistema} --arquivo {zip_path} --fonte-url {fonte_url} --origem {origem_dados}`",
    ]
    
    caminho_relatorio = RAIZ_REPOSITORIO / "docs" / f"relatorio_importacao_{sistema}.md"
    try:
        with open(caminho_relatorio, "w", encoding="utf-8") as fp:
            fp.write("\n".join(relatorio_md) + "\n")
    except Exception:
        pass

    return {
        "status": "sucesso",
        "feed_id": novo_feed_id,
        "versao": versao,
        "validade_inicio": validade_inicio,
        "validade_fim": validade_fim,
        "n_paradas": n_paradas_final,
        "n_linhas": n_linhas_final,
        "n_padroes": n_padroes_final,
        "n_viagens": n_viagens_final,
        "interpolacoes": interpolacoes_feitas,
    }


def main():
    parser = argparse.ArgumentParser(description="Importar feed GTFS para o banco SQLite.")
    parser.add_argument("--sistema", required=True, choices=["sptrans", "metroferroviario", "emtu"], help="Identificador do sistema.")
    parser.add_argument("--arquivo", required=True, type=str, help="Caminho do arquivo .zip.")
    parser.add_argument("--fonte-url", required=True, type=str, help="URL oficial de origem do feed.")
    parser.add_argument("--origem", default="real", choices=["real", "historico", "teste"], help="Origem dos dados.")
    parser.add_argument("--banco", default=None, type=str, help="Caminho do banco SQLite.")
    args = parser.parse_args()

    try:
        resultado = importar_gtfs(
            sistema=args.sistema,
            caminho_zip=args.arquivo,
            fonte_url=args.fonte_url,
            origem_dados=args.origem,
            caminho_banco=args.banco,
        )
        print(f"Sucesso: {resultado}")
        sys.exit(0)
    except Exception as exc:
        print(f"Erro na importação: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
