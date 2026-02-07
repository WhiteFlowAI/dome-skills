#!/usr/bin/env python3
"""
Calendar Client Standalone Tool
Gere eventos no Google Calendar ou Microsoft Outlook Calendar.

Este script e independente e comunica com o BFF (Backend for Frontend)
que gere a autenticacao OAuth com os providers de calendario.

Requisitos: pip install requests

Uso CLI:
    python calendar_client.py list_events <user_id> [--time_min=...] [--time_max=...] [--query=...] [--max_results=10]
    python calendar_client.py get_event <user_id> <event_id>
    python calendar_client.py create_event <user_id> <summary> [--start_date_time=...] [--end_date_time=...] [--start_date=...] [--end_date=...] [--description=...] [--location=...] [--attendees=...] [--add_conference]
    python calendar_client.py update_event <user_id> <event_id> [--summary=...] [--description=...] [--location=...] [--start_date_time=...] [--end_date_time=...]
    python calendar_client.py delete_event <user_id> <event_id>
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
        path: Caminho do endpoint (ex: /internal/calendar/events)
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
        path: Caminho do endpoint (ex: /internal/calendar/events)
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
            "error_code": data.get("code", "CALENDAR_PROVIDER_AUTH_FAILED"),
            "message": data.get("message", "Erro de autenticacao com o provider de calendario"),
            "reauthorization_required": data.get("reauthorization_required", True),
            "provider": data.get("provider"),
            "action_url": data.get("action_url"),
        }

    # Evento nao encontrado (404)
    if response.status_code == 404:
        return {
            "status": "error",
            "error_code": data.get("code", "CALENDAR_EVENT_NOT_FOUND"),
            "message": data.get("message", "Evento nao encontrado"),
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
# TOOL 1: LISTAR EVENTOS
# =============================================================================

def list_events(
    user_id: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    query: Optional[str] = None,
    max_results: int = 10,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lista eventos do calendario do utilizador.

    Args:
        user_id: ID do utilizador
        time_min: Data minima no formato RFC3339 (ex: '2025-01-15T00:00:00Z')
        time_max: Data maxima no formato RFC3339
        query: Texto para pesquisar no titulo/descricao (opcional)
        max_results: Numero maximo de eventos (default: 10, max: 100)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de eventos

    Exemplo:
        result = list_events("user-123", time_min="2025-01-15T00:00:00Z", max_results=20)
    """
    # Validar max_results
    if max_results < 1:
        max_results = 1
    elif max_results > 100:
        max_results = 100

    # Construir parametros de query
    query_params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "q": query,
        "maxResults": max_results,
    }

    result = _make_get_request(
        path="/internal/calendar/events",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    # Processar resposta
    events_data = result.get("data", {})

    # O BFF retorna { events: [...] }
    if isinstance(events_data, dict) and "events" in events_data:
        events_list = events_data.get("events", [])
        return {
            "status": "success",
            "total": len(events_list),
            "events": events_list,
        }

    # Se for uma lista diretamente
    if isinstance(events_data, list):
        return {
            "status": "success",
            "total": len(events_data),
            "events": events_data,
        }

    return {
        "status": "success",
        "total": 0,
        "events": [],
    }


# =============================================================================
# TOOL 2: OBTER DETALHES DE UM EVENTO
# =============================================================================

def get_event_detail(
    user_id: str,
    event_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem detalhes completos de um evento especifico.

    Args:
        user_id: ID do utilizador
        event_id: ID do evento a obter
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com detalhes do evento

    Exemplo:
        result = get_event_detail("user-123", "evt-abc123")
    """
    if not event_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "event_id e obrigatorio",
        }

    # URL encode do event_id para seguranca
    safe_event_id = quote(event_id, safe='')

    result = _make_get_request(
        path=f"/internal/calendar/events/{safe_event_id}",
        user_id=user_id,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    event_data = result.get("data", {})

    # O BFF pode retornar { event: {...} } ou o evento diretamente
    if isinstance(event_data, dict) and "event" in event_data:
        return {
            "status": "success",
            "event": event_data.get("event"),
        }

    return {
        "status": "success",
        "event": event_data,
    }


# =============================================================================
# TOOL 3: CRIAR EVENTO
# =============================================================================

def create_event(
    user_id: str,
    summary: str,
    start_date_time: Optional[str] = None,
    end_date_time: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    add_conference: bool = False,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria um novo evento no calendario.

    Args:
        user_id: ID do utilizador
        summary: Titulo do evento
        start_date_time: Inicio em RFC3339 para eventos com hora (ex: '2025-01-20T10:00:00Z')
        end_date_time: Fim em RFC3339 para eventos com hora
        start_date: Inicio em YYYY-MM-DD para eventos de dia inteiro
        end_date: Fim em YYYY-MM-DD para eventos de dia inteiro
        description: Descricao do evento (opcional)
        location: Localizacao (opcional)
        attendees: Lista de emails dos participantes (opcional)
        add_conference: Se True, cria link de videoconferencia (Google Meet ou Teams)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da criacao

    Exemplo:
        # Evento com hora
        result = create_event(
            user_id="user-123",
            summary="Reuniao",
            start_date_time="2025-01-20T10:00:00Z",
            end_date_time="2025-01-20T11:00:00Z"
        )

        # Evento de dia inteiro
        result = create_event(
            user_id="user-123",
            summary="Feriado",
            start_date="2025-01-20",
            end_date="2025-01-21"
        )
    """
    # Validacoes
    if not summary:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "summary (titulo) e obrigatorio",
        }

    # Validar que tem pelo menos uma combinacao start/end
    has_date_time = start_date_time and end_date_time
    has_date = start_date and end_date

    if not has_date_time and not has_date:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "Deve fornecer (start_date_time + end_date_time) OU (start_date + end_date). "
                       "Para eventos com hora, use formato RFC3339 como '2025-01-20T10:00:00Z'. "
                       "Para eventos de dia inteiro, use formato YYYY-MM-DD como '2025-01-20'.",
        }

    # Construir body do request
    request_body = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {
            "dateTime": start_date_time,
            "date": start_date,
        },
        "end": {
            "dateTime": end_date_time,
            "date": end_date,
        },
        "attendees": attendees,
        "addConference": add_conference,
    }

    result = _make_post_request(
        path="/internal/calendar/events",
        user_id=user_id,
        body=request_body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    event_data = result.get("data", {})

    response = {
        "status": "success",
        "event_id": event_data.get("id"),
        "html_link": event_data.get("htmlLink"),
    }

    if event_data.get("hangoutLink"):
        response["hangout_link"] = event_data.get("hangoutLink")
        response["message"] = "Evento criado com sucesso com link de videoconferencia"
    else:
        response["message"] = "Evento criado com sucesso"

    return response


# =============================================================================
# TOOL 4: ATUALIZAR EVENTO
# =============================================================================

def update_event(
    user_id: str,
    event_id: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    start_date_time: Optional[str] = None,
    end_date_time: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atualiza um evento existente.

    Args:
        user_id: ID do utilizador
        event_id: ID do evento a atualizar
        summary: Novo titulo (opcional)
        description: Nova descricao (opcional)
        location: Nova localizacao (opcional)
        start_date_time: Novo inicio em RFC3339 (opcional)
        end_date_time: Novo fim em RFC3339 (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da atualizacao

    Exemplo:
        result = update_event(
            user_id="user-123",
            event_id="evt-abc123",
            summary="Novo titulo",
            start_date_time="2025-01-20T14:00:00Z",
            end_date_time="2025-01-20T15:00:00Z"
        )
    """
    if not event_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "event_id e obrigatorio",
        }

    # Verificar se ha algo para atualizar
    if not any([summary, description, location, start_date_time, end_date_time]):
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "Deve fornecer pelo menos um campo para atualizar",
        }

    # Construir body do request - apenas com campos fornecidos
    request_body = {}

    if summary is not None:
        request_body["summary"] = summary
    if description is not None:
        request_body["description"] = description
    if location is not None:
        request_body["location"] = location

    if start_date_time is not None:
        request_body["start"] = {"dateTime": start_date_time}
    if end_date_time is not None:
        request_body["end"] = {"dateTime": end_date_time}

    # URL encode do event_id para seguranca
    safe_event_id = quote(event_id, safe='')

    result = _make_post_request(
        path=f"/internal/calendar/events/{safe_event_id}",
        user_id=user_id,
        body=request_body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    event_data = result.get("data", {})

    # O BFF pode retornar { event: {...} } ou o evento diretamente
    if isinstance(event_data, dict) and "event" in event_data:
        return {
            "status": "success",
            "event": event_data.get("event"),
            "message": "Evento atualizado com sucesso",
        }

    return {
        "status": "success",
        "event": event_data,
        "message": "Evento atualizado com sucesso",
    }


# =============================================================================
# TOOL 5: APAGAR EVENTO
# =============================================================================

def delete_event(
    user_id: str,
    event_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apaga um evento do calendario.

    Args:
        user_id: ID do utilizador
        event_id: ID do evento a apagar
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da operacao

    Exemplo:
        result = delete_event("user-123", "evt-abc123")
    """
    if not event_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "event_id e obrigatorio",
        }

    # URL encode do event_id para seguranca
    safe_event_id = quote(event_id, safe='')

    result = _make_post_request(
        path=f"/internal/calendar/events/{safe_event_id}/delete",
        user_id=user_id,
        body={},
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "message": f"Evento {event_id} apagado com sucesso",
    }


# =============================================================================
# INTERFACE DE EXECUCAO (para uso direto via terminal ou por agente)
# =============================================================================

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool (list_events, get_event_detail, create_event,
                   update_event, delete_event)
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execucao
    """
    tools = {
        "list_events": list_events,
        "calendar_list_events": list_events,
        "get_event_detail": get_event_detail,
        "calendar_get_event_detail": get_event_detail,
        "get_event": get_event_detail,
        "calendar_get_event": get_event_detail,
        "create_event": create_event,
        "calendar_create_event": create_event,
        "update_event": update_event,
        "calendar_update_event": update_event,
        "delete_event": delete_event,
        "calendar_delete_event": delete_event,
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
    print("  list_events <user_id> [--time_min=...] [--time_max=...] [--query=...] [--max_results=10]")
    print("  get_event <user_id> <event_id>")
    print("  create_event <user_id> <summary> [--start_date_time=...] [--end_date_time=...] [--start_date=...] [--end_date=...] [--description=...] [--location=...] [--attendees=...] [--add_conference]")
    print("  update_event <user_id> <event_id> [--summary=...] [--description=...] [--location=...] [--start_date_time=...] [--end_date_time=...]")
    print("  delete_event <user_id> <event_id>")
    print("\nExemplos:")
    print('  python calendar_client.py list_events user-123 --max_results=5')
    print('  python calendar_client.py list_events user-123 --time_min="2025-01-15T00:00:00Z" --query="reuniao"')
    print('  python calendar_client.py get_event user-123 evt-abc123')
    print('  python calendar_client.py create_event user-123 "Reuniao Projeto" --start_date_time="2025-01-20T10:00:00Z" --end_date_time="2025-01-20T11:00:00Z"')
    print('  python calendar_client.py create_event user-123 "Feriado" --start_date="2025-01-20" --end_date="2025-01-21"')
    print('  python calendar_client.py update_event user-123 evt-abc123 --summary="Novo titulo"')
    print('  python calendar_client.py delete_event user-123 evt-abc123')


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

    if tool_name in ["list_events", "calendar_list_events"]:
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            print("Uso: python calendar_client.py list_events <user_id> [--time_min=...] [--time_max=...] [--query=...] [--max_results=10]")
            sys.exit(1)

        user_id = positional[0]
        try:
            max_results = int(named.get("max_results", 10))
        except ValueError:
            max_results = 10
        result = list_events(
            user_id=user_id,
            time_min=named.get("time_min"),
            time_max=named.get("time_max"),
            query=named.get("query"),
            max_results=max_results,
        )

    elif tool_name in ["get_event", "get_event_detail", "calendar_get_event"]:
        if len(positional) < 2:
            print("Erro: user_id e event_id obrigatorios")
            print("Uso: python calendar_client.py get_event <user_id> <event_id>")
            sys.exit(1)

        user_id = positional[0]
        event_id = positional[1]
        result = get_event_detail(user_id=user_id, event_id=event_id)

    elif tool_name in ["create_event", "calendar_create_event"]:
        if len(positional) < 2:
            print("Erro: user_id e summary obrigatorios")
            print("Uso: python calendar_client.py create_event <user_id> <summary> [--start_date_time=...] [--end_date_time=...] [--start_date=...] [--end_date=...] [--description=...] [--location=...] [--attendees=...] [--add_conference]")
            sys.exit(1)

        user_id = positional[0]
        summary = positional[1]

        # Parse attendees se fornecido (separados por virgula)
        attendees = None
        if named.get("attendees"):
            attendees = [email.strip() for email in named.get("attendees").split(",")]

        # add_conference e flag booleana
        add_conference = named.get("add_conference", False)
        if isinstance(add_conference, str):
            add_conference = add_conference.lower() in ("true", "1", "yes")

        result = create_event(
            user_id=user_id,
            summary=summary,
            start_date_time=named.get("start_date_time"),
            end_date_time=named.get("end_date_time"),
            start_date=named.get("start_date"),
            end_date=named.get("end_date"),
            description=named.get("description"),
            location=named.get("location"),
            attendees=attendees,
            add_conference=add_conference,
        )

    elif tool_name in ["update_event", "calendar_update_event"]:
        if len(positional) < 2:
            print("Erro: user_id e event_id obrigatorios")
            print("Uso: python calendar_client.py update_event <user_id> <event_id> [--summary=...] [--description=...] [--location=...] [--start_date_time=...] [--end_date_time=...]")
            sys.exit(1)

        user_id = positional[0]
        event_id = positional[1]
        result = update_event(
            user_id=user_id,
            event_id=event_id,
            summary=named.get("summary"),
            description=named.get("description"),
            location=named.get("location"),
            start_date_time=named.get("start_date_time"),
            end_date_time=named.get("end_date_time"),
        )

    elif tool_name in ["delete_event", "calendar_delete_event"]:
        if len(positional) < 2:
            print("Erro: user_id e event_id obrigatorios")
            print("Uso: python calendar_client.py delete_event <user_id> <event_id>")
            sys.exit(1)

        user_id = positional[0]
        event_id = positional[1]
        result = delete_event(user_id=user_id, event_id=event_id)

    else:
        print("Erro: Tool '{}' nao reconhecida".format(tool_name))
        print("\nTools disponiveis:")
        print("  list_events, get_event, create_event, update_event, delete_event")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
