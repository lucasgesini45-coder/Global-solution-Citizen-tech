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

## Segurança das rotas - validação inicial
A IA apoiou o planejamento, a elaboração e a revisão do código de inspeção da planilha e de avaliação temporal das ocorrencias

Validação realizada pelo integrante responsável:
- Execução de sete testes de atualidade, todos aprovados.
-Conferência dos totais por município, categoria e tipo de local.
- Inspeção das datas e dos limites numéricos das coordenadas.
- Identificação de 50 linhas com fato posterior ao registro.

Na execussão de 22/11/2026, com janela experimental de 90 dias:
-331.011 linhas foram selecionadas para São Paulo.
- 39.770 passaram pelo critério temporal.
dessas, 36,475 tinham coordenadas dentro dos limites numéricos.

Limitações:
- As contagens representam linhas, ainda sem duplica;cão.
- Coordenadas numericamente válidas não confirmam localização dentro do município nem precisão geográfica.
- A maior data de registro encontrada foi 30/09/2026.
- A janela de 90 dias é configurável e ainda precisa de avaliação.
- Não há cálculo de segurança de rota nem atualização automática implementados nesta etapa.
## Inspeção de boletins e validação geográfica experimental

A IA apoiou a elaboração dos scripts de inspeção, download do
contorno municipal, validação geométrica e classificação espacial.
A validação crítica realizada pela equipe incluiu execução local,
conferência dos resultados e testes com pontos simulados.

Resultados da execução registrada:
- 35.605 linhas candidatas após os filtros temporais e numéricos.
- Nenhuma repetição exata entre as linhas candidatas.
- 35.397 combinações provisórias de delegacia, ano e número do boletim.
- 203 combinações repetidas, todas com mais de uma natureza criminal.
- Uma combinação com quatro linhas e dois pontos separados por
  aproximadamente 3,22 km foi marcada como pendência de localização.
- 35.572 linhas dentro do contorno municipal.
- 29 linhas fora do contorno.
- Nenhuma linha exatamente na borda.
- Quatro linhas divergentes permaneceram separadas da classificação.

Fonte do contorno:
- API de Malhas do IBGE, município 3550308.
- URL, data de coleta e hash SHA-256 registrados no arquivo
  backend/data/limites/municipio_3550308_fonte.json.

Verificações realizadas:
- Integridade do arquivo comparada ao hash registrado na coleta.
- Estrutura, limites numéricos e fechamento dos anéis.
- Validade geométrica com Shapely.
- Testes de distância com pontos simulados.
- Testes de classificação dentro, fora e na borda.
- Teste da ordem latitude/longitude e conferência dos totais.

Limitações:
- A identificação dos boletins é provisória; combinações não são
  necessariamente ocorrências únicas.
- A referência espacial da planilha criminal ainda precisa ser confirmada.
- A referência temporal e a simplificação da malha precisam ser avaliadas.
- A classificação espacial é experimental, sem tolerância em metros na borda.
- Pontos externos não foram automaticamente considerados erros.
- Nenhum registro da planilha original foi alterado ou excluído.
- Não foi calculada uma pontuação de segurança para as rotas.
- As contagens podem variar conforme a data da consulta e a janela temporal.

Dependências utilizadas nesta etapa: openpyxl e shapely.
## Reorganização das funções geográficas

A IA apoiou a separação das funções geográficas em
backend/src/geografia.py e a criação de testes automatizados.

Validação realizada pela equipe:
- Execução de 12 testes com unittest, todos aprovados.
- Testes de coordenadas inválidas, contornos inválidos e vazios,
  pontos internos, externos, na borda e em buraco do polígono.
- Testes de distância e ordem latitude/longitude.
- Execução completa do script de inspeção após a reorganização.
- Em 24/11/2026, o relatório exportou 29 combinações pendentes,
  representando 32 linhas originais.

Limitações mantidas:
- Referência espacial da base criminal não confirmada.
- Identificação dos boletins provisória.
- Distâncias e classificação espacial experimentais.
- A janela móvel pode alterar as contagens entre execuções.
- Nenhuma alteração foi feita na planilha original.
## Exportação JSON para integração experimental

A IA apoiou a elaboração da exportação estruturada dos grupos,
das pendências e do contexto da análise.

Validação realizada pela equipe em 24/11/2026:
- Execução completa do script de inspeção.
- Exportação de 34.460 grupos provisórios:
  34.431 candidatos experimentais e 29 pendentes.
- Nenhuma linha candidata ficou sem identificação.
- Conferência dos totais e dos identificadores da exportação.
- Releitura do JSON e comparação com o documento preparado.
- Grupos pendentes receberam null no ponto para integração.

Limitações:
- Grupos provisórios não equivalem a ocorrências únicas.
- A referência espacial criminal continua não confirmada.
- Não há pontuação de segurança calculada.
- Identificadores sequenciais valem somente para cada exportação.
- O JSON real foi mantido localmente, fora do repositório.
- O leitor independente e seus testes ainda serão implementados.## Leitura e validação do JSON de segurança

A IA apoiou a criação do módulo backend/src/base_seguranca.py
e dos testes em backend/tests/teste_base_seguranca.py.

Validação realizada pela equipe:
- Execução dos 13 testes automatizados com sucesso.
- Leitura e validação do JSON real exportado.
- Conferência de 34.460 grupos totais, 34.431 candidatos
  experimentais e 29 pendentes.
- Confirmação de que os pendentes ficaram fora da seleção.
- Uso experimental permitido explicitamente na chamada.

Limitações:
- A validação verifica a estrutura e a coerência dos dados,
  não sua veracidade nem a segurança de uma rota.
- A janela temporal é conferida em relação à data de consulta
  registrada no arquivo, não à data de uso pelo passageiro.
- A referência espacial criminal permanece não confirmada.## Reavaliação temporal na data de uso

A IA apoiou a criação do módulo atualidade_base.py e de seus testes.

Validação realizada pela equipe:
- Nove testes automatizados executados com sucesso.
- Fato com exatamente 90 dias permanece elegível.
- Fato com 91 dias sai da seleção.
- Grupos pendentes permanecem fora da seleção.
- A base original não é modificada pela avaliação.
- Uso experimental bloqueado por padrão.

Teste com o JSON real em 24/11/2026:
- 34.431 candidatos elegíveis.
- Nenhum candidato excluído por idade nessa data.
- 29 grupos pendentes mantidos fora da seleção.
- Maior data de registro: 30/09/2026, com defasagem de 55 dias.
- Atualização da fonte não confirmada.

Limitações:
- Elegibilidade temporal não comprova segurança ou cobertura recente.
- A referência espacial criminal continua não confirmada.
- Ainda não foi definido um limite operacional de defasagem da fonte.## Consulta de proximidade de pontos

A IA apoiou a criação de proximidade.py e dos testes automatizados.

Validação realizada pela equipe:
- Onze testes executados com sucesso, usando dados simulados.
- Seleção de grupos dentro do raio, incluindo seu limite.
- Ordenação por distância.
- Rejeição de grupos pendentes e identificadores repetidos.
- Rejeição de coordenadas e raios inválidos.
- Confirmação de que os dados de entrada não foram alterados.

Limitações:
- A consulta considera um ponto isolado, não o percurso completo.
- A distância é aproximada e não acompanha as ruas.
- Os candidatos devem ser previamente validados e reavaliados temporalmente.
- O raio é um parâmetro de consulta, não um limite de segurança.
- Ausência de grupos próximos não significa ausência de risco.## Proximidade ao longo de trajetos

A IA apoiou a criação de proximidade_trajeto.py e seus testes.

Validação realizada pela equipe:
- Dez testes automatizados aprovados com dados simulados.
- Identificação de grupo próximo do meio do percurso.
- Respeito aos segmentos de um trajeto em L.
- Contagem única por grupo em trajetos de ida e volta.
- Rejeição de pendentes, identificadores repetidos e entradas inválidas.
- Preservação dos dados de entrada.

Limitações:
- A linha conecta os vértices na ordem fornecida e precisa representar
  o caminho real.
- Cálculo experimental em projeção local, pressupondo WGS 84.
- Vértices limitados a 20 km do primeiro ponto e raio até 2 km.
- Pré-filtro de processamento de 50 km ao redor do primeiro ponto.
- Os candidatos precisam de validação e reavaliação temporal prévias.
- Proximidade não constitui pontuação de risco ou garantia de segurança.## Consulta integrada de proximidade por rota

A IA apoiou a criação de consulta_rota.py e seus testes.

Validação realizada pela equipe:
- Onze testes automatizados aprovados com dados simulados.
- Integração de trechos de caminhada e pontos de embarque.
- Preservação das associações entre grupos e trechos.
- Contagem única de cada grupo no total da rota.
- Rejeição de trechos inválidos, identificadores repetidos
  e grupos pendentes.
- Preservação dos dados de entrada.

Limitações:
- Os candidatos devem vir da mesma exportação e passar
  previamente pela validação e reavaliação temporal.
- As caminhadas precisam representar o caminho real.
- Não são analisados deslocamentos dentro dos veículos.
- Distâncias aproximadas; não há pontuação de segurança.
- Contagens brutas não determinam qual rota é mais segura.## Integração da análise experimental de rota

A IA apoiou a criação de analise_rota.py e dos testes de integração.

Validação realizada pela equipe:
- Oito testes aprovados com JSON temporário e dados simulados.
- Integração de leitura, validação, atualidade e proximidade.
- Exclusão dos grupos pendentes da seleção.
- Contagem única de grupos associados a vários trechos.
- Distinção entre ausência de candidatos elegíveis e ausência
  de grupos próximos da rota.
- Bloqueio de base inconsistente e uso experimental não autorizado.
- Preservação do arquivo original.

Limitações:
- Não há pontuação de segurança nem recomendação de rotas.
- A referência espacial criminal permanece não confirmada.
- O teste integrado desta etapa utilizou dados simulados.## Demonstração integrada com base real e rota simulada

A IA apoiou a criação de demonstrar_analise_rota.py.

Validação realizada pela equipe em 25/11/2026:
- Leitura do JSON exportado em 24/11/2026.
- Reavaliação temporal: 34.431 candidatos iniciais,
  33.312 elegíveis e 1.119 excluídos por idade.
- Os 29 grupos pendentes permaneceram fora da seleção.
- Consulta com raio de 200 metros em uma caminhada e um
  ponto de embarque fictícios.
- Foram encontrados 28 grupos próximos da caminhada e
  19 próximos do embarque.
- Total de 28 grupos distintos e 47 associações com trechos.
- Nenhum arquivo da base foi alterado.

Limitações:
- O trajeto e o embarque são simulados, não verificados no local.
- Grupos provisórios não equivalem a ocorrências únicas.
- Último registro disponível: 30/09/2026, com defasagem de 56 dias.
- Atualização da fonte e referência espacial criminal não confirmadas.
- Nenhuma pontuação de segurança foi calculada.
- O script depende do JSON local indicado no caminho configurado.## Integração de acessibilidade e proximidade por rota

A IA apoiou a criação de avaliacao_rota.py e seus testes.

Validação realizada pela equipe:
- Oito testes aprovados com dados simulados.
- Uso dos mesmos trechos para acessibilidade e proximidade.
- Preservação das barreiras e das informações pendentes.
- Dados de acessibilidade inválidos bloqueiam a consulta geográfica.
- Rota vazia não executa consulta de proximidade.
- Contagem de grupos sem duplicação entre trechos.

Limitações:
- A acessibilidade verifica somente passagem sem degraus.
- Compatibilidade com esse critério não comprova acessibilidade completa.
- A proximidade não compensa uma barreira de acessibilidade.
- Não há pontuação de segurança nem recomendação automática.
- Tempo e custo ainda não são comparados neste módulo.### Bloqueio de acessibilidade não confirmada

A IA auxiliou na revisão da seleção de rotas e na elaboração
dos testes. A equipe executou e conferiu os resultados.

Quando há necessidade de acessibilidade informada, rotas
incompatíveis ou sem compatibilidade confirmada são retiradas
da seleção. Ganhos de tempo ou custo não compensam esse bloqueio.

O teste de integração anterior foi atualizado porque esperava
rotas sem confirmação de acessibilidade. A nova expectativa
verifica a ausência de recomendações e o motivo do bloqueio.

Validação: 83 testes da pasta backend/tests/rotas passaram.

Limitação: os testes verificam o comportamento do código.
Não confirmam a acessibilidade física dos trajetos nem
validam uma pontuação de segurança criminal.