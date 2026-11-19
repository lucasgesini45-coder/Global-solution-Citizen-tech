<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:172554,50:2563eb,100:7c3aed&height=230&section=header&text=LOCALIZA%20FACIL&fontColor=ffffff&fontSize=48&desc=Mobilidade%20Urbana%20Inteligente&descSize=18&descAlignY=72" alt="Localiza Facil — Mobilidade Urbana">

**Tecnologia a serviço de cidades mais conectadas, inclusivas e humanas.**

![FIAP](https://img.shields.io/badge/FIAP-Global%20Solution%202026.2-ED145B?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Expo](https://img.shields.io/badge/Expo-20232A?style=for-the-badge&logo=expo&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)

[Sobre](#sobre-o-projeto) · [Funcionalidades](#funcionalidades) · [Execução](#execução-obrigatória-para-correção) · [API](#endpoints) · [Equipe](#equipe) · [Vídeo](https://youtu.be/xAq7-K4gA7I)

</div>

---

## Sobre o projeto

O **Localiza Facil — Mobilidade Urbana** é um protótipo acadêmico da Global Solution 2026.2 da FIAP, desenvolvido para facilitar o planejamento de deslocamentos em São Paulo e ampliar o acesso a informações cidadãs.

A proposta reúne planejamento de trajetos, mapas interativos e um assistente inteligente em uma única plataforma web e mobile, com atenção especial às necessidades de pessoas com deficiência física e mobilidade reduzida.

### Nossa proposta

| Desafio | Solução proposta |
|---|---|
| Informações de transporte dispersas | Consulta centralizada de trajetos e orientações |
| Dificuldade para planejar deslocamentos | Mapa, busca de endereços e itinerários multimodais |
| Barreiras de mobilidade | Preferências de caminhada e indicação transparente de dados de acessibilidade não verificados |
| Dúvidas sobre serviços e direitos | Assistente cidadão com referências e limites explícitos |

## Entrega acadêmica — Citizen Assist AI

**Equipe:** Localiza Facil.  
**Global Solution 2026.2 | Ciência da Computação — FIAP**

O problema é a dificuldade de localizar informações confiáveis sobre direitos, cartões, benefícios e serviços de transporte. O público beneficiado inclui cidadãos que utilizam transporte coletivo, especialmente pessoas com deficiência ou mobilidade reduzida, idosos e estudantes.

### Execução obrigatória para correção

Na raiz do repositório, com Python 3.10 ou superior:

```powershell
git clone https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech.git
cd Global-solution-Citizen-tech
python src/sistema.py
```

O menu acadêmico funciona localmente, sem instalar pacotes, sem cadastro, sem chave de API e sem internet. A opção 4 (assistente adicional do aplicativo) é opcional e pode exigir as dependências do backend. O site é um complemento.

### Base de conhecimento e algoritmo

- [Base JSON](data/orientacoes.json): 15 registros, quatro temas (cartões, gratuidade, acessibilidade e serviços). Cada dicionário contém ID, tema, perguntas alternativas, orientação, referência, data de verificação e status.
- Python lê o JSON, valida campos obrigatórios, IDs únicos e datas. Rascunhos não podem gerar orientações.
- A busca normaliza acentos e caixa, remove palavras genéricas e calcula similaridade Dice: duas vezes a interseção dos conjuntos de termos dividida pela soma dos tamanhos. Limiar 0,55; exige dois termos coincidentes ou igualdade. Diferença de até 0,05 entre os melhores candidatos sinaliza ambiguidade.
- Um grafo em dicionário relaciona temas; o menu oferece consulta por tema e ID.

### Regras de resposta e modelos de instrução

| Modelo | Instrução |
|---|---|
| A | Recuperar apenas orientação cadastrada como verificada, com referência e data, ou declarar insuficiência. |
| B (padrão) | Aplicar as mesmas regras e avisar que o assistente não é oficial e que regras atuais devem ser confirmadas. |

São regras locais em Python, não prompts enviados a um LLM. As respostas não inventam fontes. Entrada vazia solicita nova pergunta; opções inexistentes são rejeitadas; consultas sem correspondência orientam a procurar o órgão responsável.

### Exemplos registrados na avaliação

| Entrada | Comportamento |
|---|---|
| Como emitir cartão comum? | Orienta a cadastrar-se no atendimento da SPTrans e consultar emissão e retirada. [Fonte](https://bilheteunico.sptrans.com.br/comum/), data registrada: 17/11/2026. |
| Pergunta vazia | Digite uma pergunta. |
| Qual a receita de bolo de chocolate? | Não encontrei orientação verificada. Consulte o órgão responsável ou escolha um assunto. |
| cartão comum | Caso ambíguo conhecido: a avaliação histórica retornou a emissão (ID 1), quando deveria pedir esclarecimento. |

### Plano de testes, resultados e interpretação

```powershell
python -m backend.src.avaliacao_cidada
python -m pip install pytest
python -m pytest backend/tests/test_core.py backend/tests/test_citizen_fiap.py -v
```

A avaliação mede 20 cenários por modelo: status e ID esperados versus obtidos, presença de fonte, tempo de busca e avisos. Os resultados abaixo são históricos, medidos em 17/11/2026 na implementação de origem, e devem ser reproduzidos após a integração.

| Indicador | A | B |
|---|---:|---:|
| Acertos | 19/20 (95%) | 19/20 (95%) |
| Tempo médio | 0,2171 ms | 0,2092 ms |
| Respostas OK com fonte | 18/18 | 18/18 |
| Respostas OK com aviso de não oficialidade | 0/18 | 18/18 |
| Casos de limitação corretos | 2/3 | 2/3 |

A busca é a mesma nos dois modelos; B é preferido pela transparência. A amostra é pequena e a diferença temporal não permite concluir superioridade. O roteiro automatizado de uso passou na execução histórica; não houve participante humano. O erro de ambiguidade foi mantido como limitação.

[Plano e método](docs/adequacao_fiap.md) · [Relatório completo](docs/relatorio_testes_indicadores_fiap.md) · [Resultados JSON](docs/resultados_avaliacao_cidada.json) · [Cenários](data/perguntas_cidadas_teste.json) · [Evidência CI histórica](https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech/actions/runs/44088026008)

### Clareza, acessibilidade e privacidade

Menu textual numerado e mensagens claras facilitam o uso sem interface gráfica. Não solicita CPF, nome, laudo ou localização para consultas acadêmicas; não persiste as perguntas do terminal. No mapa opcional, GPS depende de autorização. Não há vínculo oficial com órgãos públicos nem garantia sobre elevadores, tarifas ou rotas acessíveis. A revisão humana das fontes e a avaliação de usabilidade ainda precisam ser registradas.

### Conclusões e melhorias

A abordagem local demonstra leitura de arquivos, listas, dicionários, conjuntos, grafos, validação, busca e testes. Para evoluir: melhorar desambiguação de termos genéricos, ampliar paráfrases e perguntas inéditas, revisar fontes e realizar testes manuais de acessibilidade e usabilidade.

### Vídeo e identificação da equipe

- [Vídeo de apresentação no YouTube](https://youtu.be/xAq7-K4gA7I).
- [Integrantes e RMs](#equipe).
- Tutor(a) e decisão de participação na competição: **a confirmar pela equipe**.
- Modelo de organização: [FIAP — GLOBAL-SOLUTION-2](https://github.com/equipe1ccon/FIAP-PORTFOLIO-1CCON/tree/master).

### Organização para correção

| Pasta | Conteúdo |
|---|---|
| `src/` | Entrada obrigatória do terminal |
| `data/` | Base cidadã e perguntas de avaliação |
| `docs/` | Documentação, registro de IA, relatórios e resultados |
| `notebooks/` | Notebook opcional de reprodução de indicadores |
| `backend/` | Núcleo Python, API e testes |
| `frontend/` | Interface web e mobile opcional |

---

## Funcionalidades

<div align="center">
<table>
<tr>
<td width="33%"><img src="frontend/assets/metro_futurista.jpg" alt="Metrô e trem"></td>
<td width="33%"><img src="frontend/assets/onibus_futurista.jpg" alt="Ônibus"></td>
<td width="33%"><img src="frontend/assets/caminhada_futurista.jpg" alt="Caminhada"></td>
</tr>
<tr><td align="center"><b>Metrô e trem</b></td><td align="center"><b>Ônibus</b></td><td align="center"><b>Caminhada</b></td></tr>
</table>
</div>

- Busca de endereços pelo Photon / OpenStreetMap, GPS autorizado ou seleção no mapa;
- Mapa MapLibre com OpenFreeMap Positron, trajetos de caminhada, ônibus e metrô/trem coloridos;
- Planejamento multimodal via Transitous/MOTIS: linhas, estações, embarque, desembarque e baldeações quando o provedor informa;
- Preferência **priorizar menos caminhada** e registro de necessidade de percurso sem escadas, com aviso de **acessibilidade não verificada**;
- Módulo acadêmico de análise de passagem sem degraus (dados de exemplo, sem comprovação de campo);
- Assistente cidadão com base local; módulo adicional de classificação em `/assistente`;
- Motor de rotas e tarifas **simuladas**, isolado no laboratório;
- Infraestrutura de banco SQLite, migrações e importador GTFS (uso mediante fonte de dados adequada).

## Arquitetura e tecnologias

```mermaid
flowchart TD
    U[Usuário Web / Mobile] --> F[Expo · React Native · TypeScript]
    F --> M[MapLibre · OpenFreeMap]
    F --> A[API FastAPI]
    A --> P[Photon / OpenStreetMap]
    A --> T[Transitous / MOTIS]
    A --> I[Assistente cidadão]
    A --> D[SQLite · GTFS · Laboratório de rotas]
    I --> B[Base de orientações e referências]
```

| Camada | Tecnologias |
|---|---|
| Interface | React Native, Expo, TypeScript |
| Backend | Python, FastAPI, Uvicorn |
| Mapas | MapLibre, OpenFreeMap |
| Geocodificação | Photon / OpenStreetMap |
| Transporte | Transitous / MOTIS, GTFS |
| Inteligência artificial | Classificação, busca e base de orientações |
| Persistência acadêmica | SQLite |
| Qualidade | Pytest, TypeScript, GitHub Actions |

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

## Como executar localmente (site opcional)

### Pré-requisitos

Git, Python compatível com as dependências de `backend/requirements.txt`, Node.js e npm.

### 1. Clone o projeto

```powershell
git clone https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech.git
cd Global-solution-Citizen-tech
```

### 2. Inicie o backend

Na raiz do projeto, no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.src.api:app --reload --port 8000
```

Acesse [Swagger UI](http://127.0.0.1:8000/docs) ou [Health](http://127.0.0.1:8000/health).

### 3. Inicie o frontend

Abra outro terminal na raiz:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npx expo start --web --clear
```

Se já existir um arquivo `.env`, preserve suas configurações em vez de copiá-lo novamente. Abra o endereço exibido pelo Expo e mantenha os dois terminais em execução.

### 4. Teste no celular (opcional)

Configure `EXPO_PUBLIC_API_URL` em `frontend/.env` com o IP local do computador, inicie o backend com `--host 0.0.0.0` em uma rede confiável e execute `npx expo start` no frontend. O endereço `127.0.0.1` no celular não aponta para o computador.

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
.\.venv\Scripts\python.exe -m pytest backend/tests -v
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


## Equipe

**Localiza Facil — FIAP Global Solution 2026.2**

| Integrante | RM |
|---|---|
| [Lucas Ribeiro Gesini](https://github.com/lucasgesini45-coder) | RM569383 |
| [Raphael de Freitas Silva](https://github.com/raphafreitass1982) | RM570089 |
| Paulo Henrique Gonçalves Bueno | RM570456 |
| Filipe Souza Nascimento | RM573758 |
| Calebe Gonçalves Garcia de Souza | RM568743 |

[Assista ao vídeo de apresentação](https://youtu.be/xAq7-K4gA7I)

## Aviso de responsabilidade

Este projeto é educacional e não representa Metrô, CPTM, SPTrans ou outros operadores. Tarifas, horários, segurança e acessibilidade podem não estar confirmados. A preferência por evitar escadas não garante uma rota livre de barreiras. Consulte fontes oficiais antes de viajar.

<div align="center">

**FIAP | Ciência da Computação | Global Solution 2026.2**

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:172554,50:2563eb,100:7c3aed&height=100&section=footer" alt="">

</div>
