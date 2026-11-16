# Registro de Uso de Ferramentas de Inteligência Artificial - Evolução v2

| Ferramenta/modelo | Data | Responsável | Finalidade | Resumo do pedido | Saída aproveitada | Alterações humanas | Fontes conferidas | Testes realizados | Limitações |
|---|---|---|---|---|---|---|---|---|---|
| Antigravity (Gemini 3.8 Flash) | 15/11/2026 | PENDENTE | Etapa E0: Reconhecimento, sem código novo | Ler repositório, branch evolucao-v2, conferir tarifas e GTFS, criar docs | Mapeamento de testes iniciais, fontes reais e registro de dúvidas | PENDENTE | Seções 7.1, 9.2 e 15 da especificação | `python -m pytest backend/tests`: 61 passed; `cd "global solution part2 - tarifas"; python -m pytest`: 78 passed | GTFS real SPTrans não fornecido na pasta local; sem GTFS público direto para Metrô/EMTU |
| Antigravity (Gemini 3.8 Flash) | 15/11/2026 | PENDENTE | Etapa E1: Consolidar pacotes sem mudar comportamento | Mover part2/src para backend/src/rotas, fixtures e testes; remover sys.path; constantes 13.1; atualizar demo e CI | Pacotes consolidados, imports relativos e módulo autônomo backend/src/rotas | PENDENTE | Seções 4, 13.1, 14 e 15 (E1) da especificação | `python -m pytest backend/tests`: 139 passed; `python -m backend.src.rotas.exemplos.demo`: 3 rotas exibidas | Código e testes movidos mantendo comportamento anterior idêntico |

---

## Checklist Manual do Frontend (Seção 16.9)

| ID | Verificação | Status (sim / não / não verificado) | Observação |
|---|---|---|---|
| FE-C01 | Primeiro uso mostra os 4 interruptores desligados; `Agora não` mantém anônimo e **não** cria usuário. | não verificado | A ser validado na etapa E11 |
| FE-C02 | Ligar um interruptor cria a identidade e persiste após recarregar. | não verificado | A ser validado na etapa E11 |
| FE-C03 | Rota de ônibus mostra até 3 cartões, custo em pt-BR ou "Tarifa não confirmada", aviso e avisos de cobertura. | não verificado | A ser validado na etapa E11 |
| FE-C04 | `Escolher esta rota` aparece só com identidade e histórico ativo. | não verificado | A ser validado na etapa E11 |
| FE-C05 | O assistente responde, mostra respostas rápidas, 👍/👎 e `aviso`. | não verificado | A ser validado na etapa E11 |
| FE-C06 | A conversa volta ao reabrir o app (com consentimento). | não verificado | A ser validado na etapa E11 |
| FE-C07 | "Como apago meus dados?" mostra os dois botões; "Sim, apagar tudo" apaga e volta ao anônimo. | não verificado | A ser validado na etapa E11 |
| FE-C08 | `Meus dados` mostra resumo, exporta JSON e apaga tudo com confirmação. | não verificado | A ser validado na etapa E11 |
| FE-C09 | A rota a pé (`/rotas/reais`) continua funcionando como antes. | não verificado | A ser validado na etapa E11 |
| FE-C10 | Sem API no ar, o app mostra mensagem de erro amigável e não trava. | não verificado | A ser validado na etapa E11 |

---

Validação e revisão pela equipe: PENDENTE.
Conferência das tarifas em fonte oficial pela equipe: PENDENTE.
