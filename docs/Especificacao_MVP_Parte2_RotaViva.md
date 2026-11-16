# Especificação de implementação: RotaViva, MVP, Parte 2 (Rotas e tarifas)

Versão 1.0 | 08/11/2026 | Responsável: integrante 2 (Raphael de Freitas Silva)

---

## 0. Instruções ao agente de código (ler primeiro)

1. Este documento é a **única fonte de requisitos**. Implemente exatamente o que está escrito.
2. Termos normativos: **DEVE** = obrigatório; **NÃO DEVE** = proibido; **PODE** = permitido, não exigido.
3. Todo valor numérico, nome de arquivo, nome de campo, código de erro e texto entre aspas nesta especificação é **literal**. Não altere, não traduza, não "melhore".
4. Se algo estiver ambíguo ou faltando: **não decida sozinho**. Registre a dúvida em `docs/duvidas.md` (formato: `ID | trecho da especificação | dúvida | o que foi feito provisoriamente`) e use a opção mais restritiva (a que implementa menos).
5. **NÃO adicione** funcionalidades, arquivos, dependências ou parâmetros que não estejam listados aqui.
6. **NÃO invente dados reais**: nenhuma tarifa, horário, linha, parada ou regra de operador real. Use somente os dados fictícios definidos na seção 11.
7. Execute `python -m pytest` ao final de cada etapa da seção 15. Uma etapa só termina com todos os testes dela passando.
8. Ao terminar, preencha `docs/uso_ia.md` conforme a seção 14.

---

## 1. Contexto e decisões já tomadas (NÃO reabrir)

Projeto: aplicativo que compara trajetos de transporte público. Este documento cobre **somente** o módulo 2 da divisão da equipe ("Rotas e tarifas"): busca de trajetos, espera, integração tarifária e até três alternativas distintas.

| ID | Decisão |
|---|---|
| D-01 | O MVP tem **somente transporte público** (ônibus, metrô, trem) e caminhada. **Não existe modo carro** no MVP. Não implementar rede viária, A\*, nem tarifa, combustível, pedágio ou estacionamento de carro. |
| D-02 | Algoritmo de busca: **rodadas de baldeação** (seção 6). Nenhum outro algoritmo de busca. |
| D-03 | Persistência do MVP: **SQLite** (módulo `sqlite3` da biblioteca padrão). Não usar PostgreSQL, PostGIS, Redis nem ORM. |
| D-04 | Entrada de origem e destino: **clique no mapa** (o módulo recebe latitude e longitude) e **pesquisa por endereço** (seção 9). |
| D-05 | Acessibilidade e segurança **não consomem API no MVP**. Este módulo só define os **ganchos** (seção 8). Os dados são responsabilidade de outro integrante. |
| D-06 | Linguagem: Python 3.10 ou superior. Núcleo de rotas, tarifas e ranking **somente com a biblioteca padrão**. |

---

## 2. Escopo

### 2.1 DENTRO do escopo (implementar)

| Arquivo | Conteúdo |
|---|---|
| `src/config.py` | Constantes da seção 3. |
| `src/contratos.py` | Estruturas de dados da seção 4. |
| `src/rotas.py` | Busca por rodadas (seção 6). |
| `src/tarifas.py` | Cálculo tarifário (seção 7). |
| `src/ranking.py` | Viabilidade, seleção e explicações (seção 8). |
| `src/recomendar.py` | Orquestração e adaptador do pedido (seção 8). |
| `src/historico.py` | Histórico em SQLite (seção 10). |
| `src/geocodificacao.py` | Pesquisa por endereço (seção 9). |
| `src/rede_demo.py` | Rede fictícia (seção 11). |
| `data/tarifas_demo.json` | Regras tarifárias fictícias (seção 11). |
| `tests/` | Testes da seção 12. |
| `exemplos/demo.py` | Demonstração no terminal (seção 13). |
| `docs/parte2_rotas_tarifas.md`, `docs/uso_ia.md`, `docs/duvidas.md` | Documentação. |
| `requirements.txt`, `pytest.ini` | Seção 13. |

### 2.2 FORA do escopo (NÃO implementar)

- Interface web, mapa, Leaflet, HTML, CSS, JavaScript.
- Servidor HTTP real (FastAPI, Flask etc.). O módulo expõe apenas funções Python.
- Importação de GTFS real, conectores de SPTrans/Olho Vivo/Metrô/CPTM/ARTESP.
- Dados reais de acessibilidade, segurança, SSP-SP.
- Aplicativo móvel, login, contas de usuário, sessão colaborativa, relatos, moderação.
- Modo carro, previsão de tráfego, tempo real, aprendizado de máquina.

---

## 3. Constantes (arquivo `src/config.py`)

Todas as constantes abaixo DEVEM estar **somente** em `src/config.py` e ser importadas pelos demais módulos. Nenhum número destes pode aparecer escrito dentro de outro módulo.

| Constante | Valor | Unidade / observação |
|---|---|---|
| `RAIO_TERRA_M` | `6371000.0` | metros |
| `FOLGA_BALDEACAO_S` | `60` | segundos, aplicada a partir do 2º embarque |
| `CAMINHADA_BALDEACAO_MAX_M` | `500` | metros por perna a pé de baldeação |
| `ESPERA_MAX_S` | `5400` | segundos por embarque |
| `MAX_RODADAS_PADRAO` | `4` | quando `baldeacoes_max` não é informado |
| `MAX_EXECUCOES` | `10` | buscas na diversificação (seção 6.5) |
| `TAMANHO_CELULA_M` | `500` | metros, grade espacial |
| `VELOCIDADE_CAMINHADA_PADRAO_MS` | `1.2` | metros por segundo |
| `CAMINHADA_MAX_PADRAO_M` | `1000` | metros |
| `CAMINHADA_MAX_LIMITE_M` | `3000` | metros |
| `BALDEACOES_MAX_LIMITE` | `4` | |
| `PESOS` | `{"tempo": 0.5, "custo": 0.25, "exposicao": 0.25}` | |
| `REF` | `{"tempo": 90.0, "custo": 1200.0, "exposicao": 1.0}` | minutos, centavos, índice |
| `LIMIAR_SIMILARIDADE` | `0.8` | |
| `MAX_ROTAS` | `3` | |
| `FUSO` | `"America/Sao_Paulo"` | |
| `RETENCAO_HISTORICO_DIAS` | `90` | valor inicial de projeto, a validar pela equipe |
| `TTL_CACHE_GEOCODIFICACAO_DIAS` | `30` | valor inicial de projeto |
| `GEOCODIFICACAO_INTERVALO_MIN_S` | `1.1` | segundos entre chamadas de rede |
| `GEOCODIFICACAO_TIMEOUT_S` | `10` | segundos |
| `GEOCODIFICACAO_MAX_RESULTADOS` | `5` | |

Valores de `PESOS`, `REF`, `LIMIAR_SIMILARIDADE`, `FOLGA_BALDEACAO_S`, `CAMINHADA_BALDEACAO_MAX_M` e `ESPERA_MAX_S` são **iniciais**; a equipe os calibrará depois. O agente NÃO DEVE alterá-los.

---

## 4. Contratos de dados (`src/contratos.py`)

Usar `dataclasses`. Tempo é sempre **inteiro em segundos desde 00:00 do dia da partida**; pode ser maior que 86400 (passou da meia-noite) e pode ser negativo apenas internamente. Coordenadas são `(lat, lon)` em graus decimais.

### 4.1 Constantes de estado

| Nome | Valor |
|---|---|
| `ACESS_NAO_SOLICITADA` | `"NAO_SOLICITADA"` |
| `ACESS_COMPATIVEL` | `"COMPATIVEL_COM_DADOS_DISPONIVEIS"` |
| `ACESS_NAO_VERIFICADA` | `"NAO_VERIFICADA"` |
| `ACESS_INCOMPATIVEL` | `"INCOMPATIVEL"` |
| `SEG_SUFICIENTE` | `"dados_suficientes"` |
| `SEG_INSUFICIENTE` | `"dados_insuficientes"` |
| `SEG_INDISPONIVEL` | `"indisponivel"` |

### 4.2 Entrada de dados (fornecida por outro integrante)

| Estrutura | Campos (tipo) |
|---|---|
| `Parada` (imutável) | `id: str`, `nome: str`, `lat: float`, `lon: float` |
| `Viagem` (imutável) | `id: str`, `linha_id: str`, `nome_linha: str`, `operador: str`, `modal: str` (`"onibus"`, `"metro"` ou `"trem"`), `sentido: str`, `paradas: tuple[str]`, `horarios: tuple[int]`, `dias_semana: frozenset[int]` (0=segunda … 6=domingo; padrão: todos), `excecoes: frozenset[str]` (datas ISO `AAAA-MM-DD` sem operação; padrão: vazio) |
| `Rede` | `paradas: dict[str, Parada]`, `viagens: list[Viagem]`, `versao: str` (padrão `"sem_versao"`), `origem_dados: str` (padrão `"simulado"`; valores permitidos: `"real"`, `"historico"`, `"simulado"`) |

Regras de `Viagem`: `len(paradas) == len(horarios)`, senão `ValueError`. `horarios` não pode ser decrescente, senão `ValueError`. Propriedade `padrao` = `(linha_id, paradas)`. Método `opera_em(dia: date) -> bool` = `dia.weekday() in dias_semana and dia.isoformat() not in excecoes`.

Regras de `Rede`: método `validar() -> list[str]` retorna uma mensagem `"viagem {id} usa parada inexistente '{parada}'"` para cada parada referenciada que não existe em `paradas`. Método `limites() -> (lat_min, lon_min, lat_max, lon_max)` calculado sobre todas as paradas.

### 4.3 Pedido do passageiro

`Perfil`: `caminhada_max_m: int = 1000`, `baldeacoes_max: int | None = None`, `orcamento_max_centavos: int | None = None`, `acessibilidade: frozenset[str] = frozenset()`, `velocidade_caminhada_ms: float = 1.2`, `perfil_tarifario: str = "padrao"`.

Método `problemas() -> list[str]` retorna, nesta ordem, as mensagens abaixo para cada condição violada:

| Condição violada | Mensagem (literal) |
|---|---|
| `caminhada_max_m` fora de 0..3000 | `"caminhada_max_m deve estar entre 0 e 3000"` |
| `baldeacoes_max` informado e fora de 0..4 | `"baldeacoes_max deve estar entre 0 e 4"` |
| `orcamento_max_centavos` informado e menor que 0 | `"orcamento_max_centavos não pode ser negativo"` |
| `velocidade_caminhada_ms` fora de 0.5..2.0 | `"velocidade_caminhada_ms deve estar entre 0.5 e 2.0"` |

`Restricoes` (bloqueios **confirmados**; dado desconhecido NÃO entra aqui): `paradas_bloqueadas: frozenset[str]`, `linhas_bloqueadas: frozenset[str]`, `trocas_bloqueadas: frozenset[tuple[str, str]]`. Todos com padrão vazio.

### 4.4 Saída

`Trecho`: `tipo: str` (`"caminhada"`, `"espera"` ou `"transporte"`), `inicio_s: int`, `fim_s: int`, `de: str`, `para: str`, `distancia_m: float` (padrão 0.0), `modal`, `operador`, `linha_id`, `nome_linha`, `viagem_id`, `parada_de`, `parada_para` (todos `str | None`, padrão `None`), `geometria: list[tuple[float, float]]`. Propriedade `duracao_s = fim_s - inicio_s`.

`Custo`: `centavos: int | None` (padrão `None`), `confirmado: bool` (padrão `False`), `detalhe: list[str]`, `regra_versao: str | None`.

`Rota`: `trechos: list[Trecho]`, `saida_s: int`, `chegada_s: int`, `custo: Custo`, `exposicao: float | None = None`, `status_seguranca: str = "indisponivel"`, `acessibilidade: str = "NAO_SOLICITADA"`, `ordem: int = 0`, `motivos: list[str]`, `fontes: list[dict]`. Propriedades derivadas (únicas fontes de verdade; não armazenar):

| Propriedade | Definição |
|---|---|
| `transportes` | trechos com `tipo == "transporte"` |
| `tempo_total_s` | `chegada_s - saida_s` |
| `espera_s` | soma de `duracao_s` dos trechos `"espera"` |
| `caminhada_s` | soma de `duracao_s` dos trechos `"caminhada"` |
| `caminhada_m` | `round(soma de distancia_m dos trechos "caminhada")` |
| `baldeacoes` | `max(len(transportes) - 1, 0)` |
| `linhas` | tupla dos `linha_id` dos transportes, em ordem |
| `assinatura` | tupla de `(linha_id, parada_de, parada_para)` dos transportes; se não há transportes, `("a_pe",)` |

Método `componentes_somam() -> bool`: `caminhada_s + espera_s + soma(duracao_s dos transportes) == tempo_total_s`. DEVE ser `True` para toda rota produzida.

`RespostaRotas`: `rotas: list[Rota]`, `aviso: str | None`, `erro: dict | None`, `criterios_usados: list[str]`, `descartes: dict[str, int]`.

### 4.5 Formatação

`fmt_hora(seg)`: `dias, resto = divmod(int(seg), 86400)`; texto `"HH:MM"` de `resto` (horas e minutos com 2 dígitos); se `dias != 0`, acrescenta `" (+Nd)"` formatado com sinal explícito (`"(+1d)"`, `"(-1d)"`). Exemplos: `fmt_hora(30250) == "08:24"`, `fmt_hora(87250) == "00:14 (+1d)"`.

### 4.6 Serialização (`para_dict`)

`Rota.para_dict()` retorna exatamente estas chaves:

```
ordem, saida, chegada, tempo_total_s, tempo_total_min, espera_min, caminhada_m, baldeacoes,
custo{centavos, confirmado, detalhe, regra_versao}, seguranca{status, exposicao},
acessibilidade, motivos, fontes,
trechos[{tipo, inicio, fim, duracao_s, de, para, distancia_m, modal, linha, linha_id, geometria}]
```

- `saida` e `chegada` usam `fmt_hora`; `tempo_total_min = round(tempo_total_s / 60)`; `espera_min = round(espera_s / 60)`.
- Em `trechos`: `inicio` e `fim` usam `fmt_hora`; `distancia_m` é `round(distancia_m)`; `linha` é `nome_linha`; `geometria` é lista de `[lat, lon]`.

`RespostaRotas.para_dict()` retorna: `rotas` (lista de `Rota.para_dict()`), `n_rotas`, `aviso`, `erro`, `criterios_usados`, `descartes`. O resultado DEVE ser serializável com `json.dumps` sem conversões adicionais.

---

## 5. Convenções numéricas (valem para todo o código)

| ID | Regra |
|---|---|
| N-01 | Distância entre dois pontos = fórmula de Haversine com `RAIO_TERRA_M`. |
| N-02 | Tempo a pé: `seg(d, v) = 0` se `d < 1.0`; senão `round(d / v)` (função `round` do Python), inteiro. Esta mesma função DEVE ser usada na busca e na montagem dos trechos. |
| N-03 | Um trecho de caminhada com `distancia_m < 1.0` NÃO é criado (o tempo dele é 0). |
| N-04 | Dinheiro é **inteiro em centavos**. Proibido `float` para dinheiro. |
| N-05 | Percentual de perfil tarifário: `(valor * pct + 50) // 100` (inteiros; arredonda metade para cima). |
| N-06 | Valor desconhecido NUNCA é substituído por zero. Tarifa incerta = `None`; exposição desconhecida = `None`. |
| N-07 | Horário de partida é horário local sem fuso (`datetime` ingênuo). |

---

## 6. Busca de trajetos (`src/rotas.py`)

### 6.1 Índice de horários

`IndiceHorarios(rede, dia)`:
1. Para cada `k` em `(-1, 0, 1)`: `dia_servico = dia + k dias`; `deslocamento = k * 86400`.
2. Para cada viagem com `opera_em(dia_servico)`, para cada posição `i` de `0` a `len(paradas) - 2` (a última parada NÃO gera saída), registrar a ocorrência `(horarios[i] + deslocamento, viagem.id, deslocamento, viagem, i)` na chave `(paradas[i], viagem.padrao)`.
3. Ordenar cada lista por `(horario, viagem.id, deslocamento)`.
4. `padroes_na_parada(parada_id)` devolve os padrões que têm saída na parada.
5. `primeira_saida(parada_id, padrao, t_min)`: primeira ocorrência com horário `>= t_min` (busca binária). Retorna `None` se não existir **ou** se `horario - t_min > ESPERA_MAX_S`. Retorna `(horario, viagem, i, deslocamento)`.

### 6.2 Navegador

`Navegador(rede)`: monta grade espacial com células de `TAMANHO_CELULA_M`; guarda cache de índices por `dia` e de vizinhas por `(parada_id, raio)`.
- `proximas(lat, lon, raio_m)`: lista `(parada_id, distancia_m)` com distância `<= raio_m`, ordenada por `(distancia, parada_id)`.
- `vizinhas(parada_id, raio_m)`: igual a `proximas` a partir da parada, excluindo a própria parada.
- `indice(dia)`: devolve (e guarda) `IndiceHorarios(rede, dia)`.
- O `Navegador` DEVE ser criado uma vez e reutilizado entre consultas.

### 6.3 Busca por rodadas (função interna `_busca`)

Entradas: navegador, índice, origem, destino, `t0` (segundos da partida), perfil, restrições, `max_rodadas`.
`max_rodadas = perfil.baldeacoes_max + 1` se informado; senão `MAX_RODADAS_PADRAO`.

1. `origem_prox` = paradas a até `perfil.caminhada_max_m` da origem, exceto as de `paradas_bloqueadas`. `destino_prox` (dicionário parada→distância) = o mesmo para o destino. Se qualquer um estiver vazio, retorna lista vazia.
2. **Rodada 0:** para cada `(p, d)` de `origem_prox`: `chegada[0][p] = t0 + seg(d)`, predecessor `("origem", d)`. `melhor[p]` recebe esse horário. `marcadas` = paradas da rodada 0.
3. **Para k de 1 até max_rodadas:**
   1. `folga = FOLGA_BALDEACAO_S` se `k >= 2`; senão `0`.
   2. **Passo de veículo.** Para cada `p` em `marcadas` (ordem crescente de `id`): `t = chegada[k-1][p]`. Para cada `padrao` de `padroes_na_parada(p)` (ordem crescente de `(linha_id, paradas)`), ignorando padrões cuja `linha_id` esteja em `linhas_bloqueadas`: `saida = primeira_saida(p, padrao, t + folga)`; se `None`, próximo. Para cada posição `j` posterior a `i` na viagem: `p2 = viagem.paradas[j]`; ignorar se `p2` está em `paradas_bloqueadas`; `arr = viagem.horarios[j] + deslocamento`; se `arr < melhor.get(p2, infinito)` **e** `arr < atual.get(p2, infinito)`, então `atual[p2] = (arr, ("veiculo", viagem, i, j, deslocamento, p))`.
   3. **Passo a pé (uma perna por rodada).** `novos = cópia de atual`. Para cada `p2` em `atual` (ordem crescente de `id`), para cada `(p3, d)` em `vizinhas(p2, min(caminhada_max_m, CAMINHADA_BALDEACAO_MAX_M))`: ignorar se `p3` está bloqueada ou `(p2, p3)` está em `trocas_bloqueadas`; `t3 = arr + seg(d)`; se `t3 < melhor.get(p3, infinito)` e `t3 < novos.get(p3, infinito)`, então `novos[p3] = (t3, ("caminhada", p2, d, predecessor_de_veiculo_de_p2))`.
   4. Se `novos` está vazio, encerrar o laço. Senão: atualizar `melhor` com `novos`; guardar `chegada[k] = novos`; `marcadas = chaves de novos`.
   5. **Candidata da rodada.** Para cada `p` de `novos` que está em `destino_prox`: `ch = t + seg(destino_prox[p])`. Escolher o menor par `(ch, p)`. Se `ch` é **estritamente menor** que o melhor `ch` já aceito em rodadas anteriores, montar a rota (6.4) e acrescentá-la aos achados.
4. Retornar os achados.

### 6.4 Montagem da rota

Percorrer os predecessores de trás para frente a partir da parada escolhida: se o predecessor é `"caminhada"`, registrar a perna a pé e continuar com o predecessor de veículo embutido nele; para `"veiculo"`, registrar o trecho e voltar para a parada de embarque na rodada anterior; terminar em `"origem"`. Em seguida, no sentido direto, com `agora = t0`:
- **origem:** trecho `caminhada` (`de="Origem"`, `para=nome da parada`) se N-03 permitir; `agora += seg(d)`.
- **caminhada:** trecho `caminhada` entre os nomes das duas paradas; `agora += seg(d)`.
- **veículo:** `dep = horarios[i] + deslocamento`, `arr = horarios[j] + deslocamento`. Se `dep > agora`, criar trecho `espera` de `agora` a `dep` (`de` = `para` = nome da parada de embarque). Criar trecho `transporte` de `dep` a `arr` com `modal`, `operador`, `linha_id`, `nome_linha`, `viagem_id`, `parada_de`, `parada_para` e `geometria` = coordenadas de todas as paradas de `i` a `j`. `agora = arr`.
- **final:** trecho `caminhada` (`para="Destino"`) da última parada até o destino, se N-03 permitir; `agora += seg(distância final)`.
Resultado: `Rota(trechos, saida_s=t0, chegada_s=agora)`.

### 6.5 Função pública `buscar_rotas(nav, origem, destino, partida, perfil, restricoes=None, max_execucoes=MAX_EXECUCOES)`

1. `t0 = hora*3600 + minuto*60 + segundo` de `partida`; índice do dia `partida.date()`.
2. Fila de restrições começa com `[restricoes]`; conjunto `vistos` começa com `{restricoes.linhas_bloqueadas}`; contador de execuções em 0.
3. Enquanto a fila não está vazia e execuções `< max_execucoes`: retirar a primeira restrição, executar `_busca`, incrementar execuções. Para cada rota achada: guardá-la em um dicionário por `assinatura` (**mantém a primeira** de cada assinatura); para cada `linha_id` da rota, `novo = linhas_bloqueadas_atuais ∪ {linha_id}`; se `novo` não está em `vistos`, adicioná-lo e enfileirar `Restricoes(paradas_bloqueadas, novo, trocas_bloqueadas)`.
4. **Rota só a pé:** se `Haversine(origem, destino) <= perfil.caminhada_max_m`, acrescentar uma rota com um único trecho `caminhada` (`de="Origem"`, `para="Destino"`, geometria `[origem, destino]`), `saida_s=t0`, `chegada_s=t0 + seg(distância)`, desde que sua assinatura ainda não exista.
5. Retornar a lista de rotas (sem ordenação).

Premissas (registrar em `docs/parte2_rotas_tarifas.md`): viagens do mesmo padrão não se ultrapassam; caminhada em linha reta; permanência do veículo na parada ignorada.

---

## 7. Tarifas (`src/tarifas.py`)

### 7.1 Formato do arquivo de regras (JSON, lista de regras)

Campos de cada regra: `versao` (str), `fonte` (str), `confirmada` (bool), `vigencia_inicio` (`AAAA-MM-DD`), `vigencia_fim` (`AAAA-MM-DD` ou `null`), `janela_s` (int), `max_embarques_por_janela` (int), `tarifa_base` (dict modal→centavos), `integracao_adicional` (dict `"modalAnterior>modalAtual"`→centavos), `perfis_percentual` (dict perfil→inteiro, ex.: 100 = sem desconto).

### 7.2 Funções

- `carregar_regras(caminho) -> list`: lê o JSON (UTF-8).
- `regra_vigente(regras, dia)`: regras com `vigencia_inicio <= dia.isoformat() <= (vigencia_fim ou "9999-12-31")`; se houver mais de uma, a de maior `vigencia_inicio`; se nenhuma, `None`.
- `calcular_tarifa(embarques, dia, perfil_tarifario, regras) -> Custo`. `embarques` são trechos de transporte (usa `.modal`, `.inicio_s`, `.nome_linha`).

### 7.3 Algoritmo de `calcular_tarifa`

1. Sem embarques: `Custo(0, True, ["Sem embarque em transporte público."], None)`.
2. Obter a regra vigente. Retornar **custo incerto** (7.4) nos casos, nesta ordem de verificação:

| Condição | `motivo` |
|---|---|
| sem regra vigente | `"nenhuma regra vigente para a data"` |
| `confirmada` é falso ou ausente | `"regra ainda não validada"` |
| `perfil_tarifario` ausente de `perfis_percentual` | `"perfil '{perfil}' sem regra"` |

3. Ordenar embarques por `inicio_s` crescente. Variáveis: `inicio_cadeia = None`, `n_cadeia = 0`, `modal_anterior = None`, `total = 0`.
4. Para cada embarque: `base = tarifa_base.get(modal)`; se `None`, custo incerto com `motivo = "modal '{modal}' sem tarifa"`.
5. É **nova cadeia** se `inicio_cadeia is None` **ou** `inicio_s - inicio_cadeia > janela_s` **ou** `n_cadeia >= max_embarques_por_janela`. Nova cadeia: `valor = base`, rótulo `"tarifa cheia"`, `inicio_cadeia = inicio_s`, `n_cadeia = 1`. Caso contrário: `chave = f"{modal_anterior}>{modal}"`; `valor = integracao_adicional.get(chave)`; se `None`, custo incerto com `motivo = "integração '{chave}' sem regra confirmada"`; rótulo `f"integração {chave}"`; `n_cadeia += 1`.
6. `cobrado = (valor * pct + 50) // 100`; `total += cobrado`; `modal_anterior = modal`. Acrescentar a `detalhe` a linha `f"{fmt_hora(inicio_s)} {nome_linha}: R$ {cobrado / 100:.2f} ({rotulo})"`.
7. Retornar `Custo(total, True, detalhe, regra["versao"])`.

### 7.4 Custo incerto

`Custo(centavos=None, confirmado=False, detalhe=[f"Tarifa não confirmada: {motivo}"], regra_versao=<versão da regra se já obtida, senão None>)`.

A integração atravessa a meia-noite porque `inicio_s` é contínuo (pode passar de 86400): NÃO reiniciar a janela na virada do dia.

---

## 8. Ranking e orquestração (`src/ranking.py`, `src/recomendar.py`)

### 8.1 Ganchos de outros integrantes

| Gancho | Assinatura | Padrão enquanto o outro integrante não entrega |
|---|---|---|
| `verificar_acessibilidade` | `(rota, necessidades: frozenset) -> str` (um dos estados 4.1) | devolve `"NAO_VERIFICADA"` |
| `avaliar_exposicao` | `(rota) -> (float \| None, str)` | devolve `(None, "indisponivel")` |
| `restricoes` | objeto `Restricoes` | `Restricoes()` vazio |

Regras de segurança do código (DEVEM ser testadas):
- Estado de acessibilidade fora do conjunto `{"NAO_SOLICITADA", "COMPATIVEL_COM_DADOS_DISPONIVEIS", "NAO_VERIFICADA", "INCOMPATIVEL"}` é tratado como `"NAO_VERIFICADA"`.
- Se o perfil não tem necessidades de acessibilidade, o estado da rota é `"NAO_SOLICITADA"` e o gancho NÃO é chamado.
- Exposição que não seja número entre 0 e 1 (inclusive) é tratada como `None`.

### 8.2 Viabilidade (`motivo_inviabilidade(rota, perfil)`)

Verificar nesta ordem e devolver o primeiro código que se aplica; se nenhum, `None`:

| Ordem | Condição | Código |
|---|---|---|
| 1 | `rota.caminhada_m > perfil.caminhada_max_m` | `"caminhada_acima_do_limite"` |
| 2 | `baldeacoes_max` informado e `rota.baldeacoes > baldeacoes_max` | `"baldeacoes_acima_do_limite"` |
| 3 | `orcamento_max_centavos` informado **e** `rota.custo.centavos` não é `None` **e** `centavos > orcamento_max_centavos` | `"orcamento_excedido"` |
| 4 | `rota.acessibilidade == "INCOMPATIVEL"` | `"acessibilidade_incompativel"` |

Tarifa incerta NÃO descarta a rota pelo orçamento.

### 8.3 Critérios e pontuação

Valores por critério: `tempo` = `tempo_total_s / 60`; `custo` = `custo.centavos`; `exposicao` = `exposicao`; `baldeacoes`; `caminhada` = `caminhada_m`; `acess` = `0` se estado `"COMPATIVEL_COM_DADOS_DISPONIVEIS"`, senão `1`.

- **Critérios usáveis** (`criterios_usaveis(candidatas)`): sempre `"tempo"`; `"custo"` só se **todas** as candidatas têm `custo` diferente de `None`; `"exposicao"` só se **todas** têm `exposicao` diferente de `None`. Ordem da lista: `tempo`, `custo`, `exposicao`.
- **Pontuação** (`escore(rota, usar)`, menor é melhor): `soma(PESOS[c] * valor(c) / REF[c] para c em usar) / soma(PESOS[c] para c em usar)`.
- **Dominância:** dimensões = `usar` + `["baldeacoes", "caminhada"]` + (`["acess"]` se o perfil tem necessidades de acessibilidade). A rota A domina B se A é `<=` a B em todas as dimensões **e** `<` em pelo menos uma. Rotas dominadas são removidas. Rotas idênticas em todas as dimensões NÃO se dominam.
- **Similaridade** (`similares(a, b)`): se ambas não têm linhas, `True`; senão `|A ∩ B| / |A ∪ B| >= LIMIAR_SIMILARIDADE`, com A e B os **conjuntos** de `linhas`.

### 8.4 Seleção (`selecionar(candidatas, perfil)`)

1. Se não há candidatas: `([], [])`.
2. `usar = criterios_usaveis(candidatas)`; remover as dominadas.
3. Ordenar por esta chave, nesta ordem: (a) `acess` se o perfil exige acessibilidade, senão `0`; (b) `escore`; (c) `tempo_total_s`; (d) `baldeacoes`; (e) `str(assinatura)`.
4. Percorrer a lista ordenada e aceitar cada rota que não seja similar a nenhuma já aceita; parar ao chegar a `MAX_ROTAS`.
5. Retornar `(rotas aceitas, usar)`. NUNCA preencher até 3 artificialmente.

### 8.5 Textos literais

**Aviso** (`montar_aviso(escolhidas, usar)`): concatenar com um espaço, nesta ordem, as frases aplicáveis; se nenhuma, `None`.

| Condição | Frase |
|---|---|
| `"exposicao"` não está em `usar` | `"O equilíbrio entre os três critérios não pôde ser confirmado: dados de segurança insuficientes."` |
| `"custo"` não está em `usar` | `"Há alternativa com tarifa não confirmada; o custo ficou fora da ordenação."` |
| `0 < len(escolhidas) < 3` | `"Apenas {n} alternativa(s) viável(is) e distinta(s) encontrada(s)."` |

**Motivos** (`gerar_motivos(rota, escolhidas, usar, perfil)`): lista construída nesta ordem, incluindo cada item cuja condição for verdadeira:

| # | Condição | Texto |
|---|---|---|
| 1 | `len(escolhidas) == 1` | `"Única alternativa viável e distinta encontrada."` |
| 2 | `len(escolhidas) > 1` e `rota.tempo_total_s` é o menor | `"Menor tempo total entre as opções."` |
| 3 | `len(escolhidas) > 1`, não é o menor e a diferença para o menor é `<= 300` s | `"Só {round(dif/60)} min mais lenta que a mais rápida."` |
| 4 | `len(escolhidas) > 1`, `"custo"` em `usar` e o custo da rota é o menor | `"Menor custo entre as opções."` |
| 5 | `len(escolhidas) > 1`, a caminhada é a menor e existe rota com caminhada diferente | `"Menor caminhada entre as opções."` |
| 6 | a rota não tem transportes | `"Percurso inteiro a pé."` |
| 7 | tem transportes e `baldeacoes == 0` | `"Sem baldeações."` |
| 8 | `custo.centavos is None` | `"Tarifa não confirmada para esta combinação."` |
| 9 | `"exposicao"` não está em `usar` | `"Dados de segurança insuficientes para comparar este trajeto."` |
| 10 | perfil exige acessibilidade e estado `"COMPATIVEL_COM_DADOS_DISPONIVEIS"` | `"Compatível com a necessidade informada, segundo os dados disponíveis (não é garantia)."` |
| 11 | perfil exige acessibilidade e estado `"NAO_VERIFICADA"` | `"Acessibilidade NÃO verificada para este percurso."` |
| 12 | perfil exige acessibilidade e outro estado | `"Acessibilidade sem informação."` |
| 13 | sempre | `"Horários planejados (sem previsão em tempo real)."` |

**Proibido** em qualquer texto gerado: as palavras "segura", "seguro", "garantida", "garantido", "pontual" e a expressão "sem risco". A verificação é por **palavra inteira**, sem diferenciar maiúsculas de minúsculas (portanto "segurança", "pontualidade" e "insuficientes" NÃO violam a regra; use expressão regular com limites de palavra, por exemplo `\bsegura\b`).

### 8.6 Função `recomendar(rede, regras_tarifa, origem, destino, partida, perfil=None, restricoes=None, verificar_acessibilidade=None, avaliar_exposicao=None, nav=None) -> RespostaRotas`

Ordem exata:
1. Aplicar padrões (`Perfil()`, `Restricoes()`, ganchos padrão, `Navegador(rede)`).
2. **Validar** (a primeira falha encerra e devolve `RespostaRotas(erro={"codigo":..., "mensagem":...})`):

| Verificação | `codigo` | `mensagem` |
|---|---|---|
| origem não é tupla de 2 números, lat fora de -90..90 ou lon fora de -180..180 | `"origem_invalida"` | `"Origem inválida."` |
| idem para destino | `"destino_invalida"` | `"Destino inválido."` |
| `partida` não é `datetime` | `"partida_invalida"` | `"Horário de partida inválido."` |
| `perfil.problemas()` não vazio | `"preferencias_invalidas"` | mensagens de `problemas()` unidas por `"; "` |
| origem fora da área piloto | `"origem_fora_da_area_piloto"` | `"Origem fora da área piloto."` |
| destino fora da área piloto | `"destino_fora_da_area_piloto"` | `"Destino fora da área piloto."` |

   **Área piloto** = retângulo `rede.limites()` expandido em `perfil.caminhada_max_m` metros em cada lado (conversão: 1 grau de latitude = `RAIO_TERRA_M * pi / 180` metros; 1 grau de longitude = isso vezes `cos(latitude média)`).
3. `candidatas = buscar_rotas(...)`. Se vazia: erro `codigo="sem_trajeto"`, `mensagem="Nenhum trajeto encontrado para esse horário e essas condições (sem serviço, bloqueios confirmados ou paradas fora do limite de caminhada)."`.
4. Para cada candidata: calcular `custo` (seção 7); definir `acessibilidade` e `exposicao`/`status_seguranca` conforme 8.1.
5. Separar viáveis e inviáveis (8.2). Contar `descartes[codigo] += 1`. Se não há viáveis: erro `codigo="nenhuma_rota_atende"`, `mensagem="Há trajetos, mas nenhum atende às restrições informadas. Não trocamos sua necessidade por ganho de tempo ou custo."`, com `descartes` preenchido.
6. `selecionar`; para cada rota escolhida, `ordem = 1, 2, 3` na ordem de saída; `motivos = gerar_motivos(...)`; `fontes = [{"fonte": rede.versao, "rotulo": "planejado", "origem_dados": rede.origem_dados, "tarifa_regra": rota.custo.regra_versao}]`.
7. Devolver `RespostaRotas(rotas, aviso=montar_aviso(...), criterios_usados=usar, descartes=descartes)`.

### 8.7 Função `processar_pedido(pedido, rede, regras_tarifa, restricoes=None, verificar_acessibilidade=None, avaliar_exposicao=None, nav=None) -> dict`

Entrada (dicionário):

```
{"origem": {"lat": float, "lon": float}, "destino": {"lat": float, "lon": float},
 "partida": "AAAA-MM-DDTHH:MM:SS",
 "necessidades": {"caminhada_max_m": int, "baldeacoes_max": int, "orcamento_max_centavos": int,
                  "acessibilidade": [str], "perfil_tarifario": str}}
```

`necessidades` e todos os seus campos são opcionais (aplicam-se os padrões de `Perfil`). Regras:
- `origem`/`destino` sem `lat`/`lon` numéricos: erro `"origem_invalida"` / `"destino_invalida"`.
- `partida` ausente ou fora do formato ISO: erro `"partida_invalida"`, mensagem `"Informe 'partida' em formato ISO (ex.: 2026-11-09T08:00:00)."`.
- `partida` com fuso: converter para `America/Sao_Paulo` e remover o fuso.
- NUNCA levantar exceção por erro de entrada: devolver o dicionário `RespostaRotas.para_dict()` com `rotas=[]`, `n_rotas=0` e `erro` preenchido.

---

## 9. Pesquisa por endereço (`src/geocodificacao.py`)

Finalidade: converter texto digitado em candidatos `(nome, lat, lon)` dentro da área piloto. O clique no mapa NÃO usa este módulo (o front envia lat/lon direto ao `processar_pedido`).

| ID | Requisito |
|---|---|
| G-01 | Serviço: Nominatim público do OpenStreetMap, endpoint `https://nominatim.openstreetmap.org/search`. |
| G-02 | Parâmetros da consulta: `q` = texto, `format` = `jsonv2`, `limit` = `GEOCODIFICACAO_MAX_RESULTADOS`, `countrycodes` = `br`. |
| G-03 | Cabeçalho `User-Agent` DEVE vir da variável de ambiente `ROTAVIVA_USER_AGENT`. Se ausente ou vazia: NÃO fazer a chamada e devolver erro `"user_agent_ausente"`. NÃO existe valor padrão. |
| G-04 | Intervalo mínimo entre chamadas de rede: `GEOCODIFICACAO_INTERVALO_MIN_S`, **global no processo** (usar `threading.Lock` e `time.monotonic`). A espera acontece antes da chamada. |
| G-05 | Cache em SQLite (tabela da seção 10.3) consultado **antes** de qualquer chamada. Chave = texto normalizado (`strip`, minúsculas, espaços internos colapsados em um). Validade = `TTL_CACHE_GEOCODIFICACAO_DIAS`. |
| G-06 | A função só é chamada por ação explícita do usuário (botão ou Enter). NÃO implementar autocompletar nem consultas em lote. |
| G-07 | Tamanho do texto normalizado entre 3 e 200 caracteres; senão erro `"consulta_invalida"`. |
| G-08 | Resultados fora da área piloto (retângulo `rede.limites()`, sem expansão) são descartados localmente. Se nenhum resta: erro `"sem_resultado_na_area_piloto"`. |
| G-09 | Timeout `GEOCODIFICACAO_TIMEOUT_S`. Falha de rede, timeout ou HTTP diferente de 200: erro `"geocodificacao_indisponivel"`. A falha NÃO é gravada no cache. |
| G-10 | Cliente HTTP DEVE ser injetável (parâmetro) para teste. Usar `urllib.request` da biblioteca padrão por padrão. Testes NÃO DEVEM fazer chamadas de rede reais. |
| G-11 | Saída de sucesso: `{"candidatos": [{"nome": str, "lat": float, "lon": float}, ...], "atribuicao": "Dados de endereço © colaboradores do OpenStreetMap"}`. Saída de erro: `{"erro": {"codigo": str, "mensagem": str}}`. |
| G-12 | `nome` = campo `display_name` da resposta; `lat`/`lon` convertidos de texto para `float`. |

Assinatura: `buscar_endereco(texto, banco, limites, cliente_http=None, agora=None) -> dict`, com `banco` = caminho do SQLite, `limites` = `(lat_min, lon_min, lat_max, lon_max)`, `agora` = `datetime` injetável (para teste do TTL).

---

## 10. Histórico em SQLite (`src/historico.py`)

### 10.1 Regras

| ID | Requisito |
|---|---|
| H-01 | Usar apenas `sqlite3` da biblioteca padrão e consultas **parametrizadas** (proibido montar SQL por concatenação de texto). |
| H-02 | `sessao_id` é um texto gerado por quem chama (UUID4). O módulo NÃO guarda nome, e-mail, IP nem identificador de dispositivo. |
| H-03 | NÃO gravar o histórico em logs. NÃO usar `print` de coordenadas. |
| H-04 | `apagar_historico(banco, sessao_id)` remove todas as linhas daquela sessão e retorna a quantidade removida. |
| H-05 | `purgar_expirados(banco, agora)` remove linhas com `criado_em` anterior a `agora - RETENCAO_HISTORICO_DIAS` dias. |
| H-06 | `PRAGMA foreign_keys` não é necessário (sem chaves estrangeiras). |

### 10.2 Tabela `historico_buscas`

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `sessao_id` | TEXT NOT NULL | índice em `sessao_id` |
| `criado_em` | TEXT NOT NULL | ISO 8601, horário local sem fuso |
| `origem_lat`, `origem_lon`, `destino_lat`, `destino_lon` | REAL NOT NULL | exatamente como recebidos no pedido |
| `partida` | TEXT NOT NULL | ISO 8601 |
| `n_rotas` | INTEGER NOT NULL | |
| `erro_codigo` | TEXT | `NULL` se houve rotas |

### 10.3 Tabela `cache_geocodificacao`

| Coluna | Tipo |
|---|---|
| `consulta` | TEXT PRIMARY KEY (texto normalizado) |
| `resposta_json` | TEXT NOT NULL |
| `obtido_em` | TEXT NOT NULL (ISO 8601) |

### 10.4 Funções

`iniciar_banco(caminho)` (cria as tabelas e o índice se não existirem; idempotente), `registrar_busca(banco, sessao_id, pedido, resposta, agora=None) -> int` (devolve `id`), `listar_historico(banco, sessao_id, limite=20) -> list[dict]` (mais recente primeiro; chaves iguais às colunas), `apagar_historico(banco, sessao_id) -> int`, `purgar_expirados(banco, agora=None) -> int`.

`registrar_busca` extrai de `pedido` os campos de origem, destino e partida e de `resposta` (dicionário de `processar_pedido`) `n_rotas` e `erro.codigo`. NÃO grava os trajetos retornados.

---

## 11. Dados fictícios obrigatórios

### 11.1 Rede demo (`src/rede_demo.py`, função `criar_rede_demo() -> Rede`)

`Rede.versao = "demo-1"`, `origem_dados = "simulado"`. Função `ponto(x_m, y_m)` com `LAT0 = -23.5500`, `LON0 = -46.6300`, `M_POR_GRAU = 6371000.0 * pi / 180`:
`lat = LAT0 + y_m / M_POR_GRAU`; `lon = LON0 + x_m / (M_POR_GRAU * cos(radians(LAT0)))`.

**Paradas** (x, y em metros):

| id | nome | x | y |
|---|---|---|---|
| MA | Metrô Alfa | 0 | 0 |
| MB | Metrô Beta | 2000 | 0 |
| MC | Metrô Gama | 4000 | 0 |
| BA | Ponto Alfa | 0 | 100 |
| BB | Ponto Beta | 2000 | 100 |
| BC | Ponto Gama | 4000 | 100 |
| BX | Ponto Centro | 2000 | 700 |
| PD | Ponto Destino | 4000 | 300 |
| PF | Ponto Fim | 2000 | 2000 |

**Linhas.** Gerar uma viagem para cada `t` = `primeira`, `primeira + intervalo`, … enquanto `t <= ultima`. `horarios[i] = t + deslocamentos[i]`. Id da viagem = `f"{linha_id}-{n:03d}"` com `n` começando em 0. `sentido="ida"`.

| linha_id | nome_linha | operador | modal | paradas | deslocamentos (s) | primeira | ultima | intervalo | dias | exceções |
|---|---|---|---|---|---|---|---|---|---|---|
| `M1` | Metrô Linha 1 | Metrô Demo | metro | MA, MB, MC | 0, 300, 600 | 21600 | 88200 | 600 | todos | nenhuma |
| `L100` | Ônibus 100 | Ônibus Demo | onibus | BA, BX, BC | 0, 900, 1500 | 21900 | 86000 | 900 | 0–4 | `2026-11-20` |
| `L200` | Ônibus 200 | Ônibus Demo | onibus | BA, BX, PD | 0, 1000, 1800 | 22000 | 86000 | 1200 | todos | nenhuma |
| `L300` | Ônibus 300 | Ônibus Demo | onibus | BB, PF | 0, 900 | 21660 | 86000 | 600 | todos | nenhuma |

### 11.2 Regras tarifárias demo (`data/tarifas_demo.json`)

Lista com uma única regra:

```
versao: "demo-2026-01"
fonte: "DADOS DE TESTE FICTICIOS - nao usar como tarifa real"
confirmada: true
vigencia_inicio: "2026-01-01"    vigencia_fim: null
janela_s: 10800                  max_embarques_por_janela: 4
tarifa_base: {onibus: 500, metro: 520, trem: 520}
integracao_adicional: {"onibus>onibus": 0, "metro>onibus": 0, "onibus>metro": 320}
perfis_percentual: {padrao: 100, estudante: 50}
```

Esses valores são **fictícios**. O agente NÃO DEVE substituí-los por valores reais.

---

## 12. Testes obrigatórios (`tests/`)

Executados com `python -m pytest`. Pontos fixos: `O = ponto(0, -100)`; `D1 = ponto(4000, 300)`; `D3 = ponto(2000, 2100)`; partida padrão = `2026-11-09 08:00:00` (segunda-feira). Perfil padrão = `Perfil()`. Velocidade a pé = 1,2 m/s.

### 12.1 Rotas (`tests/test_rotas.py`)

| ID | Cenário | Resultado esperado |
|---|---|---|
| T-R01 | `O → D1`, partida padrão | Exatamente 3 rotas, com conjuntos de linhas `{("M1",), ("L100",), ("L200",)}`. |
| T-R02 | Rota `M1` de T-R01 | `tempo_total_s = 1450`, `espera_s = 517`, `caminhada_m = 400`, `baldeacoes = 0`, `fmt_hora(chegada_s) = "08:24"`. |
| T-R03 | Rota `L100` de T-R01 | `tempo_total_s = 1967`, `espera_s = 133`, `caminhada_m = 400`. |
| T-R04 | Rota `L200` de T-R01 | `tempo_total_s = 2200`, `espera_s = 233`, `caminhada_m = 200`. |
| T-R05 | Toda rota de T-R01 | `componentes_somam()` é `True`. |
| T-R06 | `O → D3`, partida padrão | Exatamente 1 rota, linhas `("M1", "L300")`, `tempo_total_s = 2243`, `espera_s = 794`, `caminhada_m = 300`, `baldeacoes = 1`. |
| T-R07 | `O → D3` com `baldeacoes_max = 0` | Lista vazia. |
| T-R08 | `O → D1` com `caminhada_max_m = 150` | Lista vazia. |
| T-R09 | `O → D1` com `caminhada_max_m = 250` | Lista não vazia; nenhum trecho `caminhada` com `distancia_m > 250`. |
| T-R10 | `O → D1` com `linhas_bloqueadas = {"M1"}` | Conjuntos de linhas `{("L100",), ("L200",)}`. |
| T-R11 | `O → D1` com `paradas_bloqueadas = {"MA"}` | Nenhuma rota usa `M1`. |
| T-R12 | `O → D1` com `paradas_bloqueadas = {"MA", "BA"}` | Lista vazia. |
| T-R13 | `O → D1`, sábado `2026-11-07 08:00` | `L100` ausente; `M1` presente. |
| T-R14 | `O → D1`, sexta `2026-11-20 08:00` (exceção) | `L100` ausente. |
| T-R15 | `O → D1`, `2026-11-09 23:50` | Somente `M1`; `fmt_hora(chegada_s) = "00:14 (+1d)"`. |
| T-R16 | `O → D1`, `2026-11-10 00:20` | Somente `M1`; `tempo_total_s = 1450` (usa viagem das 24:30 do dia anterior). |
| T-R17 | `O → D1`, `2026-11-10 00:40` | Lista vazia. |
| T-R18 | Origem `O`, destino `ponto(0, 600)` | Existe exatamente 1 rota sem transportes, com `caminhada_m = 700` e `tempo_total_s = 583`. |
| T-R19 | Rede mini (abaixo) | Ver abaixo. |

**T-R19, rede mini** (paradas `S1 = ponto(0,0)`, `S2 = ponto(1000,0)`, `S3 = ponto(2000,0)`; viagens de ônibus, todos os dias): `A-0` linha `A` paradas `S1,S2` horários `28900, 29500`; `B-0` linha `B` paradas `S2,S3` horários `29530, 30130`; `B-1` linha `B` paradas `S2,S3` horários `30130, 30730`. Consulta: origem = coordenada de `S1`, destino = coordenada de `S3`, partida `2026-11-09 08:00`, `Perfil(caminhada_max_m=100)`. Esperado: 1 rota com linhas `("A", "B")`, `tempo_total_s = 1930`, `componentes_somam()` verdadeiro, e a viagem do 2º transporte é `"B-1"` (a conexão de 30 s é perdida por ser menor que a folga de 60 s).

### 12.2 Tarifas (`tests/test_tarifas.py`)

Data `2026-11-09`, regra demo, perfil `"padrao"` salvo indicação. Cada embarque informado como `(modal, inicio_s)`.

| ID | Embarques | Esperado |
|---|---|---|
| T-T01 | `(onibus, 28800)` | `centavos = 500` |
| T-T02 | `(metro, 28800)` | `520` |
| T-T03 | nenhum | `centavos = 0`, `confirmado = True` |
| T-T04 | `(onibus, 28800), (onibus, 30000)` | `500` |
| T-T05 | `(onibus, 28800), (metro, 30000)` | `820` |
| T-T06 | `(metro, 28800), (onibus, 30000)` | `520` |
| T-T07 | `(onibus, 0), (onibus, 10801)` | `1000` |
| T-T08 | `(onibus, 0), (onibus, 10800)` | `500` |
| T-T09 | `(onibus, 84600), (onibus, 88200)` | `500` (atravessa a meia-noite) |
| T-T10 | 5 embarques de ônibus em `28800 + i*600`, `i = 0..4` | `1000` |
| T-T11 | `(metro, 28800), (metro, 30000)` | `centavos = None`, `confirmado = False`, detalhe contém `"metro>metro"` |
| T-T12 | `(balsa, 28800)` | `None` |
| T-T13 | `(onibus, 28800)` com `confirmada = false` | `None` |
| T-T14 | `(onibus, 28800)` na data `2025-12-31` | `None` |
| T-T15 | `(onibus, 28800)` perfil `"estudante"` | `250` |
| T-T16 | `(onibus, 28800), (metro, 30000)` perfil `"estudante"` | `410` |
| T-T17 | `(onibus, 28800)` perfil `"idoso"` | `None` |
| T-T18 | `(metro, 30000), (onibus, 28800)` (fora de ordem) | `820` |

### 12.3 Ranking (`tests/test_ranking.py`, seção "ranking")

Rotas sintéticas: tempo, custo, linhas, caminhada informados diretamente.

| ID | Cenário | Esperado |
|---|---|---|
| T-K01 | Candidatas com custos `500` e `None` | `criterios_usaveis == ["tempo"]` |
| T-K02 | Todas com `exposicao`; e depois só uma com | `["tempo","custo","exposicao"]`; e `["tempo","custo"]` |
| T-K03 | Rota 30 min, custo 600 | `escore(rota, ["tempo","custo"])` = `0.388889` (tolerância 1e-5) |
| T-K04 | Uma rota pior em tudo que outra | A pior é removida; a que é melhor só em custo permanece |
| T-K05 | 4 candidatas não dominadas | Retorna exatamente 3, ordenadas por `escore` crescente |
| T-K06 | 2 candidatas distintas | Retorna 2; `montar_aviso` contém `"Apenas 2"` |
| T-K07 | Duas rotas com a mesma linha | Retorna 1 |
| T-K08 | Sem exposição | `montar_aviso` contém `"dados de segurança insuficientes"` |
| T-K09 | `Perfil(caminhada_max_m=300, baldeacoes_max=0, orcamento_max_centavos=550)` | Cada código de 8.2 é devolvido na condição correspondente |
| T-K10 | Tarifa `None` com orçamento 100 | Rota viável |
| T-K11 | Rota rápida `NAO_VERIFICADA` e rota lenta `COMPATIVEL`, perfil exige acessibilidade | A `COMPATIVEL` vem primeiro; ambas retornam |

### 12.4 Integração (`tests/test_integracao.py`, via `processar_pedido`)

| ID | Cenário | Esperado |
|---|---|---|
| T-I01 | `O → D1` | `erro` nulo; `n_rotas = 3`; `ordem` = 1,2,3; rota 1 com `custo.centavos = 520` e `tempo_total_min = 24`; `fontes[0].rotulo = "planejado"` e `origem_dados = "simulado"` |
| T-I02 | `O → D1` | `aviso` contém `"segurança insuficientes"`; `seguranca = {"status": "indisponivel", "exposicao": None}`; `criterios_usados = ["tempo","custo"]` |
| T-I03 | `avaliar_exposicao` devolvendo `(0.2, "dados_suficientes")` | `criterios_usados = ["tempo","custo","exposicao"]`; `aviso` nulo |
| T-I04 | `avaliar_exposicao` devolvendo `(7.5, ...)` | `"exposicao"` ausente de `criterios_usados` |
| T-I05 | `orcamento_max_centavos = 510` | Custos das rotas = `[500, 500]`; `descartes = {"orcamento_excedido": 1}` |
| T-I06 | Origem `lat=-22.9, lon=-43.2` | `rotas = []`; `erro.codigo = "origem_fora_da_area_piloto"` |
| T-I07 | Pedido `{}`; partida `"ontem de manhã"`; `caminhada_max_m = 99999` | Códigos `"origem_invalida"`; `"partida_invalida"`; `"preferencias_invalidas"` |
| T-I08 | Partida `2026-11-10T00:40:00` | `rotas = []`; `erro.codigo = "sem_trajeto"` |
| T-I09 | Necessidade `["sem_degraus"]`, ganchos padrão | `n_rotas = 3`; todas `"NAO_VERIFICADA"`; algum motivo contém `"NÃO verificada"` |
| T-I10 | Gancho devolve `"INCOMPATIVEL"` se `"M1"` está nas linhas, senão `"COMPATIVEL_COM_DADOS_DISPONIVEIS"` | 2 rotas, ambas compatíveis; `descartes = {"acessibilidade_incompativel": 1}` |
| T-I11 | Gancho devolve `"TALVEZ"` | Todas `"NAO_VERIFICADA"` |
| T-I12 | Gancho devolve sempre `"INCOMPATIVEL"` | `rotas = []`; `erro.codigo = "nenhuma_rota_atende"` |
| T-I13 | `O → D3` | `n_rotas = 1`; `baldeacoes = 1`; `custo.centavos = 520` |
| T-I14 | `O → D3` sem a chave `"metro>onibus"` na regra | `custo.centavos = None`; `custo.confirmado = False`; motivos contêm `"Tarifa não confirmada"`; `aviso` contém `"tarifa não confirmada"` (comparação sem diferenciar maiúsculas) |
| T-I15 | Qualquer resposta de sucesso | `json.dumps(resposta)` funciona |
| T-I16 | Partida com fuso `2026-11-09T11:00:00+00:00` | Tratada como `08:00` local (mesmo resultado de T-I01) |
| T-I17 | Nenhum texto de `motivos`/`aviso` das respostas acima | Não contém nenhuma palavra proibida de 8.5 |

### 12.5 Histórico e geocodificação (`tests/test_historico.py`, `tests/test_geocodificacao.py`)

| ID | Cenário | Esperado |
|---|---|---|
| T-H01 | `iniciar_banco` duas vezes | Sem erro (idempotente) |
| T-H02 | `registrar_busca` e `listar_historico` | Linha com coordenadas iguais às do pedido, `n_rotas` correto, `erro_codigo` nulo quando houve rotas |
| T-H03 | Duas sessões; `apagar_historico` de uma | Retorna a contagem da sessão; a outra permanece intacta |
| T-H04 | `purgar_expirados` com uma linha de 91 dias e outra de 89 dias | Remove só a de 91 dias |
| T-H05 | `sessao_id` contendo `'; DROP TABLE historico_buscas; --` | Tabela continua existindo; valor gravado como texto |
| T-G01 | `ROTAVIVA_USER_AGENT` ausente | `erro.codigo = "user_agent_ausente"`; cliente HTTP falso NÃO é chamado |
| T-G02 | Consulta repetida (mesmo texto, com espaços e maiúsculas diferentes) | Cliente HTTP falso chamado 1 vez; 2ª resposta vem do cache |
| T-G03 | Cache com 31 dias (TTL = 30) | Nova chamada ao cliente falso |
| T-G04 | Texto com 2 caracteres e texto com 201 | `"consulta_invalida"` |
| T-G05 | Resposta falsa só com ponto fora da área piloto | `"sem_resultado_na_area_piloto"` |
| T-G06 | Cliente falso levanta erro de rede | `"geocodificacao_indisponivel"`; nada gravado no cache |
| T-G07 | Resposta falsa com 2 pontos dentro da área | `candidatos` com 2 itens, `lat`/`lon` do tipo `float`, `atribuicao` igual ao texto de G-11 |
| T-G08 | Duas chamadas de rede consecutivas com relógio falso | Intervalo medido entre elas `>= 1.1` s (injetar `sleep` e relógio para não esperar de verdade) |

### 12.6 Regras gerais de teste

- Nenhum teste faz chamada de rede real.
- Nenhum teste depende de data atual (sempre `agora`/`partida` explícitos).
- Os valores esperados acima são **conferidos à mão** e NÃO DEVEM ser alterados para fazer um teste passar. Se um teste falhar, corrigir o código; se acreditar que o valor esperado está errado, registrar em `docs/duvidas.md` e **manter** o teste falhando.

---

## 13. Entregáveis de execução

| Item | Conteúdo exato |
|---|---|
| `requirements.txt` | `pytest` e `tzdata` (este último necessário em Windows para `zoneinfo`). Nenhuma outra dependência. |
| `pytest.ini` | `[pytest]`, `pythonpath = .`, `testpaths = tests`. |
| `exemplos/demo.py` | Executável com `python -m exemplos.demo`. Para `O → D1`, partida padrão, imprime para cada rota uma linha `f"Rota {ordem}: {tempo_total_min} min | {custo} | {caminhada_m} m a pé | {baldeacoes} baldeação(ões) | {saida} -> {chegada}"` (com `custo` = `"R$ 5.20"` no formato `R$ {centavos/100:.2f}` ou `"tarifa não confirmada"`), seguida dos trechos e dos motivos, e por fim o `aviso` se existir. Saída esperada nas três primeiras linhas de rota: `Rota 1: 24 min | R$ 5.20 | 400 m a pé | 0 baldeação(ões) | 08:00 -> 08:24`; `Rota 2: 33 min | R$ 5.00 | 400 m a pé | 0 baldeação(ões) | 08:00 -> 08:32`; `Rota 3: 37 min | R$ 5.00 | 200 m a pé | 0 baldeação(ões) | 08:00 -> 08:36`. |
| `docs/parte2_rotas_tarifas.md` | Contratos com os outros integrantes (seção 4 e 8.1), premissas de 6.5, lista dos parâmetros da seção 3, lista do que NÃO foi testado (dados reais, desempenho com rede grande). |
| `docs/duvidas.md` | Dúvidas registradas conforme a seção 0, item 4. Se não houver, o arquivo contém a linha `Nenhuma dúvida registrada.` |

---

## 14. Registro de uso de IA (`docs/uso_ia.md`)

Criar uma tabela com estas colunas e preencher **uma linha por etapa** da seção 15: `Ferramenta/modelo` | `Data` | `Responsável` | `Finalidade` | `Resumo do pedido` | `Saída aproveitada` | `Alterações humanas` | `Fontes conferidas` | `Testes realizados` | `Limitações`.

- `Responsável` e `Alterações humanas` ficam com o texto `PENDENTE` (somente a equipe preenche).
- `Testes realizados` registra o comando e o resultado reais (ex.: `python -m pytest: 120 passed`), sem estimativas.
- Incluir ao final a linha: `Validação e revisão pela equipe: PENDENTE.` NÃO marcar como concluída.

---

## 15. Ordem de execução (etapas com critério de conclusão)

| Etapa | Fazer | Concluída quando |
|---|---|---|
| 1 | `config.py`, `contratos.py`, `pytest.ini`, `requirements.txt` | Importação dos módulos sem erro; `fmt_hora(30250) == "08:24"` |
| 2 | `rede_demo.py` e `tarifas_demo.json` | `rede.validar() == []` |
| 3 | `rotas.py` | T-R01 a T-R19 passam |
| 4 | `tarifas.py` | T-T01 a T-T18 passam |
| 5 | `ranking.py` e `recomendar.py` | T-K01 a T-K11 e T-I01 a T-I17 passam |
| 6 | `historico.py` | T-H01 a T-H05 passam |
| 7 | `geocodificacao.py` | T-G01 a T-G08 passam |
| 8 | `exemplos/demo.py` e documentação | A saída de 13 confere nas três linhas de rota; `docs/` completos |
| 9 | Execução final | `python -m pytest` termina com código 0 e nenhuma dependência além de `requirements.txt` |

Não iniciar uma etapa antes de concluir a anterior.

---

## 16. Critérios de aceite do módulo (todos obrigatórios)

1. `python -m pytest` termina com código 0.
2. Nenhum requisito da seção 2.2 foi implementado.
3. Nenhuma constante da seção 3 aparece escrita fora de `src/config.py`.
4. Nenhum valor de tarifa real foi usado.
5. Nenhum teste faz chamada de rede.
6. Nenhuma consulta SQL é montada por concatenação de texto.
7. `docs/uso_ia.md` marca a validação da equipe como `PENDENTE`.
8. Nenhum arquivo ou função fora do listado na seção 2.1 foi criado.

---

## 17. Responsabilidades que NÃO são deste módulo (para evitar dúvida de fronteira)

| Responsabilidade | De quem | Interface com este módulo |
|---|---|---|
| Importar GTFS e produzir `Rede` | Integrante 1 (dados) | Estruturas da seção 4.2 |
| Acessibilidade, bloqueios confirmados, índice de exposição | Integrante 3 | Ganchos da seção 8.1 |
| Mapa, clique no mapa, cartões de rota | Integrante 4 (interface) | Envia `lat`/`lon`; consome `RespostaRotas.para_dict()` |
| Servidor HTTP, `POST /rotas`, sessões | Integrante 5 | Chama `processar_pedido` e `buscar_endereco` |
