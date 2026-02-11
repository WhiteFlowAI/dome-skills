---
name: email
description: Envia e recebe emails via Google (Gmail) ou Microsoft (Outlook). Use para consultar caixa de entrada, enviar mensagens, responder a emails e gerir a comunicacao.
---

# Email - Gmail & Outlook

Skill para gestao de email com suporte a Google (Gmail) e Microsoft (Outlook).

## Quando Usar

Use esta skill quando o utilizador perguntar sobre:
- Ler emails da caixa de entrada
- Enviar novos emails
- Responder a emails existentes
- Pesquisar emails por assunto, remetente ou data
- Criar rascunhos de email
- Verificar emails recentes ou nao lidos

## Como Usar

Importa o modulo e usa as funcoes. O skill usa `requests` (sincrono).

```python
import sys
sys.path.insert(0, "/var/cache/skills/email")
from email_client import list_emails, get_email_detail, send_email, search_emails
```

## Operacoes Disponiveis

### 1. Listar Emails

```python
import sys
sys.path.insert(0, "/var/cache/skills/email")
from email_client import list_emails

# Listar os ultimos 10 emails
result = list_emails(user_id="user-123")

if result.get('status') == 'success':
    for email in result.get('emails', []):
        print(f"De: {email.get('from')}")
        print(f"Assunto: {email.get('subject')}")
        print(f"Data: {email.get('date')}")
        print("---")

# Com filtros
result = list_emails(
    user_id="user-123",
    query="fatura",           # Pesquisar por texto
    from_email="banco@exemplo.pt",  # Filtrar por remetente
    since="2025-01-01",       # Emails desde esta data
    limit=20                  # Maximo de emails
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `query` (opcional): Texto para pesquisar no assunto/corpo
- `from_email` (opcional): Filtrar por endereco do remetente
- `since` (opcional): Data no formato YYYY-MM-DD
- `limit` (opcional): Numero maximo de emails (default: 10, max: 50)
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 2. Obter Detalhes de um Email

```python
import sys
sys.path.insert(0, "/var/cache/skills/email")
from email_client import get_email_detail

# Obter email completo pelo ID
result = get_email_detail(
    user_id="user-123",
    email_id="msg-abc123"
)

if result.get('status') == 'success':
    email = result.get('email', {})
    print(f"De: {email.get('from')}")
    print(f"Para: {email.get('to')}")
    print(f"Assunto: {email.get('subject')}")
    print(f"Corpo: {email.get('body_text')}")
    print(f"Anexos: {email.get('attachments', [])}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `email_id` (obrigatorio): ID do email a obter
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

### 3. Enviar Email

```python
import sys
sys.path.insert(0, "/var/cache/skills/email")
from email_client import send_email

# Enviar email simples
result = send_email(
    user_id="user-123",
    to=["destinatario@exemplo.pt"],
    subject="Assunto do Email",
    body_text="Corpo do email em texto simples."
)

if result.get('status') == 'success':
    print(f"Email enviado! ID: {result.get('message_id')}")

# Enviar email com HTML
result = send_email(
    user_id="user-123",
    to=["destinatario@exemplo.pt", "outro@exemplo.pt"],
    subject="Newsletter",
    body_html="<h1>Titulo</h1><p>Conteudo HTML</p>"
)

# Enviar com texto e HTML
result = send_email(
    user_id="user-123",
    to=["destinatario@exemplo.pt"],
    subject="Email Completo",
    body_text="Versao texto para clientes antigos",
    body_html="<p>Versao HTML para clientes modernos</p>"
)
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `to` (obrigatorio): Lista de destinatarios
- `subject` (obrigatorio): Assunto do email
- `body_text` (opcional): Corpo em texto simples
- `body_html` (opcional): Corpo em HTML
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant
- Pelo menos um de `body_text` ou `body_html` e obrigatorio

### 4. Pesquisar Emails

```python
import sys
sys.path.insert(0, "/var/cache/skills/email")
from email_client import search_emails

# Pesquisar emails com uma query
result = search_emails(
    user_id="user-123",
    query="reuniao projeto",
    limit=15
)

if result.get('status') == 'success':
    print(f"Encontrados {result.get('total', 0)} emails")
    for email in result.get('emails', []):
        print(f"- {email.get('subject')}")
```

**Parametros:**
- `user_id` (obrigatorio): ID do utilizador
- `query` (obrigatorio): Texto para pesquisar
- `limit` (opcional): Numero maximo de resultados (default: 10)
- `tenant_id` (opcional): ID do tenant para ambientes multi-tenant

## Workflow Tipico

### Ler e responder a emails:

```python
import sys
sys.path.insert(0, "/var/cache/skills/email")
from email_client import list_emails, get_email_detail, send_email

# 1. Listar emails recentes
emails = list_emails(user_id="user-123", limit=5)

# 2. Obter detalhes de um email interessante
if emails.get('status') == 'success' and emails.get('emails'):
    email_id = emails['emails'][0]['id']
    details = get_email_detail(user_id="user-123", email_id=email_id)

    # 3. Responder ao email
    if details.get('status') == 'success':
        original = details['email']
        send_email(
            user_id="user-123",
            to=[original['from']],
            subject=f"Re: {original['subject']}",
            body_text=f"Obrigado pela mensagem.\n\n---\nOriginal: {original.get('body_text', '')[:200]}"
        )
```

## Exemplos de Perguntas do Utilizador

- "Mostra-me os meus emails recentes"
- "Tenho algum email do banco?"
- "Pesquisa emails sobre fatura"
- "Envia um email para joao@exemplo.pt sobre a reuniao"
- "Quais emails recebi esta semana?"
- "Le o ultimo email que recebi"

## Estrutura de Dados

### Email Summary (de list_emails/search_emails):
```python
{
    "id": "msg-abc123",           # ID do email
    "from": "remetente@email.pt", # Endereco do remetente
    "to": ["dest@email.pt"],      # Lista de destinatarios
    "subject": "Assunto",         # Assunto do email
    "snippet": "Preview...",      # Preview do conteudo
    "date": "2025-01-15T10:30:00Z",  # Data/hora
    "is_read": true,              # Lido ou nao
    "has_attachments": false      # Tem anexos
}
```

### Email Full (de get_email_detail):
```python
{
    "id": "msg-abc123",
    "from": "remetente@email.pt",
    "to": ["dest@email.pt"],
    "cc": ["copia@email.pt"],
    "subject": "Assunto",
    "body_text": "Conteudo em texto...",
    "body_html": "<p>Conteudo HTML...</p>",
    "date": "2025-01-15T10:30:00Z",
    "attachments": [
        {
            "filename": "documento.pdf",
            "mime_type": "application/pdf",
            "size": 1024
        }
    ]
}
```

### Send Result (de send_email):
```python
{
    "status": "success",
    "message_id": "sent-xyz789",
    "provider": "google"          # ou "microsoft"
}
```

## Erros Comuns

### Provider nao conectado
```python
{
    "status": "error",
    "error_code": "EMAIL_PROVIDER_NOT_CONNECTED",
    "message": "Utilizador nao tem provider de email conectado",
    "reauthorization_required": true,
    "action_url": "/api/oauth/google/authorize?service=email"
}
```

**Solucao**: Informar o utilizador que precisa de conectar a conta de email.

### Autenticacao expirada
```python
{
    "status": "error",
    "error_code": "EMAIL_PROVIDER_AUTH_FAILED",
    "message": "Autenticacao com o provider falhou",
    "reauthorization_required": true,
    "provider": "google"
}
```

**Solucao**: Informar o utilizador que precisa de re-autorizar o acesso ao email.

### Email nao encontrado
```python
{
    "status": "error",
    "error_code": "EMAIL_NOT_FOUND",
    "message": "Email com ID 'xyz' nao encontrado"
}
```

## Limitacoes

- Timeout: 30 segundos por request
- Limite maximo de emails por request: 50
- O envio de emails requer autorizacao OAuth previa
- Anexos de emails sao listados mas nao descarregados diretamente
- Suporta Google (Gmail) e Microsoft (Outlook) via OAuth
