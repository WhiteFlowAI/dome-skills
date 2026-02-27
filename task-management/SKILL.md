---
name: task-management
description: Gere as tarefas do utilizador. Use para listar tarefas, criar novas, alterar estado, verificar progresso, consultar historico de eventos e anexar ficheiros no contexto de uma tarefa.
---

# Task Management - Gestao de Tarefas

Skill para gerir tarefas do utilizador: listar, criar, atualizar estado, consultar eventos e anexar ficheiros.

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Quais tarefas tem pendentes, em execucao ou concluidas
- Criar uma nova tarefa ou item de trabalho
- Marcar uma tarefa como concluida, cancelada ou em progresso
- Ver detalhes ou estado de uma tarefa especifica
- Consultar o historico de eventos de uma tarefa
- Anexar ficheiros ou documentos a uma tarefa
- Ver ficheiros associados a uma tarefa
- Alterar titulo, descricao ou prioridade de uma tarefa
- Agendar uma tarefa para uma data especifica
- Organizar trabalho ou ver o que falta fazer

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import list_tasks, get_task, create_task, update_task, update_task_status, get_task_events, list_artifacts, add_artifact
```

## Operacoes Disponiveis

### 1. Listar Tarefas

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import list_tasks

# Listar todas as tarefas
result = list_tasks(user_id="user-123")

if result.get('status') == 'success':
    for task in result.get('tasks', []):
        print(f"[{task.get('display_id')}] {task.get('title')} - {task.get('status')}")

# Filtrar por estado
result = list_tasks(user_id="user-123", status="running")

# Filtrar por tipo
result = list_tasks(user_id="user-123", type="workflow")

# Combinar filtros com paginacao
result = list_tasks(user_id="user-123", status="pending", limit=10, offset=0)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `status` (opcional): Filtrar por estado ('created', 'pending', 'running', 'completed', 'failed', 'cancelled', 'planning', 'approval_plan_request')
- `type` (opcional): Filtrar por tipo ('default', 'workflow', 'deep_research')
- `limit` (opcional): Max tarefas a retornar (default: 20, max: 100)
- `offset` (opcional): Posicao inicial para paginacao (default: 0)
- `tenant_id` (opcional): ID do tenant

### 2. Obter Tarefa Especifica

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import get_task

# Por UUID
result = get_task(user_id="user-123", task_id="550e8400-e29b-41d4-a716-446655440000")

# Por display_id (ex: TSK-001)
result = get_task(user_id="user-123", task_id="TSK-001")

if result.get('status') == 'success':
    task = result.get('task', {})
    print(f"Titulo: {task.get('title')}")
    print(f"Estado: {task.get('status')}")
    print(f"Tipo: {task.get('type')}")
    print(f"Criada: {task.get('created_at')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id da tarefa (ex: 'TSK-001')
- `tenant_id` (opcional): ID do tenant

### 3. Criar Tarefa

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import create_task

# Tarefa simples
result = create_task(user_id="user-123", title="Preparar relatorio mensal")

# Tarefa com detalhes
result = create_task(
    user_id="user-123",
    title="Enviar email ao cliente",
    description="Confirmar reuniao de amanha as 15h",
    priority="high",
    kanban_column="todo"
)

# Tarefa agendada
result = create_task(
    user_id="user-123",
    title="Pesquisa de mercado",
    type="deep_research",
    scheduled_at="2025-02-01T09:00:00Z"
)

if result.get('status') == 'success':
    task = result.get('task', {})
    print(f"Tarefa criada: {task.get('display_id')} - {task.get('title')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `title` (obrigatorio): Titulo da tarefa
- `description` (opcional): Descricao detalhada
- `type` (opcional): 'default', 'workflow', 'deep_research' (default: 'default')
- `priority` (opcional): 'low', 'medium', 'high', 'urgent'
- `kanban_column` (opcional): 'backlog', 'todo', 'doing', 'done', 'waiting' (default: 'backlog')
- `conversation_id` (opcional): ID da conversa associada
- `scheduled_at` (opcional): Data agendada em ISO 8601
- `tenant_id` (opcional): ID do tenant

### 4. Atualizar Tarefa

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import update_task

# Alterar titulo
result = update_task(user_id="user-123", task_id="TSK-001", title="Novo titulo atualizado")

# Alterar prioridade e descricao
result = update_task(
    user_id="user-123",
    task_id="TSK-001",
    priority="urgent",
    description="Atualizado com urgencia"
)

# Mover para outra coluna kanban
result = update_task(user_id="user-123", task_id="TSK-001", kanban_column="doing")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id
- `title` (opcional): Novo titulo
- `description` (opcional): Nova descricao
- `priority` (opcional): 'low', 'medium', 'high', 'urgent'
- `kanban_column` (opcional): Nova coluna kanban
- `scheduled_at` (opcional): Nova data agendada em ISO 8601
- `tenant_id` (opcional): ID do tenant

**Nota:** Para alterar o estado (status), usar `update_task_status`.

### 5. Alterar Estado da Tarefa

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import update_task_status

# Iniciar execucao
result = update_task_status(user_id="user-123", task_id="TSK-001", status="running")

# Marcar como concluida
result = update_task_status(user_id="user-123", task_id="TSK-001", status="completed")

# Cancelar
result = update_task_status(user_id="user-123", task_id="TSK-001", status="cancelled")

if result.get('status') == 'success':
    task = result.get('task', {})
    print(f"Estado atualizado: {task.get('status')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id
- `status` (obrigatorio): Novo estado - 'created', 'pending', 'running', 'completed', 'failed', 'cancelled'
- `tenant_id` (opcional): ID do tenant

### 6. Historico de Eventos

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import get_task_events

result = get_task_events(user_id="user-123", task_id="TSK-001")

if result.get('status') == 'success':
    for event in result.get('events', []):
        print(f"[{event.get('created_at')}] {event.get('type')}: {event.get('payload')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id
- `limit` (opcional): Max eventos (default: 50, max: 200)
- `offset` (opcional): Posicao inicial para paginacao
- `tenant_id` (opcional): ID do tenant

### 7. Listar Artefactos (Ficheiros)

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import list_artifacts

# Todos os artefactos
result = list_artifacts(user_id="user-123", task_id="TSK-001")

# Filtrar por tipo
result = list_artifacts(user_id="user-123", task_id="TSK-001", type="input_document")

if result.get('status') == 'success':
    for artifact in result.get('artifacts', []):
        print(f"  {artifact.get('name')} ({artifact.get('type')}) - {artifact.get('mime_type')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id
- `type` (opcional): Filtrar por tipo ('input_document', 'output', 'reference', 'plan')
- `artifact_kind` (opcional): Filtrar por kind ('file')
- `tenant_id` (opcional): ID do tenant

### 8. Adicionar Artefacto (Ficheiro)

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import add_artifact

# Adicionar conteudo textual
result = add_artifact(
    user_id="user-123",
    task_id="TSK-001",
    name="notas-reuniao.txt",
    type="input_document",
    content="Notas da reuniao de hoje:\n- Ponto 1\n- Ponto 2",
    mime_type="text/plain"
)

# Adicionar referencia a ficheiro externo
result = add_artifact(
    user_id="user-123",
    task_id="TSK-001",
    name="relatorio.pdf",
    type="reference",
    storage_url="https://storage.example.com/files/relatorio.pdf",
    mime_type="application/pdf",
    size_bytes=2048000
)

if result.get('status') == 'success':
    artifact = result.get('artifact', {})
    print(f"Artefacto criado: {artifact.get('name')} (ID: {artifact.get('id')})")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id
- `name` (obrigatorio): Nome do ficheiro / artefacto
- `type` (obrigatorio): Tipo - 'input_document', 'output', 'reference'
- `content` (opcional): Conteudo textual
- `storage_url` (opcional): URL externo do ficheiro
- `mime_type` (opcional): Tipo MIME (ex: 'text/plain', 'application/pdf')
- `size_bytes` (opcional): Tamanho em bytes
- `metadata` (opcional): Metadados adicionais (dict)
- `tenant_id` (opcional): ID do tenant

## Workflow Tipico

### Verificar tarefas pendentes e atualizar progresso:

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import list_tasks, update_task_status, get_task

# 1. Listar tarefas pendentes e em execucao
pendentes = list_tasks(user_id="user-123", status="pending")
em_execucao = list_tasks(user_id="user-123", status="running")

if pendentes.get('status') == 'success':
    print(f"Tarefas pendentes: {pendentes.get('total', 0)}")
    for task in pendentes.get('tasks', []):
        print(f"  [{task.get('display_id')}] {task.get('title')}")

if em_execucao.get('status') == 'success':
    print(f"Em execucao: {em_execucao.get('total', 0)}")
    for task in em_execucao.get('tasks', []):
        print(f"  [{task.get('display_id')}] {task.get('title')}")

# 2. Marcar uma tarefa como concluida
update_task_status(user_id="user-123", task_id="TSK-001", status="completed")
```

### Criar tarefa e anexar ficheiro:

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import create_task, add_artifact

# 1. Criar tarefa
result = create_task(
    user_id="user-123",
    title="Analisar documento do cliente",
    description="Rever proposta comercial e preparar feedback",
    priority="high"
)

if result.get('status') == 'success':
    task_id = result['task']['id']

    # 2. Anexar documento de contexto
    add_artifact(
        user_id="user-123",
        task_id=task_id,
        name="proposta-comercial.pdf",
        type="input_document",
        storage_url="https://drive.google.com/...",
        mime_type="application/pdf"
    )
```

## Exemplos de Perguntas do Utilizador

- "Quais sao as minhas tarefas pendentes?"
- "Que tarefas tenho em execucao?"
- "Cria uma tarefa para preparar o relatorio mensal"
- "Marca a tarefa TSK-001 como concluida"
- "Cancela a tarefa de pesquisa"
- "Mostra-me os detalhes da tarefa TSK-005"
- "Altera a prioridade da tarefa para urgente"
- "Que ficheiros estao associados a esta tarefa?"
- "Adiciona estas notas como ficheiro na tarefa"
- "Qual e o historico de eventos da tarefa TSK-003?"
- "Quais tarefas preciso de completar esta semana?"
- "Agenda esta tarefa para amanha as 9h"

## Estrutura de Dados

### Task (de list_tasks ou get_task):
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",  # UUID
    "display_id": "TSK-001",                         # ID legivel
    "title": "Preparar relatorio mensal",
    "description": "Compilar dados de vendas Q1",
    "status": "running",                              # Estado atual
    "type": "default",                                # Tipo: default, workflow, deep_research
    "tenant_id": "tenant-uuid",
    "user_id": "user-uuid",
    "conversation_id": "conv-uuid",                   # Conversa associada (opcional)
    "plan": null,                                     # Plano de execucao (workflow tasks)
    "error_message": null,                            # Mensagem de erro (se failed)
    "kanban_column": "doing",                         # Coluna kanban
    "scheduled_at": null,                             # Data agendada (opcional)
    "created_at": "2025-01-15T10:30:00Z",
    "started_at": "2025-01-15T10:35:00Z",
    "updated_at": "2025-01-15T11:00:00Z",
    "completed_at": null
}
```

### Task Event (de get_task_events):
```python
{
    "id": "event-uuid",
    "task_id": "task-uuid",
    "type": "progress",                    # Tipo de evento
    "source": "worker",                    # Origem: worker, user, system
    "payload": {                           # Dados do evento
        "progress": 50,
        "message": "Processing step 2/4"
    },
    "created_at": "2025-01-15T10:40:00Z"
}
```

### Artifact (de list_artifacts ou add_artifact):
```python
{
    "id": "artifact-uuid",
    "task_id": "task-uuid",
    "name": "relatorio.pdf",
    "type": "input_document",              # Tipo: input_document, output, reference, plan
    "artifact_kind": "file",
    "content": null,                       # Conteudo textual (ou null se externo)
    "storage_url": "https://...",          # URL do ficheiro (ou null se inline)
    "mime_type": "application/pdf",
    "size_bytes": 2048000,
    "status": "approved",
    "is_visible": true,
    "metadata": {},
    "created_at": "2025-01-15T10:30:00Z"
}
```

## Estados Possiveis de uma Tarefa

| Estado | Descricao |
|--------|-----------|
| `created` | Tarefa criada, aguardando inicio |
| `pending` | Tarefa pendente de execucao |
| `planning` | A gerar plano de execucao (workflow) |
| `approval_plan_request` | Plano pronto, aguardando aprovacao |
| `running` | Em execucao |
| `completed` | Concluida com sucesso |
| `failed` | Falhou durante execucao |
| `cancelled` | Cancelada pelo utilizador |

## Erros Comuns

### Tarefa nao encontrada
```python
{
    "status": "error",
    "error_code": "TASK_NOT_FOUND",
    "message": "Task TSK-999 not found"
}
```
**Solucao**: Verificar se o task_id ou display_id esta correto. Usar `list_tasks` para obter IDs validos.

### Sem acesso a tarefa
```python
{
    "status": "error",
    "error_code": "FORBIDDEN",
    "message": "You do not have access to this task"
}
```
**Solucao**: O utilizador so pode aceder a tarefas do seu tenant.

### Estado invalido
```python
{
    "status": "error",
    "error_code": "INVALID_STATUS",
    "message": "Status must be one of: created, pending, running, completed, failed, cancelled"
}
```
**Solucao**: Usar um dos estados validos listados na mensagem de erro.

### Tenant em falta
```python
{
    "status": "error",
    "error_code": "MISSING_TENANT_ID",
    "message": "x-tenant-id header is required"
}
```
**Solucao**: Garantir que o `tenant_id` esta a ser enviado.

## Limitacoes

- Timeout: 30 segundos por request
- Limite maximo de tarefas por request: 100
- Limite maximo de eventos por request: 200
- A alteracao de estado via skill esta limitada a estados simples (created, pending, running, completed, failed, cancelled)
- Estados avancados de workflow (planning, approval_plan_request, etc.) sao geridos automaticamente pelo sistema
- Conteudo de artefactos textuais tem limite pratico de tamanho (recomendado < 1MB)
