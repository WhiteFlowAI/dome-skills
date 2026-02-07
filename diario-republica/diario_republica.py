#!/usr/bin/env python3
"""
Diario da Republica Standalone Tool
Pesquisa legislacao e publicacoes oficiais no Diario da Republica Eletronico (dre.pt)

Este script e independente e pode ser usado sem MCP server ou LangChain.
Requisitos: pip install requests

Uso:
    python diario_republica.py get_daily_ids "2025-01-15"
    python diario_republica.py get_daily_content "2025-01-15"
    python diario_republica.py search_dispatches "945553807"
    python diario_republica.py search_dispatches "945553807" "33"
    python diario_republica.py get_dispatch_detail "945687384"
"""
import json
import sys
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    print("Erro: requests nao instalado. Execute: pip install requests")
    sys.exit(1)


# =============================================================================
# CONFIGURACAO
# =============================================================================

DR_BASE_URL = "https://diariodarepublica.pt"
DR_IDS_URL = f'{DR_BASE_URL}/dr/screenservices/dr/Home/home/DataActionGetDRByDataCalendario'
DR_DETAILS_URL = f'{DR_BASE_URL}/dr/screenservices/dr/Legislacao_Conteudos/Conteudo_Det_Diario/DataActionGetDadosAndApplicationSettings'
DR_DISPATCH_URL = f'{DR_BASE_URL}/dr/screenservices/dr/Legislacao_Conteudos/Conteudo_Detalhe/DataActionGetConteudoDataAndApplicationSettings'

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": DR_BASE_URL,
    "Referer": f"{DR_BASE_URL}/",
    "X-CSRFToken": "T6C+9iB49TLra4jEsMeSckDMNhQ=",
}
TIMEOUT_SECONDS = 60

# API version info (can change over time, extracted from browser requests)
MODULE_VERSION = "js3TIzfxRxgjpTcGVAEKHA"
API_VERSION_IDS = "A00rktBtkSvxDLsFy+6mgg"
API_VERSION_DETAILS = "ubdtj2Twi9YBXuIVNUZoow"
API_VERSION_DISPATCH = "w90gzV9hBiZHugQkA4fDMQ"


# =============================================================================
# HTTP REQUEST HELPER
# =============================================================================

def _make_request(url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faz um request HTTP POST para a API do Diario da Republica.

    Args:
        url: URL do endpoint
        body: Corpo do request (JSON)

    Returns:
        Resposta da API como dicionario
    """
    try:
        response = requests.post(
            url,
            headers=DEFAULT_HEADERS,
            json=body,
            timeout=TIMEOUT_SECONDS,
        )
        status = response.status_code

        # Tentar parse como JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = response.text

        return {
            "status": status,
            "data": data,
        }
    except requests.exceptions.Timeout:
        return {
            "status": 504,
            "data": {"error": "Request timeout"},
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": 500,
            "data": {"error": str(e)},
        }


# =============================================================================
# TOOL 1: OBTER IDS DO DR POR DATA
# =============================================================================

def get_daily_ids(date: str) -> Dict[str, Any]:
    """
    Obtem os IDs do Diario da Republica para uma data especifica.

    Args:
        date: Data no formato YYYY-MM-DD

    Returns:
        Dicionario com lista de DRs publicados na data

    Exemplo:
        result = get_daily_ids("2025-01-15")
    """
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
        return {"status": "error", "error": "Date must be in YYYY-MM-DD format", "error_code": "INVALID_DATE"}

    body = {
        "versionInfo": {
            "moduleVersion": MODULE_VERSION,
            "apiVersion": API_VERSION_IDS,
        },
        "viewName": "Home.home",
        "screenData": {"variables": {"DataUltimaPublicacao": date}},
        "clientVariables": {"Data": date},
    }

    response = _make_request(DR_IDS_URL, body)

    if response["status"] != 200:
        return {
            "status": "error",
            "error": f"HTTP {response['status']}",
            "error_code": "HTTP_ERROR",
            "date": date,
        }

    # Extract DR data from Json_Out field
    data = response["data"].get("data", response["data"])
    json_out_str = data.get("Json_Out", "")

    if not json_out_str:
        return {
            "status": "not_found",
            "date": date,
            "message": "Nenhum Diario da Republica encontrado para esta data",
        }

    try:
        json_out_data = json.loads(json_out_str)
        hits = json_out_data.get("hits", {}).get("hits", [])

        if len(hits) == 0:
            return {
                "status": "not_found",
                "date": date,
                "message": "Nenhum Diario da Republica encontrado para esta data",
            }

        # Extract DR IDs from hits
        dr_list = []
        for hit in hits:
            source = hit.get("_source", {})
            dr_list.append({
                "dbId": source.get("dbId"),
                "numero": source.get("numero"),
                "serie": source.get("conteudoTitle", ""),
                "dataPublicacao": source.get("dataPublicacao"),
            })

        return {
            "status": "success",
            "source": "Diario da Republica",
            "date": date,
            "total_found": len(dr_list),
            "dr_list": dr_list,
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Erro ao processar resposta: {str(e)}",
            "error_code": "PARSE_ERROR",
            "date": date,
        }


# =============================================================================
# TOOL 2: OBTER CONTEUDO COMPLETO POR DATA (SIMPLIFICADO)
# =============================================================================

def get_daily_content(date: str) -> Dict[str, Any]:
    """
    Obtem todo o conteudo do Diario da Republica para uma data especifica.
    Funcao simplificada que faz tudo numa so chamada.

    Args:
        date: Data no formato YYYY-MM-DD

    Returns:
        Dicionario com todas as publicacoes e despachos da data

    Exemplo:
        result = get_daily_content("2025-01-15")
    """
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
        return {"status": "error", "error": "Date must be in YYYY-MM-DD format", "error_code": "INVALID_DATE"}

    # Step 1: Get DR IDs for the date
    ids_result = get_daily_ids(date)

    if ids_result.get("status") != "success":
        return ids_result

    dr_list_raw = ids_result.get("dr_list", [])

    # Step 2: Get details for each DR ID
    dr_details_list = []

    for dr_item in dr_list_raw:
        dr_id = dr_item.get("dbId")
        dr_serie = dr_item.get("serie", "")

        if not dr_id:
            continue

        details_body = {
            "versionInfo": {
                "moduleVersion": MODULE_VERSION,
                "apiVersion": API_VERSION_DETAILS,
            },
            "viewName": "Legislacao_Conteudos.Conteudo_Detalhe",
            "screenData": {
                "variables": {
                    "DiarioIdAux": str(dr_id),
                    "DiarioId": str(dr_id),
                },
            },
        }

        try:
            details_response = _make_request(DR_DETAILS_URL, details_body)

            if details_response["status"] == 200:
                # Extract DetalheConteudo.List
                data = details_response["data"].get("data", details_response["data"])
                detalhe_conteudo = data.get("DetalheConteudo", {})
                dispatches_list = detalhe_conteudo.get("List", [])
                count = data.get("Count", len(dispatches_list))

                dr_details_list.append({
                    "dr_id": dr_id,
                    "serie": dr_serie,
                    "basic_info": dr_item,
                    "dispatches_count": count,
                    "dispatches": dispatches_list,
                })
            else:
                dr_details_list.append({
                    "dr_id": dr_id,
                    "serie": dr_serie,
                    "basic_info": dr_item,
                    "dispatches_count": 0,
                    "dispatches": [],
                    "error": f"HTTP {details_response['status']}",
                })
        except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as e:
            dr_details_list.append({
                "dr_id": dr_id,
                "serie": dr_serie,
                "basic_info": dr_item,
                "dispatches_count": 0,
                "dispatches": [],
                "error": str(e),
            })

    # Calculate totals
    total_dispatches = sum(d.get("dispatches_count", 0) for d in dr_details_list)
    series_with_content = len([d for d in dr_details_list if d.get("dispatches")])

    return {
        "status": "success",
        "source": "Diario da Republica",
        "date": date,
        "total_series": len(dr_list_raw),
        "total_dispatches": total_dispatches,
        "series_with_content": series_with_content,
        "publications": dr_details_list,
    }


# =============================================================================
# TOOL 3: PESQUISAR DESPACHOS NUM DR
# =============================================================================

def search_dispatches(dr_id: str, part_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Pesquisa despachos num Diario da Republica especifico.

    Args:
        dr_id: ID do DR (obtido de get_daily_ids)
        part_id: ID da parte (opcional, para filtrar por parte)

    Returns:
        Dicionario com lista de despachos

    Exemplo:
        result = search_dispatches("945553807")
        result = search_dispatches("945553807", "33")  # Com filtro por parte
    """
    variables = {
        "DiarioIdAux": str(dr_id),
        "DiarioId": str(dr_id),
    }

    if part_id:
        variables["ParteIdAux"] = str(part_id)
        variables["ParteId"] = str(part_id)

    body = {
        "versionInfo": {
            "moduleVersion": MODULE_VERSION,
            "apiVersion": API_VERSION_DETAILS,
        },
        "viewName": "Legislacao_Conteudos.Conteudo_Detalhe",
        "screenData": {"variables": variables},
    }

    response = _make_request(DR_DETAILS_URL, body)

    if response["status"] != 200:
        return {
            "status": "error",
            "error": f"HTTP {response['status']}",
            "error_code": "HTTP_ERROR",
            "dr_id": dr_id,
        }

    data = response["data"].get("data", response["data"])
    detalhe_conteudo = data.get("DetalheConteudo", {})
    dispatches_list = detalhe_conteudo.get("List", [])
    count = data.get("Count", len(dispatches_list))

    if len(dispatches_list) == 0:
        return {
            "status": "not_found",
            "dr_id": dr_id,
            "part_id": part_id,
            "message": "Nenhum despacho encontrado",
        }

    return {
        "status": "success",
        "source": "Diario da Republica",
        "dr_id": dr_id,
        "part_id": part_id,
        "total_count": count,
        "returned_dispatches": len(dispatches_list),
        "dispatches": dispatches_list,
    }


# =============================================================================
# TOOL 4: DETALHES DE UM DESPACHO
# =============================================================================

def get_dispatch_detail(dispatch_id: str) -> Dict[str, Any]:
    """
    Obtem detalhes completos de um despacho especifico.

    Args:
        dispatch_id: ID do despacho (DipLegisId de search_dispatches)

    Returns:
        Dicionario com detalhes do despacho

    Exemplo:
        result = get_dispatch_detail("945687384")
    """
    body = {
        "versionInfo": {
            "moduleVersion": MODULE_VERSION,
            "apiVersion": API_VERSION_DISPATCH,
        },
        "viewName": "Legislacao_Conteudos.Conteudo_Detalhe",
        "screenData": {"variables": {"DipLegisId": str(dispatch_id)}},
    }

    response = _make_request(DR_DISPATCH_URL, body)

    if response["status"] != 200:
        return {
            "status": "error",
            "error": f"HTTP {response['status']}",
            "error_code": "HTTP_ERROR",
            "dispatch_id": dispatch_id,
        }

    data = response["data"].get("data", response["data"])
    detalhe_conteudo = data.get("DetalheConteudo", {})

    if not detalhe_conteudo or len(detalhe_conteudo) == 0:
        return {
            "status": "not_found",
            "dispatch_id": dispatch_id,
            "message": "Despacho nao encontrado ou sem dados disponiveis",
        }

    return {
        "status": "success",
        "source": "Diario da Republica",
        "dispatch_id": dispatch_id,
        "dispatch_details": detalhe_conteudo,
    }


# =============================================================================
# INTERFACE DE EXECUCAO (para uso direto via terminal ou por agente)
# =============================================================================

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool (get_daily_ids, get_daily_content,
                   search_dispatches, get_dispatch_detail)
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execucao
    """
    tools = {
        "get_daily_ids": get_daily_ids,
        "dr_get_daily_ids": get_daily_ids,
        "get_daily_content": get_daily_content,
        "dr_get_daily_content": get_daily_content,
        "search_dispatches": search_dispatches,
        "dr_search_dispatches": search_dispatches,
        "get_dispatch_detail": get_dispatch_detail,
        "dr_get_dispatch_detail": get_dispatch_detail,
    }

    if tool_name not in tools:
        return {
            "error": f"Tool '{tool_name}' nao encontrada",
            "available_tools": list(tools.keys()),
        }

    return tools[tool_name](**kwargs)


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
    """Execucao via linha de comando."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nTools disponiveis:")
        print("  get_daily_ids <date>")
        print("  get_daily_content <date>")
        print("  search_dispatches <dr_id> [part_id]")
        print("  get_dispatch_detail <dispatch_id>")
        sys.exit(0)

    tool_name = sys.argv[1]

    if tool_name in ["get_daily_ids", "dr_get_daily_ids"]:
        if len(sys.argv) < 3:
            print("Erro: date obrigatorio")
            print("Uso: python diario_republica.py get_daily_ids <date>")
            print("Exemplo: python diario_republica.py get_daily_ids 2025-01-15")
            sys.exit(1)
        date = sys.argv[2]
        result = get_daily_ids(date)

    elif tool_name in ["get_daily_content", "dr_get_daily_content"]:
        if len(sys.argv) < 3:
            print("Erro: date obrigatorio")
            print("Uso: python diario_republica.py get_daily_content <date>")
            print("Exemplo: python diario_republica.py get_daily_content 2025-01-15")
            sys.exit(1)
        date = sys.argv[2]
        result = get_daily_content(date)

    elif tool_name in ["search_dispatches", "dr_search_dispatches"]:
        if len(sys.argv) < 3:
            print("Erro: dr_id obrigatorio")
            print("Uso: python diario_republica.py search_dispatches <dr_id> [part_id]")
            print("Exemplo: python diario_republica.py search_dispatches 945553807")
            sys.exit(1)
        dr_id = sys.argv[2]
        part_id = sys.argv[3] if len(sys.argv) > 3 else None
        result = search_dispatches(dr_id, part_id)

    elif tool_name in ["get_dispatch_detail", "dr_get_dispatch_detail"]:
        if len(sys.argv) < 3:
            print("Erro: dispatch_id obrigatorio")
            print("Uso: python diario_republica.py get_dispatch_detail <dispatch_id>")
            print("Exemplo: python diario_republica.py get_dispatch_detail 945687384")
            sys.exit(1)
        dispatch_id = sys.argv[2]
        result = get_dispatch_detail(dispatch_id)

    else:
        print(f"Erro: Tool '{tool_name}' nao reconhecida")
        print("\nTools disponiveis:")
        print("  get_daily_ids, get_daily_content")
        print("  search_dispatches, get_dispatch_detail")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
