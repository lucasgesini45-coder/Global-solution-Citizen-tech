# Esquema do Banco de Dados SQL Único (Citizen Mobilidade)

Documento gerado automaticamente por introspecção do banco SQLite (`PRAGMA table_info`, `foreign_key_list`, `index_list`).

---

## Tabela `cache_geocodificacao`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `consulta` | `TEXT` | Não | `-` | Sim |
| `resposta_json` | `TEXT` | Sim | `-` | Não |
| `obtido_em` | `TEXT` | Sim | `-` | Não |

---

## Tabela `consentimentos`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `usuario_id` | `TEXT` | Sim | `-` | Sim |
| `finalidade` | `TEXT` | Sim | `-` | Sim |
| `concedido` | `INTEGER` | Sim | `-` | Não |
| `texto_versao` | `TEXT` | Sim | `-` | Não |
| `atualizado_em` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `usuario_id` | `usuarios` | `id` | `CASCADE` |

---

## Tabela `conversas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `TEXT` | Não | `-` | Sim |
| `usuario_id` | `TEXT` | Sim | `-` | Não |
| `criado_em` | `TEXT` | Sim | `-` | Não |
| `atualizado_em` | `TEXT` | Sim | `-` | Não |
| `titulo` | `TEXT` | Não | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `usuario_id` | `usuarios` | `id` | `CASCADE` |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_conversas_usuario` | Não | Não |

---

## Tabela `conversas_contexto`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `conversa_id` | `TEXT` | Não | `-` | Sim |
| `ultima_intencao_id` | `TEXT` | Não | `-` | Não |
| `ultima_busca_id` | `INTEGER` | Não | `-` | Não |
| `acao_pendente` | `TEXT` | Não | `-` | Não |
| `pendente_expira_em` | `TEXT` | Não | `-` | Não |
| `atualizado_em` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `ultima_busca_id` | `historico_buscas` | `id` | `SET NULL` |
| `conversa_id` | `conversas` | `id` | `CASCADE` |

---

## Tabela `feedback_mensagens`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `mensagem_id` | `INTEGER` | Não | `-` | Sim |
| `util` | `INTEGER` | Sim | `-` | Não |
| `criado_em` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `mensagem_id` | `mensagens` | `id` | `CASCADE` |

---

## Tabela `feeds`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `INTEGER` | Não | `-` | Sim |
| `sistema` | `TEXT` | Sim | `-` | Não |
| `fonte_url` | `TEXT` | Sim | `-` | Não |
| `arquivo_nome` | `TEXT` | Sim | `-` | Não |
| `arquivo_sha256` | `TEXT` | Sim | `-` | Não |
| `versao` | `TEXT` | Sim | `-` | Não |
| `validade_inicio` | `TEXT` | Não | `-` | Não |
| `validade_fim` | `TEXT` | Não | `-` | Não |
| `origem_dados` | `TEXT` | Sim | `-` | Não |
| `importado_em` | `TEXT` | Sim | `-` | Não |
| `ativo` | `INTEGER` | Sim | `0` | Não |
| `n_paradas` | `INTEGER` | Sim | `-` | Não |
| `n_linhas` | `INTEGER` | Sim | `-` | Não |
| `n_padroes` | `INTEGER` | Sim | `-` | Não |
| `n_viagens` | `INTEGER` | Sim | `-` | Não |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_feeds_ativo` | Sim | Sim |

---

## Tabela `historico_buscas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `INTEGER` | Não | `-` | Sim |
| `sessao_id` | `TEXT` | Sim | `-` | Não |
| `criado_em` | `TEXT` | Sim | `-` | Não |
| `origem_lat` | `REAL` | Sim | `-` | Não |
| `origem_lon` | `REAL` | Sim | `-` | Não |
| `destino_lat` | `REAL` | Sim | `-` | Não |
| `destino_lon` | `REAL` | Sim | `-` | Não |
| `partida` | `TEXT` | Sim | `-` | Não |
| `n_rotas` | `INTEGER` | Sim | `-` | Não |
| `erro_codigo` | `TEXT` | Não | `-` | Não |
| `origem_nome` | `TEXT` | Não | `-` | Não |
| `destino_nome` | `TEXT` | Não | `-` | Não |
| `feed_versao` | `TEXT` | Não | `-` | Não |
| `regra_tarifa_versao` | `TEXT` | Não | `-` | Não |
| `tempo_calculo_ms` | `INTEGER` | Não | `-` | Não |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_historico_sessao` | Não | Não |

---

## Tabela `historico_rota_linhas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `rota_id` | `INTEGER` | Sim | `-` | Sim |
| `posicao` | `INTEGER` | Sim | `-` | Sim |
| `linha_id` | `TEXT` | Sim | `-` | Não |
| `nome_linha` | `TEXT` | Sim | `-` | Não |
| `modal` | `TEXT` | Sim | `-` | Não |
| `operador` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `rota_id` | `historico_rotas` | `id` | `CASCADE` |

---

## Tabela `historico_rotas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `INTEGER` | Não | `-` | Sim |
| `busca_id` | `INTEGER` | Sim | `-` | Não |
| `ordem` | `INTEGER` | Sim | `-` | Não |
| `saida_s` | `INTEGER` | Sim | `-` | Não |
| `chegada_s` | `INTEGER` | Sim | `-` | Não |
| `tempo_total_s` | `INTEGER` | Sim | `-` | Não |
| `espera_s` | `INTEGER` | Sim | `-` | Não |
| `caminhada_m` | `INTEGER` | Sim | `-` | Não |
| `baldeacoes` | `INTEGER` | Sim | `-` | Não |
| `custo_centavos` | `INTEGER` | Não | `-` | Não |
| `custo_confirmado` | `INTEGER` | Sim | `-` | Não |
| `escolhida` | `INTEGER` | Sim | `0` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `busca_id` | `historico_buscas` | `id` | `CASCADE` |

---

## Tabela `linhas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `id` | `TEXT` | Sim | `-` | Sim |
| `nome_curto` | `TEXT` | Sim | `-` | Não |
| `nome_longo` | `TEXT` | Não | `-` | Não |
| `operador` | `TEXT` | Sim | `-` | Não |
| `modal` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `feeds` | `id` | `CASCADE` |

---

## Tabela `mensagens`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `INTEGER` | Não | `-` | Sim |
| `conversa_id` | `TEXT` | Sim | `-` | Não |
| `papel` | `TEXT` | Sim | `-` | Não |
| `texto` | `TEXT` | Sim | `-` | Não |
| `criado_em` | `TEXT` | Sim | `-` | Não |
| `intencao_id` | `TEXT` | Não | `-` | Não |
| `tema` | `TEXT` | Não | `-` | Não |
| `confianca` | `REAL` | Não | `-` | Não |
| `fallback` | `INTEGER` | Não | `-` | Não |
| `usou_contexto` | `INTEGER` | Não | `-` | Não |
| `tempo_ms` | `INTEGER` | Não | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `conversa_id` | `conversas` | `id` | `CASCADE` |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_mensagens_conversa` | Não | Não |

---

## Tabela `meta`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `chave` | `TEXT` | Não | `-` | Sim |
| `valor` | `TEXT` | Sim | `-` | Não |

---

## Tabela `padrao_paradas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `padrao_id` | `INTEGER` | Sim | `-` | Sim |
| `posicao` | `INTEGER` | Sim | `-` | Sim |
| `parada_id` | `TEXT` | Sim | `-` | Não |
| `deslocamento_s` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `paradas` | `feed_id` | `CASCADE` |
| `parada_id` | `paradas` | `id` | `CASCADE` |
| `feed_id` | `padroes` | `feed_id` | `CASCADE` |
| `padrao_id` | `padroes` | `id` | `CASCADE` |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_padrao_paradas` | Não | Não |

---

## Tabela `padroes`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `id` | `INTEGER` | Sim | `-` | Sim |
| `linha_id` | `TEXT` | Sim | `-` | Não |
| `sentido` | `TEXT` | Sim | `-` | Não |
| `n_paradas` | `INTEGER` | Sim | `-` | Não |
| `duracao_s` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `linhas` | `feed_id` | `CASCADE` |
| `linha_id` | `linhas` | `id` | `CASCADE` |

---

## Tabela `paradas`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `id` | `TEXT` | Sim | `-` | Sim |
| `nome` | `TEXT` | Sim | `-` | Não |
| `lat` | `REAL` | Sim | `-` | Não |
| `lon` | `REAL` | Sim | `-` | Não |
| `celula_x` | `INTEGER` | Sim | `-` | Não |
| `celula_y` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `feeds` | `id` | `CASCADE` |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_paradas_celula` | Não | Não |

---

## Tabela `perguntas_sem_resposta`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `INTEGER` | Não | `-` | Sim |
| `texto` | `TEXT` | Sim | `-` | Não |
| `criado_em` | `TEXT` | Sim | `-` | Não |
| `confianca` | `REAL` | Sim | `-` | Não |
| `intencao_sugerida` | `TEXT` | Não | `-` | Não |
| `revisada` | `INTEGER` | Sim | `0` | Não |

---

## Tabela `preferencias`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `usuario_id` | `TEXT` | Não | `-` | Sim |
| `caminhada_max_m` | `INTEGER` | Sim | `1000` | Não |
| `baldeacoes_max` | `INTEGER` | Não | `-` | Não |
| `orcamento_max_centavos` | `INTEGER` | Não | `-` | Não |
| `velocidade_caminhada_ms` | `REAL` | Sim | `1.2` | Não |
| `perfil_tarifario` | `TEXT` | Sim | `'padrao'` | Não |
| `atualizado_em` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `usuario_id` | `usuarios` | `id` | `CASCADE` |

---

## Tabela `preferencias_acessibilidade`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `usuario_id` | `TEXT` | Sim | `-` | Sim |
| `necessidade` | `TEXT` | Sim | `-` | Sim |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `usuario_id` | `usuarios` | `id` | `CASCADE` |

---

## Tabela `schema_versao`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `versao` | `INTEGER` | Não | `-` | Sim |
| `nome` | `TEXT` | Sim | `-` | Não |
| `aplicada_em` | `TEXT` | Sim | `-` | Não |

---

## Tabela `servicos`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `id` | `TEXT` | Sim | `-` | Sim |
| `dia0` | `INTEGER` | Sim | `-` | Não |
| `dia1` | `INTEGER` | Sim | `-` | Não |
| `dia2` | `INTEGER` | Sim | `-` | Não |
| `dia3` | `INTEGER` | Sim | `-` | Não |
| `dia4` | `INTEGER` | Sim | `-` | Não |
| `dia5` | `INTEGER` | Sim | `-` | Não |
| `dia6` | `INTEGER` | Sim | `-` | Não |
| `inicio` | `TEXT` | Sim | `-` | Não |
| `fim` | `TEXT` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `feeds` | `id` | `CASCADE` |

---

## Tabela `servicos_excecoes`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `servico_id` | `TEXT` | Sim | `-` | Sim |
| `data` | `TEXT` | Sim | `-` | Sim |
| `tipo` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `servicos` | `feed_id` | `CASCADE` |
| `servico_id` | `servicos` | `id` | `CASCADE` |

---

## Tabela `tarifas_base`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `regra_id` | `INTEGER` | Sim | `-` | Sim |
| `modal` | `TEXT` | Sim | `-` | Sim |
| `centavos` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `regra_id` | `tarifas_regras` | `id` | `CASCADE` |

---

## Tabela `tarifas_integracao`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `regra_id` | `INTEGER` | Sim | `-` | Sim |
| `de_modal` | `TEXT` | Sim | `-` | Sim |
| `para_modal` | `TEXT` | Sim | `-` | Sim |
| `centavos` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `regra_id` | `tarifas_regras` | `id` | `CASCADE` |

---

## Tabela `tarifas_perfis`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `regra_id` | `INTEGER` | Sim | `-` | Sim |
| `perfil` | `TEXT` | Sim | `-` | Sim |
| `percentual` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `regra_id` | `tarifas_regras` | `id` | `CASCADE` |

---

## Tabela `tarifas_regras`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `INTEGER` | Não | `-` | Sim |
| `versao` | `TEXT` | Sim | `-` | Não |
| `fonte_descricao` | `TEXT` | Sim | `-` | Não |
| `fonte_url` | `TEXT` | Sim | `-` | Não |
| `verificada_em` | `TEXT` | Não | `-` | Não |
| `confirmada` | `INTEGER` | Sim | `-` | Não |
| `origem_dados` | `TEXT` | Sim | `-` | Não |
| `vigencia_inicio` | `TEXT` | Sim | `-` | Não |
| `vigencia_fim` | `TEXT` | Não | `-` | Não |
| `janela_s` | `INTEGER` | Sim | `-` | Não |
| `max_embarques_por_janela` | `INTEGER` | Sim | `-` | Não |
| `janela_integrada_s` | `INTEGER` | Não | `-` | Não |
| `max_onibus_integrada` | `INTEGER` | Não | `-` | Não |
| `max_trilho_integrada` | `INTEGER` | Não | `-` | Não |

---

## Tabela `usuarios`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `id` | `TEXT` | Não | `-` | Sim |
| `token_hash` | `TEXT` | Sim | `-` | Não |
| `criado_em` | `TEXT` | Sim | `-` | Não |
| `ultimo_acesso_em` | `TEXT` | Sim | `-` | Não |

---

## Tabela `viagens`

### Colunas
| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |
|---|---|---|---|---|
| `feed_id` | `INTEGER` | Sim | `-` | Sim |
| `id` | `TEXT` | Sim | `-` | Sim |
| `padrao_id` | `INTEGER` | Sim | `-` | Não |
| `servico_id` | `TEXT` | Sim | `-` | Não |
| `inicio_s` | `INTEGER` | Sim | `-` | Não |

### Chaves Estrangeiras
| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |
|---|---|---|---|
| `feed_id` | `servicos` | `feed_id` | `CASCADE` |
| `servico_id` | `servicos` | `id` | `CASCADE` |
| `feed_id` | `padroes` | `feed_id` | `CASCADE` |
| `padrao_id` | `padroes` | `id` | `CASCADE` |

### Índices
| Nome do Índice | Único? | Parcial? |
|---|---|---|
| `idx_viagens_padrao` | Não | Não |
| `idx_viagens_servico` | Não | Não |

---
