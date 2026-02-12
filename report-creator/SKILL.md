---
name: report-creator
description: Cria relatórios estruturados a partir de dados recolhidos. Gera ficheiros markdown profissionais com tabelas, métricas e análise. O relatório é guardado automaticamente no workspace e devolvido no resultado da tarefa. Usar SEMPRE que o objetivo seja gerar um relatório, resumo ou documento com dados. NÃO usar skills de Drive para criar relatórios - o Drive é apenas para quando o utilizador pede explicitamente guardar num serviço externo.
---

# Report Creator

Skill para criacao de relatorios estruturados a partir de dados recolhidos em steps anteriores do workflow.

## Quando Usar

Use esta skill quando o utilizador pedir:
- Criar um relatorio com dados recolhidos
- Gerar um resumo ou documento com metricas
- Compilar resultados de pesquisas ou consultas a APIs
- Formatar dados em tabelas ou documentos estruturados

## Processo

### 1. Recolher Dados

Antes de escrever, le TODOS os dados dos steps anteriores. Os dados estao organizados em dois tipos de ficheiros:

**a) Dados estruturados — `steps.json`**

```bash
cat {execution_dir}/steps.json
```

Este ficheiro contem TODOS os steps com: IDs recolhidos, metricas, items, ferramentas usadas, duracao e estado. Estrutura por step:
- `ids` — listas de IDs (ex: `contract_ids`, `email_ids`)
- `metrics` — valores numericos (ex: `total`, `count`)
- `items` — lista de objectos com dados detalhados (contratos, emails, etc.)
- `key_values` — outros pares chave-valor extraidos
- `status` — "completed" ou "failed"
- `summary` — resumo do step

**b) Relatorios narrativos — `step_NNN_report.md`**

```bash
cat {execution_dir}/step_001_report.md
cat {execution_dir}/step_002_report.md
```

Cada step tem um mini-relatorio com contexto e analise do que foi executado.

**c) Dados overflow (se existirem) — `step_NNN_items.json`**

Se um step recolheu muitos items (>20), os detalhes completos estao num ficheiro separado:

```bash
cat {execution_dir}/step_001_items.json
```

**Processo:**
- Le SEMPRE `steps.json` primeiro — e a fonte principal de dados
- Le os `step_NNN_report.md` para contexto narrativo
- Verifica se existem `step_NNN_items.json` para dados completos
- NAO comeces a escrever sem ter lido todos os dados

### 2. Estruturar o Relatorio

O relatorio DEVE seguir esta estrutura:

```markdown
# [Titulo do Relatorio]

**Data:** YYYY-MM-DD | **Gerado por:** WhiteFlow AI

## Resumo Executivo

[2-3 frases com as conclusoes principais e numeros-chave]

## Dados Recolhidos

[Tabelas markdown com os dados - NUNCA omitir registos]

## Analise

[Interpretacao dos dados, padroes identificados, destaques]

## Conclusoes

[Pontos-chave e recomendacoes se aplicavel]
```

### 3. Guardar

Usa `file_write` para criar o relatorio no workspace:

```
file_write(path="relatorio.md", content="# Titulo...\n\n...")
```

- O path DEVE ser `relatorio.md` (ou nome descritivo com extensao `.md`)
- NUNCA uses tools de Drive, email ou upload externo
- O ficheiro no workspace e automaticamente devolvido no resultado da tarefa

## Regras

### Dados
- Inclui TODOS os dados recolhidos - nunca omitas registos ou linhas
- Usa tabelas markdown para dados tabulares (contratos, metricas, listas)
- NAO inventes dados - usa apenas o que esta em `steps.json` e nos ficheiros de report/overflow
- Se um step tem `status: "failed"` em `steps.json`, menciona isso no relatorio
- Usa os `items` de `steps.json` (ou `step_NNN_items.json` para overflow) como fonte de dados para tabelas

### Formatacao
- Escreve em Portugues de Portugal
- Usa headers hierarquicos (## e ###) para organizar seccoes
- Tabelas devem ter headers claros e alinhamento consistente
- Numeros e valores monetarios devem estar formatados (ex: 1.234,56 EUR)

### Output
- Usa SEMPRE `file_write` - nunca `run_bash` com heredoc
- Extensao DEVE ser `.md` (nunca `.txt`)
- O ficheiro e o unico deliverable deste step

## Exemplo de Tabela de Dados

```markdown
## Contratos Ativos

| # | ID | Descricao | Valor | Data Inicio |
|---|---|---|---|---|
| 1 | 12345 | Servico de limpeza | 15.000,00 EUR | 2025-01-15 |
| 2 | 12346 | Manutencao AVAC | 8.500,00 EUR | 2025-03-01 |
| 3 | 12347 | Seguranca | 22.000,00 EUR | 2025-02-10 |

**Total:** 3 contratos | **Valor total:** 45.500,00 EUR
```

## Limitacoes

- O relatorio e gerado em formato markdown
- Dados dependem da qualidade dos dados em steps.json e mini-reports
- Graficos e visualizacoes nao sao suportados (apenas tabelas markdown)
