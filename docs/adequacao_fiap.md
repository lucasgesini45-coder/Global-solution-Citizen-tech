# Adequação Citizen Assist AI — Global Solution 2026.2

## Base cidadã
15 registros de 4 temas: cartões, gratuidade, acessibilidade e serviços. O arquivo backend/data/orientacoes.json contém identificador, tema, perguntas, orientação, URL, data de verificação e status. Referências oficiais consultadas em 17/11/2026; a equipe deve revisar a curadoria antes da entrega. Regras podem mudar.

## Busca e navegação
O Python carrega uma lista de dicionários, valida campos, unicidade e datas. A busca normaliza acentos, remove palavras genéricas e calcula Dice (2 × interseção / soma do número de tokens), comparando cada pergunta com as frases de cada registro verificado. Pontuação mínima de 0,55; exige dois tokens coincidentes ou igualdade; diferença de até 0,05 entre os dois melhores registros indica ambiguidade. Nenhum rascunho responde. O grafo conecta cartões, gratuidade, acessibilidade, direitos e serviços; o menu permite escolher um tema disponível e um registro por identificador. Limitação: termos sinônimos e perguntas longas podem não coincidir; ampliar reformulações e calibrar limites com novas perguntas.

## Modelos de instrução
- A: "Atue como orientador cidadão acadêmico. Recupere somente um registro verificado; reproduza a orientação resumida e cite a referência e a data. Sem correspondência suficiente, informe a limitação."
- B: mesmas regras de A e acrescente aviso para confirmar regras atuais no canal oficial, esclarecendo que o assistente não é oficial.
Ambos são instruções implementadas por regras em Python, não prompts enviados a um LLM. A busca é idêntica; a diferença é a apresentação. B é a opção padrão por explicitar limites. A comparação de clareza humana ainda precisa de revisão.

## Avaliação
Execute na raiz:
```powershell
python -m backend.src.avaliacao_cidada
python -m pytest backend/tests/test_citizen_fiap.py -v
python src/sistema.py
```
A avaliação usa 20 perguntas simuladas, incluindo reformulações, entrada vazia, ambiguidade e pergunta fora do escopo. Gera docs/resultados_avaliacao_cidada.json com status/ID esperado e obtido, texto, fontes, acerto, tempo e médias por modelo. Um acerto requer status correto, ID correto quando aplicável e presença/ausência apropriada de fonte. Resultados devem ser gerados e conferidos; não atribuir números sem execução. Não mede utilidade subjetiva nem veracidade futura da fonte.

## Roteiro de facilidade de uso
Teste automatizado: opção inexistente; pergunta vazia; escolher primeiro tema (acessibilidade) e orientação 10; alternar modelo A; consultar cartão comum e sair. Registra sucesso funcional por assertivas. Complementar com execução manual, tempo de tarefas, dificuldades observadas, taxa de conclusão e percepção de clareza. Não declarar participação humana sem realização.

## Entrega
Pendente: nomes e RMs, nome final da equipe, revisão humana de fontes, relatório com resultados executados e interpretados, usabilidade, verificação da estrutura oficial (tabelas ausentes do texto recebido), vídeo não listado e TXT com apenas os dois links. A interface web e o mapa são diferenciais, não substituem o terminal.
