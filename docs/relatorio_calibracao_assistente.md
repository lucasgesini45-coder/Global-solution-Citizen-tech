<<<<<<< HEAD
# Relatório de calibração do limiar do assistente de dúvidas

- Gerado em: 12/11/2026 23:53:31
- Hash da base (12 primeiros caracteres): 4d1d685a8e98
- Versão do scikit-learn: 1.9.1
- Limiar de confiança em uso: 0.4

| Limiar | Perguntas respondidas (confiança ≥ limiar) | Respondidas corretamente | Respondidas incorretamente | Caiu no fallback |
|---|---|---|---|---|
| 0.20 | 11 | 8 | 3 | 1 |
| 0.25 | 10 | 8 | 2 | 2 |
| 0.30 | 9 | 8 | 1 | 3 |
| 0.35 | 9 | 8 | 1 | 3 |
| 0.40 | 9 | 8 | 1 | 3 |
| 0.45 | 8 | 7 | 1 | 4 |
| 0.50 | 5 | 5 | 0 | 7 |
| 0.55 | 4 | 4 | 0 | 8 |
| 0.60 | 4 | 4 | 0 | 8 |
| 0.65 | 2 | 2 | 0 | 10 |
| 0.70 | 2 | 2 | 0 | 10 |
| 0.75 | 0 | 0 | 0 | 12 |
| 0.80 | 0 | 0 | 0 | 12 |
=======
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
>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e

O limiar em uso é o valor de LIMIAR_CONFIANCA em backend/src/assistente/config.py. Este relatório NÃO altera esse valor; a decisão é da equipe.

Estimativa baseada em 12 perguntas; use com cautela.
