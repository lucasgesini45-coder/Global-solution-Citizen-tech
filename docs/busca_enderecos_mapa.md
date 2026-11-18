# Configurar mapa e busca de endereços

## O que está disponível

- Tela principal sem caixa "IA Cidadã" e sem botões dos pontos simulados.
- Sugestões de endereço por `GET /enderecos/sugestoes?q=...` em português, usando Photon/OpenStreetMap.
- Após selecionar origem e destino, os dois marcadores aparecem no mapa integrado.
- Mapa Leaflet com estilo OSM padrão; estilo visual **CARTO Voyager** disponível com chave pública em `EXPO_PUBLIC_CARTO_KEY`. Não é o Google Maps, mas apresenta ruas, nomes e zoom com aparência de mapa urbano convencional.
- Para **caminhada**, traçado real e estimativas dentro do site via OpenRouteService se a chave do serviço estiver configurada.
- Para **ônibus, metrô e trem**, ainda não existem itinerários/GTFS atuais conectados; a interface informa a limitação, sem mostrar duração ou tarifa fictícias.

## Chaves

No terminal onde inicia o backend (PowerShell):

```powershell
$env:ORS_API_KEY = "SUA_CHAVE_OPENROUTESERVICE"
python -m uvicorn backend.src.api:app --reload
```

Obtenha a chave diretamente em [openrouteservice](https://openrouteservice.org/).
Ela deve ficar no **backend**, fora do GitHub, nunca em `EXPO_PUBLIC_*`.

Para estilo CARTO Voyager (opcional), solicite chave em
[carto.com/basemaps/apikey](https://carto.com/basemaps/apikey/).
Crie ou edite `frontend/.env` com:

```env
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
EXPO_PUBLIC_CARTO_KEY=CHAVE_PUBLICA_DE_MAPA
```

Essa chave é visível no frontend: restrinja por domínio e serviço no painel CARTO.
Atenda à atribuição © OpenStreetMap contributors e © CARTO.

## Testes

```powershell
python -m unittest discover -s backend/tests -v
cd frontend
npm install
npx tsc --noEmit
npm run web
```

Busque por "Rua Maracá 270 São Paulo" e selecione um dos resultados relevantes.
Caso não apareça, inclua bairro e município. Photon é um serviço de demonstração
sem garantia de disponibilidade e com controle de uso. Uso público em grande escala exige servidor próprio ou plano contratado.

**Não confunda:** um endereço encontrado não garante que o sistema possua rotas de transporte público naquele local. Não se deve afirmar que a caminhada é segura: o campo de segurança permanece "não verificada".

## Imagens dos transportes
As três artes originais geradas (metrô, ônibus e caminhada azuis) devem ser copiadas em
`frontend/assets/` e referenciadas por `require("../assets/arquivo.jpg")` para uso offline.
As fotos remotas atuais são provisórias até que o grupo envie as imagens ao GitHub.

## Próxima integração de transporte coletivo
Para rotas reais de metrô/trem/ônibus: obter GTFS atualizado e regras oficiais de tarifa, calcular caminhos e tempos com horários reais, documentar cobertura e fontes.
