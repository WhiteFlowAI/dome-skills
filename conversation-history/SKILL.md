---
name: conversation-history
description: Consulta o historico de conversas e mensagens do utilizador. Use para pesquisar conversas anteriores, obter mensagens de uma conversa especifica e analisar o contexto de interacoes passadas.
---

# Conversation History - Historico de Conversas

Skill para consultar o historico de conversas e mensagens do utilizador, permitindo analisar contexto de interacoes anteriores e ajudar nos proximos passos.

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Conversas anteriores ou historico de interacoes
- Retomar trabalho ou topicos discutidos anteriormente
- O que foi feito ou discutido numa conversa passada
- Pesquisar conversas por titulo ou tema
- Consultar detalhes de uma conversa especifica
- Verificar o contexto antes de iniciar uma nova tarefa
- Relembrar decisoes ou informacoes de sessoes anteriores

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/conversation-history")
from conversation_client import list_conversations, get_conversation_messages
```

## Operacoes Disponiveis

### 1. Listar Conversas

```python
import sys
sys.path.insert(0, "/var/cache/skills/conversation-history")
from conversation_client import list_conversations

# Listar as ultimas 10 conversas
result = list_conversations(user_id="user-123")

if result.get('status') == 'success':
    for conv in result.get('conversations', []):
        print(f"Titulo: {conv.get('title')}")
        print(f"Data: {conv.get('last_message_timestamp')}")
        print(f"ID: {conv.get('id')}")
        print("---")

# Pesquisar conversas por titulo
result = list_conversations(
    user_id="user-123",
    search="projeto",
    limit=20
)

# Filtrar por intervalo de datas
result = list_conversations(
    user_id="user-123",
    created_after="2025-01-01T00:00:00Z",
    created_before="2025-01-31T23:59:59Z",
    limit=50
)

# Combinar filtros
result = list_conversations(
    user_id="user-123",
    search="relatorio",
    created_after="2025-06-01T00:00:00Z",
    limit=10
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `limit` (opcional): Numero maximo de conversas a retornar (default: 10, max: 100)
- `search` (opcional): Texto para pesquisar no titulo da conversa
- `created_after` (opcional): Data minima no formato ISO 8601 (ex: '2025-01-15T00:00:00Z')
- `created_before` (opcional): Data maxima no formato ISO 8601
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

**Nota:** As conversas favoritas sao sempre retornadas primeiro, seguidas das nao-favoritas ordenadas por data da ultima mensagem (mais recente primeiro).

### 2. Obter Mensagens de uma Conversa

```python
import sys
sys.path.insert(0, "/var/cache/skills/conversation-history")
from conversation_client import get_conversation_messages

# Obter apenas perguntas e respostas (mais conciso)
result = get_conversation_messages(
    user_id="user-123",
    conversation_id="conv-abc123",
    message_types="user_text,text",
    limit=50
)

if result.get('status') == 'success':
    for msg in result.get('messages', []):
        tipo = msg.get('type')
        conteudo = msg.get('content')
        print(f"[{tipo}] {conteudo[:100]}...")
        print("---")

# Obter tudo incluindo reasoning (para analise detalhada)
result = get_conversation_messages(
    user_id="user-123",
    conversation_id="conv-abc123",
    include_reasoning=True,
    limit=100
)

# Paginacao (para conversas longas)
result = get_conversation_messages(
    user_id="user-123",
    conversation_id="conv-abc123",
    message_types="user_text,text",
    limit=20,
    offset=0   # Primeira pagina
)

# Segunda pagina
result = get_conversation_messages(
    user_id="user-123",
    conversation_id="conv-abc123",
    message_types="user_text,text",
    limit=20,
    offset=20  # Proximos 20
)

# Filtrar por intervalo de ordem (para obter parte especifica da conversa)
result = get_conversation_messages(
    user_id="user-123",
    conversation_id="conv-abc123",
    start_order=0,
    end_order=10
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `conversation_id` (obrigatorio): ID da conversa
- `limit` (opcional): Numero maximo de mensagens a retornar (default: 50, max: 200)
- `offset` (opcional): Posicao inicial para paginacao (default: 0)
- `message_types` (opcional): Tipos de mensagem separados por virgula. Tipos disponiveis:
  - `user_text` - Mensagens do utilizador
  - `text` - Respostas do assistente
  - `reasoning` - Processo de raciocinio da IA
  - `reasoning_websearch` - Raciocinio com pesquisa web
  - `reasoning_extension` - Raciocinio com extensoes/ferramentas
  - `citations` - Referencias e citacoes
  - `clarification` - Pedidos de esclarecimento do assistente
  - `plan` - Planos gerados pelo assistente
  - `user_options` - Selecoes multi-opcao do utilizador
- `include_reasoning` (opcional): Se True, inclui automaticamente mensagens de reasoning (reasoning, reasoning_websearch, reasoning_extension). Default: False
- `start_order` (opcional): Numero de ordem inicial (inclusivo)
- `end_order` (opcional): Numero de ordem final (inclusivo)
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

**Dica:** Para obter um resumo rapido da conversa, usa `message_types="user_text,text"` que retorna apenas perguntas e respostas, sem reasoning ou citacoes.

## Workflow Tipico

### Consultar historico e retomar trabalho:

```python
import sys
sys.path.insert(0, "/var/cache/skills/conversation-history")
from conversation_client import list_conversations, get_conversation_messages

# 1. Listar conversas recentes
conversas = list_conversations(
    user_id="user-123",
    limit=5
)

if conversas.get('status') == 'success':
    print(f"Encontradas {conversas.get('total', 0)} conversas recentes:")
    for conv in conversas.get('conversations', []):
        print(f"  - [{conv.get('id')[:8]}...] {conv.get('title')} ({conv.get('last_message_timestamp')})")

# 2. Obter mensagens da conversa relevante
if conversas.get('conversations'):
    conv_id = conversas['conversations'][0]['id']

    mensagens = get_conversation_messages(
        user_id="user-123",
        conversation_id=conv_id,
        message_types="user_text,text",
        limit=30
    )

    if mensagens.get('status') == 'success':
        print(f"\nUltimas {mensagens.get('total', 0)} mensagens:")
        for msg in mensagens.get('messages', []):
            tipo = "Utilizador" if msg.get('type') == 'user_text' else "Assistente"
            conteudo = msg.get('content', '')
            if isinstance(conteudo, str):
                print(f"  [{tipo}] {conteudo[:150]}...")

# 3. Usar o contexto para ajudar o utilizador
# Com base nas mensagens anteriores, o agente pode:
# - Resumir o que foi discutido
# - Identificar tarefas pendentes
# - Sugerir proximos passos
```

### Pesquisar conversa especifica:

```python
import sys
sys.path.insert(0, "/var/cache/skills/conversation-history")
from conversation_client import list_conversations, get_conversation_messages

# 1. Pesquisar por titulo
resultado = list_conversations(
    user_id="user-123",
    search="relatorio vendas",
    limit=10
)

if resultado.get('status') == 'success' and resultado.get('total', 0) > 0:
    conv = resultado['conversations'][0]
    print(f"Encontrada: {conv.get('title')}")

    # 2. Obter mensagens com reasoning para analise completa
    mensagens = get_conversation_messages(
        user_id="user-123",
        conversation_id=conv['id'],
        include_reasoning=True,
        limit=100
    )

    if mensagens.get('status') == 'success':
        for msg in mensagens.get('messages', []):
            print(f"[{msg.get('type')}] {str(msg.get('content', ''))[:200]}")
```

## Exemplos de Perguntas do Utilizador

- "O que discutimos ontem?"
- "Consegues ver as minhas conversas anteriores?"
- "Retoma o trabalho que estavamos a fazer"
- "Na ultima conversa, o que ficou decidido?"
- "Pesquisa nas minhas conversas por 'projeto X'"
- "Mostra-me o historico da conversa sobre o relatorio"
- "O que me tinhas sugerido fazer da ultima vez?"
- "Quais foram as minhas ultimas conversas?"
- "Ve se ja discutimos este tema antes"
- "Continua de onde paramos"

## Estrutura de Dados

### Conversation (de list_conversations):
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",  # UUID da conversa
    "title": "Discussao sobre projeto X",           # Titulo (pode ser null)
    "started_at": "2025-01-15T10:30:00Z",           # Data de inicio
    "last_message_timestamp": "2025-01-15T11:45:00Z",# Data da ultima mensagem
    "favorite": false,                                # Se e favorita
    "active": true,                                   # Se esta ativa
    "type": "chat",                                   # Tipo de conversa (opcional)
    "tasks": [                                        # Tarefas associadas
        {
            "id": "task-uuid",
            "title": "Titulo da tarefa"
        }
    ]
}
```

### Message (de get_conversation_messages):
```python
{
    "id": "msg-uuid",                                # UUID da mensagem
    "conversation_id": "conv-uuid",                  # UUID da conversa
    "content": "Texto da mensagem...",               # Conteudo (string ou JSON)
    "type": "text",                                  # Tipo da mensagem
    "status": "completed",                           # Status: sent, completed, pending
    "order_number": 5,                               # Numero de ordem (ou null para reasoning)
    "created_at": "2025-01-15T10:30:00Z",           # Data de criacao
    "model": "openai/gpt-4o",                       # Modelo usado (opcional)
    "metrics": {                                     # Metricas (opcional)
        "duration_ms": 2345,
        "tokens": {
            "prompt_tokens": 150,
            "completion_tokens": 320,
            "total_tokens": 470
        }
    },
    "files": [                                       # Ficheiros anexos (opcional)
        {
            "id": "file-uuid",
            "filename": "documento.pdf",
            "mimeType": "application/pdf",
            "size": 1024000
        }
    ]
}
```

## Erros Comuns

### Conversa nao encontrada
```python
{
    "status": "error",
    "error_code": "CONVERSATION_NOT_FOUND",
    "message": "Conversa conv-abc123 nao encontrada"
}
```

**Solucao**: Verificar se o conversation_id esta correto. Usar `list_conversations` para obter IDs validos.

### Sem acesso a conversa
```python
{
    "status": "error",
    "error_code": "FORBIDDEN",
    "message": "Sem acesso a esta conversa"
}
```

**Solucao**: O utilizador so pode aceder as suas proprias conversas. Verificar se o user_id esta correto.

### Tenant em falta
```python
{
    "status": "error",
    "error_code": "MISSING_TENANT_ID",
    "message": "x-tenant-id header is required"
}
```

**Solucao**: Garantir que o `tenant_id` esta a ser enviado no request.

### Request invalido
```python
{
    "status": "error",
    "error_code": "INVALID_REQUEST",
    "message": "conversation_id e obrigatorio"
}
```

## Limitacoes

- Timeout: 30 segundos por request
- Limite maximo de conversas por request: 100
- Limite maximo de mensagens por request: 200
- Apenas conversas ativas sao retornadas (conversas desativadas/arquivadas nao aparecem)
- A pesquisa por titulo (`search`) nao pesquisa dentro do conteudo das mensagens
- O conteudo de mensagens do tipo `reasoning_websearch` e `reasoning_extension` e armazenado em formato JSON, nao texto simples
