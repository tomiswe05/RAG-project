import re


def chunk_by_markdown_headers(text: str) -> list[dict]:
    """Split text by markdown ## headers, keeping header with content."""

    # Pattern to match ## headers
    pattern = r"(^## .+$)"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    chunks = []
    current_header = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.startswith("## "):
            current_header = part
        else:
            chunks.append({
                "header": current_header,
                "content": part
            })

    return chunks


def recursive_chunk(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Recursively split text using multiple separators."""

    separators = ["\n\n", "\n", ". ", " "]

    def split_text(text: str, sep_index: int = 0) -> list[str]:
        # Base case: text is small enough
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        # Try current separator
        if sep_index >= len(separators):
            # Last resort: hard split by characters
            chunks = []
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunks.append(text[i:i + chunk_size])
            return chunks

        separator = separators[sep_index]
        parts = text.split(separator)

        chunks = []
        current_chunk = ""

        for part in parts:
            test_chunk = current_chunk + separator + part if current_chunk else part

            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If single part is too big, recurse with next separator
                if len(part) > chunk_size:
                    chunks.extend(split_text(part, sep_index + 1))
                else:
                    current_chunk = part

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    return split_text(text)


def chunk_document(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Main chunking function: markdown-aware + recursive."""

    # First, try splitting by markdown headers
    header_chunks = chunk_by_markdown_headers(text)

    final_chunks = []

    if header_chunks:
        for hc in header_chunks:
            header = hc["header"] or ""
            content = hc["content"]

            # If section is small enough, keep as one chunk
            if len(header) + len(content) <= chunk_size:
                chunk_text = f"{header}\n\n{content}" if header else content
                final_chunks.append(chunk_text.strip())
            else:
                # Recursively split large sections
                sub_chunks = recursive_chunk(content, chunk_size - len(header) - 10, chunk_overlap)
                for sub in sub_chunks:
                    # Prepend header to each sub-chunk for context
                    chunk_text = f"{header}\n\n{sub}" if header else sub
                    final_chunks.append(chunk_text.strip())
    else:
        # No headers found, use recursive chunking directly
        final_chunks = recursive_chunk(text, chunk_size, chunk_overlap)

    return final_chunks
