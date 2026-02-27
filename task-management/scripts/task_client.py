#!/usr/bin/env python3
"""
Task Management Client Standalone Tool
Gere tarefas do utilizador: listar, criar, atualizar estado e anexar ficheiros.

Este script e independente e comunica com o BFF (Backend for Frontend)
para aceder e manipular as tarefas do utilizador autenticado.

Requisitos: pip install requests

Uso CLI:
    python task_client.py list_tasks <user_id> [--status=...] [--type=...] [--limit=20] [--tenant_id=...]
    python task_client.py get_task <user_id> <task_id> [--tenant_id=...]
    python task_client.py create_task <user_id> <description> [--title=...] [--tenant_id=...]
    python task_client.py update_task <user_id> <task_id> [--title=...] [--description=...] [--priority=...] [--tenant_id=...]
    python task_client.py update_task_status <user_id> <task_id> <status> [--tenant_id=...]
    python task_client.py get_task_events <user_id> <task_id> [--limit=50] [--tenant_id=...]
    python task_client.py list_artifacts <user_id> <task_id> [--type=...] [--tenant_id=...]
    python task_client.py get_task_output <user_id> <task_id> [--tenant_id=...]
    python task_client.py add_artifact <user_id> <task_id> <name> <type> [--content=...] [--storage_url=...] [--mime_type=...] [--tenant_id=...]
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
# HTTP REQUEST HELPERS
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
        path: Caminho do endpoint (ex: /internal/tasks)
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
            "message": "Request timeout after {} seconds".format(TIMEOUT_SECONDS),
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
        path: Caminho do endpoint
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
            url, headers=headers, json=body or {}, timeout=TIMEOUT_SECONDS
        )
        return _process_response(response)

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_code": "TIMEOUT",
            "message": "Request timeout after {} seconds".format(TIMEOUT_SECONDS),
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_code": "REQUEST_ERROR",
            "message": str(e),
        }


def _make_patch_request(
    path: str,
    user_id: str,
    body: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Faz um request HTTP PATCH para o BFF.

    Args:
        path: Caminho do endpoint
        user_id: ID do utilizador
        body: Corpo do request (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Resposta do BFF
    """
    url = f"{BFF_BASE_URL}{path}"
    headers = _build_headers(user_id, tenant_id)

    try:
        response = requests.patch(
            url, headers=headers, json=body or {}, timeout=TIMEOUT_SECONDS
        )
        return _process_response(response)

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_code": "TIMEOUT",
            "message": "Request timeout after {} seconds".format(TIMEOUT_SECONDS),
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

    # Task nao encontrada (404)
    if response.status_code == 404:
        return {
            "status": "error",
            "error_code": data.get("code", "TASK_NOT_FOUND"),
            "message": data.get("message", "Task not found"),
        }

    # Acesso negado (403)
    if response.status_code == 403:
        return {
            "status": "error",
            "error_code": data.get("code", "FORBIDDEN"),
            "message": data.get("message", "Access denied to this task"),
        }

    # Request invalido (400)
    if response.status_code == 400:
        return {
            "status": "error",
            "error_code": data.get("code", "INVALID_REQUEST"),
            "message": data.get("message", "Invalid request"),
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
# TOOL 1: LISTAR TAREFAS
# =============================================================================

def list_tasks(
    user_id: str,
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lista as tarefas do utilizador com filtros opcionais.

    Args:
        user_id: ID do utilizador
        status: Filtrar por estado (ex: 'created', 'pending', 'running', 'completed',
                'failed', 'cancelled', 'planning', 'approval_plan_request')
        type: Filtrar por tipo de tarefa (ex: 'default', 'workflow', 'deep_research')
        limit: Numero maximo de tarefas a retornar (default: 20, max: 100)
        offset: Posicao inicial para paginacao (default: 0)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de tarefas

    Exemplo:
        result = list_tasks("user-123")
        result = list_tasks("user-123", status="running")
        result = list_tasks("user-123", status="pending", type="workflow")
    """
    # Validar limit
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100

    # Validar offset
    if offset < 0:
        offset = 0

    # Construir parametros de query
    query_params = {
        "status": status,
        "type": type,
        "limit": limit,
        "offset": offset,
    }

    result = _make_get_request(
        path="/internal/tasks",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    # Processar resposta
    tasks_data = result.get("data", [])

    if isinstance(tasks_data, list):
        return {
            "status": "success",
            "total": len(tasks_data),
            "tasks": tasks_data,
        }

    return {
        "status": "success",
        "total": 0,
        "tasks": [],
    }


# =============================================================================
# TOOL 2: OBTER TAREFA ESPECIFICA
# =============================================================================

def get_task(
    user_id: str,
    task_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem os detalhes de uma tarefa especifica.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id, ex: 'TSK-001')
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com detalhes da tarefa

    Exemplo:
        result = get_task("user-123", "550e8400-e29b-41d4-a716-446655440000")
        result = get_task("user-123", "TSK-001")
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }

    safe_task_id = quote(task_id, safe='')

    result = _make_get_request(
        path=f"/internal/tasks/{safe_task_id}",
        user_id=user_id,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "task": result.get("data", {}),
    }


# =============================================================================
# TOOL 3: CRIAR TAREFA
# =============================================================================

def create_task(
    user_id: str,
    description: str,
    title: Optional[str] = None,
    type: str = "default",
    priority: str = "medium",
    kanban_column: str = "backlog",
    conversation_id: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria uma nova tarefa.

    O campo principal e a descricao (o que o utilizador quer que seja feito).
    O titulo e gerado automaticamente pelo sistema a partir da descricao.
    Tipo e sempre 'default' e prioridade e sempre 'medium' - NAO pedir ao utilizador.

    Args:
        user_id: ID do utilizador
        description: Descricao detalhada do que o utilizador quer (obrigatorio).
                     O agente deve enriquecer e melhorar o texto fornecido pelo utilizador.
        title: Titulo curto (opcional - gerado automaticamente pelo sistema se nao fornecido)
        type: Tipo de tarefa (default: 'default'). NAO alterar.
        priority: Prioridade (default: 'medium'). NAO alterar.
        kanban_column: Coluna kanban (default: 'backlog')
        conversation_id: ID da conversa associada (opcional)
        scheduled_at: Data agendada no formato ISO 8601 (opcional, apenas se o utilizador mencionar)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com a tarefa criada

    Exemplo:
        result = create_task("user-123", description="Preparar o relatorio mensal de vendas com dados do ultimo trimestre")
        result = create_task("user-123", description="Enviar email ao cliente para confirmar a reuniao de amanha as 15h")
    """
    if not description:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "description is required",
        }

    body = {
        "description": description,
        "type": type,
        "priority": priority,
        "kanban_column": kanban_column,
    }

    if title:
        body["title"] = title
    if conversation_id:
        body["conversation_id"] = conversation_id
    if scheduled_at:
        body["scheduled_at"] = scheduled_at

    result = _make_post_request(
        path="/internal/tasks",
        user_id=user_id,
        body=body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "task": result.get("data", {}),
    }


# =============================================================================
# TOOL 4: ATUALIZAR TAREFA
# =============================================================================

def update_task(
    user_id: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    kanban_column: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atualiza campos de uma tarefa (titulo, descricao, prioridade, etc.).
    NAO altera o estado - para isso usar update_task_status.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id)
        title: Novo titulo (opcional)
        description: Nova descricao (opcional)
        priority: Nova prioridade: 'low', 'medium', 'high', 'urgent' (opcional)
        kanban_column: Nova coluna kanban (opcional)
        scheduled_at: Nova data agendada em ISO 8601 (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com a tarefa atualizada

    Exemplo:
        result = update_task("user-123", "TSK-001", title="Novo titulo")
        result = update_task("user-123", "TSK-001", priority="urgent", description="Atualizado com urgencia")
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }

    # Construir body apenas com campos fornecidos
    body = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if priority is not None:
        body["priority"] = priority
    if kanban_column is not None:
        body["kanban_column"] = kanban_column
    if scheduled_at is not None:
        body["scheduled_at"] = scheduled_at

    if not body:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "At least one field to update is required",
        }

    safe_task_id = quote(task_id, safe='')

    result = _make_patch_request(
        path=f"/internal/tasks/{safe_task_id}",
        user_id=user_id,
        body=body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "task": result.get("data", {}),
    }


# =============================================================================
# TOOL 5: ATUALIZAR ESTADO DA TAREFA
# =============================================================================

def update_task_status(
    user_id: str,
    task_id: str,
    status: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atualiza o estado de uma tarefa.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id)
        status: Novo estado. Valores validos:
                'created', 'pending', 'running', 'completed', 'failed', 'cancelled'
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com a tarefa atualizada

    Exemplo:
        result = update_task_status("user-123", "TSK-001", "running")
        result = update_task_status("user-123", "TSK-001", "completed")
        result = update_task_status("user-123", "TSK-001", "cancelled")
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }

    if not status:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "status is required",
        }

    valid_statuses = ["created", "pending", "running", "completed", "failed", "cancelled"]
    if status not in valid_statuses:
        return {
            "status": "error",
            "error_code": "INVALID_STATUS",
            "message": "Status must be one of: {}".format(", ".join(valid_statuses)),
        }

    safe_task_id = quote(task_id, safe='')

    result = _make_patch_request(
        path=f"/internal/tasks/{safe_task_id}/status",
        user_id=user_id,
        body={"status": status},
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "task": result.get("data", {}),
    }


# =============================================================================
# TOOL 6: OBTER EVENTOS DA TAREFA
# =============================================================================

def get_task_events(
    user_id: str,
    task_id: str,
    limit: int = 50,
    offset: int = 0,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem o historico de eventos de uma tarefa.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id)
        limit: Numero maximo de eventos (default: 50, max: 200)
        offset: Posicao inicial para paginacao (default: 0)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de eventos

    Exemplo:
        result = get_task_events("user-123", "TSK-001")
        result = get_task_events("user-123", "TSK-001", limit=10)
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }

    # Validar limit
    if limit < 1:
        limit = 1
    elif limit > 200:
        limit = 200

    if offset < 0:
        offset = 0

    safe_task_id = quote(task_id, safe='')

    query_params = {
        "limit": limit,
        "offset": offset,
    }

    result = _make_get_request(
        path=f"/internal/tasks/{safe_task_id}/events",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    events_data = result.get("data", [])

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
# TOOL 7: LISTAR ARTEFACTOS DA TAREFA
# =============================================================================

def list_artifacts(
    user_id: str,
    task_id: str,
    type: Optional[str] = None,
    artifact_kind: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lista os artefactos (ficheiros, documentos) associados a uma tarefa.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id)
        type: Filtrar por tipo de artefacto (ex: 'input_document', 'output', 'plan') (opcional)
        artifact_kind: Filtrar por kind (ex: 'file') (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de artefactos

    Exemplo:
        result = list_artifacts("user-123", "TSK-001")
        result = list_artifacts("user-123", "TSK-001", type="input_document")
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }

    safe_task_id = quote(task_id, safe='')

    query_params = {
        "type": type,
        "artifact_kind": artifact_kind,
    }

    result = _make_get_request(
        path=f"/internal/tasks/{safe_task_id}/artifacts",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    artifacts_data = result.get("data", [])

    if isinstance(artifacts_data, list):
        return {
            "status": "success",
            "total": len(artifacts_data),
            "artifacts": artifacts_data,
        }

    return {
        "status": "success",
        "total": 0,
        "artifacts": [],
    }


# =============================================================================
# TOOL 8: OBTER OUTPUT/RESULTADO DE UMA TAREFA
# =============================================================================

def get_task_output(
    user_id: str,
    task_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem o resultado/output de uma tarefa concluida.

    Retorna os artefactos de tipo 'output_artifact' que contem o conteudo
    gerado pela execucao da tarefa. Usar esta funcao para consultar resultados
    de tarefas anteriores sem precisar de re-executar.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id, ex: 'TSK-001')
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com os outputs da tarefa. Cada output tem:
        - name: Nome do artefacto
        - content: Conteudo completo do resultado (texto, JSON, etc.)
        - storage_url: URL se armazenado externamente
        - metadata: Informacoes adicionais (tipo de output, resumo, etc.)

    Exemplo:
        # Obter resultado de uma tarefa que buscou emails
        result = get_task_output("user-123", "TSK-001")
        if result.get('status') == 'success':
            for output in result.get('outputs', []):
                print(f"Output: {output.get('name')}")
                print(f"Conteudo: {output.get('content')}")
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }

    safe_task_id = quote(task_id, safe='')

    # Buscar artefactos do tipo output_artifact
    query_params = {
        "type": "output_artifact",
    }

    result = _make_get_request(
        path=f"/internal/tasks/{safe_task_id}/artifacts",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    artifacts_data = result.get("data", [])

    if isinstance(artifacts_data, list) and len(artifacts_data) > 0:
        outputs = []
        for artifact in artifacts_data:
            outputs.append({
                "id": artifact.get("id"),
                "name": artifact.get("name"),
                "content": artifact.get("content"),
                "storage_url": artifact.get("storage_url"),
                "mime_type": artifact.get("mime_type"),
                "metadata": artifact.get("metadata"),
                "version": artifact.get("version"),
                "created_at": artifact.get("created_at"),
            })

        return {
            "status": "success",
            "total": len(outputs),
            "outputs": outputs,
        }

    return {
        "status": "success",
        "total": 0,
        "outputs": [],
        "message": "No outputs found for this task. The task may not have completed yet or may not produce output artifacts.",
    }


# =============================================================================
# TOOL 9: ADICIONAR ARTEFACTO A TAREFA
# =============================================================================

def add_artifact(
    user_id: str,
    task_id: str,
    name: str,
    type: str,
    content: Optional[str] = None,
    storage_url: Optional[str] = None,
    mime_type: Optional[str] = None,
    size_bytes: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Adiciona um artefacto (ficheiro, documento) a uma tarefa.

    Args:
        user_id: ID do utilizador
        task_id: ID da tarefa (UUID ou display_id)
        name: Nome do artefacto / ficheiro (obrigatorio)
        type: Tipo do artefacto (obrigatorio). Exemplos:
              'input_document' - Documento de input para a tarefa
              'output' - Resultado gerado pela tarefa
              'reference' - Material de referencia
        content: Conteudo textual do artefacto (opcional)
        storage_url: URL se armazenado externamente (opcional)
        mime_type: Tipo MIME (ex: 'text/plain', 'application/pdf') (opcional)
        size_bytes: Tamanho do ficheiro em bytes (opcional)
        metadata: Metadados adicionais (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com o artefacto criado

    Exemplo:
        result = add_artifact("user-123", "TSK-001", "notas.txt", "input_document", content="Notas da reuniao...")
        result = add_artifact("user-123", "TSK-001", "relatorio.pdf", "reference", storage_url="https://...", mime_type="application/pdf")
    """
    if not task_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "task_id is required",
        }
    if not name:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "name is required",
        }
    if not type:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "type is required",
        }

    safe_task_id = quote(task_id, safe='')

    body = {
        "name": name,
        "type": type,
    }
    if content is not None:
        body["content"] = content
    if storage_url is not None:
        body["storage_url"] = storage_url
    if mime_type is not None:
        body["mime_type"] = mime_type
    if size_bytes is not None:
        body["size_bytes"] = size_bytes
    if metadata is not None:
        body["metadata"] = metadata

    result = _make_post_request(
        path=f"/internal/tasks/{safe_task_id}/artifacts",
        user_id=user_id,
        body=body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "artifact": result.get("data", {}),
    }


# =============================================================================
# INTERFACE DE EXECUCAO (para uso direto via terminal ou por agente)
# =============================================================================

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execucao
    """
    tools = {
        "list_tasks": list_tasks,
        "task_management_list_tasks": list_tasks,
        "get_task": get_task,
        "task_management_get_task": get_task,
        "create_task": create_task,
        "task_management_create_task": create_task,
        "update_task": update_task,
        "task_management_update_task": update_task,
        "update_task_status": update_task_status,
        "task_management_update_task_status": update_task_status,
        "get_task_events": get_task_events,
        "task_management_get_task_events": get_task_events,
        "list_artifacts": list_artifacts,
        "task_management_list_artifacts": list_artifacts,
        "get_task_output": get_task_output,
        "task_management_get_task_output": get_task_output,
        "add_artifact": add_artifact,
        "task_management_add_artifact": add_artifact,
    }

    if tool_name not in tools:
        return {
            "error": "Tool '{}' not found".format(tool_name),
            "available_tools": [
                "list_tasks", "get_task", "create_task",
                "update_task", "update_task_status",
                "get_task_events", "list_artifacts", "get_task_output",
                "add_artifact",
            ],
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
    print("  list_tasks <user_id> [--status=...] [--type=...] [--limit=20] [--tenant_id=...]")
    print("  get_task <user_id> <task_id> [--tenant_id=...]")
    print("  create_task <user_id> <description> [--title=...] [--tenant_id=...]")
    print("  update_task <user_id> <task_id> [--title=...] [--description=...] [--priority=...] [--tenant_id=...]")
    print("  update_task_status <user_id> <task_id> <status> [--tenant_id=...]")
    print("  get_task_events <user_id> <task_id> [--limit=50] [--tenant_id=...]")
    print("  list_artifacts <user_id> <task_id> [--type=...] [--tenant_id=...]")
    print("  get_task_output <user_id> <task_id> [--tenant_id=...]")
    print("  add_artifact <user_id> <task_id> <name> <type> [--content=...] [--storage_url=...] [--mime_type=...] [--tenant_id=...]")


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

    if tool_name in ["list_tasks", "task_management_list_tasks"]:
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            sys.exit(1)

        user_id = positional[0]
        try:
            limit = int(named.get("limit", 20))
        except ValueError:
            limit = 20

        try:
            offset_val = int(named.get("offset", 0))
        except ValueError:
            offset_val = 0

        result = list_tasks(
            user_id=user_id,
            status=named.get("status"),
            type=named.get("type"),
            limit=limit,
            offset=offset_val,
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["get_task", "task_management_get_task"]:
        if len(positional) < 2:
            print("Erro: user_id e task_id obrigatorios")
            sys.exit(1)

        result = get_task(
            user_id=positional[0],
            task_id=positional[1],
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["create_task", "task_management_create_task"]:
        if len(positional) < 2:
            print("Erro: user_id e description obrigatorios")
            sys.exit(1)

        result = create_task(
            user_id=positional[0],
            description=positional[1],
            title=named.get("title"),
            type=named.get("type", "default"),
            priority=named.get("priority", "medium"),
            kanban_column=named.get("kanban_column", "backlog"),
            conversation_id=named.get("conversation_id"),
            scheduled_at=named.get("scheduled_at"),
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["update_task", "task_management_update_task"]:
        if len(positional) < 2:
            print("Erro: user_id e task_id obrigatorios")
            sys.exit(1)

        result = update_task(
            user_id=positional[0],
            task_id=positional[1],
            title=named.get("title"),
            description=named.get("description"),
            priority=named.get("priority"),
            kanban_column=named.get("kanban_column"),
            scheduled_at=named.get("scheduled_at"),
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["update_task_status", "task_management_update_task_status"]:
        if len(positional) < 3:
            print("Erro: user_id, task_id e status obrigatorios")
            sys.exit(1)

        result = update_task_status(
            user_id=positional[0],
            task_id=positional[1],
            status=positional[2],
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["get_task_events", "task_management_get_task_events"]:
        if len(positional) < 2:
            print("Erro: user_id e task_id obrigatorios")
            sys.exit(1)

        try:
            limit = int(named.get("limit", 50))
        except ValueError:
            limit = 50

        try:
            offset_val = int(named.get("offset", 0))
        except ValueError:
            offset_val = 0

        result = get_task_events(
            user_id=positional[0],
            task_id=positional[1],
            limit=limit,
            offset=offset_val,
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["list_artifacts", "task_management_list_artifacts"]:
        if len(positional) < 2:
            print("Erro: user_id e task_id obrigatorios")
            sys.exit(1)

        result = list_artifacts(
            user_id=positional[0],
            task_id=positional[1],
            type=named.get("type"),
            artifact_kind=named.get("artifact_kind"),
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["get_task_output", "task_management_get_task_output"]:
        if len(positional) < 2:
            print("Erro: user_id e task_id obrigatorios")
            sys.exit(1)

        result = get_task_output(
            user_id=positional[0],
            task_id=positional[1],
            tenant_id=named.get("tenant_id"),
        )

    elif tool_name in ["add_artifact", "task_management_add_artifact"]:
        if len(positional) < 4:
            print("Erro: user_id, task_id, name e type obrigatorios")
            sys.exit(1)

        metadata = None
        if named.get("metadata"):
            try:
                metadata = json.loads(named["metadata"])
            except json.JSONDecodeError:
                metadata = None

        size_bytes = None
        if named.get("size_bytes"):
            try:
                size_bytes = int(named["size_bytes"])
            except ValueError:
                size_bytes = None

        result = add_artifact(
            user_id=positional[0],
            task_id=positional[1],
            name=positional[2],
            type=positional[3],
            content=named.get("content"),
            storage_url=named.get("storage_url"),
            mime_type=named.get("mime_type"),
            size_bytes=size_bytes,
            metadata=metadata,
            tenant_id=named.get("tenant_id"),
        )

    else:
        print("Erro: Tool '{}' nao reconhecida".format(tool_name))
        print("\nTools disponiveis:")
        print("  list_tasks, get_task, create_task, update_task,")
        print("  update_task_status, get_task_events, list_artifacts,")
        print("  get_task_output, add_artifact")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
