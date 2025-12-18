#!/usr/bin/env python3
"""CLI search interface for RAG."""
import argparse
import json

import chromadb
from sentence_transformers import SentenceTransformer

from config import REPOS, MODEL, DB_PATH, DEFAULT_TOP_K
from indexer import get_collection_name


def search(
    query: str,
    namespace: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """Search the codebase."""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    model = SentenceTransformer(MODEL)

    query_embedding = model.encode([query])[0].tolist()

    results = []
    namespaces = [namespace] if namespace else list(REPOS.keys())

    for ns in namespaces:
        collection_name = get_collection_name(ns)
        try:
            collection = client.get_collection(collection_name)
        except ValueError:
            continue  # Collection doesn't exist

        response = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if response["ids"] and response["ids"][0]:
            for i, doc_id in enumerate(response["ids"][0]):
                metadata = response["metadatas"][0][i]
                distance = response["distances"][0][i]
                document = response["documents"][0][i]

                # Convert distance to similarity score (cosine)
                score = 1 - distance

                results.append({
                    "id": doc_id,
                    "file": metadata["file"],
                    "name": metadata["name"],
                    "type": metadata["type"],
                    "repo": metadata["repo"],
                    "start_line": metadata["start_line"],
                    "end_line": metadata["end_line"],
                    "score": round(score, 4),
                    "snippet": document[:200] + "..." if len(document) > 200 else document,
                })

    # Sort by score and limit
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def main():
    parser = argparse.ArgumentParser(description="Search codebase")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--namespace", "-n", help="Limit to namespace (scenarios, specter-diy)")
    parser.add_argument("--top-k", "-k", type=int, default=DEFAULT_TOP_K, help="Number of results")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = search(args.query, args.namespace, args.top_k)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(f"\n[{r['score']:.2f}] {r['file']}:{r['start_line']}-{r['end_line']}")
            print(f"  {r['type']}: {r['name']}")
            print(f"  {r['snippet'][:100]}...")


if __name__ == "__main__":
    main()
