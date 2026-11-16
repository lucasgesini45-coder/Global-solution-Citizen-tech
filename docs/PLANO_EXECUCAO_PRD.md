# Plano de execução do PRD — Citizen Tech

**Referência:** PRD v1.0 de 16/11/2026, Global Solution FIAP.  
**Branch de entrega:** `main`.  
**Status:** consolidação de módulos do grupo; **não** constitui certificação de acessibilidade ou homologação de produção.

## Integrações realizadas

| Entrega | Origem | Status | Verificação |
|---|---|---|---|
| Core Python, frontend Expo e mapa | `main` e branches integradas anteriormente | Incorporado | Revisar em web e dispositivo real |
| Rotas multimodais Transitous e Photon | `main` | Incorporado | Testar origem GPS, ausência de geometria e interrupções |
| Assistente modular de classificação | `evolucao-v2` | Código integrado | Base acadêmica precisa revisão de evidências |
| SQLite e migrações | `evolucao-v2` | Código integrado | Homologar persistência, purga, migrações e LGPD |
| Importador GTFS | `evolucao-v2` | Código integrado | Testes usam fixture; feed real depende de fonte licenciada |
| Motor demonstrativo de tarifas | `evolucao-v2` | Código integrado | Sempre rotular dados fictícios |
| Análise de passagem sem degraus | `raphael/acessibilidade` via PR #4 | Integrado | **Dados simulados**; não confere acessibilidade real |
| Preferências de mobilidade | PR #4 | Parcial | `priorizar_menos_caminhada` afeta ranking; `evitar_escadas` registra necessidade sem garantir rota livre de escadas |
| CI | PR #3 e #4 | Ambos passaram no GitHub Actions | Manter testes e typecheck no ciclo de PR |

## Fase 1 — Garantir qualidade do MVP

- [x] Unificar módulos funcionais existentes sem substituir o mapa.
- [x] Integrar o analisador de acessibilidade do grupo e preservar sua documentação.
- [x] Conectar preferência por menor caminhada ao ranking atual.
- [x] Exibir indisponibilidade de comprovação de acessibilidade.
- [ ] Homologar pelo menos 12 viagens reais na região de SP (ônibus, trem, metrô e caminhada).
- [ ] Conferir o desenho no MapLibre Web e no WebView mobile.
- [ ] Verificar GPS aproximado, permissões negadas, falta de feed e falha HTTP.
- [ ] Avaliar critérios WCAG 2.2 AA nas telas críticas.
- [ ] Validar manualmente o fluxo do assistente e suas referências, sem dados pessoais.

## Fase 2 — Rotas alternativas e melhor acessibilidade

- [ ] Exibir múltiplos itinerários reais com seleção sincronizada no mapa (RF-08).
- [ ] Integrar dados oficiais de elevadores, rampas e acessos, com fonte, data e validade (RF-10).
- [ ] Acrescentar preferências de baldeações e limite de caminhada configurável (RF-09).
- [ ] Impedir selo "acessível" quando houver trecho sem evidência.
- [ ] Inserir comparação de caminhada, tempo e baldeações entre alternativas.

## Fase 3 — Conteúdo cidadão e locais acessíveis

- [ ] Curadoria de informações cidadãs com revisão de fontes e datas (RF-12).
- [ ] Catálogo de locais acessíveis mediante informações verificadas (RF-11).
- [ ] Cadastro de benefícios/promoções somente com parceiro e validade confirmados.
- [ ] Testes com usuários, métricas de sucesso e relatório acadêmico de validação.

## Contratos atuais importantes

- `POST /rotas/reais`: `origem`, `destino`, `modal`, `priorizar_menos_caminhada` (bool), `evitar_escadas` (bool).
- `/rotas/reais` devolve `acessibilidade.status = NAO_VERIFICADA` até haver dados confiáveis, mesmo quando `evitar_escadas = true`.
- `POST /acessibilidade/avaliar`: recebe trechos explicitamente fornecidos com `passagem_sem_degraus`; resultado refere-se somente a esses dados e não a vistoria em campo.
- `POST /rotas` e `GET /rotas/exemplo`: simulador de rede e tarifa, jamais substituir o resultado real.

## Riscos e decisões

1. **Cobertura Transitous/GTFS:** resultados variam conforme provedores e horários; não criar geometrias fictícias.
2. **Acessibilidade:** sem data e fonte verificadas, usar `NAO_VERIFICADA`; uma preferência não implica rota sem escadas.
3. **Mapas:** fontes compatíveis com OpenFreeMap; preservar renderização parcial quando faltarem trechos.
4. **Privacidade:** GPS apenas sob permissão e sem retenção não autorizada.
5. **Arquitetura:** os módulos SQLite/GTFS são infraestrutura acadêmica e não significam que itinerários reais já sejam planejados a partir do banco local.
6. **Entrega:** executar testes automatizados, registrar evidências visuais e levantar pendências por responsável.

## Comandos para validação local

```powershell
git pull origin main
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests -v
python -m uvicorn backend.src.api:app --reload --port 8000
```

Em outro terminal:

```powershell
cd frontend
npm install
npx tsc --noEmit
npx expo start --web --clear
```

## Histórico de integração

- PR #3 — `evolucao-v2`: integrado, GitHub Actions concluído com sucesso.
- PR #4 — preferência/acessibilidade: integrado, GitHub Actions concluído com sucesso.
- PR #2 — código incorporado pelo PR #4; encerrado por conflito em `docs/uso_ia.md`. Registro do Raphael preservado na documentação unificada.
