import re
from pathlib import Path


def extract_metadata(content: str, source: str) -> dict:
    """Extract metadata from markdown content and file path."""

    path = Path(source)

    metadata = {
        "source": source,
        "filename": path.stem,
        "category": path.parent.name,
    }

    # Extract title from frontmatter
    frontmatter_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)

    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

    # Fallback: get title from first # heading if not in frontmatter
    if "title" not in metadata:
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        else:
            # Last fallback: use filename
            metadata["title"] = path.stem.replace("-", " ").title()

    return metadata


def process_document(content: str, source: str, cleaned_content: str) -> dict:
    """Combine cleaned content with metadata into a single document."""

    metadata = extract_metadata(content, source)

    return {
        "content": cleaned_content,
        **metadata
    }

def attach_metadata_to_chunks(chunks: list[str], metadata: dict) ->    list[dict]:
      """Attach metadata to each chunk."""

      result = []
      for i, chunk in enumerate(chunks):
          chunk_data = {
              "content": chunk,
              "chunk_index": i,
              **metadata
          }
          result.append(chunk_data)

      return result
