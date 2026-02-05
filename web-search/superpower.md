---
name: web-search
description: Search the web using Tavily API. Use when the user needs current information, research, or facts from the internet.
---

# Web Search Skill

## Overview

This skill provides web search capabilities using the Tavily API. Use it to find current information, research topics, or verify facts.

## Prerequisites

The Tavily API key is already configured in the worker environment (`TAVILY_API_KEY`).

## How to Search

Use `run_python` with the following pattern:

```python
import os
import requests

api_key = os.environ.get("TAVILY_API_KEY")
if not api_key:
    raise ValueError("TAVILY_API_KEY not configured")

response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": api_key,
        "query": "your search query here",
        "search_depth": "basic",  # or "advanced" for deeper search
        "max_results": 5
    }
)

results = response.json()
for result in results.get("results", []):
    print(f"## {result['title']}")
    print(f"URL: {result['url']}")
    print(f"{result['content']}\n")
```

## Parameters

- `query`: The search query (required)
- `search_depth`: "basic" (fast) or "advanced" (thorough)
- `max_results`: Number of results (1-10, default 5)
- `include_domains`: List of domains to include
- `exclude_domains`: List of domains to exclude

## Examples

### Example 1: Basic search

```python
import os
import requests

response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": os.environ["TAVILY_API_KEY"],
        "query": "Python 3.12 new features",
        "max_results": 3
    }
)
for r in response.json()["results"]:
    print(f"- {r['title']}: {r['url']}")
```

### Example 2: Domain-filtered search

```python
import os
import requests

response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": os.environ["TAVILY_API_KEY"],
        "query": "machine learning best practices",
        "include_domains": ["arxiv.org", "github.com"],
        "max_results": 5
    }
)
for r in response.json()["results"]:
    print(f"- {r['title']}")
    print(f"  {r['content'][:200]}...")
```
