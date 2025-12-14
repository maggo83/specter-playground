#!/usr/bin/env python3
"""Index codebase into ChromaDB."""
import argparse
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from config import REPOS, MODEL, DB_PATH
from chunker import chunk_repo


def get_collection_name(repo_name: str) -> str:
    """Generate collection name for a repo."""
    return f"code_{repo_name.replace('-', '_')}"


def index_repo(
    client: chromadb.PersistentClient,
    model: SentenceTransformer,
    repo_name: str,
    repo_config: dict,
    rebuild: bool = False,
) -> int:
    """Index a single repository."""
    collection_name = get_collection_name(repo_name)
    repo_path = Path(repo_config["path"])

    if not repo_path.exists():
        print(f"Warning: Repo path does not exist: {repo_path}")
        return 0

    # Get or create collection
    if rebuild:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except (ValueError, chromadb.errors.NotFoundError):
            pass  # Collection didn't exist

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"repo": repo_name, "hnsw:space": "cosine"},
    )

    # Chunk and index
    chunks = list(chunk_repo(repo_path, repo_name, repo_config["extensions"]))
    if not chunks:
        print(f"No chunks found in {repo_name}")
        return 0

    print(f"Indexing {len(chunks)} chunks from {repo_name}...")

    # Batch processing
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        documents = [c["content"] for c in batch]
        embeddings = model.encode(documents, show_progress_bar=False).tolist()

        ids = [f"{c['file']}:{c['start_line']}" for c in batch]
        metadatas = [
            {
                "name": c["name"],
                "type": c["type"],
                "file": c["file"],
                "repo": c["repo"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "docstring": c["docstring"][:500] if c["docstring"] else "",
            }
            for c in batch
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    print(f"Indexed {len(chunks)} chunks into {collection_name}")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Index codebase into ChromaDB")
    parser.add_argument("--rebuild", action="store_true", help="Clear and rebuild index")
    parser.add_argument("--repo", type=str, help="Index only this repo")
    args = parser.parse_args()

    # Initialize
    DB_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_PATH))
    print(f"Loading model: {MODEL}")
    model = SentenceTransformer(MODEL)

    total = 0
    repos_to_index = {args.repo: REPOS[args.repo]} if args.repo else REPOS

    for repo_name, repo_config in repos_to_index.items():
        count = index_repo(client, model, repo_name, repo_config, args.rebuild)
        total += count

    print(f"\nTotal: {total} chunks indexed")


if __name__ == "__main__":
    main()
