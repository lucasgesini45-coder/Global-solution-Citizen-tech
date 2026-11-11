# Novo layout — página única

O frontend em `frontend/app/index.tsx` foi reorganizado conforme o protótipo visual:

- Logo/texto `Citizen Tech` e `Mobilidade Urbana`
- Planejador de rotas no início, com localização mediante consentimento, origem e destino
- Três opções de transporte na mesma tela: trem/metrô, ônibus e a pé
- Área de chat com sugestões de perguntas (sem a antiga grade de assuntos)
- Mapa incorporado, com abertura de trajeto real no Google Maps
- Seção de indicadores regionais mantida como **em desenvolvimento**
- Bordas moderadas nos painéis; bordas mais arredondadas apenas na conversa

## Rodar a versão atualizada

```powershell
git switch integracao/citizen-mobilidade
git pull origin integracao/citizen-mobilidade
cd frontend
npm install
npm run web
```

**Atenção**: as imagens cinematográficas geradas para os três modais foram entregues em um pacote separado. Para inseri-las no repositório, extraia os arquivos JPG em `frontend/assets/`, depois substitua o atributo `foto` em `frontend/app/index.tsx` por imports locais:

```typescript
const fotos = {
  ferroviario: require("../assets/metro_futurista.jpg"),
  onibus: require("../assets/onibus_futurista.jpg"),
  ape: require("../assets/caminhada_futurista.jpg"),
};
```

Depois altere `ImageBackground source={{uri:t.foto}}` para `ImageBackground source={fotos[t.id]}`.

A versão publicada usa imagens remotas provisórias, para que a página continue carregando mesmo antes de adicionar as novas artes.

## Dados reais e protótipo

- Sem uma integração com API de roteamento, o tempo de chegada e a melhor rota são consultados via Google Maps; o mapa local não finge calcular esses resultados.
- A chave pública opcional `EXPO_PUBLIC_GOOGLE_MAPS_EMBED_KEY`, quando configurada, permite mostrar direções no mapa incorporado.
- O agente de orientações não deve inventar respostas: dados em rascunho da base não são respondidos como verificados.
- O mapa de indicadores de segurança por região ainda é apenas um aviso de funcionalidade futura.

## Validar antes do merge

Teste no navegador e celular: alinhamento e rolagem, permissão de localização, inversão origem/destino, seleção de modal, perguntas sugeridas, envio de chat, carregamento do mapa e acesso externo para consulta de ETA.
