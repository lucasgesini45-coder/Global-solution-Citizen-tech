# Documento de IA: Assistente de dúvidas do Citizen Mobilidade

## 1. Objetivo e limites
O assistente tira dúvidas sobre o **uso do app** em três temas: **rota**, **tarifas** e **histórico/privacidade**. Ele **classifica** a pergunta do usuário em uma de 15 intenções e devolve a **resposta fixa** cadastrada para ela. Ele **não gera texto**, não consulta serviços externos e não tem memória de conversa. Acessibilidade e segurança **não** são temas do assistente.

## 2. Algoritmo utilizado
Classificador de intenção em um `Pipeline` do scikit-learn com duas etapas, nesta ordem:
- `tfidf`: `TfidfVectorizer` com `lowercase=True`, `strip_accents="unicode"`, `ngram_range=(1, 2)`, `sublinear_tf=True`, `min_df=1`, sem stop words.
- `clf`: `LogisticRegression` com `C=10.0`, `max_iter=1000`, `solver="lbfgs"`, `random_state=42`.

Todos os parâmetros ficam em `backend/src/assistente/config.py`.

## 3. Dados de treinamento
180 frases (15 intenções × 12 frases) em `backend/data/assistente/base_conhecimento.json`, escritas por IA e **ainda não revisadas pela equipe**. A base também guarda a resposta, o status da funcionalidade (`implementada`, `parcial` ou `planejada`) e os arquivos do repositório que confirmam cada fato.

## 4. Variáveis de entrada e de saída
- **Entrada:** `pergunta` (texto de 3 a 300 caracteres, após remover espaços das pontas).
- **Saída:** `resposta`, `intencao_id` (nulo no fallback), `tema` (nulo no fallback), `confianca` (maior probabilidade, 4 casas), `sugestoes` (vazia quando há resposta; no fallback, as 3 perguntas canônicas mais prováveis) e `aviso` (somente nas respostas de tarifas: "Plataforma acadêmica, não é canal oficial.").

## 5. Pipeline de dados (reaproveitado do Challenge)
| Etapa | O que faz | Módulo |
|---|---|---|
| Coleta | Lê e valida a base e as perguntas de teste (regras V-01 a V-10 e A-01 a A-06) | `base.py` |
| Pré-processamento | `normalizar_para_comparacao` (comparar textos) e normalização do próprio `TfidfVectorizer` | `preprocessamento.py` |
| Treino | Treina o `Pipeline` com as 180 frases | `treino.py`, `modelo.py` |
| Previsão | Calcula as probabilidades, aplica o limiar e devolve resposta ou fallback | `previsao.py` |
| Entrega | API (`/assistente`) e terminal (menu do `sistema.py`) | `rotas_api.py`, `cli.py` |

**Divisão treino/teste:** não é aleatória. O treino usa só as frases da base; o teste usa só as 12 perguntas de `perguntas_teste.json`, e o código **barra** qualquer coincidência entre as duas (regra V-07).
**Atualização periódica:** não há agendamento. O modelo salvo em `backend/models/assistente_intencoes.joblib` é carregado quando válido e **re-treinado** quando o arquivo falta, está corrompido ou foi gerado por outra versão da base (hash SHA-256) ou do scikit-learn.

## 6. Métricas de avaliação
Top-1, top-3 e tempo de resposta, geradas por `python -m src.assistente.avaliacao` em `docs/relatorio_avaliacao_assistente.md`. Resultado da geração inicial (12 perguntas): **top-1 8/12 (66,7%)**, **top-3 12/12 (100%)**, tempo médio abaixo de 1 ms. Esses números dependem do ambiente e devem ser regerados pela equipe.

## 7. Limiar de confiança e calibração
`LIMIAR_CONFIANCA = 0.40` (valor inicial). `python -m src.assistente.calibracao` gera `docs/relatorio_calibracao_assistente.md` com 13 limiares. Na geração inicial, em 0,40 houve 8 acertos, 1 erro e 3 perguntas no fallback; a partir de 0,50 não houve erros, mas 7 das 12 perguntas caíram no fallback. **A decisão de mudar o limiar é da equipe.**

## 8. Integração com a plataforma
- **API:** `POST /assistente/perguntar` e `GET /assistente/saude` (documentadas em `/docs`).
- **Terminal:** opção "Assistente de dúvidas" no menu de `python src/sistema.py`.
- **Frequência:** a cada pergunta; não há agendamento.

## 9. Privacidade
Nenhuma pergunta é guardada em banco, arquivo ou log. Isso é verificado por teste automatizado (T-A15).

## 10. Limitações conhecidas
- Só português do Brasil; cada pergunta é independente (sem memória de conversa).
- O assistente só conhece o que está na base: perguntas fora dela caem no fallback ou, com menos sorte, são associadas a uma intenção parecida.
- Há erro conhecido: com a base inicial, a pergunta "Dá pra digitar o nome da rua em vez de marcar no mapa?" foi respondida com a intenção R02 (mapa) em vez de R03 (endereço), com confiança acima do limiar. Ampliar as frases de treino de R02 e R03 com redações novas **e** criar um conjunto de teste novo é a correção indicada.
- Avaliação com apenas 12 perguntas: os percentuais são apenas indicativos; R02, T05 e H05 não têm pergunta de teste.
- As respostas refletem o estado do app em 12/11/2026 e **devem ser atualizadas** quando uma função mudar (ver status em `assistente_fontes.md`).
- Respostas e frases escritas por IA, ainda não revisadas pela equipe.
