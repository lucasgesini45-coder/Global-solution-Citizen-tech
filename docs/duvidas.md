# Registro de Dúvidas e Decisões Provisórias

| ID | Trecho da especificação | Dúvida | O que foi feito provisoriamente |
|---|---|---|---|
| DUV-01 | Seção 7.1 e 18: Download do GTFS da SPTrans | Portal SPTrans exige cadastro para download do GTFS e o arquivo não se encontra na pasta `backend/data/gtfs/sptrans/`. | Registrado como pendência da equipe conforme Seção 18. O pipeline e testes utilizam a fixture `gtfs_mini` (E3). |
| DUV-02 | Seção 7.1: GTFS de `metroferroviario` e `emtu` | Não foram encontrados feeds GTFS públicos oficiais consolidados para download direto nos sites do Governo do Estado sem credenciamento. | Conforme §7.1 e §8.4, esses sistemas ficam sem feed ativo no momento, e a API retornará os avisos de cobertura correspondentes. |
| DUV-03 | Seção 9.2: Janela e limites da cadeia integrada (janela_integrada_s, max_onibus, max_trilho) | Fontes secundárias divergem (2h vs 3h para a janela integrada com trilho; até 3 ou 4 ônibus). | Adotados os valores de partida da seção 9.2 (`janela_integrada_s = 7200`, `max_onibus_integrada = 3`, `max_trilho_integrada = 1`) com `confirmada=false` na regra tarifária até homologação definitiva pela equipe. |
