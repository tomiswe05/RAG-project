from app.processing.loader import load_markdown_files
from app.processing.cleaner import clean_markdown
from app.processing.chunker import chunk_document
from app.processing.metadata import extract_metadata, attach_metadata_to_chunks


def process_all_documents(directory: str, chunk_size: int = 500) -> list[dict]:
    """
    Run the full pipeline on all markdown files.

    Returns a list of all chunks with metadata, ready for embedding.
    """

    # Step 1: Load all documents
    docs = load_markdown_files(directory)
    print(f"Loaded {len(docs)} documents")

    all_chunks = []

    for doc in docs:
        # Step 2: Clean the content
        cleaned = clean_markdown(doc["content"])

        # Step 3: Extract metadata (from raw content)
        metadata = extract_metadata(doc["content"], doc["source"])

        # Step 4: Chunk the cleaned content
        chunks = chunk_document(cleaned, chunk_size=chunk_size)

        # Step 5: Attach metadata to each chunk
        chunks_with_metadata = attach_metadata_to_chunks(chunks, metadata)

        all_chunks.extend(chunks_with_metadata)

    print(f"Total chunks created: {len(all_chunks)}")

    return all_chunks


if __name__ == "__main__":
    # Run the pipeline
    chunks = process_all_documents("data/learn")

    # Show some examples
    print("\n=== Example chunks ===")
    for i in range(3):
        print(f"\n--- Chunk {i} ---")
        print(f"Title: {chunks[i]['title']}")
        print(f"Source: {chunks[i]['source']}")
        print(f"Content: {chunks[i]['content'][:150]}...")
