# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**dome-superpowers** is a skills repository for the WhiteFlowAI agent execution platform. Each skill is a self-contained folder that provides instructions and helper scripts enabling an AI agent to interact with external services (email, calendar, cloud storage, government APIs, etc.).

Skills are loaded at runtime by the worker service from `/var/cache/skills/<skill-name>/` and executed as Python code within agent workflows.

## Repository Structure

```
<skill-name>/
├── SKILL.md              # Required: frontmatter (name, description) + full agent instructions
├── scripts/
│   ├── requirements.txt  # Python dependencies (installed at deploy time)
│   └── <module>.py       # Helper Python module imported by the agent
```

**Current skills:** basegov, calendar, diario-republica, drive, email, report-creator

## Skill Conventions

- **SKILL.md frontmatter** must include `name` (lowercase, hyphens) and `description` (used for context injection to decide when to activate the skill)
- **Folder name** must match the `name` field in frontmatter
- Python scripts use `sys.path.insert(0, "/var/cache/skills/<skill-name>")` for imports at runtime
- All API-calling skills use synchronous `requests` library, except `basegov` which uses async `aiohttp`
- Skills return dicts with `status: "success"` or `status: "error"` with `error_code` and `message`
- OAuth errors include `reauthorization_required: true` and `action_url` for re-auth flow
- All skills require `user_id` as the first parameter for API calls
- Content is written in Portuguese (Portugal)
- `report-creator` is the only skill without a `scripts/` directory — it provides instructions for the agent to generate markdown reports using `file_write`

## Adding a New Skill

1. Create a folder with the skill name (lowercase, hyphens)
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`) and full agent instructions
3. Include sections: "Quando Usar", "Como Usar", "Operacoes Disponiveis", "Workflow Tipico", "Estrutura de Dados", "Erros Comuns", "Limitacoes"
4. If the skill needs Python helpers, add `scripts/requirements.txt` and `scripts/<module>.py`
5. Follow the existing pattern: import example, parameter docs, return value schemas, error handling examples

## Git Workflow

Do not run `git commit` or `git push` unless explicitly requested via `/CommitAndPush`.
