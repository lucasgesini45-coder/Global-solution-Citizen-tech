# Integração, servidor local e evidências de testes (parte 5)

Responsável: integrante 5 - Servidor e integração.
Arquivos desta parte: `app.py`, `backend/src/sessoes.py`, `backend/tests/integracao/`, `README.md` e este documento.

## 1. Servidor local

`app.py` é a raiz de composição. Ele reaproveita a API de `backend/src/api.py` (sem alterá-la), acrescenta a sessão colaborativa e o endpoint `GET /integracao/status`.

```powershell
python app.py                    # http://127.0.0.1:8000  (documentação em /docs)
python app.py --porta 8010       # outra porta
python app.py --verificar        # confere contratos e base; sai com código 0 (ok) ou 1 (falha)
python app.py --host 0.0.0.0     # acessível ao celular na rede local, SEM autenticação
```

Comportamento:

- Por padrão escuta só em `127.0.0.1`. Qualquer outro `--host` imprime um aviso.
- Valida `CITIZEN_MODO` (`desenvolvimento`, `producao` ou `teste`) antes de subir; valor inválido encerra com código 2 e mensagem clara.
- Carrega o classificador do assistente antes de aceitar pedidos. Se não carregar, a API continua de pé e o terminal informa.
- `python -m uvicorn backend.src.api:app` continua funcionando, mas sem sessões e sem `/integracao/status`.

## 2. Contratos entre módulos

A tabela está em `app.py` (constante `CONTRATOS`). `GET /integracao/status` e `python app.py --verificar` conferem se cada endpoint existe. Os testes em `backend/tests/integracao/test_contratos.py` conferem o **formato** das respostas.

| Responsável | Endpoint | Promessa que os outros módulos podem assumir |
|---|---|---|
| 1 - Dados e fontes | `GET /temas` | Grafo de temas; todo vizinho é um tema existente. |
| 1 | `POST /consultar` | Sempre traz `status`, `resposta`, `fontes`, `relacionados`. `status` vale `ok`, `sem_resposta`, `ambiguo` ou `entrada_invalida`. Só registro `verificado` gera `ok`, e `ok` vem com referência e data. Base ausente vira 422, não 500. |
| 2 - Rotas e tarifas | `POST /rotas`, `GET /rotas/exemplo` | Resposta marcada como `modo = demonstracao` e dados fictícios; até 3 rotas com `ordem` 1..n. Erro de domínio (ex.: `partida` inválida) volta com HTTP 200 e `resultado.erro = {codigo, mensagem}`; coordenadas inválidas voltam 422. |
| 3 - Acessibilidade e segurança | `POST /acessibilidade/avaliar` | Dado desconhecido nunca vira `COMPATIVEL`: um trecho `null` mantém `NAO_VERIFICADA`; um trecho `false` torna `INCOMPATIVEL`. Sempre `verificacao_em_campo = false` e `aviso`. |
| 3 / 4 | `POST /rotas`, `POST /rotas/reais` | Com `sem_degraus` pedido e sem dado confirmado, a acessibilidade é `NAO_VERIFICADA`. |
| 4 - Interface e mapa | `GET /enderecos/sugestoes` | `q` com pelo menos 4 caracteres. |
| 4 | `POST /rotas/reais` | Falha do provedor externo vira 503 com `detail` legível. Resposta traz `acessibilidade.status = NAO_VERIFICADA`. |
| 4 | `POST /agente/conversar` | Sem origem/destino não chama o motor de rotas e pede os pontos. Sem base verificada não inventa direitos nem fontes. Falha de rota responde 200 com `origem_resposta = rota_indisponivel`. |
| Todos | Erros de validação | Sempre HTTP 422 com a chave `detail` (o frontend lê esse formato). |
| 5 - Servidor | `POST /sessoes...` | Ver seção 3. |

Regras transversais testadas:

- O chat (`/agente/conversar`) e a sessão aceitam e recusam os mesmos valores de `modal`: `todos`, `onibus`, `ferroviario`, `ape`.
- A sessão e `/rotas/reais` validam latitude/longitude do mesmo modo (reuso de `Coordenadas`).
- A API só libera `GET`, `POST` e o cabeçalho `Content-Type` no CORS (`backend/src/api.py`). Por isso a sessão usa só `POST` e o token vai no corpo JSON.

## 3. Sessão colaborativa básica

Pensada para duas ou mais pessoas verem o mesmo planejamento (por exemplo, quem tem mobilidade reduzida e quem acompanha).

| Endpoint | Uso |
|---|---|
| `POST /sessoes` `{apelido?}` | Cria a sessão. Devolve `codigo` (6 caracteres), `token` secreto, `participante_id`, `estado`, `versao`, `expira_em`. HTTP 201. |
| `POST /sessoes/{codigo}/entrar` `{apelido?}` | Entra com o código. Devolve o próprio `token`. |
| `POST /sessoes/{codigo}/sincronizar` `{token, desde?}` | Estado atual, participantes e eventos com versão maior que `desde` (polling). |
| `POST /sessoes/{codigo}/estado` `{token, versao_base?, origem?, destino?, modal?, priorizar_menos_caminhada?, evitar_escadas?, rota_selecionada?}` | Atualiza só os campos enviados. `origem`, `destino` e `rota_selecionada` podem ser limpos com `null`. |
| `POST /sessoes/{codigo}/sair` `{token}` | Sai. O último a sair apaga a sessão; se o criador sai, o próximo vira criador. |
| `POST /sessoes/{codigo}/encerrar` `{token}` | Apaga a sessão para todos (só o criador). |

Regras:

- Estado compartilhado: `origem`/`destino` (`lat`, `lon`, `rotulo` opcional), `modal`, `priorizar_menos_caminhada`, `evitar_escadas`, `rota_selecionada` (0 a 2, as três alternativas).
- Cada alteração real aumenta `versao` e gera um evento. Alteração igual ao estado atual não muda nada (`alterado: false`).
- Mudar origem, destino, modal ou preferência zera `rota_selecionada`, porque a alternativa escolhida deixa de valer. Enviar a nova escolha na mesma atualização a preserva.
- Se `versao_base` for diferente da versão atual, a resposta é 409 com `versao_atual` e `estado`, e nada é gravado.
- Erros: 404 código inexistente, malformado ou expirado; 403 token inválido; 409 conflito ou sessão cheia (6 pessoas); 422 corpo inválido; 503 limite de 200 sessões ativas.

Privacidade e limites (também em `AVISO_PRIVACIDADE`, devolvido em toda resposta):

- Memória do servidor apenas: nada vai para disco nem para o SQLite; reiniciar o servidor apaga tudo.
- Expira após 2 horas sem atividade. Há no máximo 200 sessões, 6 participantes e 100 eventos por sessão.
- Só apelido. E-mail, telefone ou sequência longa de dígitos no apelido são recusados (422). Nenhum token de outra pessoa aparece nas respostas.
- Quem sabe o código pode entrar; trate o código como convite. Sem autenticação de rede: use só em rede de confiança.
- A sessão não calcula rotas nem afirma acessibilidade. Só guarda o que os participantes escolheram.

## 4. Testes de integração

```powershell
python -m pytest backend/tests/integracao -v     # só esta parte (80 testes)
python -m pytest backend/tests -v                # tudo, como no GitHub Actions
python app.py --verificar                        # conferência rápida de contratos
```

Nenhum teste usa a internet: Photon e Transitous são substituídos por respostas simuladas (`unittest.mock.patch`). O GitHub Actions já executa `backend/tests` inteiro, então estes testes entram no CI sem alterar o workflow.

| Arquivo | Testes | O que cobre |
|---|---|---|
| `test_sessoes.py` | 35 | Regras do gerenciador (código, apelido, expiração com relógio simulado, limites, token, versões, conflito, herança do criador, concorrência com 30 threads) e o contrato HTTP. |
| `test_servidor.py` | 18 | Montagem do `app.py`, `/health`, `/integracao/status`, contratos no OpenAPI, CORS do frontend Expo, linha de comando (`--verificar`, porta inválida, modo inválido, aviso de host de rede, `--reload`). |
| `test_contratos.py` | 27 | Promessas entre módulos da seção 2 e um fluxo ponta a ponta com duas pessoas: busca de endereço, plano compartilhado, rota real, escolha, mudança de plano e encerramento. |

### Evidência da execução

Executado em Linux, Python 3.13, `fastapi 0.163.2`, `httpx 0.28.1`, com `CITIZEN_MODO=teste`, sobre a `main` de 17/11/2026:

| Comando | Resultado |
|---|---|
| `python -m pytest backend/tests/integracao -q` | 80 passed em 0,47 s |
| `python -m pytest backend/tests -q` | 252 passed em 4,75 s (172 anteriores + 80 desta parte) |
| `python app.py --verificar` | 5 módulos `[OK]`; base de orientações carregada (3 registros); código de saída 0 |
| `python app.py --porta 8765` + `curl` | `/health` 200; `/integracao/status` com `ok = true`; `POST /sessoes` 201 |

### O que estes testes NÃO provam

- Não testam Photon, Transitous ou OpenRouteService reais; a integração com esses provedores precisa de teste manual com internet.
- Não testam o frontend (Expo/MapLibre). O que está provado é o contrato de API que ele consome e a compatibilidade com o CORS.
- Não são homologação de acessibilidade nem de percursos reais.
- A sessão usa polling. Não há WebSocket, nem proteção contra tentativa repetida de adivinhar o código (6 caracteres de um alfabeto de 31 símbolos) além do limite de sessões.

## 5. Pendências observadas na integração (de outros módulos)

1. `backend/data/orientacoes.json` tem 3 registros, todos `rascunho`. O enunciado exige 15 registros verificados em pelo menos 3 temas, com fonte e data. Enquanto isso, `/consultar` nunca retorna `ok`.
2. O enunciado pede `python src/sistema.py`, mas `python backend/src/sistema.py` falha com `ModuleNotFoundError: No module named 'backend'`. O comando que funciona hoje é `python -m backend.src.sistema`. Vale decidir se o README usa esse comando ou se `sistema.py` recebe um ajuste de `sys.path`.
3. `docs/uso_ia.md` ainda tem a coluna Responsável como `PENDENTE` nas linhas da evolução v2.
4. A execução completa de `pytest backend/tests` regenera `docs/relatorio_importacao_sptrans.md` (data, hash e tempo mudam a cada execução); lembrar de não commitar essa mudança por engano.
