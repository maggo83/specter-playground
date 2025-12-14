"""AST-based Python code chunker."""
import ast
from pathlib import Path
from typing import Generator


def get_source_segment(source: str, node: ast.AST) -> str:
    """Extract source code for an AST node."""
    lines = source.splitlines(keepends=True)
    start = node.lineno - 1
    end = node.end_lineno
    segment_lines = lines[start:end]
    if segment_lines:
        # Handle first line col_offset
        segment_lines[0] = segment_lines[0][node.col_offset:]
    return "".join(segment_lines)


def chunk_python_file(file_path: Path, repo_name: str) -> Generator[dict, None, None]:
    """Parse Python file and yield chunks for functions/classes."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IOError) as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        print(f"Warning: Syntax error in {file_path}: {e}")
        return

    # Track what we've processed to handle nested classes/functions
    processed_lines = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Skip if this is a nested definition we already covered
            if node.lineno in processed_lines:
                continue

            content = get_source_segment(source, node)
            docstring = ast.get_docstring(node)

            yield {
                "content": content,
                "name": node.name,
                "type": node.__class__.__name__,
                "file": str(file_path),
                "repo": repo_name,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "docstring": docstring or "",
            }

            # Mark lines as processed
            for line in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                processed_lines.add(line)

    # Handle module-level code (imports, constants, top-level statements)
    module_lines = []
    for i, line in enumerate(source.splitlines(), 1):
        if i not in processed_lines and line.strip() and not line.strip().startswith("#"):
            module_lines.append((i, line))

    if module_lines:
        # Group contiguous module-level code
        content = "\n".join(line for _, line in module_lines)
        if content.strip():
            yield {
                "content": content,
                "name": "__module__",
                "type": "Module",
                "file": str(file_path),
                "repo": repo_name,
                "start_line": module_lines[0][0] if module_lines else 1,
                "end_line": module_lines[-1][0] if module_lines else 1,
                "docstring": ast.get_docstring(tree) or "",
            }


def chunk_repo(repo_path: Path, repo_name: str, extensions: list[str]) -> Generator[dict, None, None]:
    """Chunk all files in a repository."""
    for ext in extensions:
        for file_path in repo_path.rglob(f"*{ext}"):
            # Skip __pycache__ and hidden dirs
            if "__pycache__" in str(file_path) or "/." in str(file_path):
                continue
            yield from chunk_python_file(file_path, repo_name)
