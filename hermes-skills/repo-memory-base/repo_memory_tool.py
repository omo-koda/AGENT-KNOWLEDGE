'''repo_memory_tool.py
A Hermes tool that exposes the RepoMemoryEngine as a callable function.
It supports four sub‑commands via a single tool definition:

- `load`   – Scan a repo and build (or rebuild) the index.
- `query`  – Search the indexed docs and return top‑k snippets.
- `show`   – Return the full content of a document by numeric index.
- `status` – Return basic statistics about the loaded index.

The tool is registered under the `memory` toolset so you can enable it with
`hermes tools enable memory` (it is enabled by default in most configs).

Usage examples (via Hermes slash commands or the `execute_code` tool):
```
/repo_memory_load /Users/bino/AGENT-KNOWLEDGE
/repo_memory_query "birth stack" --top_k 5
/repo_memory_show 0
/repo_memory_status
```
''' 

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure the skill directory is on the Python path so we can import the engine.
skill_dir = Path(__file__).parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

# Import the engine implementation.
from indexer import RepoMemoryEngine

# Lazily create a single global engine instance – it will load the persisted index on import.
_engine = RepoMemoryEngine()

# Helper to turn a Python object into the JSON string that Hermes expects from a tool.
def _json_response(**kwargs) -> str:
    return json.dumps(kwargs, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Tool entry‑point – Hermes will call this function with the parsed arguments.
# The schema is defined below; Hermes passes the arguments as a dict.
# ---------------------------------------------------------------------------
def repo_memory_tool(params: Dict[str, Any]) -> str:
    """Main entry point for the `repo_memory` tool.

    Params must contain a top‑level key `action` with one of:
        * `load`   – optional `repo_path` (defaults to the skill's default repo).
        * `query`  – required `query` string, optional `top_k` int.
        * `show`   – required `index` int.
        * `status` – no extra fields.
    """
    action = params.get('action')
    if not action:
        return _json_response(error='Missing "action" field')

    if action == 'load':
        repo_path = params.get('repo_path') or _engine.repo_path_default
        max_files = int(params.get('max_files', 1000))
        try:
            num = _engine.load_repo(repo_path=repo_path, max_files=max_files)
            return _json_response(success=True, indexed=num, repo_path=repo_path)
        except Exception as e:
            return _json_response(success=False, error=str(e))

    if action == 'query':
        query = params.get('query')
        if not query:
            return _json_response(error='"query" field is required for action=query')
        top_k = int(params.get('top_k', 3))
        results = _engine.query_repo(query, top_k=top_k)
        return _json_response(success=True, query=query, results=results)

    if action == 'show':
        try:
            idx = int(params.get('index'))
        except Exception:
            return _json_response(error='"index" must be an integer for action=show')
        doc = _engine.show_doc(idx)
        if doc is None:
            return _json_response(error=f'No document at index {idx}')
        return _json_response(success=True, document=doc)

    if action == 'status':
        return _json_response(success=True, status=_engine.status())

    return _json_response(error=f'Unsupported action "{action}"')

# ---------------------------------------------------------------------------
# Register the tool with Hermes' tool registry.
# ---------------------------------------------------------------------------
try:
    # The `hermes_tools` package is available inside Hermes runtime.
    from hermes_tools import registry
except Exception:
    # Fallback for offline testing – create a dummy registry that does nothing.
    class _DummyRegistry:
        def register(self, **kwargs):
            pass
    registry = _DummyRegistry()

registry.register(
    name='repo_memory',
    toolset='memory',  # belongs to the generic memory/toolset group
    description='Repository‑based memory base: load, query, show, status for AGENT‑KNOWLEDGE repo.',
    schema={
        'name': 'repo_memory',
        'description': 'Interact with the AGENT‑KNOWLEDGE memory base.',
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'enum': ['load', 'query', 'show', 'status'],
                    'description': 'Operation to perform.'
                },
                'repo_path': {
                    'type': 'string',
                    'description': 'Path to the repo to index (optional, defaults to built‑in repo).'
                },
                'max_files': {
                    'type': 'integer',
                    'description': 'Maximum number of files to index when loading.',
                    'default': 1000
                },
                'query': {
                    'type': 'string',
                    'description': 'Search query string (required for action=query).'
                },
                'top_k': {
                    'type': 'integer',
                    'description': 'Number of top results to return (default 3).',
                    'default': 3
                },
                'index': {
                    'type': 'integer',
                    'description': 'Numeric document index to retrieve (required for action=show).'
                }
            },
            'required': ['action']
        }
    },
    handler=lambda args, **kw: repo_memory_tool(args),
    check_fn=lambda: True  # always available – no external deps.
)
