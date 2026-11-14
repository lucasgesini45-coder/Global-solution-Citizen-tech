# Citizen Mobilidade — FIAP Global Solution 2026

Plataforma acadêmica de orientação cidadã sobre transporte público, benefícios e acessibilidade. **Não é canal oficial.**

## Arquitetura
- **backend/**: núcleo Python, busca e API FastAPI
- **frontend/**: Expo, React Native e TypeScript para web e smartphones
- **docs/**: arquitetura, uso de IA e plano de testes

## Executar no terminal (requisito FIAP)
```powershell
python backend/src/sistema.py
```

## Executar API
```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.src.api:app --reload
```
API: http://localhost:8000/docs

## Testes
```powershell
python -m pytest backend/tests -v
cd "global solution part2 - tarifas"
python -m pytest -v
```

## Executar site
```powershell
cd frontend
npm install
npx expo start --web
```

Para conectar um smartphone ao backend, defina `EXPO_PUBLIC_API_URL` com o endereço IP acessível do servidor, não com localhost.

**Importante:** Os registros são exemplos não verificados, bloqueados para respostas. Falta inserir 15 orientações verificadas, testar 12 perguntas, comparar 2 estratégias, medir resultados e concluir a avaliação de usabilidade. Rotas e tarifas reais não estão implementadas.
