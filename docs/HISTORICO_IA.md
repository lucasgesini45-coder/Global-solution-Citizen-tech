# Histórico opcional do agente — PostgreSQL

## Finalidade e privacidade

A interface exibe uma caixa de consentimento desmarcada por padrão. O usuário pode conversar sem aceitar, desativar a coleta e excluir os registros da sessão. O backend só registra novas interações quando `consentimento_historico=true`. A sessão é identificada por UUID aleatório, sem cadastro. No navegador o identificador fica no sessionStorage da aba para permitir exclusão após recarregar a página; a autorização não é persistida. No mobile, a sessão é mantida em memória. Não há recuperação de sessões após fechar a aba/app.

O sistema não envia coordenadas GPS, IP, cabeçalhos, geometria ou endereços estruturados para esta tabela. Interações sobre rotas e textos com indícios de dados pessoais ou sensíveis são registrados apenas como metadados (sem pergunta/resposta). O filtro é conservador, mas não reconhece todos os dados pessoais em texto livre; o conteúdo não deve ser tratado como anônimo. Não use informações pessoais na demonstração, não publique exportações de conversas e restrinja acesso à equipe responsável. Revise a política de privacidade antes de disponibilizar ao público.

A retenção é de 30 dias. Registros expirados são excluídos ao gravar ou consultar o histórico; configure limpeza agendada diariamente para assegurar eliminação também durante períodos sem uso. Backups do provedor têm política própria; confirme essa política. O aplicativo não modifica logs externos do provedor.

## Render

1. Abra o serviço web do projeto e confirme a branch de deploy.
2. Crie um PostgreSQL no mesmo workspace/região, ou use um banco PostgreSQL autorizado existente. Confirme custos e disponibilidade antes de contratar.
3. No serviço web, em Environment, configure **CHAT_HISTORY_DATABASE_URL** com a Internal Database URL do banco. Não coloque a URL no GitHub, Expo ou variável EXPO_PUBLIC.
4. Gere um token administrativo aleatório de pelo menos 32 caracteres, por exemplo localmente:
   ```powershell
   python -c "import secrets;print(secrets.token_urlsafe(48))"
   ```
   Configure **CHAT_HISTORY_ADMIN_TOKEN** apenas no backend. Não compartilhe em chat ou commit.
5. Faça deploy da branch que contém esta funcionalidade. A tabela `citizen_ia_interacoes` é criada na primeira gravação autônoma ou consulta administrativa. O usuário do banco precisa de permissão para criar a tabela, índices e ler/inserir/excluir registros.
6. Configure um job diário (por exemplo, Render Cron Job) no mesmo repositório e com a mesma variável de banco. Comando a partir da raiz: `python -m backend.src.historico_ia`. Verifique que o job executou. Sem job, a purga ocorre somente quando houver atividade. Em bancos existentes, faça backup e revise permissões.

## Consultar o histórico

Use PowerShell. Digite o token localmente sem registrá-lo no repositório. No exemplo, substitua a URL pela URL pública da API Python se estiver em outro serviço.

```powershell
$secure = Read-Host "Token administrativo" -AsSecureString
$token = [System.Net.NetworkCredential]::new("", $secure).Password
$dados = Invoke-RestMethod -Uri "https://citizen-tech-mobilidade.onrender.com/agente/historico/admin?limit=100" -Headers @{ Authorization = "Bearer $token" }
$dados.resumo
$dados.categorias
$dados.interacoes | Format-Table criado_em,categoria,origem_resposta,respondida,pergunta
Remove-Variable token,secure
```

Use `offset` para paginar. O endpoint não é público; sem token válido retorna HTTP 401. Se não houver banco configurado, a coleta fica indisponível e o chat continua normalmente. Não inclua o token no frontend. O endpoint POST /agente/historico/apagar recebe o UUID secreto da sessão e exclui apenas essa sessão.

A métrica `respondida` indica que o agente produziu uma resposta de uma categoria considerada atendida. Não é uma medida de correção, satisfação ou assertividade; essas exigem avaliação independente das respostas. O histórico não registra a pergunta quando o filtro a considera sensível.

## Testes

```powershell
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests -v
cd frontend
npx tsc --noEmit
```

Teste manualmente: consentimento desativado, consentimento ativado, pergunta sem dados pessoais, pergunta com texto sensível, consulta administrativa autenticada, exclusão da sessão e falha de banco. Confirme a existência da tabela e os registros no PostgreSQL de homologação antes da apresentação.
