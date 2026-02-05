# Dome Superpowers

Skills repository for WhiteFlowAI agent execution.

## Skill Structure

Each skill is a folder containing:

```
skill-name/
├── superpower.md      # Required: frontmatter + full instructions
├── requirements.txt   # Optional: Python dependencies
└── src/               # Optional: helper Python modules
    └── helpers.py
```

## superpower.md Format

```markdown
---
name: skill-name
description: Brief description for agent context injection.
---

# Full Instructions

Detailed instructions the agent reads via `read_file` when needed.
```

## Adding a Skill

1. Create a folder with the skill name (lowercase, hyphens)
2. Add `superpower.md` with frontmatter and instructions
3. Optionally add `requirements.txt` for dependencies
4. Commit and push
