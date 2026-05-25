---
name: repo-memory-base
description: Memory base skill that loads the AGENT-KNOWLEDGE repository as a knowledge base and provides query access to build context.
version: 0.1.0
author: Hermes Agent
license: MIT
category: memory
---

Overview
- Scans a local git repo (e.g., AGENT-KNOWLEDGE) for markdown and text files and builds a searchable in-memory index.
- Exposes simple CLI/slash-command-like actions (load, query, show, status).
- Persists index state to disk so memory survives restarts.

Usage concepts
- load_repo(repo_path, max_files=1000): index content from the repo.
- query_repo(query, top_k=3): return top matches with path/title/snippet.
- show_doc(index): show full document by index.
- status(): report index size and health.

Persistence
- State stored at: ~/.hermes/skills/repo-memory-base/state.json (index persisted on each load). Re‑run `/repo_memory_load` whenever new markdown/text files are added to the repo.

References
- references/AGENT-KNOWLEDGE-overview.md – concise excerpt of the AGENT‑KNOWLEDGE repository overview.
- If you want to avoid persistence, clear state after loading.

Examples
- /repo_memory_load AGENT-KNOWLEDGE /Users/bino/AGENT-KNOWLEDGE
- /repo_memory_query "agent birth" --top-k 5
- /repo_memory_status

---
