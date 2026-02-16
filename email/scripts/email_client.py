#!/usr/bin/env python3
"""
Email Client Standalone Tool
Envia e recebe emails via Google (Gmail) ou Microsoft (Outlook).

Este script e independente e comunica com o BFF (Backend for Frontend)
que gere a autenticacao OAuth com os providers de email.

Requisitos: pip install requests

Uso CLI:
    python email_client.py list_emails <user_id> [--query=...] [--from=...] [--since=...] [--limit=10]
    python email_client.py get_email <user_id> <email_id>
    python email_client.py send_email <user_id> <to> <subject> <body>
    python email_client.py search_emails <user_id> <query> [--limit=10]
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
        path: Caminho do endpoint (ex: /internal/email/list)
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


def _make_post_request(
    path: str,
    user_id: str,
    body: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Faz um request HTTP POST para o BFF.

    Args:
        path: Caminho do endpoint (ex: /internal/email/send)
        user_id: ID do utilizador
        body: Corpo do request (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Resposta do BFF
    """
    url = f"{BFF_BASE_URL}{path}"
    headers = _build_headers(user_id, tenant_id)

    try:
        response = requests.post(
            url,
            headers=headers,
            json=body or {},
            timeout=TIMEOUT_SECONDS,
        )
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

    # Erros de autenticacao OAuth (409 Conflict)
    if response.status_code == 409:
        return {
            "status": "error",
            "error_code": data.get("code", "EMAIL_PROVIDER_AUTH_FAILED"),
            "message": data.get("message", "Erro de autenticacao com o provider de email"),
            "reauthorization_required": data.get("reauthorization_required", True),
            "provider": data.get("provider"),
            "action_url": data.get("action_url"),
        }

    # Email nao encontrado (404)
    if response.status_code == 404:
        return {
            "status": "error",
            "error_code": data.get("code", "EMAIL_NOT_FOUND"),
            "message": data.get("message", "Email nao encontrado"),
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
# TOOL 1: LISTAR EMAILS
# =============================================================================

def list_emails(
    user_id: str,
    query: Optional[str] = None,
    from_email: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 10,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lista emails da caixa de entrada do utilizador.

    Args:
        user_id: ID do utilizador
        query: Texto para pesquisar no assunto/corpo (opcional)
        from_email: Filtrar por endereco do remetente (opcional)
        since: Data minima no formato YYYY-MM-DD (opcional)
        limit: Numero maximo de emails (default: 10, max: 50)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de emails

    Exemplo:
        result = list_emails("user-123", query="fatura", limit=20)
    """
    # Validar limit
    if limit < 1:
        limit = 1
    elif limit > 50:
        limit = 50

    # Construir parametros de query
    query_params = {
        "query": query,
        "from": from_email,
        "since": since,
        "limit": limit,
    }

    result = _make_get_request(
        path="/internal/email/list",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    # Processar resposta - o BFF retorna uma lista diretamente
    emails_data = result.get("data", [])

    # Se for uma lista, processar como emails
    if isinstance(emails_data, list):
        return {
            "status": "success",
            "total": len(emails_data),
            "emails": emails_data,
        }

    # Se for dicionario com erro
    return {
        "status": "success",
        "total": 0,
        "emails": [],
    }


# =============================================================================
# TOOL 2: OBTER DETALHES DE UM EMAIL
# =============================================================================

def get_email_detail(
    user_id: str,
    email_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem detalhes completos de um email especifico.

    Args:
        user_id: ID do utilizador
        email_id: ID do email a obter
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com detalhes do email

    Exemplo:
        result = get_email_detail("user-123", "msg-abc123")
    """
    if not email_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "email_id e obrigatorio",
        }

    # URL encode do email_id para seguranca
    safe_email_id = quote(email_id, safe='')

    result = _make_get_request(
        path=f"/internal/email/{safe_email_id}",
        user_id=user_id,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    email_data = result.get("data", {})

    return {
        "status": "success",
        "email": email_data,
    }


# =============================================================================
# TOOL 3: ENVIAR EMAIL
# =============================================================================

def send_email(
    user_id: str,
    to: List[str],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Envia um email, opcionalmente com anexos.

    Args:
        user_id: ID do utilizador
        to: Lista de destinatarios (emails)
        subject: Assunto do email
        body_text: Corpo em texto simples (opcional se body_html fornecido)
        body_html: Corpo em HTML (opcional se body_text fornecido)
        attachments: Lista de anexos do workspace S3 (opcional).
                     Cada anexo e um dict com:
                       - task_id (str): ID da task que gerou o ficheiro
                       - file_path (str): Caminho do ficheiro no workspace
                       - filename (str, opcional): Nome para o anexo no email
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado do envio

    Exemplo:
        result = send_email(
            user_id="user-123",
            to=["dest@email.pt"],
            subject="Assunto",
            body_text="Conteudo do email"
        )

        # Com anexos
        result = send_email(
            user_id="user-123",
            to=["dest@email.pt"],
            subject="Relatorio Mensal",
            body_text="Segue em anexo o relatorio.",
            attachments=[
                {
                    "task_id": "task-456",
                    "file_path": "reports/relatorio.pdf",
                    "filename": "relatorio-janeiro.pdf"
                }
            ],
            tenant_id="tenant-789"
        )
    """
    # Validacoes
    if not to or len(to) == 0:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "Lista de destinatarios (to) nao pode estar vazia",
        }

    if not subject:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "Assunto (subject) e obrigatorio",
        }

    if not body_text and not body_html:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "Pelo menos body_text ou body_html e obrigatorio",
        }

    # Validar attachments
    if attachments:
        for att in attachments:
            if not att.get("task_id") or not att.get("file_path"):
                return {
                    "status": "error",
                    "error_code": "INVALID_REQUEST",
                    "message": "Cada anexo requer 'task_id' e 'file_path'",
                }

    # Construir body do request
    request_body = {
        "to": to,
        "subject": subject,
        "bodyText": body_text,
        "bodyHtml": body_html,
    }

    if attachments:
        request_body["attachments"] = attachments

    result = _make_post_request(
        path="/internal/email/send",
        user_id=user_id,
        body=request_body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    send_data = result.get("data", {})

    return {
        "status": "success",
        "message_id": send_data.get("id"),
        "provider": send_data.get("provider"),
    }


# =============================================================================
# TOOL 4: PESQUISAR EMAILS (wrapper de list_emails)
# =============================================================================

def search_emails(
    user_id: str,
    query: str,
    limit: int = 10,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pesquisa emails por texto.
    Wrapper simplificado de list_emails para pesquisas.

    Args:
        user_id: ID do utilizador
        query: Texto para pesquisar
        limit: Numero maximo de resultados (default: 10)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com emails encontrados

    Exemplo:
        result = search_emails("user-123", "reuniao projeto", limit=15)
    """
    if not query:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "Query de pesquisa e obrigatoria",
        }

    return list_emails(
        user_id=user_id,
        query=query,
        limit=limit,
        tenant_id=tenant_id,
    )


# =============================================================================
# INTERFACE DE EXECUCAO (para uso direto via terminal ou por agente)
# =============================================================================

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool (list_emails, get_email_detail,
                   send_email, search_emails)
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execucao
    """
    tools = {
        "list_emails": list_emails,
        "email_list_emails": list_emails,
        "get_email_detail": get_email_detail,
        "email_get_email_detail": get_email_detail,
        "get_email": get_email_detail,
        "email_get_email": get_email_detail,
        "send_email": send_email,
        "email_send_email": send_email,
        "search_emails": search_emails,
        "email_search_emails": search_emails,
    }

    if tool_name not in tools:
        return {
            "error": "Tool '{}' nao encontrada".format(tool_name),
            "available_tools": list(set(tools.keys())),
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
    print("  list_emails <user_id> [--query=...] [--from=...] [--since=...] [--limit=10]")
    print("  get_email <user_id> <email_id>")
    print("  send_email <user_id> <to> <subject> <body>")
    print("  search_emails <user_id> <query> [--limit=10]")
    print("\nExemplos:")
    print('  python email_client.py list_emails user-123 --limit=5')
    print('  python email_client.py get_email user-123 msg-abc123')
    print('  python email_client.py send_email user-123 "dest@email.pt" "Assunto" "Corpo do email"')
    print('  python email_client.py search_emails user-123 "reuniao" --limit=10')


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

    if tool_name in ["list_emails", "email_list_emails"]:
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            print("Uso: python email_client.py list_emails <user_id> [--query=...] [--from=...] [--since=...] [--limit=10]")
            sys.exit(1)

        user_id = positional[0]
        try:
            limit = int(named.get("limit", 10))
        except ValueError:
            limit = 10
        result = list_emails(
            user_id=user_id,
            query=named.get("query"),
            from_email=named.get("from"),
            since=named.get("since"),
            limit=limit,
        )

    elif tool_name in ["get_email", "get_email_detail", "email_get_email"]:
        if len(positional) < 2:
            print("Erro: user_id e email_id obrigatorios")
            print("Uso: python email_client.py get_email <user_id> <email_id>")
            sys.exit(1)

        user_id = positional[0]
        email_id = positional[1]
        result = get_email_detail(user_id=user_id, email_id=email_id)

    elif tool_name in ["send_email", "email_send_email"]:
        if len(positional) < 4:
            print("Erro: user_id, to, subject e body obrigatorios")
            print("Uso: python email_client.py send_email <user_id> <to> <subject> <body>")
            print('Exemplo: python email_client.py send_email user-123 "dest@email.pt" "Assunto" "Corpo"')
            sys.exit(1)

        user_id = positional[0]
        to = positional[1].split(",")  # Suporta multiplos destinatarios separados por virgula
        subject = positional[2]
        body = positional[3]
        result = send_email(
            user_id=user_id,
            to=to,
            subject=subject,
            body_text=body,
        )

    elif tool_name in ["search_emails", "email_search_emails"]:
        if len(positional) < 2:
            print("Erro: user_id e query obrigatorios")
            print("Uso: python email_client.py search_emails <user_id> <query> [--limit=10]")
            sys.exit(1)

        user_id = positional[0]
        query = positional[1]
        try:
            limit = int(named.get("limit", 10))
        except ValueError:
            limit = 10
        result = search_emails(
            user_id=user_id,
            query=query,
            limit=limit,
        )

    else:
        print("Erro: Tool '{}' nao reconhecida".format(tool_name))
        print("\nTools disponiveis:")
        print("  list_emails, get_email, send_email, search_emails")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
