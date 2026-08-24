import re
from typing import List, TypedDict


class Chunk(TypedDict):
    chunk_index: int
    text: str
    char_start: int
    char_end: int


def _split_long_paragraph(
    paragraph: str,
    chunk_size: int,
    overlap: int
) -> List[str]:
    """
    Split a paragraph that is larger than chunk_size
    without cutting words in half.
    """

    pieces = []
    start = 0

    while start < len(paragraph):
        target_end = min(start + chunk_size, len(paragraph))

        if target_end >= len(paragraph):
            piece = paragraph[start:].strip()

            if piece:
                pieces.append(piece)

            break

        # Look backwards for a word boundary
        split_position = paragraph.rfind(" ", start, target_end)

        if split_position <= start:
            split_position = target_end

        piece = paragraph[start:split_position].strip()

        if piece:
            pieces.append(piece)

        # Calculate next starting position using overlap
        next_start = max(split_position - overlap, start + 1)

        # Move backwards to a word boundary
        while (
            next_start > start
            and paragraph[next_start] != " "
        ):
            next_start -= 1

        start = next_start

    return pieces


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> List[Chunk]:
    """
    Split cleaned legal text into overlapping chunks.

    The chunker:
    - preserves paragraph boundaries where possible
    - avoids cutting words in half
    - supports overlap
    - keeps accurate character offsets
    """

    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Find paragraph ranges in the ORIGINAL text.
    paragraph_matches = list(
        re.finditer(
            r"\S(?:.*?\S)?(?=\n\s*\n|\Z)",
            text,
            re.DOTALL
        )
    )

    paragraphs = []

    for match in paragraph_matches:
        paragraph_text = match.group().strip()

        if paragraph_text:
            paragraphs.append(
                {
                    "text": paragraph_text,
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    chunks = []

    current_start = None
    current_end = None

    def add_chunk(start, end):
        chunk_text_value = text[start:end].strip()

        if not chunk_text_value:
            return

        # Adjust boundaries after stripping whitespace
        actual_start = start
        actual_end = end

        while (
            actual_start < actual_end
            and text[actual_start].isspace()
        ):
            actual_start += 1

        while (
            actual_end > actual_start
            and text[actual_end - 1].isspace()
        ):
            actual_end -= 1

        chunks.append(
            Chunk(
                chunk_index=len(chunks),
                text=text[actual_start:actual_end],
                char_start=actual_start,
                char_end=actual_end,
            )
        )

    for paragraph in paragraphs:

        paragraph_text = paragraph["text"]
        paragraph_start = paragraph["start"]
        paragraph_end = paragraph["end"]

        # ---------------------------------------------
        # Long paragraph
        # ---------------------------------------------

        if len(paragraph_text) > chunk_size:

            # Save current chunk first
            if current_start is not None:
                add_chunk(current_start, current_end)

                current_start = None
                current_end = None

            pieces = _split_long_paragraph(
                paragraph_text,
                chunk_size,
                overlap
            )

            search_position = paragraph_start

            for piece in pieces:

                piece_position = text.find(
                    piece,
                    search_position,
                    paragraph_end
                )

                if piece_position == -1:
                    continue

                piece_end = piece_position + len(piece)

                add_chunk(
                    piece_position,
                    piece_end
                )

                search_position = max(
                    piece_position + 1,
                    piece_end - overlap
                )

            continue

        # ---------------------------------------------
        # Start first chunk
        # ---------------------------------------------

        if current_start is None:

            current_start = paragraph_start
            current_end = paragraph_end

            continue

        # ---------------------------------------------
        # Can paragraph fit?
        # ---------------------------------------------

        proposed_length = (
            current_end - current_start
            + 2
            + len(paragraph_text)
        )

        if proposed_length <= chunk_size:

            current_end = paragraph_end

        else:

            # Save current chunk
            add_chunk(
                current_start,
                current_end
            )

            # -----------------------------------------
            # Create overlap from previous chunk
            # -----------------------------------------

            overlap_start = max(
                current_start,
                current_end - overlap
            )

            # Don't start in the middle of a word
            while (
                overlap_start > current_start
                and not text[overlap_start].isspace()
            ):
                overlap_start -= 1

            current_start = overlap_start
            current_end = paragraph_end

    # Add final chunk
    if current_start is not None:
        add_chunk(
            current_start,
            current_end
        )

    return chunks