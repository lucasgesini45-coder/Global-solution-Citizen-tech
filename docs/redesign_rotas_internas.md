# Redesign e planejamento de rotas na mesma página

## O que foi implementado

- Novo destaque com linguagem de mobilidade e ícone tecnológico, sem trem decorativo.
- Chat, planejamento e mapa na tela principal.
- `MapaPreview` recebe `trajeto` como lista de coordenadas e desenha a polilinha usando Leaflet + OpenStreetMap dentro do site.
- `/rotas` já retorna tempo estimado, custo, estado da segurança, distância a pé, baldeações e geometria para cada trecho.
- Seleção explícita de pontos **fictícios** da rede piloto. O frontend escolhe a alternativa mais rápida dentro do modal selecionado quando houver alternativas compatíveis.
- Rótulos de segurança: informação ainda **não verificada**. Nunca usar dados incompletos para prometer trajetos seguros.

## Limites — importante para a apresentação

**Os trajetos exibidos nesta fase NÃO são serviços reais.** A API executa o motor de demonstração do integrante 2 com rede e tarifas fictícias.

- O traçado no mapa representa a geometria da rede de teste e não necessariamente o arruamento ou o traçado ferroviário verdadeiro.
- Tempo e tarifa são calculados **para a simulação**, não podem ser usados para realizar viagens.
- A geolocalização serve para centralizar o mapa, mas **não alimenta ainda o cálculo de rota real**.
- O campo livre de endereços é um elemento visual preparado para futura integração com geocodificação/GTFS; os botões dos pontos pilotos são a entrada efetiva nesta fase.
- A opção de caminhada pode não encontrar um trajeto na rede simulada. O sistema informa a indisponibilidade sem inventar uma rota.
- Para viagens verdadeiras, serão necessários dados de transportadoras em formato GTFS/GTFS-RT, roteador multimodal ou APIs de rotas com cobertura e licenciamento adequados.
- Segurança: ainda sem índice de ocorrências verificado. Nenhuma escala fictícia ou rótulo de região segura/perigosa será apresentado.

## Imagens

Foram geradas três artes futuristas de metrô, ônibus e caminhada. O código no GitHub ainda usa fotos temporárias porque os arquivos JPG precisam ser incorporados ao repositório. O pacote `citizen_cards_prontos_para_github.zip` contém os arquivos e um script PowerShell que os copia para `frontend/assets` e altera os imports em `frontend/app/index.tsx`. Após executar, revisar diff e enviar commit.

## Testar

```powershell
git switch integracao/citizen-mobilidade
git pull origin integracao/citizen-mobilidade
python -m unittest discover -s backend/tests -v
cd "global solution part2 - tarifas"
python -m pytest -v
```

Volte à raiz para iniciar a API:
```powershell
python -m uvicorn backend.src.api:app --reload
```

Em outro terminal:
```powershell
cd frontend
npm install
npm run web
```

Teste a simulação Alfa → Destino com o card Trem/Metrô, conferindo geometria, tempo, tarifa fictícia e segurança não verificada. Depois selecione Ônibus. Ao escolher A pé, verifique que não há rota falsa quando os dados não suportam o trajeto.

Não efetuar merge na `main` sem executar os testes no ambiente do projeto.
