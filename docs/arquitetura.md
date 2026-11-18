# Arquitetura Citizen Mobilidade

Site e aplicativo Expo → API FastAPI → JSON validado → algoritmo de busca → retorno com fontes.

A execução `python src/sistema.py` roda sem Expo nem API. Listas e dicionários representam registros; um dicionário de listas representa o grafo de temas. Busca por sobreposição de palavras normalizadas e pontuação. Empates retornam pedido de esclarecimento. Apenas registros com status `verificado`, fonte e data podem gerar respostas.

Rotas, tarifas em tempo real e navegação GPS são evoluções futuras, não funcionalidade entregue.
