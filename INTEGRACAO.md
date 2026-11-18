# Como integrar o assistente ao repositório

Este pacote tem a **estrutura do repositório** (`backend/`, `docs/`). Siga os passos na ordem.

## 1. Copiar os arquivos
Copie o conteúdo deste pacote para a **raiz do repositório** (a pasta que contém `backend/`, `frontend/` e `docs/`), **substituindo** os arquivos que o Antigravity começou a escrever:
`backend/src/assistente/*`, `backend/tests/assistente/__init__.py`, `backend/data/assistente/perguntas_teste.json`, `backend/requirements.txt`, `docs/assistente_fontes.md` e `docs/duvidas.md`.

> Os arquivos do Antigravity aparecem com **acentos corrompidos** na gravação (ex.: `dÃºvidas`). Os desta entrega estão em UTF-8 limpo. Depois de copiar, abra `backend/src/assistente/config.py` e confirme que o texto `TEXTO_FALLBACK` começa com "Não encontrei" (e não "NÃ£o encontrei").

## 2. Instalar as dependências
```
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
Se o `pip` recusar `numpy==2.5.3`, use a versão que estiver instalada no seu ambiente (ver `docs/duvidas.md`, D-04).

## 3. Rodar os testes do assistente
```
cd backend
python -m pytest tests/assistente
```
Esperado: **46 testes aprovados** (no ambiente do Claude). Se algum falhar na sua máquina, não altere os testes: abra uma linha em `docs/duvidas.md` e me envie a mensagem de erro.

## 4. Ligar o assistente à API (2 linhas)
Em `backend/src/api.py` (o módulo que expõe `app`, usado em `python -m uvicorn src.api:app --reload`), acrescente:
```
from src.assistente.rotas_api import roteador as roteador_assistente
app.include_router(roteador_assistente)
```
A primeira linha vai junto dos outros `import`; a segunda, **depois** de `app` ser criado (junto dos outros `include_router`, se houver). Se `api.py` for uma pasta, use o `__init__.py` ou o arquivo onde `app` é criado.
Teste: suba a API e abra `/docs`; devem aparecer `POST /assistente/perguntar` e `GET /assistente/saude`.

## 5. Ligar o assistente ao terminal (menu do `sistema.py`)
Em `backend/src/sistema.py`:
1. No topo, junto dos imports: `from src.assistente.cli import abrir_assistente` (se o arquivo usa imports relativos, use o mesmo estilo dele).
2. Acrescente uma opção chamada **"Assistente de dúvidas"** no menu, **seguindo o estilo das opções que já existem** (numeração e textos), e, quando for escolhida, chame `abrir_assistente()`.

`abrir_assistente()` imprime as boas-vindas e fica lendo perguntas até o usuário digitar `sair`, quando devolve o controle ao menu.

## 6. Atualizar `.gitignore`, `README.md` e `docs/uso_ia.md`
- `.gitignore`: acrescente a linha `backend/models/*.joblib`
- `README.md`: acrescente uma seção **Assistente de dúvidas** com: o que é (tira dúvidas sobre rotas, tarifas e histórico/privacidade, usando scikit-learn), os comandos abaixo e o aviso `Respostas do assistente ainda não revisadas pela equipe.`
  - Terminal: `cd backend` e `python src/sistema.py` (opção "Assistente de dúvidas")
  - Avaliação: `cd backend` e `python -m src.assistente.avaliacao`
  - Calibração: `cd backend` e `python -m src.assistente.calibracao`
- `docs/uso_ia.md`: acrescente as linhas de `docs/uso_ia_assistente.md`.

## 7. Regressão (obrigatória)
Rode a suíte **existente** do projeto antes e depois da integração e confirme que nenhum teste que passava passou a falhar. O Claude não teve acesso a essa suíte.

## 8. Regerar os relatórios na sua máquina
Os relatórios que vêm no pacote foram gerados no ambiente do Claude. Regere-os no seu:
```
cd backend
python -m src.assistente.avaliacao
python -m src.assistente.calibracao
```

## 9. O que a equipe ainda precisa fazer
1. **Revisar as 15 respostas e as 180 frases** em `backend/data/assistente/base_conhecimento.json`; depois, trocar `revisada_pela_equipe` para `true` (o modelo é re-treinado sozinho no próximo início).
2. **Conferir as linhas com ⚠** em `docs/assistente_fontes.md` (R04, H03, H04 e H05) e a existência (ou não) de conta/login no app.
3. **Decidir o limiar** (`LIMIAR_CONFIANCA`, hoje 0.40) com base em `docs/relatorio_calibracao_assistente.md`.
4. **Melhorar R02 e R03**: com a base inicial, a pergunta sobre "digitar o nome da rua em vez de marcar no mapa" foi respondida com R02. A correção é acrescentar redações novas de treino nessas duas intenções e testar com perguntas novas.
5. **Manter a base atualizada** quando uma função do app mudar (resposta e `status_funcionalidade`).
