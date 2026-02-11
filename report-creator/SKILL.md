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

Antes de escrever, le TODOS os outputs dos steps anteriores:

```bash
ls {execution_dir}/
cat {execution_dir}/step_001_output.md
cat {execution_dir}/step_002_output.md
```

- Le TODOS os ficheiros step_NNN_output.md disponiveis
- Identifica dados concretos: IDs, valores, listas, metricas
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
- NAO inventes dados - usa apenas o que foi recolhido nos steps anteriores
- Se um step falhou ou nao tem dados, menciona isso no relatorio

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
- Dados dependem da qualidade dos outputs dos steps anteriores
- Graficos e visualizacoes nao sao suportados (apenas tabelas markdown)
