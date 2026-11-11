# Mobilidade visual — versão inicial

Nova tela: `/mobilidade` (acessível pela página inicial).

## Funcionalidades implementadas
- Cards com foto para **Trem/Metrô**, **Ônibus** e **A pé**
- Seleção de modal e formulário de origem/destino
- Geolocalização por consentimento, sem localização em segundo plano
- Mapa incorporado da região com OpenStreetMap, e opção de abrir trajeto real no Google Maps
- Links para mapa da rede metroferroviária e informações de itinerários da SPTrans
- Painel informativo sobre futura camada de indicadores de segurança

## Rodar

Na raiz:
```powershell
git switch integracao/citizen-mobilidade
git pull origin integracao/citizen-mobilidade
cd frontend
npm install
npx expo install --fix
npm run web
```

Na tela inicial clique em **Explorar transportes e mapas**.

### Mapa do percurso dentro do app (opcional)

O mapa básico embutido usa OpenStreetMap e mostra a região/origem, mas **não desenha percurso de ruas nem calcula ETA**.

Se você habilitar a **Google Maps Embed API** em uma conta Google Cloud com faturamento e uma chave de API apropriada, preencha `frontend/.env`:
```
EXPO_PUBLIC_GOOGLE_MAPS_EMBED_KEY=SUA_CHAVE_PUBLICA_RESTRITA
```

Ao escolher um modal e clicar em **Traçar percurso e ver tempo estimado**, um mapa Google com direções será exibido dentro do app. A visualização Google Embed não suporta necessariamente restringir exclusivamente ônibus ou ferroviário, portanto confira o modal sugerido. Sem chave, o botão abre o Google Maps, que pode calcular trajetos, distância e duração. Não há cálculo próprio de ETA nesta fase.

**Segurança da chave**: `EXPO_PUBLIC_*` é visível no aplicativo e deve ser restrita por domínio/plataforma e API, conforme orientações do provedor; nunca colocar uma chave secreta de servidor neste campo.

## Limitações
- Roteamento real ainda usa Google Maps, **não** o motor de rotas simuladas que já existe no backend.
- Mapas carregados de provedores externos dependem de conexão e políticas desses serviços.
- Fotos são obtidas externamente (Metrô e caminhada: Wikimedia Commons; ônibus: SPTrans). Verificar atribuições/licenças específicas antes de distribuição pública.
- A função de regiões com maior incidência de crimes ainda é apenas informativa; não há classificação de risco ou mapa de ocorrências.
- A permissão de localização é solicitada apenas quando o usuário clica no botão.

## Próxima implementação: indicadores de ocorrências

Fonte inicial candidata: [Dados Abertos da SSP-SP](https://www.ssp.sp.gov.br/transparencia/dados-abertos).

Requisitos mínimos antes de criar camadas coloridas:
1. Determinar a área geográfica, tipos de ocorrências e período.
2. Baixar dados agregados publicamente disponíveis, revisar unidade geográfica e cobertura.
3. Normalizar taxas por população ou exposição, conforme adequação dos dados.
4. Exibir data, fonte, incertezas e aviso de subnotificação.
5. Nunca afirmar que um caminho é seguro, nem inferir risco individual a partir de crimes por região.
