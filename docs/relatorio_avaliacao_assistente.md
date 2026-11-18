# Relatório de avaliação do assistente de dúvidas

- Gerado em: 12/11/2026 23:53:30
- Hash da base (12 primeiros caracteres): 4d1d685a8e98
- Versão do scikit-learn: 1.9.1
- Limiar de confiança em uso: 0.4

## Resumo

| Métrica | Resultado |
|---|---|
| Top-1 | 8 de 12 (66.7%) |
| Top-3 | 12 de 12 (100.0%) |
| Tempo médio de resposta (ms) | 0.42 |
| Tempo máximo de resposta (ms) | 0.97 |

## Detalhe por pergunta

| # | Pergunta | Esperada | Prevista | Confiança | Top-1 | Top-3 | Tempo (ms) |
|---|---|---|---|---|---|---|---|
| 1 | Quero ir de um ponto a outro da cidade, por onde começo no app? | R01 | T01 | 0.2586 | não | sim | 0.97 |
| 2 | Dá pra digitar o nome da rua em vez de marcar no mapa? | R03 | R02 | 0.4682 | não | sim | 0.39 |
| 3 | O que quer dizer baldeações e espera no resultado da rota? | R04 | R04 | 0.6316 | sim | sim | 0.37 |
| 4 | Coloquei origem e destino e não apareceu nenhuma rota, o que houve? | R05 | R05 | 0.4790 | sim | sim | 0.36 |
| 5 | Onde vejo quanto vai custar a viagem? | T01 | T01 | 0.4665 | sim | sim | 0.34 |
| 6 | Apareceu tarifa não confirmada, isso significa o quê? | T02 | T02 | 0.7225 | sim | sim | 0.39 |
| 7 | Se eu pegar ônibus e depois metrô, pago duas passagens? | T03 | T03 | 0.4028 | sim | sim | 0.36 |
| 8 | Posso limitar quanto quero gastar na viagem? | T04 | H04 | 0.2300 | não | sim | 0.33 |
| 9 | O aplicativo grava as rotas que eu pesquisei? | H01 | H02 | 0.1769 | não | sim | 0.40 |
| 10 | Como faço para limpar minhas buscas anteriores? | H02 | H02 | 0.7382 | sim | sim | 0.35 |
| 11 | Preciso fazer cadastro ou ligar o GPS pra usar? | H03 | H03 | 0.5499 | sim | sim | 0.42 |
| 12 | Dá para avisar o app sobre um problema que vi na viagem? | H04 | H04 | 0.6269 | sim | sim | 0.36 |

## Limitações

Avaliação feita com apenas 12 perguntas; os percentuais são apenas indicativos. As intenções R02, T05 e H05 não possuem pergunta de teste. Respostas revisadas pela equipe: 0 de 15 no momento da geração.
