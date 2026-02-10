---
name: calendar
description: Gere eventos no Google Calendar ou Microsoft Outlook Calendar. Use para consultar agenda, criar reunioes, atualizar eventos e verificar disponibilidade.
---

# Calendar - Google & Outlook

Skill para gestao de calendario com suporte a Google Calendar e Microsoft Outlook Calendar.

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Ver agenda ou eventos do calendario
- Criar reunioes ou eventos
- Atualizar ou modificar eventos existentes
- Apagar eventos
- Verificar disponibilidade
- Responder a convites de reuniao

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import list_events, get_event_detail, create_event, update_event, delete_event
```

## Operacoes Disponiveis

### 1. Listar Eventos

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import list_events

# Listar os proximos 10 eventos
result = list_events(user_id="user-123")

if result.get('status') == 'success':
    for event in result.get('events', []):
        print(f"Titulo: {event.get('summary')}")
        print(f"Inicio: {event.get('start')}")
        print(f"Fim: {event.get('end')}")
        print("---")

# Com filtros de data
result = list_events(
    user_id="user-123",
    time_min="2025-01-15T00:00:00Z",  # RFC3339 format
    time_max="2025-01-31T23:59:59Z",
    max_results=20
)

# Pesquisar eventos por texto
result = list_events(
    user_id="user-123",
    query="reuniao projeto",
    max_results=15
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `time_min` (opcional): Data minima no formato RFC3339 (ex: '2025-01-15T00:00:00Z')
- `time_max` (opcional): Data maxima no formato RFC3339
- `query` (opcional): Texto para pesquisar no titulo/descricao
- `max_results` (opcional): Numero maximo de eventos (default: 10, max: 100)

### 2. Obter Detalhes de um Evento

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import get_event_detail

# Obter evento completo pelo ID
result = get_event_detail(
    user_id="user-123",
    event_id="evt-abc123"
)

if result.get('status') == 'success':
    event = result.get('event', {})
    print(f"Titulo: {event.get('summary')}")
    print(f"Descricao: {event.get('description')}")
    print(f"Localizacao: {event.get('location')}")
    print(f"Inicio: {event.get('start')}")
    print(f"Fim: {event.get('end')}")
    print(f"Participantes: {event.get('attendees', [])}")
    print(f"Link: {event.get('htmlLink')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `event_id` (obrigatorio): ID do evento a obter

### 3. Criar Evento

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import create_event

# Criar evento com hora especifica
result = create_event(
    user_id="user-123",
    summary="Reuniao de Projeto",
    start_date_time="2025-01-20T10:00:00Z",
    end_date_time="2025-01-20T11:00:00Z",
    description="Discussao sobre o progresso do projeto",
    location="Sala de reunioes A"
)

if result.get('status') == 'success':
    print(f"Evento criado! ID: {result.get('event_id')}")
    print(f"Link: {result.get('html_link')}")

# Criar evento de dia inteiro
result = create_event(
    user_id="user-123",
    summary="Feriado - Dia de Portugal",
    start_date="2025-06-10",
    end_date="2025-06-11"  # Para dia inteiro, end_date e o dia seguinte
)

# Criar reuniao com participantes e videoconferencia
result = create_event(
    user_id="user-123",
    summary="Weekly Standup",
    start_date_time="2025-01-22T09:00:00Z",
    end_date_time="2025-01-22T09:30:00Z",
    attendees=["joao@empresa.pt", "maria@empresa.pt"],
    add_conference=True  # Cria link Google Meet ou Teams automaticamente
)

if result.get('status') == 'success':
    print(f"Reuniao criada!")
    print(f"Link videoconferencia: {result.get('hangout_link')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `summary` (obrigatorio): Titulo do evento
- `start_date_time` (opcional): Inicio em RFC3339 (ex: '2025-01-20T10:00:00Z')
- `end_date_time` (opcional): Fim em RFC3339
- `start_date` (opcional): Inicio em YYYY-MM-DD para eventos de dia inteiro
- `end_date` (opcional): Fim em YYYY-MM-DD para eventos de dia inteiro
- `description` (opcional): Descricao do evento
- `location` (opcional): Localizacao
- `attendees` (opcional): Lista de emails dos participantes
- `add_conference` (opcional): Se True, cria link de videoconferencia (Google Meet ou Teams)

**Nota:** E obrigatorio fornecer (start_date_time + end_date_time) OU (start_date + end_date).

### 4. Atualizar Evento

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import update_event

# Atualizar titulo e hora
result = update_event(
    user_id="user-123",
    event_id="evt-abc123",
    summary="Reuniao Adiada",
    start_date_time="2025-01-20T14:00:00Z",
    end_date_time="2025-01-20T15:00:00Z"
)

if result.get('status') == 'success':
    print("Evento atualizado!")

# Atualizar apenas a descricao
result = update_event(
    user_id="user-123",
    event_id="evt-abc123",
    description="Nova descricao do evento"
)

# Alterar localizacao
result = update_event(
    user_id="user-123",
    event_id="evt-abc123",
    location="Sala B - Piso 2"
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `event_id` (obrigatorio): ID do evento a atualizar
- `summary` (opcional): Novo titulo
- `description` (opcional): Nova descricao
- `location` (opcional): Nova localizacao
- `start_date_time` (opcional): Novo inicio em RFC3339
- `end_date_time` (opcional): Novo fim em RFC3339

### 5. Apagar Evento

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import delete_event

# Apagar evento pelo ID
result = delete_event(
    user_id="user-123",
    event_id="evt-abc123"
)

if result.get('status') == 'success':
    print("Evento apagado!")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `event_id` (obrigatorio): ID do evento a apagar

## Workflow Tipico

### Ver agenda e criar reuniao:

```python
import sys
sys.path.insert(0, "/var/cache/skills/calendar")
from calendar_client import list_events, create_event

# 1. Ver eventos da proxima semana
from datetime import datetime, timedelta
now = datetime.utcnow()
next_week = now + timedelta(days=7)

events = list_events(
    user_id="user-123",
    time_min=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    time_max=next_week.strftime("%Y-%m-%dT%H:%M:%SZ"),
    max_results=20
)

if events.get('status') == 'success':
    print(f"Tens {events.get('total', 0)} eventos esta semana:")
    for evt in events.get('events', []):
        print(f"  - {evt.get('summary')} em {evt.get('start')}")

# 2. Criar nova reuniao com videoconferencia
result = create_event(
    user_id="user-123",
    summary="Sync semanal equipa",
    start_date_time="2025-01-24T10:00:00Z",
    end_date_time="2025-01-24T10:30:00Z",
    attendees=["equipa@empresa.pt"],
    add_conference=True
)

if result.get('status') == 'success':
    print(f"Reuniao criada: {result.get('html_link')}")
    if result.get('hangout_link'):
        print(f"Link videoconferencia: {result.get('hangout_link')}")
```

## Exemplos de Perguntas do Utilizador

- "Mostra-me a minha agenda para hoje"
- "Que reunioes tenho esta semana?"
- "Cria uma reuniao com o Joao para amanha as 10h"
- "Agenda uma chamada com a Maria na sexta"
- "Muda a reuniao das 15h para as 16h"
- "Cancela o evento de amanha"
- "Estou livre na quarta de manha?"
- "Marca uma reuniao com videoconferencia"

## Estrutura de Dados

### Event Summary (de list_events):
```python
{
    "id": "evt-abc123",             # ID do evento
    "summary": "Reuniao Projeto",   # Titulo
    "start": {
        "dateTime": "2025-01-20T10:00:00Z",  # Para eventos com hora
        "date": "2025-01-20"        # Para eventos de dia inteiro
    },
    "end": {
        "dateTime": "2025-01-20T11:00:00Z",
        "date": "2025-01-21"
    },
    "location": "Sala A",           # Localizacao (opcional)
    "status": "confirmed",          # Status: confirmed, tentative, cancelled
    "htmlLink": "https://...",      # Link para abrir no calendario
}
```

### Event Full (de get_event_detail):
```python
{
    "id": "evt-abc123",
    "summary": "Reuniao Projeto",
    "description": "Descricao completa...",
    "location": "Sala A",
    "start": {
        "dateTime": "2025-01-20T10:00:00Z",
        "timeZone": "Europe/Lisbon"
    },
    "end": {
        "dateTime": "2025-01-20T11:00:00Z",
        "timeZone": "Europe/Lisbon"
    },
    "attendees": [
        {
            "email": "joao@empresa.pt",
            "displayName": "Joao Silva",
            "responseStatus": "accepted"  # accepted, declined, tentative, needsAction
        }
    ],
    "organizer": {
        "email": "organizador@empresa.pt",
        "displayName": "Maria Santos"
    },
    "htmlLink": "https://...",
    "hangoutLink": "https://meet.google.com/...",  # Se tiver videoconferencia
    "status": "confirmed"
}
```

### Create/Update Result:
```python
{
    "status": "success",
    "event_id": "evt-xyz789",
    "html_link": "https://...",
    "hangout_link": "https://meet.google.com/...",  # Se add_conference=True
    "message": "Event created successfully with video conference link"
}
```

## Erros Comuns

### Provider nao conectado
```python
{
    "status": "error",
    "error_code": "CALENDAR_PROVIDER_NOT_CONNECTED",
    "message": "Utilizador nao tem provider de calendario conectado",
    "reauthorization_required": true,
    "action_url": "/api/oauth/google/authorize?service=calendar"
}
```

**Solucao**: Informar o utilizador que precisa de conectar a conta de calendario na seccao de Integracoes.

### Autenticacao expirada
```python
{
    "status": "error",
    "error_code": "CALENDAR_PROVIDER_AUTH_FAILED",
    "message": "Autenticacao com o provider falhou",
    "reauthorization_required": true,
    "provider": "google"
}
```

**Solucao**: Informar o utilizador que precisa de re-autorizar o acesso ao calendario.

### Evento nao encontrado
```python
{
    "status": "error",
    "error_code": "CALENDAR_EVENT_NOT_FOUND",
    "message": "Evento com ID 'xyz' nao encontrado"
}
```

### Request invalido
```python
{
    "status": "error",
    "error_code": "INVALID_REQUEST",
    "message": "Deve fornecer (startDateTime + endDateTime) OU (startDate + endDate)"
}
```

## Formatos de Data

### Eventos com hora (RFC3339):
- `2025-01-20T10:00:00Z` - UTC
- `2025-01-20T10:00:00+01:00` - Com timezone

### Eventos de dia inteiro (YYYY-MM-DD):
- `2025-01-20` - Data inicio
- `2025-01-21` - Data fim (sempre o dia seguinte para eventos de 1 dia)

## Limitacoes

- Timeout: 30 segundos por request
- Limite maximo de eventos por request: 100
- A criacao de eventos requer autorizacao OAuth previa
- Suporta Google Calendar e Microsoft Outlook Calendar via OAuth
- Videoconferencia automatica: Google Meet para Google, Teams para Microsoft
