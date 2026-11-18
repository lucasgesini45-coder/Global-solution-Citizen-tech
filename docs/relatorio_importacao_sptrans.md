# Relatório de Importação GTFS - SPTRANS

- **Data e Hora:** 2026-11-17T19:22:39.197800
- **Arquivo:** `gtfs_exp.zip`
- **SHA-256:** `740bf6eadea870da05a8fa47f263bd0ce7d58e7d884c93404d638376b51b4843`
- **Versão do Feed:** `gtfs-expirado`
- **Período de Validade:** `2020-01-01` a `2020-12-31`
- **Origem dos Dados:** `teste`
- **Tempo Total de Importação:** 0.06 s

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
`python -m backend.src.transporte.importar_gtfs --sistema sptrans --arquivo /tmp/pytest-of-root/pytest-4/test_t_gt13_validade_fim_expir0/gtfs_exp.zip --fonte-url https://sptrans.com.br --origem teste`
