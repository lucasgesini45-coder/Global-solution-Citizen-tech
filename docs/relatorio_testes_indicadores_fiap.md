# Relatório de testes e indicadores — Citizen Assist AI

**Global Solution 2026.2 — FIAP | Citizen Tech Mobilidade Urbana**

Data: 17/11/2026. Evidência: [GitHub Actions, execução 44088026008](https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech/actions/runs/44088026008), commit `a06c91619ee841ccfbf2247b0156e5627186587f`, Python 3.13 em Ubuntu. O relatório refere-se ao núcleo de orientação cidadã, não ao classificador de dúvidas do aplicativo ou ao motor de transporte.

## 1. Objetivo e método

Foram avaliados 20 cenários fictícios em cada um dos dois modelos de instrução (40 consultas). A base contém 15 registros em quatro temas: cartões, gratuidade, acessibilidade e serviços. Cada teste contém pergunta, estado e ID esperados; o código registra orientação esperada, texto efetivamente retornado, fonte, estado e ID obtidos, classificação de acerto e duração medida com `perf_counter`. Acerto = estado esperado, ID esperado e presença de fonte quando aplicável. A fonte constar na saída não comprova sua validade factual atual.

## 2. Indicadores

| Indicador | A — direto | B — com aviso |
|---|---:|---:|
| Consultas | 20 | 20 |
| Acertos | 19 | 19 |
| Erros | 1 | 1 |
| Taxa de acerto | 95% | 95% |
| Tempo médio (ms) | 0,2171 | 0,2092 |
| Saídas com estado ok | 18 | 18 |
| Saídas ok com fonte | 18 | 18 |
| Saídas ok com aviso de não oficialidade | 0/18 | 18/18 |
| Limitações tratadas corretamente | 2/3 | 2/3 |

Taxa de acerto = 19 ÷ 20 × 100 = 95%. Tempo médio = soma dos tempos individuais ÷ 20. A execução também registrou **177 testes automatizados aprovados, 1 advertência**, além do typecheck do frontend aprovado. Isso não equivale a homologação com usuários nem validação de todas as fontes.

## 3. Registro individual dos testes

Os dois modelos retornaram os mesmos estados e IDs, pois compartilham o algoritmo de busca. Os textos completos, fontes e orientações esperadas estão no [registro JSON de resultados medidos](resultados_avaliacao_cidada.json); abaixo está o resumo por pergunta. Os tempos são em milissegundos.

| Nº | Pergunta | Esperado (estado/ID) | Obtido A e B | Classificação | Tempo A | Tempo B |
|---:|---|---|---|---|---:|---:|
| 1 | Como emitir cartão comum? | ok / 1 | ok / 1 | Acerto | 0,3553 | 0,2185 |
| 2 | segunda via cartão comum | ok / 2 | ok / 2 | Acerto | 0,2375 | 0,2178 |
| 3 | recarga bilhete unico comum | ok / 3 | ok / 3 | Acerto | 0,2279 | 0,2158 |
| 4 | posto atendimento cartao comum | ok / 4 | ok / 4 | Acerto | 0,2228 | 0,2264 |
| 5 | bilhete especial pcd laudo medico | ok / 5 | ok / 5 | Acerto | 0,2428 | 0,2172 |
| 6 | cartao idoso 65 | ok / 6 | ok / 6 | Acerto | 0,2198 | 0,2126 |
| 7 | desconto estudante transporte | ok / 7 | ok / 7 | Acerto | 0,2162 | 0,2441 |
| 8 | requisitos passe livre antt | ok / 8 | ok / 8 | Acerto | 0,2171 | 0,2290 |
| 9 | pedir passe livre digital | ok / 9 | ok / 9 | Acerto | 0,2295 | 0,2159 |
| 10 | assento preferencial metro | ok / 10 | ok / 10 | Acerto | 0,2206 | 0,2161 |
| 11 | cachorro guia metro | ok / 11 | ok / 11 | Acerto | 0,2157 | 0,2138 |
| 12 | van adaptada atende mais | ok / 12 | ok / 12 | Acerto | 0,2136 | 0,2213 |
| 13 | telefone atende mais | ok / 13 | ok / 13 | Acerto | 0,2120 | 0,2214 |
| 14 | horario abre fecha estacao | ok / 14 | ok / 14 | Acerto | 0,2251 | 0,2179 |
| 15 | perdi documento estacao | ok / 15 | ok / 15 | Acerto | 0,2125 | 0,2161 |
| 16 | Quando o metrô fecha na estação? | ok / 14 | ok / 14 | Acerto | 0,2149 | 0,2150 |
| 17 | Como coloco crédito no cartão comum? | ok / 3 | ok / 3 | Acerto | 0,2162 | 0,2255 |
| 18 | (vazia) | entrada_invalida | entrada_invalida | Acerto | 0,0084 | 0,0056 |
| 19 | cartão comum | ambiguo | ok / 1 | Erro | 0,2165 | 0,2159 |
| 20 | Qual a receita de bolo de chocolate? | sem_resposta | sem_resposta | Acerto | 0,2177 | 0,2185 |

## 4. Comparação das instruções

**Modelo A:** recuperar exclusivamente uma orientação da base verificada, exibir seu conteúdo e fonte/data; informar insuficiência quando não houver correspondência.

**Modelo B:** aplicar as mesmas regras do A e acrescentar aviso para confirmar regras atuais no canal oficial, informando que o assistente não é oficial.

Exemplo — pergunta "Como emitir cartão comum?":

- Orientação esperada: Para obter o Bilhete Único Comum, preencha o cadastro no site de atendimento da SPTrans. Consulte no portal as instruções de emissão e retirada.
- Resposta A: Para obter o Bilhete Único Comum, preencha o cadastro no site de atendimento da SPTrans. Consulte no portal as instruções de emissão e retirada.
- Resposta B: Para obter o Bilhete Único Comum, preencha o cadastro no site de atendimento da SPTrans. Consulte no portal as instruções de emissão e retirada. Confirme as regras atuais no canal oficial. Este assistente não é um serviço oficial.
- Fonte em ambos: https://bilheteunico.sptrans.com.br/comum/ (data registrada na base: 2026-11-17).

Os modelos têm a mesma taxa de acerto. B foi escolhido como padrão porque explicita a limitação em todas as 18 saídas com estado ok, enquanto A não apresenta o aviso padronizado. A pequena diferença temporal não permite afirmar superioridade de velocidade. A clareza foi comparada pelo conteúdo e pelo aviso, não por avaliação subjetiva humana. As instruções são regras Python, não prompts executados por um LLM.

## 5. Facilidade de uso — roteiro de tarefas executado

O teste automatizado `test_roteiro_terminal` foi aprovado na execução indicada. Utilizou entradas programadas e inspecionou as saídas do menu. Não houve participante humano.

| Tarefa | Resultado do roteiro |
|---|---|
| Inserir opção inexistente | Mensagem de opção inválida conferida |
| Enviar pergunta vazia | Mensagem solicitando pergunta conferida |
| Navegar pelo tema acessibilidade e selecionar ID 10 | Fluxo executado; fonte presente na saída do roteiro |
| Alternar para modelo A | Confirmação de seleção conferida |
| Consultar cartão comum | Fluxo executado; fonte presente na saída do roteiro |
| Sair | Execução encerrou normalmente |

O roteiro demonstra navegabilidade funcional sem interrupção, mas não mede satisfação, tempo por tarefa humana ou acessibilidade com tecnologia assistiva. A dificuldade observada na avaliação de consultas foi o termo genérico "cartão comum", que não acionou o pedido de esclarecimento. Recomenda-se complementar o roteiro com participante real e registrar tempo, dificuldades e comentários por tarefa.

## 6. Interpretação, limitações e melhorias

O caso 19 deveria retornar ambiguidade, mas selecionou ID 1 (emissão do cartão) nos dois modelos. A informação retornada pertence à base, porém não atende ao critério esperado de desambiguação. Não se deve ocultar esse erro nem reinterpretá-lo como acerto. Entrada vazia e consulta fora do tema tiveram o comportamento esperado. As perguntas são uma amostra pequena e várias coincidem com frases do cadastro; portanto 95% não é estimativa de desempenho para a população geral. Os tempos medem apenas a busca local, excluindo rede, interface, carregamento inicial e APIs de transporte. A revisão humana de todas as fontes e datas permanece necessária.

Melhorias propostas:
1. Detectar perguntas genéricas de assunto antes de selecionar um registro; exibir opções de emissão, recarga e segunda via e ampliar testes independentes de ambiguidade.
2. Expandir paráfrases, sinônimos e perguntas inéditas, recalibrar limiares sem usar o conjunto final de teste para ajuste.
3. Revisar periodicamente as referências institucionais, documentando revisão pela equipe e retirando registros desatualizados.
4. Realizar teste manual com usuários e recursos de acessibilidade, medindo conclusão das tarefas, tempo e clareza.

## 7. Reprodução

Na raiz do repositório:

```powershell
python -m backend.src.avaliacao_cidada
python -m pytest backend/tests/test_citizen_fiap.py -v
python src/sistema.py
```

A avaliação gera novamente `docs/resultados_avaliacao_cidada.json`; tempos variam conforme equipamento e execução. Conservar a evidência original no histórico Git. A avaliação não envolve dados pessoais de cidadãos.
