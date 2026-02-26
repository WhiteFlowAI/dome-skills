"""
Skill Creator - Cria skills personalizadas do utilizador.

Valida codigo Python, faz upload para o user vault via Files API
do context-management, e regista metadata no BFF.
"""

import json
import os
from typing import Any, Dict, Optional

import requests

from ast_validator import validate_code_ast

BFF_BASE_URL = os.getenv("BFF_BASE_URL", "http://localhost:3001")
CONTEXT_MANAGEMENT_BASE_URL = os.getenv("CONTEXT_MANAGEMENT_BASE_URL") or os.getenv("CONTEXT_MANAGEMENT_URL", "http://localhost:3003")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
TIMEOUT_SECONDS = 30

# Try to load tenant_id from task.json (available in worker containers)
_TASK_TENANT_ID = None
for _task_path in ["/workspace/.agent/auto_execute/task.json", "task.json"]:
    try:
        with open(_task_path, "r") as _f:
            _task_data = json.load(_f)
            _TASK_TENANT_ID = _task_data.get("tenant_id")
            if _TASK_TENANT_ID:
                break
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass

# User vault path for skills
_VAULT_FOLDER = "myDocuments"
_VAULT_SKILLS_PREFIX = ".agent/skills"


def _build_headers(user_id: str, tenant_id: Optional[str] = None) -> Dict[str, str]:
    """Constroi headers para chamadas internas."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-internal-api-key": INTERNAL_API_KEY,
        "x-user-id": user_id,
    }
    if tenant_id:
        headers["x-tenant-id"] = tenant_id
    return headers


def _make_post_request(
    base_url: str,
    path: str,
    user_id: str,
    body: dict,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Faz POST request a um servico interno."""
    url = f"{base_url}{path}"
    headers = _build_headers(user_id, tenant_id)
    try:
        response = requests.post(url, json=body, headers=headers, timeout=TIMEOUT_SECONDS)
        return _process_response(response)
    except requests.Timeout:
        return {"status": "error", "error": "Request timeout", "error_type": "TIMEOUT"}
    except requests.ConnectionError:
        return {"status": "error", "error": "Connection failed", "error_type": "CONNECTION_ERROR"}
    except requests.RequestException as e:
        return {"status": "error", "error": str(e), "error_type": "REQUEST_ERROR"}


def _make_put_request(
    base_url: str,
    path: str,
    user_id: str,
    body: dict,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Faz PUT request a um servico interno."""
    url = f"{base_url}{path}"
    headers = _build_headers(user_id, tenant_id)
    try:
        response = requests.put(url, json=body, headers=headers, timeout=TIMEOUT_SECONDS)
        return _process_response(response)
    except requests.Timeout:
        return {"status": "error", "error": "Request timeout", "error_type": "TIMEOUT"}
    except requests.ConnectionError:
        return {"status": "error", "error": "Connection failed", "error_type": "CONNECTION_ERROR"}
    except requests.RequestException as e:
        return {"status": "error", "error": str(e), "error_type": "REQUEST_ERROR"}


def _process_response(response: requests.Response) -> Dict[str, Any]:
    """Processa resposta HTTP."""
    if response.ok:
        try:
            return {"status": "success", "data": response.json()}
        except ValueError:
            return {"status": "success", "data": response.text}

    error_msg = f"HTTP {response.status_code}"
    try:
        error_data = response.json()
        if "error" in error_data:
            error_msg = f"{error_msg}: {error_data['error']}"
        elif "message" in error_data:
            error_msg = f"{error_msg}: {error_data['message']}"
    except ValueError:
        error_msg = f"{error_msg}: {response.text[:200]}"

    return {"status": "error", "error": error_msg, "error_type": "HTTP_ERROR"}


def _guess_mime_type(filename: str) -> str:
    """Guess MIME type from filename extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime_map = {
        "md": "text/markdown",
        "py": "text/plain",
        "txt": "text/plain",
        "json": "application/json",
        "csv": "text/csv",
    }
    return mime_map.get(ext, "text/plain")


def _upload_file_to_vault(
    user_id: str,
    skill_name: str,
    file_path: str,
    content: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload um ficheiro para o vault via Documents API do context-management (upsert)."""
    vault_path = f"{_VAULT_SKILLS_PREFIX}/{skill_name}"
    if "/" in file_path:
        sub_dir = file_path.rsplit("/", 1)[0]
        vault_path = f"{vault_path}/{sub_dir}"
        filename = file_path.rsplit("/", 1)[1]
    else:
        filename = file_path

    headers = {
        "x-internal-api-key": INTERNAL_API_KEY,
        "x-user-id": user_id,
    }
    if tenant_id:
        headers["x-tenant-id"] = tenant_id

    mime_type = _guess_mime_type(filename)
    content_bytes = content.encode("utf-8")

    try:
        # Try POST (create)
        url = f"{CONTEXT_MANAGEMENT_BASE_URL}/api/documents/{user_id}"
        files = {"file": (filename, content_bytes, mime_type)}
        data = {"title": filename, "path": vault_path}
        response = requests.post(url, headers=headers, files=files, data=data, timeout=TIMEOUT_SECONDS)

        if response.ok:
            return _process_response(response)

        # If file already exists, try PUT (update)
        error_text = response.text.lower()
        if response.status_code in (400, 409) and "already exists" in error_text:
            doc_id = f"{vault_path}/{filename}"
            update_url = f"{CONTEXT_MANAGEMENT_BASE_URL}/api/documents/{user_id}/{doc_id}/file"
            files = {"file": (filename, content_bytes, mime_type)}
            response = requests.put(update_url, headers=headers, files=files, timeout=TIMEOUT_SECONDS)
            return _process_response(response)

        return _process_response(response)
    except requests.Timeout:
        return {"status": "error", "error": "Request timeout", "error_type": "TIMEOUT"}
    except requests.ConnectionError:
        return {"status": "error", "error": "Connection failed", "error_type": "CONNECTION_ERROR"}
    except requests.RequestException as e:
        return {"status": "error", "error": str(e), "error_type": "REQUEST_ERROR"}


def validate_code(
    user_id: str,
    code: str,
    filename: str = "main.py",
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Valida codigo Python contra regras de seguranca.

    Args:
        user_id: ID do utilizador
        code: Codigo Python a validar
        filename: Nome do ficheiro (default: "main.py")
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com status, valid (bool), e lista de erros

    Exemplo:
        result = validate_code("user-123", "import json\\ndef hello(): return {'ok': True}")
    """
    result = validate_code_ast(code, filename=filename)
    return {
        "status": "success",
        "valid": result["valid"],
        "errors": result["errors"],
    }


def create_skill(
    user_id: str,
    name: str,
    display_name: str,
    description: str,
    skill_md: str,
    scripts: Optional[Dict[str, str]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria uma skill completa: valida codigo, faz upload e regista.

    Args:
        user_id: ID do utilizador
        name: Nome unico da skill (lowercase-hyphens)
        display_name: Nome para mostrar ao utilizador
        description: Descricao curta da skill
        skill_md: Conteudo completo do SKILL.md
        scripts: Dict de {filename: code} dos scripts Python (opcional)
        tenant_id: ID do tenant (opcional)

    Returns:
        Dicionario com status e dados da skill criada

    Exemplo:
        result = create_skill(
            user_id="user-123",
            name="meu-relatorio",
            display_name="Meu Relatorio",
            description="Gera relatorios no meu formato",
            skill_md="# Meu Relatorio\\n...",
            scripts={"main.py": "def generate(): ..."}
        )
    """
    # Resolve tenant_id: argument > task.json > None
    if not tenant_id:
        tenant_id = _TASK_TENANT_ID

    # 1. Validate all Python scripts
    if scripts:
        for filename, code in scripts.items():
            if filename.endswith(".py"):
                validation = validate_code_ast(code, filename=filename)
                if not validation["valid"]:
                    return {
                        "status": "error",
                        "error": f"Validacao falhou para {filename}",
                        "validation_errors": validation["errors"],
                    }

    # 2. Upload files to vault via context-management Files API
    # Upload SKILL.md
    result = _upload_file_to_vault(user_id, name, "SKILL.md", skill_md, tenant_id)
    if result["status"] == "error":
        return {"status": "error", "error": f"Falha ao guardar SKILL.md: {result['error']}"}

    # Upload scripts
    if scripts:
        for filename, code in scripts.items():
            result = _upload_file_to_vault(user_id, name, f"scripts/{filename}", code, tenant_id)
            if result["status"] == "error":
                return {"status": "error", "error": f"Falha ao guardar scripts/{filename}: {result['error']}"}

    storage_path = f"{_VAULT_SKILLS_PREFIX}/{name}"

    # 3. Register skill metadata in BFF
    register_result = _make_post_request(
        BFF_BASE_URL,
        "/internal/skills/user",
        user_id,
        {
            "name": name,
            "display_name": display_name,
            "description": description,
            "storage_path": storage_path,
        },
        tenant_id,
    )

    if register_result["status"] == "error":
        return register_result

    return {
        "status": "success",
        "message": f"Skill '{display_name}' criada com sucesso!",
        "skill": register_result.get("data", {}).get("skill"),
    }


# CLI support and tool dispatcher
def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Dispatcher de ferramentas."""
    tools = {
        "validate_code": validate_code,
        "skill_creator_validate_code": validate_code,
        "create_skill": create_skill,
        "skill_creator_create_skill": create_skill,
    }
    func = tools.get(tool_name)
    if not func:
        return {"status": "error", "error": f"Ferramenta desconhecida: {tool_name}"}
    return func(**kwargs)


def parse_cli_args():
    """Parse CLI arguments no formato --key=value."""
    import sys as _sys
    args = {}
    for arg in _sys.argv[1:]:
        if arg.startswith("--") and "=" in arg:
            key, value = arg[2:].split("=", 1)
            args[key.replace("-", "_")] = value
    return args


def main():
    """CLI entry point para testes."""
    args = parse_cli_args()
    tool_name = args.pop("tool", None)
    if not tool_name:
        print(json.dumps({"status": "error", "error": "Uso: --tool=<nome> --user-id=<id> [args]"}))
        return

    result = execute_tool(tool_name, **args)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
