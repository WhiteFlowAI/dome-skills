---
name: user-vault
description: Cofre pessoal do utilizador. Gere contexto pessoal, documentos (MyDocuments) e base de conhecimento. Use para consultar pastas, ler documentos, guardar notas e preferencias.
---

# User Vault - Contexto, Documentos e Knowledge

Skill para gestao do cofre pessoal do utilizador: contexto, documentos e base de conhecimento.

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Consultar ou atualizar o seu contexto pessoal (preferencias, notas)
- Listar, ler ou guardar documentos pessoais (MyDocuments)
- Explorar pastas e ver previews de documentos
- Guardar ou consultar conhecimento estruturado (chave/valor)
- Gerir tags e categorias de conhecimento
- Eliminar documentos ou entradas de knowledge

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import get_user_context, update_user_context, list_documents, get_document, upload_document, delete_document, list_folder, list_knowledge, get_knowledge, set_knowledge, delete_knowledge
```

## Operacoes Disponiveis

### Contexto

#### 1. Obter Perfil do Utilizador (About Me + Rules)

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import get_user_context

result = get_user_context(user_id="user-123")

if result.get("status") == "success":
    ctx = result["data"]
    print(f"About Me: {ctx.get('about_me')}")
    print(f"Rules: {ctx.get('rules')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador

**Retorna:**
- `about_me`: Texto markdown do "About Me" (ou None)
- `rules`: Texto markdown das regras/preferencias (ou None)

#### 2. Atualizar About Me ou Rules

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import update_user_context

# Atualizar About Me
result = update_user_context(
    user_id="user-123",
    content="# Sobre Mim\nSou developer em Lisboa, interessado em IA."
)

# Atualizar Rules/Preferencias
result = update_user_context(
    user_id="user-123",
    content="- Responder sempre em PT-PT\n- Tom formal",
    key="rules"
)

if result.get("status") == "success":
    print("Perfil atualizado com sucesso")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `content` (obrigatorio): Conteudo (markdown)
- `key` (opcional): `"about_me"` (default) ou `"rules"`

### Documentos

#### 3. Listar Documentos

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import list_documents

result = list_documents(user_id="user-123", limit=20)

if result.get("status") == "success":
    for doc in result["data"]:
        print(f"{doc.get('filename')} - {doc.get('title', 'Sem titulo')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `limit` (opcional): Numero maximo de documentos (default: 50)

#### 4. Obter Documento

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import get_document

result = get_document(user_id="user-123", document_id="doc-abc123")

if result.get("status") == "success":
    doc = result["data"]
    print(f"Titulo: {doc.get('title')}")
    print(f"Ficheiro: {doc.get('filename')}")
    print(f"Conteudo: {doc.get('content', '')[:200]}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `document_id` (obrigatorio): ID do documento

#### 5. Upload de Documento

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import upload_document

# Upload simples
result = upload_document(
    user_id="user-123",
    filename="notas.md",
    content="# Notas da Reuniao\n\n- Ponto 1\n- Ponto 2"
)

if result.get("status") == "success":
    print(f"Documento criado: {result['data'].get('id')}")

# Upload com metadados
result = upload_document(
    user_id="user-123",
    filename="relatorio.md",
    content="# Relatorio Mensal\n\nConteudo do relatorio...",
    title="Relatorio Janeiro 2026",
    tags=["relatorio", "mensal"],
    path="relatorios/2026"
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `filename` (obrigatorio): Nome do ficheiro
- `content` (obrigatorio): Conteudo do ficheiro (texto)
- `title` (opcional): Titulo do documento (default: filename)
- `tags` (opcional): Lista de tags
- `path` (opcional): Pasta onde guardar

#### 6. Eliminar Documento

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import delete_document

result = delete_document(user_id="user-123", document_id="doc-abc123")

if result.get("status") == "success":
    print("Documento eliminado com sucesso")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `document_id` (obrigatorio): ID do documento

#### 7. Listar Pasta (com Preview)

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import list_folder

result = list_folder(user_id="user-123", folder_path="contracts")

if result.get("status") == "success":
    for doc in result["data"].get("documents", result["data"] if isinstance(result["data"], list) else []):
        print(f"{doc['filename']} - preview: {doc.get('preview', 'N/A')[:50]}")

# Com preview personalizado
result = list_folder(
    user_id="user-123",
    folder_path="relatorios/2026",
    preview_chars=200
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `folder_path` (obrigatorio): Caminho da pasta
- `preview_chars` (opcional): Numero de caracteres de preview (default: 500)

### Knowledge

#### 8. Listar Knowledge

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import list_knowledge

result = list_knowledge(user_id="user-123")

if result.get("status") == "success":
    for entry in result["data"]:
        print(f"{entry.get('key')}: {entry.get('value')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador

#### 9. Obter Knowledge

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import get_knowledge

result = get_knowledge(user_id="user-123", key="communication_style")

if result.get("status") == "success":
    entry = result["data"]
    print(f"Chave: {entry.get('key')}")
    print(f"Valor: {entry.get('value')}")
    print(f"Categoria: {entry.get('category')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `key` (obrigatorio): Chave da entrada

#### 10. Guardar Knowledge

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import set_knowledge

# Guardar valor simples
result = set_knowledge(
    user_id="user-123",
    key="lingua_preferida",
    value="pt-PT"
)

if result.get("status") == "success":
    print("Knowledge guardado com sucesso")

# Guardar valor estruturado com categoria e tags
result = set_knowledge(
    user_id="user-123",
    key="communication_style",
    value={"tone": "formal", "language": "pt-PT"},
    category="preferences",
    tags=["style", "language"]
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `key` (obrigatorio): Chave da entrada
- `value` (obrigatorio): Valor (qualquer tipo serializavel em JSON)
- `category` (opcional): Categoria
- `tags` (opcional): Lista de tags

#### 11. Eliminar Knowledge

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import delete_knowledge

result = delete_knowledge(user_id="user-123", key="communication_style")

if result.get("status") == "success":
    print("Knowledge eliminado com sucesso")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `key` (obrigatorio): Chave da entrada

## Workflow Tipico

### Explorar documentos e analisar conteudo:

```python
import sys
sys.path.insert(0, "/var/cache/skills/user-vault")
from user_vault import list_folder, get_document, get_user_context

# 1. Consultar contexto do utilizador
context = get_user_context(user_id="user-123")

# 2. Listar pasta com previews
folder = list_folder(user_id="user-123", folder_path="contracts", preview_chars=300)

# 3. Analisar previews e obter documento completo
if folder.get("status") == "success":
    docs = folder["data"] if isinstance(folder["data"], list) else folder["data"].get("documents", [])
    for doc in docs:
        preview = doc.get("preview", "")
        if "renovacao" in preview.lower():
            # 4. Obter documento completo
            full_doc = get_document(user_id="user-123", document_id=doc["id"])
            if full_doc.get("status") == "success":
                print(f"Documento encontrado: {full_doc['data'].get('title')}")
```

## Estrutura de Dados

### Perfil (de get_user_context):
```python
{
    "user_id": "user-123",
    "about_me": "# Sobre Mim\nSou developer em Lisboa",
    "rules": "- Tom: formal\n- Lingua: pt-PT"
}
```

### Documento (de get_document):
```python
{
    "id": "doc-abc123",
    "filename": "notas.md",
    "title": "Minhas Notas",
    "content": "# Notas\nConteudo...",
    "path": "notas",
    "tags": ["pessoal"],
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
}
```

### Documento com Preview (de list_folder):
```python
{
    "id": "doc-abc123",
    "filename": "contrato.md",
    "title": "Contrato de Servico",
    "preview": "# Contrato\nEste contrato estabelece...",
    "path": "contracts",
    "tags": ["legal"]
}
```

### Knowledge Entry (de get_knowledge):
```python
{
    "key": "communication_style",
    "value": {"tone": "formal", "language": "pt-PT"},
    "category": "preferences",
    "tags": ["style", "language"],
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
}
```

## Erros Comuns

### Perfil nao existe
```python
{
    "status": "success",
    "data": {
        "user_id": "user-123",
        "about_me": null,
        "rules": null
    }
}
```

**Solucao**: Nao e erro. Perfil ainda nao foi criado. Use `update_user_context` para criar.

### Documento nao encontrado
```python
{
    "status": "error",
    "error": "HTTP 404",
    "code": "404"
}
```

**Solucao**: Verificar o `document_id` com `list_documents` ou `list_folder`.

### Knowledge nao encontrada
```python
{
    "status": "error",
    "error": "HTTP 404",
    "code": "404"
}
```

**Solucao**: Verificar a `key` com `list_knowledge`.

### Parametro obrigatorio em falta
```python
{
    "status": "error",
    "error": "content e obrigatorio",
    "code": "INVALID_REQUEST"
}
```

**Solucao**: Verificar que todos os parametros obrigatorios estao preenchidos.

### Timeout
```python
{
    "status": "error",
    "error": "Request timeout apos 30 segundos",
    "code": "TIMEOUT"
}
```

**Solucao**: Tentar novamente. Se persistir, o Context Management MS pode estar indisponivel.

## Limitacoes

- Timeout: 30 segundos por request
- Upload de documentos apenas suporta conteudo de texto (nao binario)
- O conteudo do contexto e em formato markdown
- Knowledge values devem ser serializaveis em JSON
- Comunicacao sincrona com o Context Management MS
- Sem suporte a paginacao em list_documents e list_knowledge
- Preview de documentos limitado ao numero de caracteres configurado (default: 500)
