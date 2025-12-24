# src/profile_rag.py

from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions

from src.resume_source import get_resume_chunks


# Directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / ".chroma_profile"

# Globals for lazy init
_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def _get_client() -> chromadb.PersistentClient:
    """
    Return a global PersistentClient for Chroma.
    """
    global _client
    if _client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def _get_collection() -> chromadb.Collection:
    """
    Return (and lazily create) the Chroma collection for resume-based profile chunks.
    """
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name="profile_resume_chunks",
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )
    return _collection


# src/profile_rag.py

def build_or_refresh_profile_index() -> None:
    collection = _get_collection()

    print("Rebuilding profile index from resume chunks...")

    # Clear existing docs
    if collection.count() > 0:
        print("Deleting existing documents from collection...")
        collection.delete(where={})
        print("Existing documents deleted.")

    chunks: List[Dict] = get_resume_chunks()
    print(f"Got {len(chunks)} chunks from resume_source.")

    if not chunks:
        print("No chunks found; leaving collection empty.")
        return

    ids = [c.get("id", f"resume_chunk_{i}") for i, c in enumerate(chunks)]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {"section": c.get("section", "resume"), "order": c.get("order", i)}
        for i, c in enumerate(chunks)
    ]

    print("Calling collection.add(...) with", len(ids), "documents...")
    collection.add(ids=ids, documents=texts, metadatas=metadatas)
    print(f"Indexed {len(chunks)} resume-based profile chunks into Chroma.")




def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
) -> List[str]:
    """
    Given a query (e.g., job description or task description), return text
    of the top_k most relevant resume chunks.

    Assumes build_or_refresh_profile_index() has been called at least once
    after setting the current resume.
    """
    collection = _get_collection()

    if collection.count() == 0:
        # Best-effort: try to build index now (in case it hasn't been built yet)
        build_or_refresh_profile_index()

    if collection.count() == 0:
        # Still empty → no resume / no chunks
        return []

    result = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    docs = result.get("documents", [[]])[0]
    return docs
