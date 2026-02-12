#!/usr/bin/env python3
"""
Conversation History Client Standalone Tool
Consulta o historico de conversas e mensagens do utilizador.

Este script e independente e comunica com o BFF (Backend for Frontend)
para aceder ao historico de conversas do utilizador autenticado.

Requisitos: pip install requests

Uso CLI:
    python conversation_client.py list_conversations <user_id> [--limit=10] [--search=...] [--created_after=...] [--created_before=...] [--tenant_id=...]
    python conversation_client.py get_conversation_messages <user_id> <conversation_id> [--limit=50] [--offset=0] [--message_types=...] [--include_reasoning] [--tenant_id=...]
"""
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, quote

try:
    import requests
except ImportError:
    print("Erro: requests nao instalado. Execute: pip install requests")
    sys.exit(1)


# =============================================================================
# CONFIGURACAO
# =============================================================================

BFF_BASE_URL = os.getenv("BFF_BASE_URL", "http://localhost:3001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
TIMEOUT_SECONDS = 30


# =============================================================================
# HTTP REQUEST HELPER
# =============================================================================

def _build_headers(user_id: str, tenant_id: Optional[str] = None) -> Dict[str, str]:
    """
    Constroi headers para autenticacao com o BFF.

    Args:
        user_id: ID do utilizador
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com headers
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-internal-api-key": INTERNAL_API_KEY,
        "x-user-id": user_id,
    }

    if tenant_id:
        headers["x-tenant-id"] = tenant_id

    return headers


def _make_get_request(
    path: str,
    user_id: str,
    query: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Faz um request HTTP GET para o BFF.

    Args:
        path: Caminho do endpoint (ex: /internal/conversations)
        user_id: ID do utilizador
        query: Parametros de query (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Resposta do BFF
    """
    url = f"{BFF_BASE_URL}{path}"

    # Filtrar valores None da query
    if query:
        query = {k: v for k, v in query.items() if v is not None}
        if query:
            url = f"{url}?{urlencode(query)}"

    headers = _build_headers(user_id, tenant_id)

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        return _process_response(response)

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_code": "TIMEOUT",
            "message": "Request timeout apos {} segundos".format(TIMEOUT_SECONDS),
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_code": "REQUEST_ERROR",
            "message": str(e),
        }


def _process_response(response: requests.Response) -> Dict[str, Any]:
    """
    Processa a resposta HTTP do BFF.

    Args:
        response: Resposta HTTP

    Returns:
        Dicionario com status e dados ou erro
    """
    try:
        data = response.json()
    except json.JSONDecodeError:
        data = {"raw_response": response.text}

    # Conversa nao encontrada (404)
    if response.status_code == 404:
        return {
            "status": "error",
            "error_code": data.get("code", "CONVERSATION_NOT_FOUND"),
            "message": data.get("message", "Conversa nao encontrada"),
        }

    # Acesso negado (403)
    if response.status_code == 403:
        return {
            "status": "error",
            "error_code": data.get("code", "FORBIDDEN"),
            "message": data.get("message", "Sem acesso a esta conversa"),
        }

    # Request invalido (400)
    if response.status_code == 400:
        return {
            "status": "error",
            "error_code": data.get("code", "INVALID_REQUEST"),
            "message": data.get("message", "Request invalido"),
        }

    # Outros erros
    if not response.ok:
        return {
            "status": "error",
            "error_code": "HTTP_ERROR",
            "message": "HTTP {}: {}".format(response.status_code, data),
        }

    # Sucesso - retorna os dados
    return {
        "status": "success",
        "data": data,
    }


# =============================================================================
# TOOL 1: LISTAR CONVERSAS
# =============================================================================

def list_conversations(
    user_id: str,
    limit: int = 10,
    search: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lista as conversas mais recentes do utilizador.

    Args:
        user_id: ID do utilizador
        limit: Numero maximo de conversas a retornar (default: 10, max: 100)
        search: Texto para pesquisar no titulo da conversa (opcional)
        created_after: Data minima no formato ISO 8601 (ex: '2025-01-15T00:00:00Z') (opcional)
        created_before: Data maxima no formato ISO 8601 (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de conversas

    Exemplo:
        result = list_conversations("user-123", limit=5)
        result = list_conversations("user-123", search="projeto", limit=10)
        result = list_conversations("user-123", created_after="2025-01-01T00:00:00Z")
    """
    # Validar limit
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100

    # Construir parametros de query
    query_params = {
        "limit": limit,
        "search": search,
        "created_after": created_after,
        "created_before": created_before,
    }

    result = _make_get_request(
        path="/internal/conversations",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    # Processar resposta
    conversations_data = result.get("data", [])

    if isinstance(conversations_data, list):
        return {
            "status": "success",
            "total": len(conversations_data),
            "conversations": conversations_data,
        }

    return {
        "status": "success",
        "total": 0,
        "conversations": [],
    }


# =============================================================================
# TOOL 2: OBTER MENSAGENS DE UMA CONVERSA
# =============================================================================

def get_conversation_messages(
    user_id: str,
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    message_types: Optional[str] = None,
    include_reasoning: bool = False,
    start_order: Optional[int] = None,
    end_order: Optional[int] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem as mensagens de uma conversa especifica.

    Args:
        user_id: ID do utilizador
        conversation_id: ID da conversa
        limit: Numero maximo de mensagens a retornar (default: 50, max: 200)
        offset: Posicao inicial para paginacao (default: 0)
        message_types: Tipos de mensagem separados por virgula (ex: 'user_text,text')
                       Tipos disponiveis: user_text, text, reasoning, reasoning_websearch,
                       reasoning_extension, citations, clarification, plan, user_options
        include_reasoning: Se True, inclui automaticamente mensagens de reasoning
                          (reasoning, reasoning_websearch, reasoning_extension)
        start_order: Numero de ordem inicial (inclusivo) para filtrar mensagens (opcional)
        end_order: Numero de ordem final (inclusivo) para filtrar mensagens (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de mensagens

    Exemplo:
        # Obter apenas perguntas e respostas
        result = get_conversation_messages("user-123", "conv-abc", message_types="user_text,text")

        # Obter tudo incluindo reasoning
        result = get_conversation_messages("user-123", "conv-abc", include_reasoning=True)

        # Paginacao
        result = get_conversation_messages("user-123", "conv-abc", limit=20, offset=0)
    """
    if not conversation_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "conversation_id e obrigatorio",
        }

    # Validar limit
    if limit < 1:
        limit = 1
    elif limit > 200:
        limit = 200

    # Validar offset
    if offset < 0:
        offset = 0

    # Construir message_types com include_reasoning
    final_message_types = message_types
    if include_reasoning:
        reasoning_types = "reasoning,reasoning_websearch,reasoning_extension"
        if final_message_types:
            final_message_types = f"{final_message_types},{reasoning_types}"
        else:
            final_message_types = reasoning_types

    # URL encode do conversation_id para seguranca
    safe_conversation_id = quote(conversation_id, safe='')

    # Construir parametros de query
    query_params = {
        "limit": limit,
        "offset": offset,
        "message_types": final_message_types,
        "start_order": start_order,
        "end_order": end_order,
    }

    result = _make_get_request(
        path=f"/internal/conversations/{safe_conversation_id}/messages",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    # Processar resposta
    messages_data = result.get("data", [])

    if isinstance(messages_data, list):
        return {
            "status": "success",
            "total": len(messages_data),
            "messages": messages_data,
        }

    return {
        "status": "success",
        "total": 0,
        "messages": [],
    }


# =============================================================================
# INTERFACE DE EXECUCAO (para uso direto via terminal ou por agente)
# =============================================================================

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool (list_conversations, get_conversation_messages)
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execucao
    """
    tools = {
        "list_conversations": list_conversations,
        "conversation_history_list_conversations": list_conversations,
        "get_conversation_messages": get_conversation_messages,
        "conversation_history_get_conversation_messages": get_conversation_messages,
        "get_messages": get_conversation_messages,
        "conversation_history_get_messages": get_conversation_messages,
    }

    if tool_name not in tools:
        return {
            "error": "Tool '{}' nao encontrada".format(tool_name),
            "available_tools": list(set(tools.values())),
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


def print_usage():
    """Imprime instrucoes de uso."""
    print(__doc__)
    print("\nTools disponiveis:")
    print("  list_conversations <user_id> [--limit=10] [--search=...] [--created_after=...] [--created_before=...] [--tenant_id=...]")
    print("  get_conversation_messages <user_id> <conversation_id> [--limit=50] [--offset=0] [--message_types=...] [--include_reasoning] [--tenant_id=...]")
    print("\nExemplos:")
    print('  python conversation_client.py list_conversations user-123 --limit=5')
    print('  python conversation_client.py list_conversations user-123 --search="projeto" --limit=10')
    print('  python conversation_client.py get_conversation_messages user-123 conv-abc --limit=20')
    print('  python conversation_client.py get_conversation_messages user-123 conv-abc --message_types="user_text,text"')
    print('  python conversation_client.py get_conversation_messages user-123 conv-abc --include_reasoning')


def parse_cli_args(args: List[str]) -> Dict[str, Any]:
    """
    Parse argumentos CLI com suporte a --key=value.

    Args:
        args: Lista de argumentos

    Returns:
        Dicionario com argumentos posicionais e named
    """
    positional = []
    named = {}

    for arg in args:
        if arg.startswith("--"):
            if "=" in arg:
                key, value = arg[2:].split("=", 1)
                named[key] = value
            else:
                named[arg[2:]] = True
        else:
            positional.append(arg)

    return {"positional": positional, "named": named}


def main():
    """Execucao via linha de comando."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    tool_name = sys.argv[1]
    args = parse_cli_args(sys.argv[2:])
    positional = args["positional"]
    named = args["named"]

    if tool_name in ["list_conversations", "conversation_history_list_conversations"]:
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            print("Uso: python conversation_client.py list_conversations <user_id> [--limit=10] [--search=...] [--created_after=...] [--created_before=...]")
            sys.exit(1)

        user_id = positional[0]
        try:
            limit = int(named.get("limit", 10))
        except ValueError:
            limit = 10

        result = list_conversations(
            user_id=user_id,
            limit=limit,
            search=named.get("search"),
            created_after=named.get("created_after"),
            created_before=named.get("created_before"),
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["get_conversation_messages", "get_messages", "conversation_history_get_conversation_messages"]:
        if len(positional) < 2:
            print("Erro: user_id e conversation_id obrigatorios")
            print("Uso: python conversation_client.py get_conversation_messages <user_id> <conversation_id> [--limit=50] [--offset=0] [--message_types=...] [--include_reasoning]")
            sys.exit(1)

        user_id = positional[0]
        conversation_id = positional[1]

        try:
            limit = int(named.get("limit", 50))
        except ValueError:
            limit = 50

        try:
            offset = int(named.get("offset", 0))
        except ValueError:
            offset = 0

        include_reasoning = named.get("include_reasoning", False)
        if isinstance(include_reasoning, str):
            include_reasoning = include_reasoning.lower() in ("true", "1", "yes")

        try:
            start_order = int(named["start_order"]) if "start_order" in named else None
        except ValueError:
            start_order = None

        try:
            end_order = int(named["end_order"]) if "end_order" in named else None
        except ValueError:
            end_order = None

        result = get_conversation_messages(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
            message_types=named.get("message_types"),
            include_reasoning=include_reasoning,
            start_order=start_order,
            end_order=end_order,
            tenant_id=named.get("tenant_id"),
        )

    else:
        print("Erro: Tool '{}' nao reconhecida".format(tool_name))
        print("\nTools disponiveis:")
        print("  list_conversations, get_conversation_messages")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
