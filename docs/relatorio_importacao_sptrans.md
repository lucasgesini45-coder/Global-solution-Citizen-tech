# Relatório de Importação GTFS - SPTRANS

- **Data e Hora:** 2026-11-16T00:12:59.506279
- **Arquivo:** `gtfs_exp.zip`
- **SHA-256:** `19b3ed8b1c2d3a39720da4d1fa39dcbeb686e52f8ef899108b38ada61ec163f8`
- **Versão do Feed:** `gtfs-expirado`
- **Período de Validade:** `2020-01-01` a `2020-12-31`
- **Origem dos Dados:** `teste`
- **Tempo Total de Importação:** 0.14 s

## Contagens Importadas
- **Paradas válidas:** 9
- **Linhas válidas:** 4
- **Padrões operacionais:** 4
- **Viagens ativas:** 346

## Itens Ignorados / Interpolações
- **Paradas descartadas fora de SP_LIMITES:** 0
- **Linhas ignoradas por route_type:** 0
- **Viagens ignoradas (< 2 paradas):** 0
- **Interpolações lineares de horários realizadas:** 0

## Comando de Execução
`python -m backend.src.transporte.importar_gtfs --sistema sptrans --arquivo C:\Users\filip\AppData\Local\Temp\pytest-of-filip\pytest-22\test_t_gt13_validade_fim_expir0\gtfs_exp.zip --fonte-url https://sptrans.com.br --origem teste`
