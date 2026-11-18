# Registro de uso de IA: Assistente de dúvidas (linhas para acrescentar a `docs/uso_ia.md`)

| Ferramenta/modelo | Data | Responsável | Finalidade | Resumo do pedido | Saída aproveitada | Alterações humanas | Fontes conferidas | Testes realizados | Limitações |
|---|---|---|---|---|---|---|---|---|---|
| Google Antigravity (modelo não identificado na gravação) | 12/11/2026 | PENDENTE | E0 (reconhecimento) e parte de E1 e E2 | Executar a especificação do assistente, etapa por etapa | `config.py`, `preprocessamento.py`, `base.py` (validação), `perguntas_teste.json`, `requirements.txt` e as linhas R01 a H02 de `assistente_fontes.md` | PENDENTE | Arquivos do repositório citados em `assistente_fontes.md` | Nenhum executado (a execução parou antes) | Trabalho incompleto; acentos corrompidos nos arquivos de texto e de código |
| Claude (Anthropic), Sonnet 5.5 | 12/11/2026 | PENDENTE | Concluir E2 a E9: base de 15 intenções, treino, modelo, previsão, API, terminal, relatórios, testes e documentação | Reaproveitar o que o Antigravity escreveu (visto na gravação de tela) e entregar tudo completo | Todos os arquivos do pacote (reescritos em UTF-8 limpo) | PENDENTE | Gravação de tela do Antigravity; README e estrutura do repositório | 46 testes do assistente aprovados no ambiente do Claude (scikit-learn 1.9.1) com cópia mínima do repositório; relatórios de avaliação e calibração gerados nesse ambiente; **suíte existente do projeto NÃO executada** | `api.py` e `sistema.py` não foram vistos; R04, H03, H04 e H05 do `assistente_fontes.md` não aparecem na gravação; resultado inicial top-1 8/12 |

Revisão das 15 respostas e das 180 frases de treino pela equipe: PENDENTE.
Validação da equipe (execução dos testes no repositório real e integração): PENDENTE.
