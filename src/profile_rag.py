# src/profile_rag.py

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import chromadb
from chromadb.utils import embedding_functions


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CHROMA_DIR = Path(__file__).resolve().parents[1] / ".chroma_profile"


def load_profile_chunks() -> List[Tuple[str, str]]:
    """
    Read data/profile_chunks.md and return list of (id, text_chunk).
    Very simple parser: each chunk starts with '# ' and has a [ID]: line.
    """
    path = DATA_DIR / "profile_chunks.md"
    text = path.read_text(encoding="utf-8")

    chunks: List[Tuple[str, str]] = []
    current_id = None
    current_lines: List[str] = []

    for line in text.splitlines():
        if line.startswith("# "):
            # flush previous chunk
            if current_id and current_lines:
                chunks.append((current_id, "\n".join(current_lines).strip()))
            current_id = None
            current_lines = []
        elif line.startswith("[ID]:"):
            current_id = line.split(":", 1)[1].strip()
        else:
            if line.strip():
                current_lines.append(line)

    # last chunk
    if current_id and current_lines:
        chunks.append((current_id, "\n".join(current_lines).strip()))

    return chunks


def build_profile_vector_store() -> chromadb.Collection:
    """
    Build (or load) a persistent Chroma collection with profile chunks.
    """
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))  # local on disk [web:141][web:144]
    collection = client.get_or_create_collection(
        name="profile_chunks",
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),  # built-in small model
    )

    # If empty, populate
    if collection.count() == 0:
        chunks = load_profile_chunks()
        ids = [cid for cid, _ in chunks]
        texts = [txt for _, txt in chunks]
        collection.add(ids=ids, documents=texts)
        print(f"Indexed {len(chunks)} profile chunks into Chroma.")
    else:
        print(f"Loaded existing profile_chunks collection with {collection.count()} items.")

    return collection


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
) -> List[str]:
    """
    Given a query (e.g., job description or task description), return text
    of the top_k most relevant profile chunks.
    """
    collection = build_profile_vector_store()
    result = collection.query(query_texts=[query], n_results=top_k)  # vector search [web:137][web:138][web:141][web:144]

    docs = result.get("documents", [[]])[0]
    return docs
