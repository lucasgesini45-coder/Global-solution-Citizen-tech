# Registro de Uso de Ferramentas de Inteligência Artificial - Evolução v2

| Ferramenta/modelo | Data | Responsável | Finalidade | Resumo do pedido | Saída aproveitada | Alterações humanas | Fontes conferidas | Testes realizados | Limitações |
|---|---|---|---|---|---|---|---|---|---|
| Antigravity (Gemini 3.8 Flash) | 15/11/2026 | PENDENTE | Etapa E0: Reconhecimento, sem código novo | Ler repositório, branch evolucao-v2, conferir tarifas e GTFS, criar docs | Mapeamento de testes iniciais, fontes reais e registro de dúvidas | PENDENTE | Seções 7.1, 9.2 e 15 da especificação | `python -m pytest backend/tests`: 61 passed; `cd "global solution part2 - tarifas"; python -m pytest`: 78 passed | GTFS real SPTrans não fornecido na pasta local; sem GTFS público direto para Metrô/EMTU |
| Antigravity (Gemini 3.8 Flash) | 15/11/2026 | PENDENTE | Etapa E1: Consolidar pacotes sem mudar comportamento | Mover part2/src para backend/src/rotas, fixtures e testes; remover sys.path; constantes 13.1; atualizar demo e CI | Pacotes consolidados, imports relativos e módulo autônomo backend/src/rotas | PENDENTE | Seções 4, 13.1, 14 e 15 (E1) da especificação | `python -m pytest backend/tests`: 139 passed; `python -m backend.src.rotas.exemplos.demo`: 3 rotas exibidas | Código e testes movidos mantendo comportamento anterior idêntico |
| Antigravity (Gemini 3.8 Flash) | 15/11/2026 | PENDENTE | Etapa E2: Banco SQL único | Implementar backend/src/db/, config_app.py, 6 migrações, documentar, purgar e apagar_tudo | Banco SQLite único com migrações numeradas, retenção LGPD e documentação | PENDENTE | Seções 6, 13.2, 14 e 15 (E2) da especificação | `python -m pytest backend/tests/db/test_banco.py`: 10 passed; `python -m pytest backend/tests`: 149 passed; `python -m backend.src.db.documentar`: gerado docs/esquema_banco.md | Esquema estruturado e purga implementados conforme requisitos DB-01 a DB-13 |
| Antigravity (Gemini 3.8 Flash) | 15/11/2026 | PENDENTE | Etapa E3: Importador GTFS e fixtures | Implementar importar_gtfs.py, validacao.py, fixture gtfs_mini e testes T-GT01 a T-GT13 | Importador de GTFS em fluxo sem descompactar em disco, troca atômica, padrões de viagem e relatório | PENDENTE | Seções 7, 13.1, 14 e 15 (E3) da especificação | `python -m pytest backend/tests/transporte/test_importar_gtfs.py`: 13 passed; `python -m pytest backend/tests`: 162 passed | GTFS real SPTrans aguardando download pela equipe (cadastro exigido); testes e pipeline usam fixture |

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

---

## Módulo de acessibilidade — Raphael

### Apoio de IA
O ChatGPT foi utilizado para explicar conceitos de Python,
apoiar a construção da lógica, revisar o código e planejar testes.
Também auxiliou na correção de erros de digitação, indentação,
importações e caminhos de arquivos.

### Validação crítica
O código foi executado e conferido pelo integrante responsável.
Foram verificados:
- Trechos com passagem sem degraus.
- Barreiras antes e depois de informações desconhecidas.
- Rotas vazias.
- Identificação detalhada de barreiras e pendências.
- Bloqueio de dados inválidos da rota e das necessidades.
- Leitura de uma rota em JSON.
- Tratamento de arquivo inexistente e JSON malformado.

Os testes revelaram problemas que foram corrigidos e testados
novamente, incluindo o nome da exceção JSONDecodeError.

### Limitações
Os dados utilizados são simulados.
A avaliação considera somente a necessidade de passagem sem degraus.
Não certifica a acessibilidade completa de uma rota.
Ainda não há integração com dados reais de segurança pública.
Nenhum modelo de IA externo é executado pelo módulo.

## Adequação aos requisitos FIAP — 17/11/2026

- Ferramenta: ChatGPT. Finalidade: análise do enunciado, comparação com código existente, apoio à curadoria de 15 orientações, implementação de busca e terminal, criação de cenários e documentação de dois modelos.
- Instruções A/B: recuperar somente orientação verificada e referência; B acrescenta avisos de limitação e confirmação oficial.
- Fontes: páginas institucionais de SPTrans, Metrô e ANTT registradas individualmente no JSON da base.
- Validação: testes automatizados e script de avaliação comparativa adicionados. A revisão humana da base, a interpretação dos resultados e o teste manual de usabilidade ainda devem ser realizados pela equipe. Não registrar aprovação ou métricas antes de executar os testes.
- Limites: consulta às fontes na data registrada não garante vigência futura; não houve validação de acessibilidade física. Os modelos A/B são regras locais, não execução de um LLM.

### Evidências da avaliação — 17/11/2026

Execução GitHub Actions 44088026008: 177 testes aprovados, 1 advertência e typecheck aprovado. Avaliação cidadã A/B: 19 de 20 acertos por modelo (95%); tempos médios de 0,2171 ms e 0,2092 ms. O erro de ambiguidade foi preservado no relatório. Roteiro automatizado aprovado, sem participante humano. A IA auxiliou na organização e interpretação das medições reais; revisão humana das fontes e resultados permanece pendente. Ver [relatório](relatorio_testes_indicadores_fiap.md).
