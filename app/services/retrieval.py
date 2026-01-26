from rank_bm25 import BM25Okapi
from app.services.embeddings import get_embedding
from app.services.vectorstore import collection


# Load all documents for BM25
def _load_bm25_index():
    """Load all documents and create BM25 index."""

    # Get all documents from ChromaDB
    all_data = collection.get(include=["documents", "metadatas"])

    documents = all_data["documents"]
    ids = all_data["ids"]
    metadatas = all_data["metadatas"]

    # Tokenize documents (split into words)
    tokenized = [doc.lower().split() for doc in documents]

    # Create BM25 index
    bm25 = BM25Okapi(tokenized)

    return bm25, documents, ids, metadatas


# Initialize BM25 index (runs once when module loads)
bm25_index, all_documents, all_ids, all_metadatas = _load_bm25_index()


def bm25_search(query: str, top_k: int = 5) -> list[dict]:
    """Search using BM25 keyword matching."""

    # Tokenize query
    query_tokens = query.lower().split()

    # Get BM25 scores for all documents
    scores = bm25_index.get_scores(query_tokens)

    # Get top_k indices (highest scores first)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    # Format results
    formatted = []
    for idx in top_indices:
        formatted.append({
            "id": all_ids[idx],
            "content": all_documents[idx],
            "metadata": all_metadatas[idx],
            "score": scores[idx]
        })

    return formatted


def vector_search(query: str, top_k: int = 5) -> list[dict]:
    """Search using vector similarity."""

    # Step 1: Convert query to embedding
    query_embedding = get_embedding(query)

    # Step 2: Search ChromaDB for similar vectors
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # Step 3: Format results
    formatted = []
    for i in range(len(results["ids"][0])):
        formatted.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return formatted


def _apply_filter(results: list[dict], filter: dict) -> list[dict]:
    """Filter results by metadata."""

    filtered = []
    for r in results:
        match = True
        for key, value in filter.items():
            # Check if metadata value contains the filter value (case-insensitive)
            metadata_value = r["metadata"].get(key, "")
            if value.lower() not in metadata_value.lower():
                match = False
                break
        if match:
            filtered.append(r)

    return filtered


def hybrid_search(query: str, top_k: int = 5, vector_weight: float = 0.5, filter: dict = None) -> list[dict]:
    """
    Combine vector search and BM25 search.

    Args:
        query: Search query
        top_k: Number of results to return
        vector_weight: Weight for vector search (0-1). BM25 weight = 1 - vector_weight
        filter: Metadata filter e.g. {"category": "learn"} or {"title": "Managing State"}
    """

    # Get more results from both to have enough to combine
    vector_results = vector_search(query, top_k=top_k * 2)
    bm25_results = bm25_search(query, top_k=top_k * 2)

    # Apply metadata filter if provided
    if filter:
        vector_results = _apply_filter(vector_results, filter)
        bm25_results = _apply_filter(bm25_results, filter)

    # Create a dict to store combined scores by id
    combined_scores = {}

    # Normalize vector distances (lower is better, convert to 0-1 score)
    if vector_results:
        max_dist = max(r["distance"] for r in vector_results)
        min_dist = min(r["distance"] for r in vector_results)
        dist_range = max_dist - min_dist if max_dist != min_dist else 1

        for r in vector_results:
            # Convert distance to score (1 = best, 0 = worst)
            normalized_score = 1 - (r["distance"] - min_dist) / dist_range
            combined_scores[r["id"]] = {
                "content": r["content"],
                "metadata": r["metadata"],
                "vector_score": normalized_score,
                "bm25_score": 0
            }

    # Normalize BM25 scores (higher is better, convert to 0-1)
    if bm25_results:
        max_score = max(r["score"] for r in bm25_results)
        min_score = min(r["score"] for r in bm25_results)
        score_range = max_score - min_score if max_score != min_score else 1

        for r in bm25_results:
            normalized_score = (r["score"] - min_score) / score_range

            if r["id"] in combined_scores:
                combined_scores[r["id"]]["bm25_score"] = normalized_score
            else:
                combined_scores[r["id"]] = {
                    "content": r["content"],
                    "metadata": r["metadata"],
                    "vector_score": 0,
                    "bm25_score": normalized_score
                }

    # Calculate final combined score
    bm25_weight = 1 - vector_weight
    results = []
    for id, data in combined_scores.items():
        final_score = (data["vector_score"] * vector_weight) + (data["bm25_score"] * bm25_weight)
        results.append({
            "id": id,
            "content": data["content"],
            "metadata": data["metadata"],
            "score": final_score,
            "vector_score": data["vector_score"],
            "bm25_score": data["bm25_score"]
        })

    # Sort by final score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]
