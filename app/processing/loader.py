from pathlib import Path


def load_markdown_files(directory: str) -> list[dict]:
    """Load all markdown files from a directory."""
    documents = []
    dir_path = Path(directory)

    for file_path in dir_path.rglob("*.md"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            documents.append({
                "content": content,
                "source": str(file_path)
            })

    return documents
