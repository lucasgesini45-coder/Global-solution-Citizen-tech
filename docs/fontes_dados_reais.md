# Fontes de Dados Reais - São Paulo (2026)

Documento de conferência de dados reais de transporte e tarifas para a evolução v2 do Citizen Mobilidade, em conformidade com as seções 7.1 e 9.2 da especificação.

Data de verificação: 15/11/2026

---

## 1. Tarifas e Regras Tarifárias

| Item | Valor | Fonte (URL) | Data de conferência | Oficial? (sim/não) |
|---|---|---|---|---|
| Ônibus municipal (SPTrans) - tarifa básica / Bilhete Único comum | R$ 5,30 (530 centavos) | https://www.sptrans.com.br/tarifas/ (Portaria SMT.GAB nº 005/2026) | 15/11/2026 | Sim |
| Metrô, trem e monotrilho (Trilhos) - tarifa básica unitária / comum | R$ 5,40 (540 centavos) | https://www.cptm.sp.gov.br e https://www.metro.sp.gov.br (Resolução STM nº 018/2025) | 15/11/2026 | Sim |
| Integração Ônibus municipal (SPTrans) + Metrô/Trem (Bilhete Único comum) | R$ 9,38 (938 centavos) | https://www.sptrans.com.br/tarifas/ e https://www.cptm.sp.gov.br | 15/11/2026 | Sim |
| Adicional 2º embarque: Ônibus municipal -> Metrô/Trem | R$ 4,08 (408 centavos: 938 - 530) | https://www.sptrans.com.br/tarifas/ e https://www.cptm.sp.gov.br | 15/11/2026 | Sim |
| Adicional 2º embarque: Metrô/Trem -> Ônibus municipal | R$ 3,98 (398 centavos: 938 - 540) | https://www.sptrans.com.br/tarifas/ e https://www.cptm.sp.gov.br | 15/11/2026 | Sim |
| Ônibus municipal para Ônibus municipal na janela de 3h | R$ 0,00 adicional (até 4 embarques) | https://timesbrasil.com.br/empresas-e-negocios/transporte/tarifa-de-onibus-em-sao-paulo-vai-subir-em-janeiro-confira-valor/ (Portaria SMT/SPTrans) | 15/11/2026 | Não (fonte oficial simplificada não explicita texto da portaria integral na web sem login/diário oficial) |
| Janela e limites da cadeia integrada (janela_integrada_s, max_onibus_integrada, max_trilho_integrada) | 2h (7200s), até 3 ônibus e 1 trilho (ou 3h em outras fontes) | Exame / Diário do Transporte | 15/11/2026 | Não (fontes divergem; pendente de conferência em regulamento oficial) |
| Trilho para trilho (ex: metrô > trem, trem > metrô, metrô > metrô em transferência externa) | Sem valor oficial confirmado | Pesquisa oficial Metrô/CPTM (transferências gratuitas nas estações de integração internas; sem tarifa confirmada para validação externa) | 15/11/2026 | Não (não encontrado valor oficial; tarifa não confirmada) |
| Corredor ABD, EMTU | R$ 6,30 a R$ 6,35 | Diário do Transporte | 15/11/2026 | Não (fora do escopo da v2; sem regra confirmada) |
| Vale-transporte, estudante, idoso, Madrugador, bilhetes temporais | Diversos | SPTrans / CPTM / Metrô | 15/11/2026 | Sim (tarifas existem, porém mantidas fora do escopo do perfil 'padrao' v2 conforme §9.3) |

---

## 2. Investigação de Feeds GTFS Oficiais

| Sistema | Identificador | Fonte / URL | Situação / Resultado da Investigação |
|---|---|---|---|
| Ônibus municipais de São Paulo | `sptrans` | https://www.sptrans.com.br/desenvolvedores/ | **Exige cadastro e login** para download do arquivo GTFS (.zip). Arquivo não encontrado localmente em `backend/data/gtfs/sptrans/`. O agente não pode burlar autenticação; responsabilidade atribuída à equipe (seção 18). |
| Metrô e Trens (CPTM, Metrô, ViaQuatro, ViaMobilidade, TIC Trens, Trivia Trens) | `metroferroviario` | https://dadosabertos.sp.gov.br e https://www.metro.sp.gov.br | **Não encontrado** feed GTFS público oficial consolidado e atualizado diretamente para download sem convênio ou solicitação formal. Sistema sem feed ativo nesta versão. |
| Ônibus metropolitanos (EMTU / ARTESP) | `emtu` | https://dadosabertos.artesp.sp.gov.br e https://www.emtu.sp.gov.br | Portal ARTESP possui dados de linhas intermunicipais, mas feed GTFS unificado EMTU RMSP oficial direto não confirmado sem login/solicitação. Sistema sem feed ativo nesta versão. |
