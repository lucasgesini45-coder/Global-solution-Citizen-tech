# Plano de testes — entrega FIAP

Ver [método e modelos](adequacao_fiap.md), [relatório histórico](relatorio_testes_indicadores_fiap.md) e [20 cenários](../data/perguntas_cidadas_teste.json). Cobrir validação de JSON, entradas inválidas, correspondência correta, ausência de fonte, ambiguidade, navegação e modelos A/B. Reexecutar `python -m backend.src.avaliacao_cidada` e `python -m pytest backend/tests/test_core.py backend/tests/test_citizen_fiap.py -v`. Registrar resultados reais e falhas; fazer revisão humana de fontes e roteiro manual com participante antes da entrega.
