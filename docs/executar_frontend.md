# Executar o Citizen Mobilidade (web e celular)

## Requisitos
- Python 3.13
- Node.js LTS e npm
- Duas janelas de terminal abertas na **raiz do repositório**

## 1. Backend
```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.src.api:app --reload
```

Verifique http://127.0.0.1:8000/docs. Devem existir `POST /consultar` e `POST /rotas`.

## 2. Frontend web (novo terminal)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run web
```

O Expo exibe no terminal a URL para abrir no navegador (normalmente http://localhost:8081).

## 3. Frontend no celular
O celular precisa acessar a API pela rede. O endereço 127.0.0.1 do telefone não é o PC.
- Descubra o IPv4 local do computador com `ipconfig`
- No arquivo `frontend/.env`, configure `EXPO_PUBLIC_API_URL=http://IP_DO_PC:8000`
- Inicie a API para conexões de rede com `python -m uvicorn backend.src.api:app --host 0.0.0.0 --port 8000`
- Ajuste o CORS para as origens efetivamente utilizadas, se necessário, e permita a porta no firewall apenas em rede confiável
- Em `frontend`, use `npm start` e siga as instruções do Expo Go

**Não exponha a API de desenvolvimento diretamente na internet.**

## O que testar
1. A tela abre em desktop e largura de celular.
2. A pesquisa vazia exibe aviso.
3. Perguntas sobre cartão retornam o estado de base sem resposta verificada (base atual contém apenas rascunhos).
4. A aba Planejar rota apresenta origens e destinos fictícios.
5. Alfa → Destino com perfil padrão retorna alternativas fictícias.
6. Origem e destino iguais são bloqueados.
7. A API não exibe tarifas de demonstração como tarifas oficiais.

## Limitações conhecidas
- A base atual tem somente 3 orientações em rascunho. Ainda faltam ao menos 15 entradas verificadas, com fontes confiáveis.
- A rede, os horários e as tarifas em `/rotas` são dados fictícios.
- A demonstração usa partida fixa de 09/11/2026 às 08:00 para ser reproduzível.
- Não há integração com GTFS/serviços externos de transporte nesta etapa.
