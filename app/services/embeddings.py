import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text: str) -> list[float]:
    """Get embedding for a single text."""

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts at once (more efficient)."""

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    return [item.embedding for item in response.data]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add embeddings to each chunk."""

    # Extract content from each chunk
    texts = [chunk["content"] for chunk in chunks]

    # Get embeddings in batches (OpenAI has a limit per request)
    print(f"Embedding {len(texts)} chunks...")

    batch_size = 100
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = get_embeddings_batch(batch)
        all_embeddings.extend(embeddings)
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    # Add embedding to each chunk
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = all_embeddings[i]

    print("Embedding complete!")
    return chunks
