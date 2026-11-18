# Citizen Tech — Mobilidade Urbana | FIAP Global Solution 2026

Protótipo acadêmico **web e mobile** para planejar deslocamentos na região de São Paulo e consultar orientações cidadãs. O foco de evolução é **mobilidade inclusiva** para pessoas com deficiência física e mobilidade reduzida.

> **Aviso:** não é um canal oficial de Metrô, CPTM, SPTrans ou demais operadores. Horários, acessibilidade, tarifas, segurança e disponibilidade podem não estar confirmados. O projeto **não garante** rotas sem barreiras ou elevadores operacionais.

## Equipe

**Nome da equipe:** PREENCHER

| Responsável | Módulo | Integrante | RM |
|---|---|---|---|
| 1 | Dados e fontes | PREENCHER | PREENCHER |
| 2 | Rotas e tarifas | Raphael de Freitas Silva | PREENCHER |
| 3 | Acessibilidade e segurança | PREENCHER | PREENCHER |
| 4 | Interface e mapa | PREENCHER | PREENCHER |
| 5 | Servidor e integração | PREENCHER | PREENCHER |

**Vídeo de apresentação (YouTube, não listado):** PREENCHER

## Funcionalidades integradas

- Busca de endereços pelo Photon / OpenStreetMap, GPS autorizado ou seleção no mapa;
- Mapa MapLibre com OpenFreeMap Positron, trajetos de caminhada, ônibus e metrô/trem coloridos;
- Planejamento multimodal via Transitous/MOTIS: linhas, estações, embarque, desembarque e baldeações quando o provedor informa;
- Preferência **priorizar menos caminhada** e registro de necessidade de percurso sem escadas, com aviso de **acessibilidade não verificada**;
- Módulo acadêmico de análise de passagem sem degraus (dados de exemplo, sem comprovação de campo);
- Assistente cidadão com base local; módulo adicional de classificação em `/assistente`;
- Motor de rotas e tarifas **simuladas**, isolado no laboratório;
- Infraestrutura de banco SQLite, migrações e importador GTFS (uso mediante fonte de dados adequada);
- Servidor local único (`app.py`) com conferência dos contratos entre módulos em `/integracao/status`;
- Sessão colaborativa básica: duas ou mais pessoas compartilham origem, destino, preferências e a rota escolhida, sem conta e sem guardar dados em disco.

## Estrutura

| Diretório | Responsabilidade |
|---|---|
| `frontend/` | Expo, React Native, TypeScript, Web e aplicativo |
| `frontend/components/MapaPreview.web.tsx` | MapLibre no navegador |
| `frontend/components/MapaPreview.tsx` | MapLibre em WebView no mobile |
| `app.py` | Servidor local: monta a API, a sessão colaborativa e `/integracao/status` |
| `backend/src/api.py` | FastAPI e montagem dos endpoints |
| `backend/src/sessoes.py` | Sessão colaborativa (em memória, com expiração) |
| `backend/tests/integracao/` | Testes de contrato entre módulos, servidor e sessão |
| `backend/src/transitous_api.py` | Planejamento com dados de transporte |
| `backend/src/enderecos_api.py` | Geocodificação e consulta de rotas |
| `backend/src/acessibilidade.py` | Analisador de dados de passagem sem degraus |
| `backend/src/acessibilidade_api.py` | API de avaliação, sem verificação em campo |
| `backend/src/assistente/` | Classificador e assistente |
| `backend/src/rotas/` | Algoritmos do laboratório acadêmico |
| `backend/src/db/` | SQLite e migrações |
| `backend/src/transporte/` | Importador GTFS |
| `docs/` | PRD, documentação e roteiro de implantação |

## Instalação no Windows

No PowerShell, a partir da **raiz do repositório**:

```powershell
git pull origin main
python -m pip install -r backend/requirements.txt
python app.py
```

O servidor abre em http://127.0.0.1:8000 e só aceita conexões do próprio computador. Outras opções: `python app.py --porta 8010`, `python app.py --verificar` (confere os contratos entre módulos e sai) e `python app.py --host 0.0.0.0` (para o celular acessar pela rede local, sem autenticação). O comando anterior, `python -m uvicorn backend.src.api:app --reload --port 8000`, continua válido, mas sem sessões e sem `/integracao/status`.

Em **outro terminal**, na raiz:

```powershell
cd frontend
npm install
npx expo start --web --clear
```

Abra o endereço local exibido pelo Expo. A API e a documentação interativa ficam em http://127.0.0.1:8000/docs.

**Interface textual (sem Expo e sem API):** `python -m backend.src.sistema`, a partir da raiz do repositório. Oferece menu de temas, pergunta em texto e o assistente de dúvidas.

**No celular**, configure `EXPO_PUBLIC_API_URL` com o endereço de rede local acessível do backend; `127.0.0.1` aponta para o próprio telefone.

## Endpoints

| Método | Endpoint | Uso |
|---|---|---|
| GET | `/health` | Verificar API |
| GET | `/integracao/status` | Conferir se cada módulo expõe os endpoints do contrato; modo e sessões ativas |
| POST | `/sessoes` | Criar sessão colaborativa (devolve código e token) |
| POST | `/sessoes/{codigo}/entrar` | Entrar na sessão com o código |
| POST | `/sessoes/{codigo}/sincronizar` | Ler o estado e os eventos novos |
| POST | `/sessoes/{codigo}/estado` | Atualizar origem, destino, modal, preferências e rota escolhida |
| POST | `/sessoes/{codigo}/sair` | Sair da sessão |
| POST | `/sessoes/{codigo}/encerrar` | Encerrar para todos (somente o criador) |
| GET | `/temas` | Temas do assistente original |
| POST | `/consultar` | Orientação com referências locais |
| GET | `/enderecos/sugestoes?q=...` | Buscar endereços |
| POST | `/rotas/reais` | Consultar trajeto multimodal |
| POST | `/acessibilidade/avaliar` | Analisar dados de passagem sem degraus **fornecidos** |
| GET | `/assistente/saude` | Estado do classificador |
| POST | `/assistente/perguntar` | Consulta ao classificador |
| POST | `/agente/conversar` | Chat integrado: respostas acadêmicas, informações verificadas e rotas reais com atualização no mapa |
| GET | `/rotas/exemplo` | Simulação acadêmica |
| POST | `/rotas` | Motor simulado |

O chat do frontend utiliza `POST /agente/conversar` e envia a pergunta, origem e destino selecionados, modal e preferências. Quando o backend retorna `rota` com geometria válida, o frontend sincroniza o mapa. A ausência de dados oficiais para benefícios e acessibilidade não é substituída por uma afirmação gerada pelo classificador.

O corpo de `POST /rotas/reais` permite:

```json
{
  "origem": {"lat": -23.5505, "lon": -46.6333},
  "destino": {"lat": -23.5580, "lon": -46.6610},
  "modal": "ferroviario",
  "priorizar_menos_caminhada": true,
  "evitar_escadas": true
}
```

`evitar_escadas` **não filtra com garantia** as barreiras reais: sinaliza a necessidade e retorna status `NAO_VERIFICADA` até integrar evidências confiáveis.

## Sessão colaborativa

Quem cria a sessão recebe um código de 6 caracteres para convidar os outros e um token secreto; cada participante recebe o seu. Todos veem o mesmo planejamento e a atualização chega por consulta periódica (`sincronizar`). Se duas pessoas alteram ao mesmo tempo e enviam `versao_base`, a segunda recebe 409 com o estado atual em vez de apagar a edição da primeira. Mudar origem, destino ou preferências zera a rota escolhida.

Privacidade: tudo fica na memória do servidor, expira após 2 horas sem atividade, aceita só um apelido (e-mail e telefone são recusados) e não guarda localização contínua. A sessão apenas compartilha escolhas; não calcula rotas nem afirma acessibilidade. Detalhes, limites e códigos de erro em [docs/integracao.md](docs/integracao.md).

## Testes

```powershell
python -m pytest backend/tests -v                # todos, como no GitHub Actions
python -m pytest backend/tests/integracao -v     # contratos entre módulos, servidor e sessão
python app.py --verificar                        # conferência rápida dos contratos
cd frontend
npx tsc --noEmit
```

Em 17/11/2026, na `main`, a suíte completa teve 252 testes aprovados (80 em `backend/tests/integracao`), sem usar a internet: Photon e Transitous são simulados nos testes. A tabela de contratos, a evidência da execução e o que os testes **não** provam estão em [docs/integracao.md](docs/integracao.md).

GitHub Actions executa os testes do backend e o typecheck do frontend nos pull requests. Não confunda testes automatizados com homologação de percursos reais.

## Exemplos de entrada e de comportamento com entradas inválidas

| Entrada | Resposta |
|---|---|
| `POST /consultar` com pergunta vazia | `status = entrada_invalida`, `resposta = "Digite uma pergunta."` |
| `POST /consultar` sem registro verificado | `status = sem_resposta`, sem fontes, com temas relacionados |
| `POST /consultar` com mais de 500 caracteres ou `modelo` diferente de A/B | HTTP 422 com `detail` |
| `POST /agente/conversar` pedindo rota sem origem e destino | Pede os pontos; não consulta o motor de rotas |
| `POST /agente/conversar` sobre direitos sem base verificada | `origem_resposta = sem_resposta_verificada`, sem fontes |
| `POST /acessibilidade/avaliar` com trecho de passagem desconhecida | `NAO_VERIFICADA`, nunca "acessível" |
| `POST /rotas/reais` com provedor fora do ar | HTTP 503 com mensagem legível; o app não trava |
| `POST /sessoes/{codigo}/entrar` com código inexistente ou expirado | HTTP 404 "Sessão não encontrada ou expirada." |

## Cuidados com clareza, acessibilidade, privacidade e informação não oficial

- O projeto não é canal oficial e não promete integração com órgãos públicos; os avisos aparecem nas respostas.
- Informação sem fonte e data verificadas não vira orientação: o assistente informa o limite e sugere outro tema.
- Acessibilidade desconhecida permanece `NAO_VERIFICADA`; só bloqueio comprovado altera o resultado.
- Nenhum dado pessoal é exigido. Sessões colaborativas usam apelido, ficam só em memória e expiram. GPS só com autorização.
- Dados de rotas, horários e tarifas do motor de laboratório são fictícios e rotulados como tal.

## Limitações conhecidas

- A base de orientações cidadãs ainda está em revisão: faltam registros verificados com fonte e data para atingir o mínimo do enunciado.
- A sessão colaborativa usa consulta periódica (sem WebSocket) e não tem autenticação de rede; use só em rede de confiança.
- Os testes automatizados não substituem testes manuais em Web e celular, nem a homologação de percursos reais.
- Cobertura e horários dependem dos provedores externos (Transitous/OpenStreetMap), que podem recusar ou limitar consultas.

## Próximas entregas do PRD

Consulte [o plano de integração e evolução](docs/PLANO_EXECUCAO_PRD.md). Prioridades: validar dados oficiais de acessibilidade, exibir alternativas reais, reduzir trajetos a pé inadequados, confirmar horários por operadora, testes manuais Web/mobile e finalizar a avaliação acadêmica do assistente.

## Integração do grupo

- `evolucao-v2` → `main`: PR #3 (banco, GTFS, assistente, motor e testes);
- `raphael/acessibilidade` → `main`: código integrado e documentado no PR #4 para resolver o conflito no PR #2;
- `ia-integrada`, `integracao/citizen-mobilidade`, `part2-tarifas` e `feat/estrutura-inicial-citizen-mobilidade`: mudanças já ancestrais da `main`.

**FIAP Global Solution — protótipo educacional; não use suas previsões como única base para deslocamento seguro.**
