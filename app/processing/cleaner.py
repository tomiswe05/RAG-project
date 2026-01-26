import re
import unicodedata


def clean_markdown(text: str) -> str:
    """Clean markdown text for processing."""

    # Remove frontmatter (--- blocks at the start)
    text = re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.DOTALL)

    # Remove HTML/JSX tags like <Intro>, <Note>, </Intro>, etc.
    text = re.sub(r"<[^>]+>", "", text)

    # Remove JSX slug comments {/*...*/}
    text = re.sub(r"\{/\*.*?\*/\}", "", text)

    # Remove image markdown ![alt](url)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Remove link URLs but keep text [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Collapse multiple newlines into two (keep paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces into one
    text = re.sub(r" {2,}", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)

    return text
