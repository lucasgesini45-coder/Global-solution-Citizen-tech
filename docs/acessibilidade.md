# Módulo de acessibilidade

Responsável: Raphael de Freitas Silva.

## Objetivo
Avaliar se uma rota atende à necessidade de passagem sem degraus,
identificando barreiras e informações desconhecidas.

## Arquivos
- backend/src/acessibilidade.py: funções de leitura, validação e avaliação.
- backend/tests/teste_acessibilidade.py: exemplos e testes.
- backend/data/rota_exemplo.json: rota com dados simulados.

## Executar os testes
Na pasta principal do repositório:

```bash
python3 -m backend.tests.teste_acessibilidade
```

## Usar em outro módulo
```python
from backend.src.acessibilidade import analisar_acessibilidade

resultado = analisar_acessibilidade(
    rota,
    {"precisa_sem_degraus": True}
)
```

A variável rota deve ser uma lista de trechos com os campos:
id, descricao e passagem_sem_degraus.

## Resultados
- COMPATIVEL: todos os trechos atendem ao critério avaliado.
- INCOMPATIVEL: existe uma barreira conhecida.
- NAO_VERIFICADA: faltam informações ou a rota está vazia.
- NAO_SE_APLICA: o passageiro não solicitou esse critério.
- DADOS_INVALIDOS: os dados falharam nas validações implementadas.

O resultado contém status, barreiras, pendencias e erros.

## Leitura de JSON
A função carregar_rota_json recebe o caminho do arquivo.
Após a leitura, os dados devem passar por analisar_acessibilidade.
Falhas de leitura são comunicadas por ValueError.

## Limitações
Os dados do exemplo são simulados.
O módulo avalia somente passagem sem degraus, não toda a acessibilidade.
Não confirma condições em tempo real.
A integração com segurança pública ainda não foi implementada.