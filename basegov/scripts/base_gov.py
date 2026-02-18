#!/usr/bin/env python3
"""
BASE.gov.pt Standalone Tool
Pesquisa contratos e anúncios públicos na BASE.gov.pt (Portal dos Contratos Públicos de Portugal)

Este script é independente e pode ser usado sem MCP server ou LangChain.
Requisitos: pip install aiohttp

Uso:
    python base_gov.py search_contracts "desdedatacontrato=2024-01-01&adjudicante=501306099"
    python base_gov.py contract_detail "11650203"
    python base_gov.py search_announcements "desdedatapublicacao=2024-01-01&texto=software"
    python base_gov.py announcement_detail "330322"
"""
import asyncio
import json
import sys
from typing import Any, Dict, Optional

try:
    import aiohttp
except ImportError:
    print("Erro: aiohttp não instalado. Execute: pip install aiohttp")
    sys.exit(1)


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

BASE_URL = "https://www.base.gov.pt/Base4/pt/resultados/"
API_VERSION = "139.0"
DEFAULT_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Origin": "https://www.base.gov.pt",
    "Referer": "https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos",
    "Accept": "text/plain, */*; q=0.01",
    "Cookie": "ACCEPTED_TERMS=true",
}
TIMEOUT_SECONDS = 60
MAX_PAGE_SIZE = 50


# =============================================================================
# HTTP REQUEST HELPER
# =============================================================================

async def _make_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faz um request HTTP POST para a API da BASE.gov.pt.

    Args:
        body: Corpo do request (form-urlencoded)

    Returns:
        Resposta da API como dicionário
    """
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            BASE_URL,
            headers=DEFAULT_HEADERS,
            data=body,
            allow_redirects=True,
        ) as response:
            status = response.status
            text = await response.text()

            # Tentar parse como JSON
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = text

            return {
                "status": status,
                "data": data,
            }


# =============================================================================
# TOOL 1: PESQUISA DE CONTRATOS
# =============================================================================

async def search_contracts(
    query: str,
    page: int = 0,
    size: int = 50,
) -> Dict[str, Any]:
    """
    Pesquisa contratos públicos na BASE.gov.pt.

    Args:
        query: Filtros no formato "campo1=valor1&campo2=valor2"
               Filtros disponíveis:
               - desdedatacontrato: Data inicial (YYYY-MM-DD)
               - atedatacontrato: Data final (YYYY-MM-DD)
               - adjudicante: NIF da entidade contratante
               - adjudicataria: NIF do fornecedor
               - texto: Pesquisa por texto livre
        page: Página (0-indexed, default: 0)
        size: Resultados por página (max 50, default: 50)

    Returns:
        Dicionário com resultados da pesquisa

    Exemplo:
        result = await search_contracts("desdedatacontrato=2024-01-01&adjudicante=501306099")
    """
    body = {
        "type": "search_contratos",
        "version": API_VERSION,
        "page": str(page),
        "size": str(min(size, MAX_PAGE_SIZE)),
        "query": query,
    }

    response = await _make_request(body)

    if response["status"] != 200:
        return {"error": f"HTTP {response['status']}", "data": response["data"]}

    data = response["data"]
    if isinstance(data, dict):
        return {
            "status": "success",
            "source": "BASE.gov.pt (Contratos Públicos)",
            "total_contracts": data.get("total", 0),
            "returned_items": len(data.get("items", [])),
            "page": page,
            "size": size,
            "contracts": data.get("items", []),
        }

    return {"error": "Formato de resposta inesperado", "data": data}


# =============================================================================
# TOOL 2: DETALHES DE CONTRATO
# =============================================================================

async def get_contract_detail(contract_id: str) -> Dict[str, Any]:
    """
    Obtém detalhes completos de um contrato específico.

    Args:
        contract_id: ID do contrato (obtido na pesquisa)

    Returns:
        Dicionário com detalhes do contrato

    Exemplo:
        result = await get_contract_detail("11650203")
    """
    body = {
        "type": "detail_contratos",
        "version": API_VERSION,
        "id": str(contract_id),
    }

    response = await _make_request(body)

    if response["status"] != 200:
        return {"error": f"HTTP {response['status']}", "data": response["data"]}

    data = response["data"]
    if data:
        return {
            "status": "success",
            "source": "BASE.gov.pt (Contratos Públicos)",
            "contract_id": contract_id,
            "contract_details": data,
        }

    return {
        "status": "not_found",
        "contract_id": contract_id,
        "message": "Contrato não encontrado",
    }


# =============================================================================
# TOOL 3: PESQUISA DE ANÚNCIOS
# =============================================================================

async def search_announcements(
    query: str,
    page: int = 0,
    size: int = 50,
) -> Dict[str, Any]:
    """
    Pesquisa anúncios de concursos públicos na BASE.gov.pt.

    Args:
        query: Filtros no formato "campo1=valor1&campo2=valor2"
               Filtros disponíveis:
               - desdedatapublicacao: Data inicial publicação (OBRIGATÓRIO)
               - atedatapublicacao: Data final publicação
               - emissora: NIF da entidade emissora
               - texto: Pesquisa por texto livre
        page: Página (0-indexed, default: 0)
        size: Resultados por página (max 50, default: 50)

    Returns:
        Dicionário com resultados da pesquisa

    Exemplo:
        result = await search_announcements("desdedatapublicacao=2024-01-01&texto=software")
    """
    body = {
        "type": "search_anuncios",
        "version": API_VERSION,
        "query": query,
        "sort": "-drPublicationDate",
        "page": str(page),
        "size": str(min(size, MAX_PAGE_SIZE)),
    }

    response = await _make_request(body)

    if response["status"] != 200:
        return {"error": f"HTTP {response['status']}", "data": response["data"]}

    data = response["data"]
    if isinstance(data, dict):
        return {
            "status": "success",
            "source": "BASE.gov.pt (Anúncios de Concursos)",
            "total_announcements": data.get("total", 0),
            "returned_items": len(data.get("items", [])),
            "page": page,
            "size": size,
            "announcements": data.get("items", []),
        }

    return {"error": "Formato de resposta inesperado", "data": data}


# =============================================================================
# TOOL 4: DETALHES DE ANÚNCIO
# =============================================================================

async def get_announcement_detail(announcement_id: str) -> Dict[str, Any]:
    """
    Obtém detalhes completos de um anúncio específico.

    Args:
        announcement_id: ID do anúncio (obtido na pesquisa)

    Returns:
        Dicionário com detalhes do anúncio

    Exemplo:
        result = await get_announcement_detail("330322")
    """
    body = {
        "type": "detail_anuncios",
        "version": API_VERSION,
        "id": str(announcement_id),
    }

    response = await _make_request(body)

    if response["status"] != 200:
        return {"error": f"HTTP {response['status']}", "data": response["data"]}

    data = response["data"]
    if data:
        return {
            "status": "success",
            "source": "BASE.gov.pt (Anúncios de Concursos)",
            "announcement_id": announcement_id,
            "announcement_details": data,
        }

    return {
        "status": "not_found",
        "announcement_id": announcement_id,
        "message": "Anúncio não encontrado",
    }


# =============================================================================
# INTERFACE DE EXECUÇÃO (para uso direto via terminal ou por agente)
# =============================================================================

async def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool (search_contracts, contract_detail,
                   search_announcements, announcement_detail)
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execução
    """
    tools = {
        "search_contracts": search_contracts,
        "base_search_contracts": search_contracts,
        "contract_detail": get_contract_detail,
        "base_get_contract_detail": get_contract_detail,
        "search_announcements": search_announcements,
        "base_search_announcements": search_announcements,
        "announcement_detail": get_announcement_detail,
        "base_get_announcement_detail": get_announcement_detail,
    }

    if tool_name not in tools:
        return {
            "error": f"Tool '{tool_name}' não encontrada",
            "available_tools": list(set(tools.keys())),
        }

    return await tools[tool_name](**kwargs)


def execute_tool_sync(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Versão síncrona de execute_tool (para uso em ambientes não-async).
    """
    return asyncio.run(execute_tool(tool_name, **kwargs))


# =============================================================================
# CLI
# =============================================================================

def print_result(result: Dict[str, Any], pretty: bool = True):
    """Imprime o resultado formatado."""
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


def main():
    """Execução via linha de comando."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nTools disponíveis:")
        print("  search_contracts <query> [page] [size]")
        print("  contract_detail <contract_id>")
        print("  search_announcements <query> [page] [size]")
        print("  announcement_detail <announcement_id>")
        sys.exit(0)

    tool_name = sys.argv[1]

    if tool_name in ["search_contracts", "base_search_contracts"]:
        if len(sys.argv) < 3:
            print("Erro: query obrigatória")
            print("Uso: python base_gov.py search_contracts <query> [page] [size]")
            sys.exit(1)
        query = sys.argv[2]
        page = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        size = int(sys.argv[4]) if len(sys.argv) > 4 else 50
        result = asyncio.run(search_contracts(query, page, size))

    elif tool_name in ["contract_detail", "base_get_contract_detail"]:
        if len(sys.argv) < 3:
            print("Erro: contract_id obrigatório")
            print("Uso: python base_gov.py contract_detail <contract_id>")
            sys.exit(1)
        contract_id = sys.argv[2]
        result = asyncio.run(get_contract_detail(contract_id))

    elif tool_name in ["search_announcements", "base_search_announcements"]:
        if len(sys.argv) < 3:
            print("Erro: query obrigatória")
            print("Uso: python base_gov.py search_announcements <query> [page] [size]")
            sys.exit(1)
        query = sys.argv[2]
        page = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        size = int(sys.argv[4]) if len(sys.argv) > 4 else 50
        result = asyncio.run(search_announcements(query, page, size))

    elif tool_name in ["announcement_detail", "base_get_announcement_detail"]:
        if len(sys.argv) < 3:
            print("Erro: announcement_id obrigatório")
            print("Uso: python base_gov.py announcement_detail <announcement_id>")
            sys.exit(1)
        announcement_id = sys.argv[2]
        result = asyncio.run(get_announcement_detail(announcement_id))

    else:
        print(f"Erro: Tool '{tool_name}' não reconhecida")
        print("\nTools disponíveis:")
        print("  search_contracts, contract_detail")
        print("  search_announcements, announcement_detail")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
