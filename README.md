# Citizen Tech — Mobilidade Urbana | FIAP Global Solution 2026

Protótipo acadêmico **web e mobile** para planejar deslocamentos na região de São Paulo e consultar orientações cidadãs. O foco de evolução é **mobilidade inclusiva** para pessoas com deficiência física e mobilidade reduzida.

> **Aviso:** não é um canal oficial de Metrô, CPTM, SPTrans ou demais operadores. Horários, acessibilidade, tarifas, segurança e disponibilidade podem não estar confirmados. O projeto **não garante** rotas sem barreiras ou elevadores operacionais.

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
| GET | `/rotas/exemplo` | Simulação acadêmica |
| POST | `/rotas` | Motor simulado |

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
