#!/usr/bin/env python3
"""
Drive Client Standalone Tool
Gere ficheiros no Google Drive ou Microsoft OneDrive.

Este script e independente e comunica com o BFF (Backend for Frontend)
que gere a autenticacao OAuth com os providers de drive.

Requisitos: pip install requests

Uso CLI:
    python drive_client.py list_files <user_id> [--folder_id=...] [--query=...] [--limit=20] [--sort_by=...]
    python drive_client.py get_file <user_id> <file_id>
    python drive_client.py read_file_content <user_id> <file_id>
    python drive_client.py create_file <user_id> <name> --content=... [--folder_id=...] [--content_type=...]
    python drive_client.py update_file <user_id> <file_id> --content=...
    python drive_client.py delete_file <user_id> <file_id>
    python drive_client.py create_folder <user_id> <name> [--folder_id=...]
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
        path: Caminho do endpoint (ex: /internal/drive/files)
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
        path: Caminho do endpoint (ex: /internal/drive/files)
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
            "error_code": data.get("code", "DRIVE_PROVIDER_AUTH_FAILED"),
            "message": data.get("message", "Erro de autenticacao com o provider de drive"),
            "reauthorization_required": data.get("reauthorization_required", True),
            "provider": data.get("provider"),
            "action_url": data.get("action_url"),
        }

    # Ficheiro nao encontrado (404)
    if response.status_code == 404:
        return {
            "status": "error",
            "error_code": data.get("code", "DRIVE_FILE_NOT_FOUND"),
            "message": data.get("message", "Ficheiro nao encontrado"),
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
# TOOL 1: LISTAR FICHEIROS
# =============================================================================

def list_files(
    user_id: str,
    folder_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    sort_by: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lista ficheiros no drive do utilizador.

    Args:
        user_id: ID do utilizador
        folder_id: ID da pasta para listar (opcional, default: raiz)
        query: Texto para pesquisar no nome dos ficheiros (opcional)
        limit: Numero maximo de ficheiros (default: 20)
        sort_by: Ordenacao (ex: 'modifiedTime desc', 'name')
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com lista de ficheiros

    Exemplo:
        result = list_files("user-123", query="relatorio", limit=10)
    """
    # Construir parametros de query
    query_params = {
        "q": query,
        "pageSize": limit,
        "orderBy": sort_by,
    }

    # Se folder_id fornecido, adicionar a query de pesquisa
    if folder_id:
        folder_query = f"'{folder_id}' in parents"
        if query:
            query_params["q"] = f"{folder_query} and name contains '{query}'"
        else:
            query_params["q"] = folder_query

    result = _make_get_request(
        path="/internal/drive/files",
        user_id=user_id,
        query=query_params,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    # Processar resposta
    files_data = result.get("data", {})

    # O BFF retorna { files: [...] }
    if isinstance(files_data, dict) and "files" in files_data:
        files_list = files_data.get("files", [])
        return {
            "status": "success",
            "total": len(files_list),
            "files": files_list,
        }

    # Se for uma lista diretamente
    if isinstance(files_data, list):
        return {
            "status": "success",
            "total": len(files_data),
            "files": files_data,
        }

    return {
        "status": "success",
        "total": 0,
        "files": [],
    }


# =============================================================================
# TOOL 2: OBTER METADADOS DE UM FICHEIRO
# =============================================================================

def get_file(
    user_id: str,
    file_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtem metadados de um ficheiro especifico.

    Args:
        user_id: ID do utilizador
        file_id: ID do ficheiro
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com metadados do ficheiro

    Exemplo:
        result = get_file("user-123", "file-abc123")
    """
    if not file_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "file_id e obrigatorio",
        }

    safe_file_id = quote(file_id, safe='')

    result = _make_get_request(
        path=f"/internal/drive/files/{safe_file_id}",
        user_id=user_id,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    file_data = result.get("data", {})

    # O BFF pode retornar { file: {...} } ou o ficheiro diretamente
    if isinstance(file_data, dict) and "file" in file_data:
        return {
            "status": "success",
            "file": file_data.get("file"),
        }

    return {
        "status": "success",
        "file": file_data,
    }


# =============================================================================
# TOOL 3: LER CONTEUDO DE UM FICHEIRO
# =============================================================================

def read_file_content(
    user_id: str,
    file_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Le o conteudo de um ficheiro como texto.

    Args:
        user_id: ID do utilizador
        file_id: ID do ficheiro a ler
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com conteudo do ficheiro

    Exemplo:
        result = read_file_content("user-123", "file-abc123")
    """
    if not file_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "file_id e obrigatorio",
        }

    safe_file_id = quote(file_id, safe='')

    result = _make_get_request(
        path=f"/internal/drive/files/{safe_file_id}/content",
        user_id=user_id,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    content_data = result.get("data", {})

    # O BFF pode retornar { content: "..." } ou dados directamente
    if isinstance(content_data, dict) and "content" in content_data:
        return {
            "status": "success",
            "content": content_data.get("content"),
            "file_id": content_data.get("id", file_id),
            "name": content_data.get("name"),
            "mimeType": content_data.get("mimeType"),
        }

    # Se retornar texto directamente
    if isinstance(content_data, str):
        return {
            "status": "success",
            "content": content_data,
            "file_id": file_id,
        }

    return {
        "status": "success",
        "content": content_data,
        "file_id": file_id,
    }


# =============================================================================
# TOOL 4: CRIAR FICHEIRO
# =============================================================================

def create_file(
    user_id: str,
    name: str,
    content: str,
    folder_id: Optional[str] = None,
    content_type: str = "text/plain",
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria um novo ficheiro no drive.

    Args:
        user_id: ID do utilizador
        name: Nome do ficheiro
        content: Conteudo do ficheiro
        folder_id: ID da pasta destino (opcional, default: raiz)
        content_type: MIME type do conteudo (default: 'text/plain')
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da criacao

    Exemplo:
        result = create_file(
            user_id="user-123",
            name="notas.md",
            content="# Notas\\n\\nConteudo..."
        )
    """
    if not name:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "name (nome do ficheiro) e obrigatorio",
        }

    if content is None:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "content (conteudo) e obrigatorio",
        }

    request_body = {
        "name": name,
        "content": content,
        "mimeType": content_type,
    }

    if folder_id:
        request_body["parentId"] = folder_id

    result = _make_post_request(
        path="/internal/drive/files",
        user_id=user_id,
        body=request_body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    file_data = result.get("data", {})

    return {
        "status": "success",
        "file_id": file_data.get("id"),
        "name": file_data.get("name", name),
        "message": "Ficheiro criado com sucesso",
    }


# =============================================================================
# TOOL 5: ATUALIZAR CONTEUDO DE UM FICHEIRO
# =============================================================================

def update_file(
    user_id: str,
    file_id: str,
    content: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atualiza o conteudo de um ficheiro existente.

    Args:
        user_id: ID do utilizador
        file_id: ID do ficheiro a atualizar
        content: Novo conteudo do ficheiro
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da atualizacao

    Exemplo:
        result = update_file(
            user_id="user-123",
            file_id="file-abc123",
            content="Novo conteudo..."
        )
    """
    if not file_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "file_id e obrigatorio",
        }

    if content is None:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "content (conteudo) e obrigatorio",
        }

    safe_file_id = quote(file_id, safe='')

    result = _make_post_request(
        path=f"/internal/drive/files/{safe_file_id}/content",
        user_id=user_id,
        body={"content": content},
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    file_data = result.get("data", {})

    return {
        "status": "success",
        "file_id": file_data.get("id", file_id),
        "message": "Ficheiro atualizado com sucesso",
    }


# =============================================================================
# TOOL 6: APAGAR FICHEIRO
# =============================================================================

def delete_file(
    user_id: str,
    file_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apaga um ficheiro do drive.

    Args:
        user_id: ID do utilizador
        file_id: ID do ficheiro a apagar
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da operacao

    Exemplo:
        result = delete_file("user-123", "file-abc123")
    """
    if not file_id:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "file_id e obrigatorio",
        }

    safe_file_id = quote(file_id, safe='')

    result = _make_post_request(
        path=f"/internal/drive/files/{safe_file_id}/delete",
        user_id=user_id,
        body={},
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    return {
        "status": "success",
        "message": f"Ficheiro {file_id} apagado com sucesso",
    }


# =============================================================================
# TOOL 7: CRIAR PASTA
# =============================================================================

def create_folder(
    user_id: str,
    name: str,
    folder_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria uma nova pasta no drive.

    Args:
        user_id: ID do utilizador
        name: Nome da pasta
        folder_id: ID da pasta pai (opcional, default: raiz)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com resultado da criacao

    Exemplo:
        result = create_folder("user-123", "Projetos 2025")
    """
    if not name:
        return {
            "status": "error",
            "error_code": "INVALID_REQUEST",
            "message": "name (nome da pasta) e obrigatorio",
        }

    request_body = {
        "name": name,
    }

    if folder_id:
        request_body["parentId"] = folder_id

    result = _make_post_request(
        path="/internal/drive/folders",
        user_id=user_id,
        body=request_body,
        tenant_id=tenant_id,
    )

    if result.get("status") == "error":
        return result

    folder_data = result.get("data", {})

    return {
        "status": "success",
        "folder_id": folder_data.get("id"),
        "name": folder_data.get("name", name),
        "message": "Pasta criada com sucesso",
    }


# =============================================================================
# INTERFACE DE EXECUCAO (para uso direto via terminal ou por agente)
# =============================================================================

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma tool pelo nome.

    Args:
        tool_name: Nome da tool (list_files, get_file, read_file_content,
                   create_file, update_file, delete_file, create_folder)
        **kwargs: Argumentos da tool

    Returns:
        Resultado da execucao
    """
    tools = {
        "list_files": list_files,
        "drive_list_files": list_files,
        "get_file": get_file,
        "drive_get_file": get_file,
        "read_file_content": read_file_content,
        "drive_read_file_content": read_file_content,
        "create_file": create_file,
        "drive_create_file": create_file,
        "update_file": update_file,
        "drive_update_file": update_file,
        "delete_file": delete_file,
        "drive_delete_file": delete_file,
        "create_folder": create_folder,
        "drive_create_folder": create_folder,
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
    print("  list_files <user_id> [--folder_id=...] [--query=...] [--limit=20] [--sort_by=...]")
    print("  get_file <user_id> <file_id>")
    print("  read_file_content <user_id> <file_id>")
    print("  create_file <user_id> <name> --content=... [--folder_id=...] [--content_type=...]")
    print("  update_file <user_id> <file_id> --content=...")
    print("  delete_file <user_id> <file_id>")
    print("  create_folder <user_id> <name> [--folder_id=...]")
    print("\nExemplos:")
    print('  python drive_client.py list_files user-123 --limit=5')
    print('  python drive_client.py list_files user-123 --query="relatorio"')
    print('  python drive_client.py get_file user-123 file-abc123')
    print('  python drive_client.py read_file_content user-123 file-abc123')
    print('  python drive_client.py create_file user-123 "notas.md" --content="# Notas"')
    print('  python drive_client.py update_file user-123 file-abc123 --content="Novo conteudo"')
    print('  python drive_client.py delete_file user-123 file-abc123')
    print('  python drive_client.py create_folder user-123 "Projetos 2025"')


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

    if tool_name in ["list_files", "drive_list_files"]:
        if len(positional) < 1:
            print("Erro: user_id obrigatorio")
            print("Uso: python drive_client.py list_files <user_id> [--folder_id=...] [--query=...] [--limit=20] [--sort_by=...]")
            sys.exit(1)

        user_id = positional[0]
        try:
            limit = int(named.get("limit", 20))
        except ValueError:
            limit = 20
        result = list_files(
            user_id=user_id,
            folder_id=named.get("folder_id"),
            query=named.get("query"),
            limit=limit,
            sort_by=named.get("sort_by"),
        )

    elif tool_name in ["get_file", "drive_get_file"]:
        if len(positional) < 2:
            print("Erro: user_id e file_id obrigatorios")
            print("Uso: python drive_client.py get_file <user_id> <file_id>")
            sys.exit(1)

        user_id = positional[0]
        file_id = positional[1]
        result = get_file(user_id=user_id, file_id=file_id)

    elif tool_name in ["read_file_content", "drive_read_file_content"]:
        if len(positional) < 2:
            print("Erro: user_id e file_id obrigatorios")
            print("Uso: python drive_client.py read_file_content <user_id> <file_id>")
            sys.exit(1)

        user_id = positional[0]
        file_id = positional[1]
        result = read_file_content(user_id=user_id, file_id=file_id)

    elif tool_name in ["create_file", "drive_create_file"]:
        if len(positional) < 2:
            print("Erro: user_id e name obrigatorios")
            print("Uso: python drive_client.py create_file <user_id> <name> --content=... [--folder_id=...] [--content_type=...]")
            sys.exit(1)

        user_id = positional[0]
        name = positional[1]
        content = named.get("content", "")

        result = create_file(
            user_id=user_id,
            name=name,
            content=content,
            folder_id=named.get("folder_id"),
            content_type=named.get("content_type", "text/plain"),
        )

    elif tool_name in ["update_file", "drive_update_file"]:
        if len(positional) < 2:
            print("Erro: user_id e file_id obrigatorios")
            print("Uso: python drive_client.py update_file <user_id> <file_id> --content=...")
            sys.exit(1)

        user_id = positional[0]
        file_id = positional[1]
        content = named.get("content", "")

        result = update_file(
            user_id=user_id,
            file_id=file_id,
            content=content,
        )

    elif tool_name in ["delete_file", "drive_delete_file"]:
        if len(positional) < 2:
            print("Erro: user_id e file_id obrigatorios")
            print("Uso: python drive_client.py delete_file <user_id> <file_id>")
            sys.exit(1)

        user_id = positional[0]
        file_id = positional[1]
        result = delete_file(user_id=user_id, file_id=file_id)

    elif tool_name in ["create_folder", "drive_create_folder"]:
        if len(positional) < 2:
            print("Erro: user_id e name obrigatorios")
            print("Uso: python drive_client.py create_folder <user_id> <name> [--folder_id=...]")
            sys.exit(1)

        user_id = positional[0]
        name = positional[1]
        result = create_folder(
            user_id=user_id,
            name=name,
            folder_id=named.get("folder_id"),
        )

    else:
        print("Erro: Tool '{}' nao reconhecida".format(tool_name))
        print("\nTools disponiveis:")
        print("  list_files, get_file, read_file_content, create_file, update_file, delete_file, create_folder")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    main()
