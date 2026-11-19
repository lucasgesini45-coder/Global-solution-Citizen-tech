# Citizen Tech — Mobilidade Urbana | FIAP Global Solution 2026

Protótipo acadêmico **web e mobile** para planejar deslocamentos na região de São Paulo e consultar orientações cidadãs. O foco de evolução é **mobilidade inclusiva** para pessoas com deficiência física e mobilidade reduzida.

> **Aviso:** não é um canal oficial de Metrô, CPTM, SPTrans ou demais operadores. Horários, acessibilidade, tarifas, segurança e disponibilidade podem não estar confirmados. O projeto **não garante** rotas sem barreiras ou elevadores operacionais.

## Entrega acadêmica — Citizen Assist AI

- **Equipe e RMs:** preencher com os dados reais dos integrantes antes da entrega.
- **Vídeo:** inserir URL do vídeo não listado no YouTube após publicação.

O módulo obrigatório é executável na raiz do repositório, sem APIs externas e sem instalar bibliotecas adicionais:

```powershell
python src/sistema.py
```

O assistente de orientação cidadã consulta 15 registros em quatro temas (cartões, gratuidade, acessibilidade e serviços), com fontes oficiais e datas de consulta. Permite pesquisar por pergunta ou selecionar tema e identificador. Não exige cadastro nem dados pessoais. O mapa e o site são complementos.

**Exemplos:** "Como emitir cartão comum?", "Posso levar cão-guia no metrô?" e "O que é o serviço Atende+?". Consulte a fonte exibida. Entradas vazias, opções inválidas, ambiguidades e consultas fora do escopo recebem mensagens de limitação.

A busca usa listas, dicionários, normalização de palavras, comparação Dice e um grafo de temas relacionados. O modelo A apresenta orientação e fonte; o B também explicita os limites e a necessidade de conferir atualizações. A escolha padrão é B. Consulte [a documentação acadêmica](docs/adequacao_fiap.md).

Para executar os 20 cenários em ambos os modelos e gerar indicadores e respostas obtidas:

```powershell
python -m backend.src.avaliacao_cidada
```

### Indicadores acadêmicos — execução de 17/11/2026

| Indicador | Modelo A | Modelo B |
|---|---:|---:|
| Consultas | 20 | 20 |
| Acertos | 19 (95%) | 19 (95%) |
| Tempo médio | 0,2171 ms | 0,2092 ms |
| Saídas com estado ok e fonte | 18/18 | 18/18 |
| Aviso de não oficialidade nas saídas ok | 0/18 | 18/18 |
| Tratamento dos três casos de limitação | 2/3 | 2/3 |

Evidência: [GitHub Actions](https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech/actions/runs/44088026008), 177 testes aprovados e typecheck aprovado. O modelo B é preferido por explicitar os limites. O termo ambíguo "cartão comum" retornou ID 1 em vez de solicitar esclarecimento. Melhorias: desambiguação, novas paráfrases, revisão de fontes e usabilidade com participante. Os tempos medem somente a busca local. O roteiro automatizado de facilidade de uso passou, mas não houve avaliação humana.

- [Relatório acadêmico de testes e indicadores](docs/relatorio_testes_indicadores_fiap.md)
- [Resultados completos por consulta e modelo](docs/resultados_avaliacao_cidada.json)

A equipe deve revisar a base de fontes e a apresentação dos resultados antes da entrega.

## Funcionalidades integradas

- Busca de endereços pelo Photon / OpenStreetMap, GPS autorizado ou seleção no mapa;
- Mapa MapLibre com OpenFreeMap Positron, trajetos de caminhada, ônibus e metrô/trem coloridos;
- Planejamento multimodal via Transitous/MOTIS: linhas, estações, embarque, desembarque e baldeações quando o provedor informa;
- Preferência **priorizar menos caminhada** e registro de necessidade de percurso sem escadas, com aviso de **acessibilidade não verificada**;
- Módulo acadêmico de análise de passagem sem degraus (dados de exemplo, sem comprovação de campo);
- Assistente cidadão com base local; módulo adicional de classificação em `/assistente`;
- Motor de rotas e tarifas **simuladas**, isolado no laboratório;
- Infraestrutura de banco SQLite, migrações e importador GTFS (uso mediante fonte de dados adequada).

## Estrutura

| Diretório | Responsabilidade |
|---|---|
| `frontend/` | Expo, React Native, TypeScript, Web e aplicativo |
| `frontend/components/MapaPreview.web.tsx` | MapLibre no navegador |
| `frontend/components/MapaPreview.tsx` | MapLibre em WebView no mobile |
| `backend/src/api.py` | FastAPI e montagem dos endpoints |
| `backend/src/transitous_api.py` | Planejamento com dados de transporte |
| `backend/src/enderecos_api.py` | Geocodificação e consulta de rotas |
| `backend/src/acessibilidade.py` | Analisador de dados de passagem sem degraus |
| `backend/src/acessibilidade_api.py` | API de avaliação, sem verificação em campo |
| `backend/src/assistente/` | Classificador e assistente |
| `backend/src/rotas/` | Algoritmos do laboratório acadêmico |
| `backend/src/db/` | SQLite e migrações |
| `backend/src/transporte/` | Importador GTFS |
| `docs/` | PRD, documentação e roteiro de implantação |

## Assistente de viagem e planejamento econômico

Após calcular a rota real, abra **Assistente de viagem** para seguir etapas, consultar embarque, desembarque, horários e paradas intermediárias. A conclusão é manual; o progresso não usa localização contínua. Para uma conexão perdida, retorne ao planejador, confirme a origem atual e recalcule.

**Planejamento econômico** compara até cinco itinerários retornados na mesma consulta e modal. A estimativa soma tarifas comuns avulsas de serviços identificados (SPTrans R$ 5,30, rede ferroviária convencional R$ 5,40; ônibus municipais gratuitos aos domingos quando identificados). Não presume descontos, gratuidades pessoais ou integração. O custo fica indefinido se alguma etapa não tiver tarifa identificada. A tarifa integrada comum de R$ 9,38 é apresentada como referência, sujeita às regras do Bilhete Único. Não representa garantia de cobrança. Fontes: [SPTrans](https://www.sptrans.com.br/tarifas), [Metrô](https://www.metro.sp.gov.br/sua-viagem/bilhetes-cartoes/), [Tarifa Zero](https://www.sptrans.com.br/perguntas-e-respostas/?sobre=tarifa-zero), consultadas em 17/11/2026. Selecionar uma alternativa atualiza o mapa, as etapas e horários.

Testes específicos: `python -m pytest backend/tests/test_viagem_economia.py -v`. A disponibilidade de opções, identificação de operadoras e horários depende do Transitous. A comparação não busca exaustivamente todas as modalidades nem certifica acessibilidade.

## Instalação no Windows

No PowerShell, a partir da **raiz do repositório**:

```powershell
git pull origin main
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.src.api:app --reload --port 8000
```

Em **outro terminal**, na raiz:

```powershell
cd frontend
npm install
npx expo start --web --clear
```

Abra o endereço local exibido pelo Expo. A API e a documentação interativa ficam em http://127.0.0.1:8000/docs.

**No celular**, configure `EXPO_PUBLIC_API_URL` com o endereço de rede local acessível do backend; `127.0.0.1` aponta para o próprio telefone.

## Endpoints

| Método | Endpoint | Uso |
|---|---|---|
| GET | `/health` | Verificar API |
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

## Testes

```powershell
python -m pytest backend/tests -v
cd frontend
npx tsc --noEmit
```

GitHub Actions executa os testes do backend e o typecheck do frontend nos pull requests. Não confunda testes automatizados com homologação de percursos reais.

## Próximas entregas do PRD

Consulte [o plano de integração e evolução](docs/PLANO_EXECUCAO_PRD.md). Prioridades: validar dados oficiais de acessibilidade, exibir alternativas reais, reduzir trajetos a pé inadequados, confirmar horários por operadora, testes manuais Web/mobile e finalizar a avaliação acadêmica do assistente.

## Integração do grupo

- `evolucao-v2` → `main`: PR #3 (banco, GTFS, assistente, motor e testes);
- `raphael/acessibilidade` → `main`: código integrado e documentado no PR #4 para resolver o conflito no PR #2;
- `ia-integrada`, `integracao/citizen-mobilidade`, `part2-tarifas` e `feat/estrutura-inicial-citizen-mobilidade`: mudanças já ancestrais da `main`.

**FIAP Global Solution — protótipo educacional; não use suas previsões como única base para deslocamento seguro.**
