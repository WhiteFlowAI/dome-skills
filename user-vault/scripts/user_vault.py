#!/usr/bin/env python3
"""
User Vault - Standalone Tool
Gere contexto, documentos e knowledge do utilizador via Context Management MS.

Este script e independente e comunica diretamente com o Context Management MS.

Requisitos: pip install requests

Uso CLI:
    python user_vault.py get_user_context <user_id>
    python user_vault.py update_user_context <user_id> <content>
    python user_vault.py list_documents <user_id> [--limit=50]
    python user_vault.py get_document <user_id> <document_id>
    python user_vault.py upload_document <user_id> <filename> <content> [--title=...] [--tags=...] [--path=...]
    python user_vault.py delete_document <user_id> <document_id>
    python user_vault.py list_folder <user_id> <folder_path> [--preview_chars=500]
    python user_vault.py list_knowledge <user_id>
    python user_vault.py get_knowledge <user_id> <key>
    python user_vault.py set_knowledge <user_id> <key> <value> [--category=...] [--tags=...]
    python user_vault.py delete_knowledge <user_id> <key>
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

CONTEXT_MANAGEMENT_BASE_URL = os.getenv(
    "CONTEXT_MANAGEMENT_URL",
    os.getenv("CONTEXT_MANAGEMENT_BASE_URL", "http://localhost:3003"),
)
BFF_BASE_URL = os.getenv(
    "BFF_BASE_URL",
    "http://localhost:3001",
)
INTERNAL_API_KEY = os.getenv(
    "CONTEXT_MANAGEMENT_API_INTERNAL_KEY",
    os.getenv("BFF_API_INTERNAL_KEY",
        os.getenv("INTERNAL_API_KEY", "")),
)
TIMEOUT_SECONDS = 30


# =============================================================================
# HTTP HELPERS
# =============================================================================

def _headers() -> Dict[str, str]:
    """Headers padrao para requests JSON."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if INTERNAL_API_KEY:
        headers["x-internal-api-key"] = INTERNAL_API_KEY
    return headers


def _bff_headers(user_id: str) -> Dict[str, str]:
    """Headers para requests internos ao BFF (com x-user-id)."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-user-id": user_id,
    }
    if INTERNAL_API_KEY:
        headers["x-internal-api-key"] = INTERNAL_API_KEY
    return headers


def _bff_get(path: str, user_id: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Faz um GET request ao BFF (rotas internas).

    Args:
        path: Caminho do endpoint (ex: /internal/user-settings/profile)
        user_id: ID do utilizador (enviado como x-user-id header)
        query: Parametros de query (opcional)

    Returns:
        Dicionario com status e dados ou erro
    """
    url = f"{BFF_BASE_URL}{path}"

    if query:
        query = {k: v for k, v in query.items() if v is not None}
        if query:
            url = f"{url}?{urlencode(query)}"

    try:
        response = requests.get(url, headers=_bff_headers(user_id), timeout=TIMEOUT_SECONDS)

        if response.status_code == 204:
            return _ok(None)

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_response": response.text}

        if not response.ok:
            return _err(
                error=data.get("message", data.get("error", f"HTTP {response.status_code}")),
                code=str(response.status_code),
            )

        return _ok(data)

    except requests.exceptions.Timeout:
        return _err(
            error=f"Request timeout apos {TIMEOUT_SECONDS} segundos",
            code="TIMEOUT",
        )
    except requests.exceptions.RequestException as e:
        return _err(error=str(e), code="REQUEST_ERROR")


def _bff_put(path: str, user_id: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Faz um PUT request ao BFF (rotas internas).

    Args:
        path: Caminho do endpoint
        user_id: ID do utilizador (enviado como x-user-id header)
        body: Corpo do request (opcional)

    Returns:
        Dicionario com status e dados ou erro
    """
    url = f"{BFF_BASE_URL}{path}"

    try:
        response = requests.put(
            url, headers=_bff_headers(user_id), json=body or {}, timeout=TIMEOUT_SECONDS
        )

        if response.status_code == 204:
            return _ok(None)

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_response": response.text}

        if not response.ok:
            return _err(
                error=data.get("message", data.get("error", f"HTTP {response.status_code}")),
                code=str(response.status_code),
            )

        return _ok(data)

    except requests.exceptions.Timeout:
        return _err(
            error=f"Request timeout apos {TIMEOUT_SECONDS} segundos",
            code="TIMEOUT",
        )
    except requests.exceptions.RequestException as e:
        return _err(error=str(e), code="REQUEST_ERROR")


def _ok(data: Any) -> Dict[str, Any]:
    """Retorna resposta de sucesso."""
    return {"status": "success", "data": data}


def _err(error: str, code: str = "UNKNOWN_ERROR") -> Dict[str, Any]:
    """Retorna resposta de erro."""
    return {"status": "error", "error": error, "code": code}


def _get(path: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Faz um GET request ao Context Management MS.

    Args:
        path: Caminho do endpoint (ex: /api/context/user-123)
        query: Parametros de query (opcional)

    Returns:
        Dicionario com status e dados ou erro
    """
    url = f"{CONTEXT_MANAGEMENT_BASE_URL}{path}"

    if query:
        query = {k: v for k, v in query.items() if v is not None}
        if query:
            url = f"{url}?{urlencode(query)}"

    try:
        response = requests.get(url, headers=_headers(), timeout=TIMEOUT_SECONDS)

        if response.status_code == 204:
            return _ok(None)

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_response": response.text}

        if not response.ok:
            return _err(
                error=data.get("message", f"HTTP {response.status_code}"),
                code=str(response.status_code),
            )

        return _ok(data)

    except requests.exceptions.Timeout:
        return _err(
            error=f"Request timeout apos {TIMEOUT_SECONDS} segundos",
            code="TIMEOUT",
        )
    except requests.exceptions.RequestException as e:
        return _err(error=str(e), code="REQUEST_ERROR")


def _put(path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Faz um PUT request ao Context Management MS.

    Args:
        path: Caminho do endpoint
        body: Corpo do request (opcional)

    Returns:
        Dicionario com status e dados ou erro
    """
    url = f"{CONTEXT_MANAGEMENT_BASE_URL}{path}"

    try:
        response = requests.put(
            url, headers=_headers(), json=body or {}, timeout=TIMEOUT_SECONDS
        )

        if response.status_code == 204:
            return _ok(None)

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_response": response.text}

        if not response.ok:
            return _err(
                error=data.get("message", f"HTTP {response.status_code}"),
                code=str(response.status_code),
            )

        return _ok(data)

    except requests.exceptions.Timeout:
        return _err(
            error=f"Request timeout apos {TIMEOUT_SECONDS} segundos",
            code="TIMEOUT",
        )
    except requests.exceptions.RequestException as e:
        return _err(error=str(e), code="REQUEST_ERROR")


def _post_multipart(
    path: str,
    files: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Faz um POST multipart request ao Context Management MS.

    Args:
        path: Caminho do endpoint
        files: Ficheiros para upload (formato requests)
        data: Campos de form data (opcional)

    Returns:
        Dicionario com status e dados ou erro
    """
    url = f"{CONTEXT_MANAGEMENT_BASE_URL}{path}"

    try:
        response = requests.post(
            url,
            files=files,
            data=data or {},
            headers={"Accept": "application/json", **({"x-internal-api-key": INTERNAL_API_KEY} if INTERNAL_API_KEY else {})},
            timeout=TIMEOUT_SECONDS,
        )

        try:
            resp_data = response.json()
        except json.JSONDecodeError:
            resp_data = {"raw_response": response.text}

        if not response.ok:
            return _err(
                error=resp_data.get("message", f"HTTP {response.status_code}"),
                code=str(response.status_code),
            )

        return _ok(resp_data)

    except requests.exceptions.Timeout:
        return _err(
            error=f"Request timeout apos {TIMEOUT_SECONDS} segundos",
            code="TIMEOUT",
        )
    except requests.exceptions.RequestException as e:
        return _err(error=str(e), code="REQUEST_ERROR")


def _delete(path: str) -> Dict[str, Any]:
    """
    Faz um DELETE request ao Context Management MS.

    Args:
        path: Caminho do endpoint

    Returns:
        Dicionario com status e dados ou erro
    """
    url = f"{CONTEXT_MANAGEMENT_BASE_URL}{path}"

    try:
        response = requests.delete(
            url, headers=_headers(), timeout=TIMEOUT_SECONDS
        )

        if response.status_code == 204:
            return _ok({"deleted": True})

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_response": response.text}

        if not response.ok:
            return _err(
                error=data.get("message", f"HTTP {response.status_code}"),
                code=str(response.status_code),
            )

        return _ok(data)

    except requests.exceptions.Timeout:
        return _err(
            error=f"Request timeout apos {TIMEOUT_SECONDS} segundos",
            code="TIMEOUT",
        )
    except requests.exceptions.RequestException as e:
        return _err(error=str(e), code="REQUEST_ERROR")


# =============================================================================
# CONTEXT FUNCTIONS
# =============================================================================

def get_user_context(user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Obtem o contexto do utilizador (about_me e rules) da base de dados via BFF.

    Args:
        user_id: ID do utilizador

    Returns:
        Dicionario com about_me e rules do perfil

    Exemplo:
        result = get_user_context("user-123")
    """
    result = _bff_get("/internal/user-settings/profile", user_id=user_id)

    if result["status"] == "error":
        # Se BFF falhar, retornar contexto vazio
        if result.get("code") in ("404", "REQUEST_ERROR"):
            return _ok({
                "user_id": user_id,
                "about_me": None,
                "rules": None,
            })
        return result

    # Normalizar resposta: BFF retorna { about_me: {content: "..."}, rules: {content: "..."} }
    data = result.get("data", {})
    return _ok({
        "user_id": user_id,
        "about_me": data.get("about_me", {}).get("content") if data.get("about_me") else None,
        "rules": data.get("rules", {}).get("content") if data.get("rules") else None,
    })



def update_user_context(user_id: str, content: str, key: str = "about_me", **kwargs) -> Dict[str, Any]:
    """
    Atualiza (ou cria) o about_me ou rules do utilizador.

    Args:
        user_id: ID do utilizador
        content: Conteudo (markdown)
        key: Chave do perfil - "about_me" ou "rules" (default: "about_me")

    Returns:
        Dicionario com confirmacao

    Exemplo:
        result = update_user_context("user-123", "# Sobre mim\\nSou developer")
        result = update_user_context("user-123", "- Responder em PT-PT", key="rules")
    """
    if not content:
        return _err(error="content e obrigatorio", code="INVALID_REQUEST")

    valid_keys = ("about_me", "rules")
    if key not in valid_keys:
        return _err(
            error=f"key deve ser um de: {', '.join(valid_keys)}",
            code="INVALID_REQUEST",
        )

    return _bff_put(
        "/internal/user-settings",
        user_id=user_id,
        body={
            "category": "profile",
            "key": key,
            "value": {"content": content},
        },
    )


# =============================================================================
# DOCUMENT FUNCTIONS
# =============================================================================

def list_documents(user_id: str, limit: int = 50, **kwargs) -> Dict[str, Any]:
    """
    Lista todos os documentos do utilizador.

    Args:
        user_id: ID do utilizador
        limit: Numero maximo de documentos (default: 50)

    Returns:
        Dicionario com lista de documentos

    Exemplo:
        result = list_documents("user-123", limit=20)
    """
    return _get(f"/api/documents/{quote(user_id, safe='')}")


def get_document(user_id: str, document_id: str, **kwargs) -> Dict[str, Any]:
    """
    Obtem metadados de um documento especifico.

    Args:
        user_id: ID do utilizador
        document_id: ID do documento

    Returns:
        Dicionario com metadados do documento

    Exemplo:
        result = get_document("user-123", "doc-abc123")
    """
    if not document_id:
        return _err(error="document_id e obrigatorio", code="INVALID_REQUEST")

    return _get(
        f"/api/documents/{quote(user_id, safe='')}/{quote(document_id, safe='')}"
    )


def upload_document(
    user_id: str,
    filename: str,
    content: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    path: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Faz upload de um documento.

    Args:
        user_id: ID do utilizador
        filename: Nome do ficheiro
        content: Conteudo do ficheiro (texto)
        title: Titulo do documento (opcional, default: filename)
        tags: Lista de tags (opcional)
        path: Pasta onde guardar (opcional)

    Returns:
        Dicionario com metadados do documento criado

    Exemplo:
        result = upload_document(
            "user-123",
            "notas.md",
            "# Notas\\nConteudo aqui",
            title="Minhas Notas",
            tags=["pessoal"],
            path="notas"
        )
    """
    if not filename:
        return _err(error="filename e obrigatorio", code="INVALID_REQUEST")
    if not content:
        return _err(error="content e obrigatorio", code="INVALID_REQUEST")

    # Detect mime type from filename extension
    mime_map = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".json": "application/json",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    ext = os.path.splitext(filename)[1].lower()
    mime_type = mime_map.get(ext, "text/plain")

    # Preparar ficheiro para multipart upload
    files = {
        "file": (filename, content.encode("utf-8"), mime_type),
    }

    # Preparar form data
    form_data = {}
    form_data["original_filename"] = filename

    if title:
        form_data["title"] = title
    if tags:
        form_data["tags"] = json.dumps(tags)
    if path:
        form_data["path"] = path

    return _post_multipart(
        f"/api/documents/{quote(user_id, safe='')}",
        files=files,
        data=form_data,
    )


def delete_document(user_id: str, document_id: str, **kwargs) -> Dict[str, Any]:
    """
    Elimina um documento.

    Args:
        user_id: ID do utilizador
        document_id: ID do documento

    Returns:
        Dicionario com confirmacao de eliminacao

    Exemplo:
        result = delete_document("user-123", "doc-abc123")
    """
    if not document_id:
        return _err(error="document_id e obrigatorio", code="INVALID_REQUEST")

    return _delete(
        f"/api/documents/{quote(user_id, safe='')}/{quote(document_id, safe='')}"
    )


def list_folder(
    user_id: str,
    folder_path: str,
    preview_chars: int = 500,
    **kwargs,
) -> Dict[str, Any]:
    """
    Lista documentos numa pasta especifica com preview do conteudo.

    Args:
        user_id: ID do utilizador
        folder_path: Caminho da pasta
        preview_chars: Numero de caracteres de preview (default: 500)

    Returns:
        Dicionario com documentos da pasta

    Exemplo:
        result = list_folder("user-123", "reports/2024", preview_chars=200)
    """
    if not folder_path:
        return _err(error="folder_path e obrigatorio", code="INVALID_REQUEST")

    query_params = {
        "path": folder_path,
        "preview": "true",
        "preview_chars": str(preview_chars),
    }

    return _get(
        f"/api/documents/{quote(user_id, safe='')}",
        query=query_params,
    )


# =============================================================================
# KNOWLEDGE FUNCTIONS
# =============================================================================

def list_knowledge(user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Lista todas as entradas de knowledge do utilizador.

    Args:
        user_id: ID do utilizador

    Returns:
        Dicionario com todas as entradas de knowledge

    Exemplo:
        result = list_knowledge("user-123")
    """
    return _get(f"/api/knowledge/{quote(user_id, safe='')}")


def get_knowledge(user_id: str, key: str, **kwargs) -> Dict[str, Any]:
    """
    Obtem uma entrada de knowledge especifica.

    Args:
        user_id: ID do utilizador
        key: Chave da entrada

    Returns:
        Dicionario com a entrada de knowledge

    Exemplo:
        result = get_knowledge("user-123", "communication_style")
    """
    if not key:
        return _err(error="key e obrigatorio", code="INVALID_REQUEST")

    return _get(
        f"/api/knowledge/{quote(user_id, safe='')}/{quote(key, safe='')}"
    )


def set_knowledge(
    user_id: str,
    key: str,
    value: Any,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Cria ou atualiza uma entrada de knowledge.

    Args:
        user_id: ID do utilizador
        key: Chave da entrada
        value: Valor (qualquer tipo serializavel em JSON)
        category: Categoria (opcional)
        tags: Lista de tags (opcional)

    Returns:
        Dicionario com a entrada criada/atualizada

    Exemplo:
        result = set_knowledge(
            "user-123",
            "communication_style",
            {"tone": "formal", "language": "pt-PT"},
            category="preferences",
            tags=["style", "language"]
        )
    """
    if not key:
        return _err(error="key e obrigatorio", code="INVALID_REQUEST")
    if value is None:
        return _err(error="value e obrigatorio", code="INVALID_REQUEST")

    body = {"value": value}
    if category:
        body["category"] = category
    if tags:
        body["tags"] = tags

    return _put(
        f"/api/knowledge/{quote(user_id, safe='')}/{quote(key, safe='')}",
        body=body,
    )


def delete_knowledge(user_id: str, key: str, **kwargs) -> Dict[str, Any]:
    """
    Elimina uma entrada de knowledge.

    Args:
        user_id: ID do utilizador
        key: Chave da entrada

    Returns:
        Dicionario com confirmacao de eliminacao

    Exemplo:
        result = delete_knowledge("user-123", "communication_style")
    """
    if not key:
        return _err(error="key e obrigatorio", code="INVALID_REQUEST")

    return _delete(
        f"/api/knowledge/{quote(user_id, safe='')}/{quote(key, safe='')}"
    )


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
        # Context (via BFF)
        "get_user_context": get_user_context,
        "user_vault_get_user_context": get_user_context,
        "update_user_context": update_user_context,
        "user_vault_update_user_context": update_user_context,
        # Documents
        "list_documents": list_documents,
        "user_vault_list_documents": list_documents,
        "get_document": get_document,
        "user_vault_get_document": get_document,
        "upload_document": upload_document,
        "user_vault_upload_document": upload_document,
        "delete_document": delete_document,
        "user_vault_delete_document": delete_document,
        "list_folder": list_folder,
        "user_vault_list_folder": list_folder,
        # Knowledge
        "list_knowledge": list_knowledge,
        "user_vault_list_knowledge": list_knowledge,
        "get_knowledge": get_knowledge,
        "user_vault_get_knowledge": get_knowledge,
        "set_knowledge": set_knowledge,
        "user_vault_set_knowledge": set_knowledge,
        "delete_knowledge": delete_knowledge,
        "user_vault_delete_knowledge": delete_knowledge,
    }

    if tool_name not in tools:
        return {
            "error": "Tool '{}' nao encontrada".format(tool_name),
            "available_tools": sorted(set(tools.keys())),
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
    print("  get_user_context <user_id>")
    print("  update_user_context <user_id> <content>")
    print("  list_documents <user_id> [--limit=50]")
    print("  get_document <user_id> <document_id>")
    print('  upload_document <user_id> <filename> <content> [--title=...] [--tags=...] [--path=...]')
    print("  delete_document <user_id> <document_id>")
    print("  list_folder <user_id> <folder_path> [--preview_chars=500]")
    print("  list_knowledge <user_id>")
    print("  get_knowledge <user_id> <key>")
    print('  set_knowledge <user_id> <key> <value> [--category=...] [--tags=...]')
    print("  delete_knowledge <user_id> <key>")


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

    # --- Context ---
    if tool_name == "get_user_context":
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            sys.exit(1)
        result = get_user_context(user_id=positional[0])

    elif tool_name == "update_user_context":
        if len(positional) < 2:
            print("Erro: user_id e content obrigatorios")
            sys.exit(1)
        result = update_user_context(user_id=positional[0], content=positional[1])

    # --- Documents ---
    elif tool_name == "list_documents":
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            sys.exit(1)
        try:
            limit = int(named.get("limit", 50))
        except ValueError:
            limit = 50
        result = list_documents(user_id=positional[0], limit=limit)

    elif tool_name == "get_document":
        if len(positional) < 2:
            print("Erro: user_id e document_id obrigatorios")
            sys.exit(1)
        result = get_document(user_id=positional[0], document_id=positional[1])

    elif tool_name == "upload_document":
        if len(positional) < 3:
            print("Erro: user_id, filename e content obrigatorios")
            sys.exit(1)
        tags = None
        if "tags" in named:
            try:
                tags = json.loads(named["tags"])
            except json.JSONDecodeError:
                tags = named["tags"].split(",")
        result = upload_document(
            user_id=positional[0],
            filename=positional[1],
            content=positional[2],
            title=named.get("title"),
            tags=tags,
            path=named.get("path"),
        )

    elif tool_name == "delete_document":
        if len(positional) < 2:
            print("Erro: user_id e document_id obrigatorios")
            sys.exit(1)
        result = delete_document(user_id=positional[0], document_id=positional[1])

    elif tool_name == "list_folder":
        if len(positional) < 2:
            print("Erro: user_id e folder_path obrigatorios")
            sys.exit(1)
        try:
            preview_chars = int(named.get("preview_chars", 500))
        except ValueError:
            preview_chars = 500
        result = list_folder(
            user_id=positional[0],
            folder_path=positional[1],
            preview_chars=preview_chars,
        )

    # --- Knowledge ---
    elif tool_name == "list_knowledge":
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            sys.exit(1)
        result = list_knowledge(user_id=positional[0])

    elif tool_name == "get_knowledge":
        if len(positional) < 2:
            print("Erro: user_id e key obrigatorios")
            sys.exit(1)
        result = get_knowledge(user_id=positional[0], key=positional[1])

    elif tool_name == "set_knowledge":
        if len(positional) < 3:
            print("Erro: user_id, key e value obrigatorios")
            sys.exit(1)
        # Tentar parsear value como JSON, senao usar como string
        raw_value = positional[2]
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        tags = None
        if "tags" in named:
            try:
                tags = json.loads(named["tags"])
            except json.JSONDecodeError:
                tags = named["tags"].split(",")
        result = set_knowledge(
            user_id=positional[0],
            key=positional[1],
            value=value,
            category=named.get("category"),
            tags=tags,
        )

    elif tool_name == "delete_knowledge":
        if len(positional) < 2:
            print("Erro: user_id e key obrigatorios")
            sys.exit(1)
        result = delete_knowledge(user_id=positional[0], key=positional[1])

    else:
        print("Erro: Tool '{}' nao reconhecida".format(tool_name))
        print_usage()
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
