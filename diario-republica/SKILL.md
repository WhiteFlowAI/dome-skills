---
name: diario-republica
description: Pesquisa legislacao e publicacoes oficiais no Diario da Republica Eletronico (dre.pt). Use para encontrar leis, decretos, portarias e outros atos normativos portugueses.
---

# Diario da Republica - Legislacao Portuguesa

Skill para pesquisar e consultar publicacoes oficiais no Diario da Republica Eletronico (dre.pt).

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Publicacoes oficiais do Diario da Republica
- Legislacao portuguesa (leis, decretos-lei, portarias)
- Despachos e diplomas legais
- Nomeacoes e exoneracoes publicadas
- Atos normativos de entidades publicas
- Conteudo publicado numa data especifica no DR

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/diario-republica")
from diario_republica import get_daily_ids, get_daily_content, search_dispatches, get_dispatch_detail
```

## Operacoes Disponiveis

### 1. Obter IDs do DR por Data

```python
import sys
sys.path.insert(0, "/var/cache/skills/diario-republica")
from diario_republica import get_daily_ids

# Obter IDs das publicacoes de uma data especifica
result = get_daily_ids("2025-01-15")

print(f"Total: {result.get('total_found', 0)} publicacoes")
for dr in result.get('dr_list', []):
    print(f"- DR ID: {dr.get('dbId')} - {dr.get('serie')}")
```

**IMPORTANTE**: Use esta funcao como primeiro passo para depois obter conteudo detalhado.

### 2. Obter Conteudo Completo por Data (Simplificado)

```python
import sys
sys.path.insert(0, "/var/cache/skills/diario-republica")
from diario_republica import get_daily_content

# Obter todo o conteudo do DR de uma data (uma so chamada)
result = get_daily_content("2025-01-15")

print(f"Total series: {result.get('total_series', 0)}")
print(f"Total despachos: {result.get('total_dispatches', 0)}")

for pub in result.get('publications', []):
    print(f"\n{pub.get('serie')} - {pub.get('dispatches_count')} despachos")
    for d in pub.get('dispatches', [])[:3]:
        print(f"  - {d.get('Tipo', '')} {d.get('Numero', '')}")
```

**RECOMENDADO**: Use esta funcao quando precisar de todo o conteudo de uma data.

### 3. Pesquisar Despachos num DR

```python
import sys
sys.path.insert(0, "/var/cache/skills/diario-republica")
from diario_republica import search_dispatches

# Pesquisar despachos num DR especifico
result = search_dispatches(dr_id="945553807")

print(f"Total: {result.get('total_count', 0)} despachos")
for d in result.get('dispatches', [])[:5]:
    print(f"- {d.get('Tipo', '')} {d.get('Numero', '')} - {d.get('Sumario', '')[:50]}")

# Com filtro por parte (opcional)
result = search_dispatches(dr_id="945553807", part_id="33")
```

**Nota**: O `dr_id` obtem-se de `get_daily_ids()` ou `get_daily_content()`.

### 4. Detalhes de um Despacho

```python
import sys
sys.path.insert(0, "/var/cache/skills/diario-republica")
from diario_republica import get_dispatch_detail

# Obter detalhes completos de um despacho
result = get_dispatch_detail("945687384")

if result.get('status') == 'success':
    details = result.get('dispatch_details', {})
    print(f"Tipo: {details.get('Tipo', 'N/A')}")
    print(f"Sumario: {details.get('Sumario', 'N/A')}")
    print(f"Texto: {details.get('Texto', 'N/A')[:200]}...")
```

**Nota**: O `dispatch_id` obtem-se de `search_dispatches()` ou `get_daily_content()`.

## Workflow Tipico

### Para consultar publicacoes de uma data:

```python
import sys
sys.path.insert(0, "/var/cache/skills/diario-republica")
from diario_republica import get_daily_content, get_dispatch_detail

# 1. Obter todo o conteudo da data
result = get_daily_content("2025-01-15")

# 2. Listar despachos de interesse
for pub in result.get('publications', []):
    for dispatch in pub.get('dispatches', []):
        if 'nomeacao' in dispatch.get('Sumario', '').lower():
            print(f"Encontrado: {dispatch.get('Tipo')} {dispatch.get('Numero')}")

            # 3. Obter detalhes se necessario
            details = get_dispatch_detail(str(dispatch.get('DipLegisId')))
            print(f"Texto completo: {details}")
```

## Exemplos de Perguntas do Utilizador

- "O que foi publicado hoje no Diario da Republica?"
- "Mostra-me os despachos da Serie 2 de ontem"
- "Procura nomeacoes publicadas no DR de 15 de janeiro"
- "Quais as portarias publicadas esta semana?"
- "Detalhes do despacho n.o 1234/2025"

## Estrutura de Dados

### DR List Item (de get_daily_ids):
```python
{
    "dbId": "945553807",      # ID do DR (usar nas outras funcoes)
    "numero": "10",           # Numero do DR
    "serie": "Serie 2",       # Nome da serie
    "dataPublicacao": "2025-01-15"
}
```

### Dispatch Item (de search_dispatches/get_daily_content):
```python
{
    "DipLegisId": 945687384,  # ID do despacho (usar em get_dispatch_detail)
    "Tipo": "Despacho",       # Tipo de diploma
    "Numero": "1234/2025",    # Numero
    "Sumario": "...",         # Resumo
    "Entidade": "...",        # Entidade emissora
    "DataPublicacao": "..."   # Data
}
```

## Limitacoes

- Timeout: 60 segundos por request
- Datas sempre no formato: YYYY-MM-DD
- Alguns campos podem estar vazios dependendo do tipo de publicacao
- A API pode estar indisponivel em periodos de manutencao
