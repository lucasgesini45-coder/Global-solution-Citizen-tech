# Relatório de Calibração do Assistente de Dúvidas

- **Data e hora da geração:** 2026-11-11 23:13:26
- **Hash da base (12 caracteres):** `2394cf6aa100`
- **Versão do scikit-learn:** `1.9.1`
- **LIMIAR_CONFIANCA:** `0.40`

## Calibração de Limiares

| limiar | perguntas respondidas (confiança ≥ limiar) | respondidas corretamente | respondidas incorretamente | caiu no fallback |
|---|---|---|---|---|
| 0.20 | 9 | 8 | 1 | 3 |
| 0.25 | 8 | 8 | 0 | 4 |
| 0.30 | 6 | 6 | 0 | 6 |
| 0.35 | 5 | 5 | 0 | 7 |
| 0.40 | 5 | 5 | 0 | 7 |
| 0.45 | 1 | 1 | 0 | 11 |
| 0.50 | 1 | 1 | 0 | 11 |
| 0.55 | 1 | 1 | 0 | 11 |
| 0.60 | 1 | 1 | 0 | 11 |
| 0.65 | 1 | 1 | 0 | 11 |
| 0.70 | 1 | 1 | 0 | 11 |
| 0.75 | 1 | 1 | 0 | 11 |
| 0.80 | 1 | 1 | 0 | 11 |

O limiar em uso é o valor de LIMIAR_CONFIANCA em backend/src/assistente/config.py. Este relatório NÃO altera esse valor; a decisão é da equipe.

Estimativa baseada em 12 perguntas; use com cautela.
