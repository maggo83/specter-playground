# RAG Code Scanner Setup

Local semantic search over the codebase using ChromaDB + sentence-transformers. Exposes search via MCP for Claude Code integration.

## Quick Start

```bash
# 1. Clone repos
git clone <specter-playground-url>
cd specter-playground
git clone https://github.com/cryptoadvance/specter-diy ../specter-diy

# 2. Create symlink for specter-diy source
ln -s /path/to/specter-diy/src specter-diy-src

# 3. Setup Python environment + install deps
make rag-setup

# 4. Index the codebase
make rag-index
```

## What Gets Indexed

| Namespace | Path | Description |
|-----------|------|-------------|
| `scenarios` | `scenarios/` | MockUI code for this repo |
| `specter-diy` | `specter-diy-src/` | Main specter-diy source |

Each repo gets its own ChromaDB collection for isolated search.

## CLI Usage

```bash
# Search all repos
cd .rag && .venv/bin/python search.py "wallet keystore"

# Search specific namespace
cd .rag && .venv/bin/python search.py "menu navigation" --namespace scenarios

# JSON output (for scripts)
cd .rag && .venv/bin/python search.py "keystore" --json

# More results
cd .rag && .venv/bin/python search.py "gui screen" --top-k 10
```

## MCP Server (Claude Code Integration)

Add to `~/.claude.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "code-rag": {
      "command": "/absolute/path/to/specter-playground/.rag/.venv/bin/python",
      "args": ["/absolute/path/to/specter-playground/.rag/mcp_server.py"]
    }
  }
}
```

Then in Claude Code use the `search_codebase` tool:
- `query`: search string (required)
- `namespace`: limit to `scenarios` or `specter-diy` (optional)
- `top_k`: number of results (default: 5)

## Re-indexing

Run after significant code changes:

```bash
make rag-index
```

This clears and rebuilds the index from scratch.

## File Structure

```
.rag/
├── config.py           # Repo paths, model config
├── chunker.py          # AST-based Python chunking
├── indexer.py          # ChromaDB indexing
├── search.py           # CLI search interface
├── mcp_server.py       # MCP server for Claude Code
├── requirements.txt
├── .venv/              # Python virtualenv (gitignored)
└── chroma_db/          # Vector database (gitignored)
```

## How It Works

1. **Chunking**: Python files are parsed with AST to extract functions, classes, and module-level code
2. **Embedding**: Each chunk is embedded using `all-mpnet-base-v2` sentence-transformer
3. **Storage**: Embeddings stored in ChromaDB with metadata (file, line numbers, function name)
4. **Search**: Query is embedded and compared against stored vectors using cosine similarity

## Adding More Repos

Edit `.rag/config.py`:

```python
REPOS = {
    "scenarios": {
        "path": BASE_DIR / "scenarios",
        "extensions": [".py"],
    },
    "specter-diy": {
        "path": BASE_DIR / "specter-diy-src",
        "extensions": [".py"],
    },
    # Add new repo here:
    "my-repo": {
        "path": BASE_DIR / "path/to/repo",
        "extensions": [".py"],
    },
}
```

Then re-run `make rag-index`.
