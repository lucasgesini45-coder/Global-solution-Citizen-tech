# Uso de IA

Esta etapa usa regras computacionais, sem LLM externo.

Modelo A: exibir diretamente a orientação verificada e sua fonte.
Modelo B: exibir orientação verificada, fonte e aviso para confirmar atualizações.

Comparar ambos com as mesmas perguntas, documentar acertos, limites, legibilidade e confiabilidade. Nunca inventar informação fora da base nem exigir dados pessoais.

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