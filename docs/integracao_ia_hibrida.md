# Integração da IA do Citizen Tech

## Proveniência e decisões
A branch ia-ver2 tem dois commits adicionais em relação à main (base 4760994196d36001ba3a482a9ebc09ee7e109b9e). Os arquivos de API, base JSON e scripts de avaliação continham marcadores de conflito. A integração preserva o código executável da branch acadêmica, incorpora os testes de previsão e relatórios da ia-ver2 com imports ajustados e atualiza as respostas da base. Não foram incorporados bytecodes, caminhos obsoletos nem dependências duplicadas.

## Arquitetura
- POST /agente/conversar: validação de escopo, cálculo de rotas reais quando solicitado, orientações do aplicativo, recuperação de documentos cadastrados e classificador de intenção para funcionalidades do app.
- Classificador: TF-IDF + regressão logística, 15 intenções, 180 frases de treino, 12 perguntas de avaliação separadas. Mantém limiar 0.40; não gera fatos nem consulta órgãos por conta própria.
- Núcleo acadêmico: busca JSON, comparação A/B e 20 cenários. Métricas anteriores não equivalem ao desempenho do chat integrado.
- Perguntas sobre direitos e benefícios não usam respostas do classificador quando faltam referências apropriadas.
- Base documental: resumos locais com referências institucionais, não busca ao vivo. A revisão factual dos links e informações pela equipe continua necessária.
- Sem histórico persistente de mensagens; o aplicativo mantém o estado da conversa enquanto aberto.

## Reprodução
```bash
python -m pytest backend/tests/assistente backend/tests/test_ia_integrada.py backend/tests/test_agente_chat.py backend/tests/test_documentos_transporte.py -v
python -m backend.src.assistente.avaliacao
python -m backend.src.assistente.calibracao
python -m backend.src.avaliacao_cidada
```

Os relatórios de avaliação e calibração da ia-ver2 e as métricas anteriores são históricos. Não se atribui aumento de acurácia à integração sem uma nova execução. Testes de interface, validação manual das referências, teste de uso real e avaliação independente com novas paráfrases permanecem necessários.
