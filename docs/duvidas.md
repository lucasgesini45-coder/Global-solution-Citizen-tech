<<<<<<< HEAD
# Dúvidas e pendências registradas

| ID | Trecho da especificação | Dúvida / ocorrência | O que foi feito provisoriamente |
|---|---|---|---|
| D-01 | 0.4 (sem ambiguidade de texto) | Os arquivos escritos pelo Antigravity (`config.py`, `preprocessamento.py`, `base.py`, `assistente_fontes.md` e os `__init__.py`) aparecem na gravação com **acentos corrompidos** (por exemplo `dÃºvidas` no lugar de `dúvidas`). Provável gravação em codificação errada. | Todos os arquivos foram reescritos em UTF-8 limpo. **Substituir os arquivos do Antigravity pelos desta entrega.** |
| D-02 | 7.3 | As linhas R04, H03, H04 e H05 do `assistente_fontes.md` não aparecem na gravação (parou antes). | Foram definidas com base nos fatos vistos e marcadas com ⚠. A equipe deve conferir nos arquivos citados. |
| D-03 | 7.3 item 5 | Não está confirmado se o app exige conta ou login. | A resposta H03 não afirma nada sobre isso (só fala de GPS e de dados pessoais do histórico). |
| D-04 | 5 e 12.3 | O `requirements.txt` do Antigravity fixa `numpy==2.5.3`; no ambiente de teste do Claude foi instalado `numpy==2.5.4`. As demais versões coincidem (scikit-learn 1.9.1, joblib 1.6.0, scipy 1.18.1). | Mantidas as versões do Antigravity. Se `pip install` reclamar, usar as instaladas no seu ambiente. |
| D-05 | 3.1 e 15 | Os testes da API exigem `httpx` e `pytest`, que não estão no `requirements.txt` do projeto. | Criado `backend/requirements-dev.txt` (não altera o `requirements.txt`). |
| D-06 | 12.1 | A especificação pede carregar o modelo na inicialização da API; um roteador não tem evento de inicialização estável. | O modelo é carregado **uma vez, na primeira chamada** (com trava) e mantido em memória. `preparar_modelo()` pode ser chamada no início da API se a equipe preferir carregar antes. |
| D-07 | 12.1 e 12.2 | O Claude não viu `backend/src/api.py` nem `backend/src/sistema.py`. | As duas alterações estão descritas em `INTEGRACAO.md`, com as linhas exatas, para aplicar à mão. |
| D-08 | 14 (E0 e E9) | A suíte de testes **existente** do projeto não foi executada pelo Claude (não estava disponível). | Rodar antes e depois da integração e comparar (instruções em `INTEGRACAO.md`). |
| D-09 | 9 | Resultado inicial: top-1 8/12, top-3 12/12. Há uma resposta errada com confiança acima do limiar (pergunta 2, sobre digitar o nome da rua, vai para R02 em vez de R03). | **Nada foi ajustado** para melhorar o resultado (a especificação proíbe ajustar com base nas perguntas de teste). Ver "Limitações" em `assistente_ia.md`. |
| D-10 | 7.3 item 4 | As respostas foram escritas por IA e valem desde já (decisão D-16), mas **nenhuma foi revisada pela equipe**. | `revisada_pela_equipe` está `false` nas 15 intenções. |
=======
# Registro de Dúvidas e Decisões Provisórias

| ID | Trecho da especificação | Dúvida | O que foi feito provisoriamente |
|---|---|---|---|
| DUV-01 | Seção 7.1 e 18: Download do GTFS da SPTrans | Portal SPTrans exige cadastro para download do GTFS e o arquivo não se encontra na pasta `backend/data/gtfs/sptrans/`. | Registrado como pendência da equipe conforme Seção 18. O pipeline e testes utilizam a fixture `gtfs_mini` (E3). |
| DUV-02 | Seção 7.1: GTFS de `metroferroviario` e `emtu` | Não foram encontrados feeds GTFS públicos oficiais consolidados para download direto nos sites do Governo do Estado sem credenciamento. | Conforme §7.1 e §8.4, esses sistemas ficam sem feed ativo no momento, e a API retornará os avisos de cobertura correspondentes. |
| DUV-03 | Seção 9.2: Janela e limites da cadeia integrada (janela_integrada_s, max_onibus, max_trilho) | Fontes secundárias divergem (2h vs 3h para a janela integrada com trilho; até 3 ou 4 ônibus). | Adotados os valores de partida da seção 9.2 (`janela_integrada_s = 7200`, `max_onibus_integrada = 3`, `max_trilho_integrada = 1`) com `confirmada=false` na regra tarifária até homologação definitiva pela equipe. |
>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e
