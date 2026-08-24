import re


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text.
    Operations:
    - Normalize line endings
    - Remove invisible/control characters
    - Replace tabs and non-breaking spaces
    - Normalize quotes, apostrophes, dashes
    - Rejoin hyphenated words split across lines
    - Rejoin mid-paragraph line wraps (single \\n) while preserving
      paragraph breaks (\\n\\n+)
    - Collapse excess whitespace and blank lines
    - Strip leading/trailing whitespace
    """
    if not text:
        return ""

    # Normalize line endings first — everything downstream assumes \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove zero-width/invisible characters and form-feed page breaks
    text = re.sub(r'[\u200B-\u200D\uFEFF\u2060\x0c]', '', text)

    # Tabs and non-breaking spaces -> regular space
    text = text.replace("\t", " ").replace("\u00A0", " ")

    # Normalize quotes and apostrophes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")

    # Normalize dashes
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # Rejoin words split across a line break with a hyphen, e.g.
    # "the accu-\nsed" -> "the accused"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Rejoin mid-paragraph wraps: a single newline NOT followed by another
    # newline is a layout artifact, not a real paragraph break — turn it
    # into a space. Paragraph breaks (2+ newlines) are preserved as-is.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Collapse excessive blank lines down to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing spaces before newlines
    text = re.sub(r"[ \t]+\n", "\n", text)

    return text.strip()