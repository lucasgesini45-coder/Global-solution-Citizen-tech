# RotaViva - MVP - Módulo 2: Rotas e Tarifas

Documentação de entrega da Parte 2 do MVP do projeto RotaViva.
Responsável: Integrante 2 (Raphael de Freitas Silva)
Data de referência: 08/11/2026

---

## 1. Contratos com os outros integrantes

### 1.1 Entradas de Dados (Integrante 1 - Dados)
Conforme definido na seção 4.2 da especificação:
- `Parada`: Objeto imutável contendo `id: str`, `nome: str`, `lat: float`, `lon: float`.
- `Viagem`: Objeto imutável contendo `id: str`, `linha_id: str`, `nome_linha: str`, `operador: str`, `modal: str` (`"onibus"`, `"metro"` ou `"trem"`), `sentido: str`, `paradas: tuple[str, ...]`, `horarios: tuple[int, ...]`, `dias_semana: frozenset[int]`, `excecoes: frozenset[str]`.
- `Rede`: Contém o dicionário de `paradas: dict[str, Parada]`, lista de `viagens: list[Viagem]`, `versao: str`, `origem_dados: str`. Métodos: `validar()` e `limites()`.

### 1.2 Ganchos de Integração (Integrante 3 - Acessibilidade e Segurança)
Conforme definido na seção 8.1 da especificação:
- `verificar_acessibilidade(rota, necessidades: frozenset[str]) -> str`: Retorna um dos estados: `"NAO_SOLICITADA"`, `"COMPATIVEL_COM_DADOS_DISPONIVEIS"`, `"NAO_VERIFICADA"`, `"INCOMPATIVEL"`. Enquanto não integrado, o padrão do módulo é retornar `"NAO_VERIFICADA"`. Se o usuário não informar necessidades de acessibilidade, o estado da rota é `"NAO_SOLICITADA"` e o gancho não é invocado.
- `avaliar_exposicao(rota) -> tuple[float | None, str]`: Retorna a exposição estimada (número entre 0.0 e 1.0) e o status (`"dados_suficientes"`, `"dados_insuficientes"`, `"indisponivel"`). Enquanto não integrado, o padrão é retornar `(None, "indisponivel")`.
- `restricoes: Restricoes`: Bloqueios confirmados em `paradas_bloqueadas: frozenset[str]`, `linhas_bloqueadas: frozenset[str]` e `trocas_bloqueadas: frozenset[tuple[str, str]]`.

### 1.3 Saída Consumida pela Interface e Servidor (Integrantes 4 e 5)
- O ponto de entrada principal do módulo é `processar_pedido(pedido, rede, regras_tarifa, ...)` que recebe um dicionário contendo origem, destino, partida (ISO 8601) e necessidades opcionais, e retorna um dicionário JSON serializável via `RespostaRotas.para_dict()`.
- O ponto de entrada de busca por endereço é `buscar_endereco(texto, banco, limites, cliente_http=None, agora=None)` que retorna candidatos dentro dos limites informados.

---

## 2. Premissas de Algoritmo de Busca (Seção 6.5)

1. **Ultrapassagem de veículos:** Viagens de um mesmo padrão não se ultrapassam ao longo do trajeto planejado.
2. **Caminhada em linha reta:** As distâncias a pé entre paradas e pontos de origem/destino são calculadas pela fórmula de Haversine em linha reta, com velocidade padrão configurada no perfil.
3. **Permanência na parada:** O tempo de embarque/desembarque de veículos na parada é considerado embutido nos horários programados das viagens (permanência física não modelada adicionalmente).

---

## 3. Parâmetros e Constantes do Módulo (Seção 3)

Todas as constantes numéricas e limiares estão centralizados exclusivamente em `src/config.py`:
- `RAIO_TERRA_M = 6371000.0`
- `FOLGA_BALDEACAO_S = 60`
- `CAMINHADA_BALDEACAO_MAX_M = 500`
- `ESPERA_MAX_S = 5400`
- `MAX_RODADAS_PADRAO = 4`
- `MAX_EXECUCOES = 10`
- `TAMANHO_CELULA_M = 500`
- `VELOCIDADE_CAMINHADA_PADRAO_MS = 1.2`
- `CAMINHADA_MAX_PADRAO_M = 1000`
- `CAMINHADA_MAX_LIMITE_M = 3000`
- `BALDEACOES_MAX_LIMITE = 4`
- `PESOS = {"tempo": 0.5, "custo": 0.25, "exposicao": 0.25}`
- `REF = {"tempo": 90.0, "custo": 1200.0, "exposicao": 1.0}`
- `LIMIAR_SIMILARIDADE = 0.8`
- `MAX_ROTAS = 3`
- `FUSO = "America/Sao_Paulo"`
- `RETENCAO_HISTORICO_DIAS = 90`
- `TTL_CACHE_GEOCODIFICACAO_DIAS = 30`
- `GEOCODIFICACAO_INTERVALO_MIN_S = 1.1`
- `GEOCODIFICACAO_TIMEOUT_S = 10`
- `GEOCODIFICACAO_MAX_RESULTADOS = 5`

---

## 4. O que NÃO foi testado (Limitações do MVP)

1. **Dados reais:** O módulo foi estritamente testado com redes fictícias e regras tarifárias simuladas; não foram ingeridos feeds GTFS reais de SPTrans, CPTM, Metrô ou EMTU.
2. **Desempenho com rede grande:** A validação do algoritmo de busca por rodadas foi realizada com redes controladas (rede piloto e mini rede); o consumo de memória e latência sob malha completa de milhares de linhas e paradas deve ser avaliado em etapas posteriores.
3. **Rede externa ao vivo:** Os testes de geocodificação não realizam chamadas externas à internet, utilizando simulação local do protocolo Nominatim/OpenStreetMap.
