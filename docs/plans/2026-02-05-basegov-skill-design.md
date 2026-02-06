# BaseGov Skill Design

## Overview

Skill para pesquisar contratos e anúncios públicos na BASE.gov.pt (Portal dos Contratos Públicos de Portugal).

## Estrutura

```
dome-superpowers/
  basegov/
    superpower.md       # Instruções para o agente
    base_gov.py         # Código Python (copiado de partner-ms)
    requirements.txt    # aiohttp
```

## Operações

1. **search_contracts(query, page, size)** - Pesquisa contratos públicos
2. **get_contract_detail(contract_id)** - Detalhes de um contrato
3. **search_announcements(query, page, size)** - Pesquisa anúncios/concursos
4. **get_announcement_detail(announcement_id)** - Detalhes de um anúncio

## Decisões

- **Uma skill única** com todas as 4 operações (relacionadas)
- **Código em ficheiro separado** (397 linhas, demasiado para inline)
- **Dependência única**: aiohttp>=3.8.0

## Origem do Código

Código existente em `partner-ms/tools/base_gov/base_gov.py` - testado e funcional.

## Testes

```bash
# Local
python base_gov.py search_contracts "desdedatacontrato=2024-01-01&texto=software"

# Integrado
curl -X POST http://localhost:8001/api/agent/interactive/execute \
  -H "Content-Type: application/json" \
  -d '{"plan": "Pesquisa contratos de software", "skills": ["basegov"]}'
```
