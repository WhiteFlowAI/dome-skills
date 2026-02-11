---
name: drive
description: Gere ficheiros no Google Drive ou Microsoft OneDrive. Use para listar, ler, criar, atualizar e apagar ficheiros e pastas no armazenamento cloud do utilizador.
---

# Drive - Google Drive & OneDrive

Skill para gestao de ficheiros cloud com suporte a Google Drive e Microsoft OneDrive.

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Ver ficheiros ou pastas no Drive
- Procurar ficheiros por nome ou conteudo
- Ler o conteudo de um ficheiro
- Criar novos ficheiros ou pastas
- Atualizar conteudo de ficheiros existentes
- Apagar ficheiros ou pastas
- Organizar ficheiros em pastas

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import list_files, get_file, read_file_content, create_file, update_file, delete_file, create_folder
```

## Operacoes Disponiveis

### 1. Listar Ficheiros

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import list_files

# Listar ficheiros na raiz
result = list_files(user_id="user-123")

if result.get('status') == 'success':
    for f in result.get('files', []):
        print(f"Nome: {f.get('name')}")
        print(f"Tipo: {f.get('mimeType')}")
        print(f"Modificado: {f.get('modifiedTime')}")
        print("---")

# Pesquisar ficheiros por nome
result = list_files(
    user_id="user-123",
    query="relatorio trimestral",
    limit=20
)

# Listar ficheiros numa pasta especifica
result = list_files(
    user_id="user-123",
    folder_id="folder-abc123"
)

# Ordenar por data de modificacao
result = list_files(
    user_id="user-123",
    sort_by="modifiedTime desc",
    limit=10
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `folder_id` (opcional): ID da pasta para listar (default: raiz)
- `query` (opcional): Texto para pesquisar no nome dos ficheiros
- `limit` (opcional): Numero maximo de ficheiros (default: 20)
- `sort_by` (opcional): Ordenacao (ex: 'modifiedTime desc', 'name')
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 2. Obter Metadados de um Ficheiro

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import get_file

# Obter metadados pelo ID
result = get_file(
    user_id="user-123",
    file_id="file-abc123"
)

if result.get('status') == 'success':
    f = result.get('file', {})
    print(f"Nome: {f.get('name')}")
    print(f"Tipo: {f.get('mimeType')}")
    print(f"Tamanho: {f.get('size')}")
    print(f"Modificado: {f.get('modifiedTime')}")
    print(f"Link: {f.get('webViewLink')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `file_id` (obrigatorio): ID do ficheiro
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 3. Ler Conteudo de um Ficheiro

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import read_file_content

# Ler conteudo como texto
result = read_file_content(
    user_id="user-123",
    file_id="file-abc123"
)

if result.get('status') == 'success':
    print(f"Conteudo: {result.get('content')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `file_id` (obrigatorio): ID do ficheiro a ler
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 4. Criar Ficheiro

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import create_file

# Criar ficheiro de texto na raiz
result = create_file(
    user_id="user-123",
    name="notas.md",
    content="# Notas da Reuniao\n\n- Ponto 1\n- Ponto 2"
)

if result.get('status') == 'success':
    print(f"Ficheiro criado! ID: {result.get('file_id')}")

# Criar ficheiro numa pasta especifica
result = create_file(
    user_id="user-123",
    name="relatorio.md",
    content="# Relatorio Q1\n\nResumo...",
    folder_id="folder-abc123",
    content_type="text/markdown"
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `name` (obrigatorio): Nome do ficheiro
- `content` (obrigatorio): Conteudo do ficheiro
- `folder_id` (opcional): ID da pasta destino (default: raiz)
- `content_type` (opcional): MIME type (default: 'text/plain')
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 5. Atualizar Conteudo de um Ficheiro

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import update_file

# Atualizar conteudo
result = update_file(
    user_id="user-123",
    file_id="file-abc123",
    content="# Relatorio Atualizado\n\nNovo conteudo..."
)

if result.get('status') == 'success':
    print("Ficheiro atualizado!")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `file_id` (obrigatorio): ID do ficheiro a atualizar
- `content` (obrigatorio): Novo conteudo do ficheiro
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 6. Apagar Ficheiro

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import delete_file

# Apagar ficheiro pelo ID
result = delete_file(
    user_id="user-123",
    file_id="file-abc123"
)

if result.get('status') == 'success':
    print("Ficheiro apagado!")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `file_id` (obrigatorio): ID do ficheiro a apagar
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 7. Criar Pasta

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import create_folder

# Criar pasta na raiz
result = create_folder(
    user_id="user-123",
    name="Projetos 2025"
)

if result.get('status') == 'success':
    print(f"Pasta criada! ID: {result.get('folder_id')}")

# Criar sub-pasta
result = create_folder(
    user_id="user-123",
    name="Documentos",
    folder_id="folder-abc123"
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `name` (obrigatorio): Nome da pasta
- `folder_id` (opcional): ID da pasta pai (default: raiz)
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

## Workflow Tipico

### Procurar e ler um ficheiro:

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import list_files, read_file_content

# 1. Procurar o ficheiro
result = list_files(
    user_id="user-123",
    query="relatorio mensal",
    limit=5
)

if result.get('status') == 'success':
    files = result.get('files', [])
    print(f"Encontrados {len(files)} ficheiros:")
    for f in files:
        print(f"  - {f.get('name')} (ID: {f.get('id')})")

    # 2. Ler o primeiro resultado
    if files:
        content_result = read_file_content(
            user_id="user-123",
            file_id=files[0].get('id')
        )
        if content_result.get('status') == 'success':
            print(f"\nConteudo:\n{content_result.get('content')}")
```

### Criar pasta e ficheiro:

```python
import sys
sys.path.insert(0, "/var/cache/skills/drive")
from drive_client import create_folder, create_file

# 1. Criar pasta
folder_result = create_folder(
    user_id="user-123",
    name="Relatorios 2025"
)

if folder_result.get('status') == 'success':
    folder_id = folder_result.get('folder_id')

    # 2. Criar ficheiro na pasta
    file_result = create_file(
        user_id="user-123",
        name="janeiro.md",
        content="# Relatorio Janeiro 2025\n\nResumo...",
        folder_id=folder_id
    )
    if file_result.get('status') == 'success':
        print(f"Ficheiro criado na pasta: {file_result.get('file_id')}")
```

## Exemplos de Perguntas do Utilizador

- "Mostra-me os meus ficheiros no Drive"
- "Procura o documento sobre o projeto X"
- "Le o conteudo do ficheiro relatorio.md"
- "Cria um novo ficheiro com estas notas"
- "Atualiza o ficheiro de notas com este conteudo"
- "Apaga o ficheiro antigo"
- "Cria uma pasta para os relatorios"
- "Que ficheiros tenho na pasta Projetos?"

## Estrutura de Dados

### File Summary (de list_files):
```python
{
    "id": "file-abc123",              # ID do ficheiro
    "name": "relatorio.md",           # Nome
    "mimeType": "text/markdown",      # Tipo MIME
    "size": "1234",                   # Tamanho em bytes
    "modifiedTime": "2025-01-20T10:00:00Z",  # Ultima modificacao
    "createdTime": "2025-01-15T08:00:00Z",   # Data de criacao
    "webViewLink": "https://...",     # Link para abrir no browser
    "parents": ["folder-xyz"]         # IDs das pastas pai
}
```

### File Content (de read_file_content):
```python
{
    "status": "success",
    "content": "# Titulo\n\nConteudo do ficheiro...",
    "file_id": "file-abc123",
    "name": "relatorio.md",
    "mimeType": "text/markdown"
}
```

### Create Result (de create_file):
```python
{
    "status": "success",
    "file_id": "file-xyz789",
    "name": "notas.md",
    "message": "Ficheiro criado com sucesso"
}
```

### Update Result (de update_file):
```python
{
    "status": "success",
    "file_id": "file-xyz789",
    "message": "Ficheiro atualizado com sucesso"
}
```

### Folder Result:
```python
{
    "status": "success",
    "folder_id": "folder-xyz789",
    "message": "Pasta criada com sucesso"
}
```

## Erros Comuns

### Provider nao conectado
```python
{
    "status": "error",
    "error_code": "DRIVE_PROVIDER_NOT_CONNECTED",
    "message": "Utilizador nao tem provider de drive conectado",
    "reauthorization_required": true,
    "action_url": "/api/oauth/google/authorize?service=drive"
}
```

**Solucao**: Informar o utilizador que precisa de conectar a conta de Drive na seccao de Integracoes.

### Autenticacao expirada
```python
{
    "status": "error",
    "error_code": "DRIVE_PROVIDER_AUTH_FAILED",
    "message": "Autenticacao com o provider falhou",
    "reauthorization_required": true,
    "provider": "google"
}
```

**Solucao**: Informar o utilizador que precisa de re-autorizar o acesso ao Drive.

### Ficheiro nao encontrado
```python
{
    "status": "error",
    "error_code": "DRIVE_FILE_NOT_FOUND",
    "message": "Ficheiro com ID 'xyz' nao encontrado"
}
```

### Request invalido
```python
{
    "status": "error",
    "error_code": "INVALID_REQUEST",
    "message": "Nome do ficheiro e obrigatorio"
}
```

## Limitacoes

- Timeout: 30 segundos por request
- Limite maximo de ficheiros por listagem: depende do provider
- A gestao de ficheiros requer autorizacao OAuth previa
- Suporta Google Drive e Microsoft OneDrive via OAuth
- Leitura de conteudo funciona melhor com ficheiros de texto (markdown, txt, etc.)
- Ficheiros binarios (imagens, PDFs) podem nao ser lidos como texto
