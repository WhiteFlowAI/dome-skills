---
name: web_research  
description: "Comprehensive research grounded in web data with explicit citations. Use when you need multi-source synthesis—comparisons, current events, market analysis, detailed reports. "
---
# Research Skill

Conduct comprehensive research on any topic with automatic source gathering, analysis, and response generation with citations.

### Using the Script

```bash
./scripts/research.sh '<json>' [output_file]
```

**Examples:**

```bash
# Basic research
./scripts/research.sh '{"input": "quantum computing trends"}'

# With pro model for comprehensive analysis
./scripts/research.sh '{"input": "AI agents comparison", "model": "pro"}'

# Save to file
./scripts/research.sh '{"input": "market analysis for EVs", "model": "pro"}' ./ev-report.md

# Quick targeted research
./scripts/research.sh '{"input": "climate change impacts", "model": "mini"}'
```

## Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `input` | string | Required | Research topic or question |
| `model` | string | `"mini"` | Model: `mini`, `pro`, `auto` |

## Model Selection

**Rule of thumb**: "what does X do?" -> mini. "X vs Y vs Z" or "best way to..." -> pro.

| Model | Use Case | Speed |
|-------|----------|-------|
| `mini` | Single topic, targeted research | ~30s |
| `pro` | Comprehensive multi-angle analysis | ~60-120s |
| `auto` | API chooses based on complexity | Varies |

## Examples

### Quick Overview

```bash
./scripts/research.sh '{"input": "What is retrieval augmented generation?", "model": "mini"}'
```

### Technical Comparison

```bash
./scripts/research.sh '{"input": "LangGraph vs CrewAI for multi-agent systems", "model": "pro"}'
```

### Market Research

```bash
./scripts/research.sh '{"input": "Fintech startup landscape 2025", "model": "pro"}' fintech-report.md
```
