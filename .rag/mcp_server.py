#!/usr/bin/env python3
"""MCP server for code RAG search."""
import json
import sys
from pathlib import Path

# Add .rag to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from search import search
from config import REPOS, DEFAULT_TOP_K


server = Server("code-rag")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="search_codebase",
            description="Search the indexed codebase using semantic similarity. Returns matching code snippets with file paths and line numbers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (natural language or code snippet)",
                    },
                    "namespace": {
                        "type": "string",
                        "description": f"Limit search to namespace: {', '.join(REPOS.keys())}",
                        "enum": list(REPOS.keys()),
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": DEFAULT_TOP_K,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name != "search_codebase":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    query = arguments.get("query", "")
    namespace = arguments.get("namespace")
    top_k = arguments.get("top_k", DEFAULT_TOP_K)

    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    results = search(query, namespace, top_k)

    if not results:
        return [TextContent(type="text", text="No results found")]

    # Format results for Claude
    output = []
    for r in results:
        output.append({
            "file": r["file"],
            "name": r["name"],
            "type": r["type"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "score": r["score"],
            "snippet": r["snippet"],
        })

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
