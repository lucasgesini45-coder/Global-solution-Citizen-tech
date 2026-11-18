# Relatório de Avaliação do Assistente de Dúvidas

- **Data e hora da geração:** 2026-11-11 23:13:25
- **Hash da base (12 caracteres):** `2394cf6aa100`
- **Versão do scikit-learn:** `1.9.1`
- **LIMIAR_CONFIANCA:** `0.40`

## Resumo do Desempenho

| Métrica | Resultado |
|---|---|
| Top-1 (acertos de 12 e %) | 8 de 12 (66.7%) |
| Top-3 (acertos de 12 e %) | 11 de 12 (91.7%) |
| Tempo médio de resposta (ms, 2 casas) | 2.40 ms |
| Tempo máximo de resposta (ms, 2 casas) | 22.23 ms |

## Detalhamento das 12 Perguntas de Teste

| # | pergunta | esperada | prevista | confiança | top-1 (sim/não) | top-3 (sim/não) | tempo (ms) |
|---|---|---|---|---|---|---|---|
| 1 | Quero ir de um ponto a outro da cidade, por onde começo no app? | R01 | R03 | 0.1895 | não | sim | 22.23 |
| 2 | Dá pra digitar o nome da rua em vez de marcar no mapa? | R03 | R03 | 0.4006 | sim | sim | 0.60 |
| 3 | O que quer dizer baldeações e espera no resultado da rota? | R04 | R04 | 0.4402 | sim | sim | 0.52 |
| 4 | Coloquei origem e destino e não apareceu nenhuma rota, o que houve? | R05 | R05 | 0.3113 | sim | sim | 0.41 |
| 5 | Onde vejo quanto vai custar a viagem? | T01 | R04 | 0.1786 | não | não | 0.39 |
| 6 | Apareceu tarifa não confirmada, isso significa o quê? | T02 | T02 | 0.8836 | sim | sim | 0.41 |
| 7 | Se eu pegar ônibus e depois metrô, pago duas passagens? | T03 | T05 | 0.2028 | não | sim | 0.41 |
| 8 | Posso limitar quanto quero gastar na viagem? | T04 | H04 | 0.1168 | não | sim | 0.82 |
| 9 | O aplicativo grava as rotas que eu pesquisei? | H01 | H01 | 0.2703 | sim | sim | 0.92 |
| 10 | Como faço para limpar minhas buscas anteriores? | H02 | H02 | 0.4391 | sim | sim | 0.87 |
| 11 | Preciso fazer cadastro ou ligar o GPS pra usar? | H03 | H03 | 0.4278 | sim | sim | 0.65 |
| 12 | Dá para avisar o app sobre um problema que vi na viagem? | H04 | H04 | 0.2737 | sim | sim | 0.56 |

## Limitações

Avaliação feita com apenas 12 perguntas; os percentuais são apenas indicativos. As intenções R02, T05 e H05 não possuem pergunta de teste. Respostas revisadas pela equipe: 0 de 15 no momento da geração.
