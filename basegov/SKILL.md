---
name: basegov
description: Pesquisa contratos e anúncios públicos na BASE.gov.pt (Portal dos Contratos Públicos de Portugal). Use para consultar gastos públicos, fornecedores do estado e concursos abertos.
---

# BASE.gov.pt - Contratos Públicos

Skill para pesquisar e analisar contratos e anúncios públicos registados na BASE.gov.pt.

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Contratos públicos de empresas (por NIF)
- Contratos de entidades adjudicantes (municípios, ministérios, etc.)
- Gastos públicos por período
- Análise de fornecedores do estado
- Concursos públicos abertos ou passados
- Oportunidades de negócio com o estado

## Como Usar

Importa o módulo e usa as funções. O skill instala automaticamente `aiohttp`.

```python
import asyncio
import sys
sys.path.insert(0, "/var/cache/skills/basegov")
from base_gov import search_contracts, get_contract_detail, search_announcements, get_announcement_detail
```

## Operações Disponíveis

### 1. Pesquisar Contratos

```python
import asyncio
import sys
sys.path.insert(0, "/var/cache/skills/basegov")
from base_gov import search_contracts

# Pesquisar contratos de uma entidade desde 2024
result = asyncio.run(search_contracts(
    query="desdedatacontrato=2024-01-01&adjudicante=501306099",
    page=0,
    size=50
))

print(f"Total: {result.get('total_contracts', 0)} contratos")
for c in result.get('contracts', [])[:5]:
    print(f"- {c.get('objectBriefDescription', 'N/A')}")
    print(f"  Valor: {c.get('initialContractualPrice', 'N/A')}€")
```

**Filtros disponíveis (query):**
| Filtro | Descrição | Exemplo |
|--------|-----------|---------|
| desdedatacontrato | Data inicial | `2024-01-01` |
| atedatacontrato | Data final | `2024-12-31` |
| adjudicante | NIF da entidade contratante | `501306099` |
| adjudicataria | NIF do fornecedor | `123456789` |
| texto | Pesquisa por texto livre | `consultoria` |

### 2. Detalhes de Contrato

```python
import asyncio
import sys
sys.path.insert(0, "/var/cache/skills/basegov")
from base_gov import get_contract_detail

# Obter detalhes de um contrato específico
result = asyncio.run(get_contract_detail("11650203"))

if result.get('status') == 'success':
    details = result.get('contract_details', {})
    print(f"Descrição: {details.get('objectBriefDescription')}")
    print(f"Valor: {details.get('initialContractualPrice')}€")
```

### 3. Pesquisar Anúncios/Concursos

```python
import asyncio
import sys
sys.path.insert(0, "/var/cache/skills/basegov")
from base_gov import search_announcements

# Pesquisar concursos de software desde 2024
result = asyncio.run(search_announcements(
    query="desdedatapublicacao=2024-01-01&texto=software",
    page=0,
    size=50
))

print(f"Total: {result.get('total_announcements', 0)} anúncios")
for a in result.get('announcements', [])[:5]:
    print(f"- {a.get('title', 'N/A')}")
```

**IMPORTANTE**: Incluir sempre `desdedatapublicacao` para melhor performance.

**Filtros disponíveis (query):**
| Filtro | Descrição | Exemplo |
|--------|-----------|---------|
| desdedatapublicacao | Data inicial (OBRIGATÓRIO) | `2024-01-01` |
| atedatapublicacao | Data final | `2024-12-31` |
| emissora | NIF da entidade emissora | `501306099` |
| texto | Pesquisa por texto livre | `software` |

### 4. Detalhes de Anúncio

```python
import asyncio
import sys
sys.path.insert(0, "/var/cache/skills/basegov")
from base_gov import get_announcement_detail

# Obter detalhes de um anúncio específico
result = asyncio.run(get_announcement_detail("330322"))

if result.get('status') == 'success':
    details = result.get('announcement_details', {})
    print(f"Título: {details.get('title')}")
```

## Exemplos de Perguntas do Utilizador

**Contratos:**
- "Quantos contratos tem a empresa com NIF 501306099 desde 2024?"
- "Mostra-me contratos de software do Município do Porto"
- "Qual o valor total de contratos da empresa X em 2023?"

**Anúncios/Concursos:**
- "Que concursos públicos estão abertos para software?"
- "Procura oportunidades de negócio com o estado na área de consultoria"
- "Mostra-me os últimos anúncios do Município de Lisboa"

## Limitações

- Máximo 50 resultados por página
- Para obter todos os resultados, usar paginação (`page`: 0, 1, 2...)
- Timeout: 60 segundos
- Datas sempre no formato: YYYY-MM-DD
