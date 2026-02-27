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

## REGRAS IMPORTANTES para Criar Tarefas

Ao criar uma tarefa, o agente deve ser **autonomo** e **nao pedir campos desnecessarios** ao utilizador:

1. **Descricao (description)**: O unico campo que o utilizador deve fornecer e o que quer que seja feito. O agente deve melhorar, desenvolver e enriquecer esse texto para servir como descricao da tarefa.
2. **Titulo (title)**: **NAO pedir ao utilizador.** O titulo e gerado automaticamente pelo sistema a partir da descricao. Pode ser enviado como opcional apenas se o agente quiser sugerir um titulo mais curto.
3. **Tipo (type)**: **NAO pedir ao utilizador.** Usar SEMPRE `'default'`.
4. **Prioridade (priority)**: **NAO pedir ao utilizador.** Usar SEMPRE `'medium'` por defeito.
5. **Kanban column**: **NAO pedir ao utilizador.** Usar o default `'backlog'`.

**Resumo**: Quando o utilizador diz "cria uma tarefa para X", o agente deve imediatamente criar a tarefa usando a descricao fornecida (enriquecida), sem perguntar titulo, tipo, prioridade ou qualquer outro campo. Agir de forma rapida e autonoma.

## REGRA CRITICA: Reutilizar Resultados de Tarefas Anteriores

Antes de criar uma nova tarefa para algo que pode ja ter sido feito, o agente **DEVE** verificar tarefas anteriores:

1. **Verificar tarefas concluidas**: Chamar `list_tasks(user_id=..., status='completed')` para ver se ja existe uma tarefa relevante
2. **Obter output da tarefa**: Se encontrar uma tarefa relevante, chamar `get_task_output(user_id=..., task_id=...)` para obter o resultado
3. **Reutilizar o conteudo**: Se o output tiver `content`, usar esse conteudo diretamente sem re-executar a tarefa
4. **Informar o utilizador**: Se necessario, explicar que esta a usar os resultados de uma tarefa anterior

**Exemplo pratico**:
- Utilizador pede: "Vai buscar os meus emails" → Cria tarefa, executa, guarda output
- Utilizador pede: "Faz um resumo dos emails" → **NAO criar nova tarefa para buscar emails!** Em vez disso:
  1. Chamar `list_tasks(status='completed')` → Encontrar a tarefa de emails
  2. Chamar `get_task_output(task_id=...)` → Obter o conteudo dos emails
  3. Usar esse conteudo para fazer o resumo diretamente

**Quando reutilizar vs criar nova tarefa**:
- Se o pedido e um **follow-up** de algo ja feito → Reutilizar output anterior
- Se o pedido e algo **completamente novo** → Criar nova tarefa
- Se o pedido precisa de **dados mais recentes** (utilizador diz "atualiza" ou "busca novamente") → Criar nova tarefa

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import list_tasks, get_task, create_task, update_task, update_task_status, get_task_events, list_artifacts, get_task_output, add_artifact
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

**IMPORTANTE:** Ao criar uma tarefa, NAO perguntar titulo, tipo ou prioridade ao utilizador. Usar a descricao fornecida pelo utilizador (melhorada pelo agente) como `description`. O titulo e gerado automaticamente pelo sistema. Tipo e sempre `'default'`, prioridade e sempre `'medium'`.

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import create_task

# Utilizador disse: "cria uma tarefa para preparar o relatorio mensal"
# O agente enriquece a descricao e cria imediatamente:
result = create_task(
    user_id="user-123",
    description="Preparar o relatorio mensal de vendas, compilando os dados do ultimo mes e incluindo metricas de performance da equipa"
)

# Utilizador disse: "preciso de enviar um email ao cliente a confirmar a reuniao"
result = create_task(
    user_id="user-123",
    description="Enviar email ao cliente para confirmar a reuniao de amanha as 15h. Incluir agenda e pontos a discutir."
)

if result.get('status') == 'success':
    task = result.get('task', {})
    print(f"Tarefa criada: {task.get('display_id')} - {task.get('title')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `description` (obrigatorio na pratica): Descricao detalhada do que o utilizador quer. O agente deve enriquecer o pedido do utilizador.
- `title` (opcional): NAO pedir ao utilizador. Gerado automaticamente pelo sistema a partir da descricao. Enviar apenas se o agente quiser sugerir um titulo curto.
- `type` (NAO pedir): Usar SEMPRE 'default'
- `priority` (NAO pedir): Usar SEMPRE 'medium'
- `kanban_column` (NAO pedir): Usar o default 'backlog'
- `conversation_id` (opcional): ID da conversa associada
- `scheduled_at` (opcional): Data agendada em ISO 8601 (apenas se o utilizador mencionar uma data)
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

### 8. Obter Output/Resultado de uma Tarefa

Use esta funcao para obter o resultado de uma tarefa concluida. Essencial para reutilizar dados sem re-executar tarefas.

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import get_task_output

# Obter o resultado de uma tarefa concluida
result = get_task_output(user_id="user-123", task_id="TSK-001")

if result.get('status') == 'success':
    for output in result.get('outputs', []):
        print(f"Nome: {output.get('name')}")
        print(f"Conteudo: {output.get('content')}")

# Por display_id
result = get_task_output(user_id="user-123", task_id="TSK-005")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `task_id` (obrigatorio): UUID ou display_id da tarefa
- `tenant_id` (opcional): ID do tenant

**Retorno:**
- `outputs` (lista): Lista de outputs, cada um com:
  - `name`: Nome do artefacto de output
  - `content`: Conteudo completo do resultado (texto, JSON, etc.)
  - `storage_url`: URL se armazenado externamente
  - `metadata`: Informacoes adicionais (tipo de output, resumo, confianca)
  - `version`: Versao do output (pode haver multiplas versoes se re-executado)

### 9. Adicionar Artefacto (Ficheiro)

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

# 1. Criar tarefa (sem pedir titulo/tipo/prioridade ao utilizador)
result = create_task(
    user_id="user-123",
    description="Analisar a proposta comercial do cliente XYZ e preparar feedback detalhado com pontos fortes e areas de melhoria"
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

### Reutilizar resultado de tarefa anterior (follow-up):

```python
import sys
sys.path.insert(0, "/var/cache/skills/task-management")
from task_client import list_tasks, get_task_output

# 1. Utilizador pediu "faz um resumo dos emails" (ja tinha buscado emails antes)
# Primeiro, verificar se ja existe tarefa com os emails
completed = list_tasks(user_id="user-123", status="completed")

if completed.get('status') == 'success':
    # Procurar tarefa relevante (ex: que tenha "email" no titulo)
    email_task = None
    for task in completed.get('tasks', []):
        if 'email' in (task.get('title', '') or '').lower():
            email_task = task
            break

    if email_task:
        # 2. Obter o output (conteudo dos emails)
        output = get_task_output(user_id="user-123", task_id=email_task['id'])
        if output.get('status') == 'success' and output.get('total', 0) > 0:
            # 3. Usar o conteudo para gerar resumo (sem re-executar tarefa!)
            email_content = output['outputs'][0].get('content')
            # ... usar email_content para gerar o resumo
```

## Exemplos de Perguntas do Utilizador

- "Quais sao as minhas tarefas pendentes?"
- "Que tarefas tenho em execucao?"
- "Cria uma tarefa para preparar o relatorio mensal" → Criar imediatamente sem perguntar mais nada
- "Preciso de fazer uma analise de mercado" → Criar tarefa com descricao enriquecida
- "Marca a tarefa TSK-001 como concluida"
- "Cancela a tarefa de pesquisa"
- "Mostra-me os detalhes da tarefa TSK-005"
- "Altera a prioridade da tarefa para urgente"
- "Que ficheiros estao associados a esta tarefa?"
- "Adiciona estas notas como ficheiro na tarefa"
- "Qual e o historico de eventos da tarefa TSK-003?"
- "Quais tarefas preciso de completar esta semana?"
- "Agenda esta tarefa para amanha as 9h"
- "Faz um resumo dos emails que buscastes" → Reutilizar output da tarefa anterior (NAO re-buscar)
- "Qual foi o resultado da tarefa X?" → Usar `get_task_output`
- "Agora com esses dados, cria um relatorio" → Reutilizar output anterior

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
    "type": "input_document",              # Tipo: input_document, output, output_artifact, reference, plan
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
