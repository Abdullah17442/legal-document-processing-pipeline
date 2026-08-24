import os
from typing import List

from google import genai
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# EMBEDDING CONFIGURATION
# ============================================================

EMBEDDING_MODEL = "gemini-embedding-001"

# Your actual tested embedding dimension
EMBEDDING_DIMENSION = 3072


# ============================================================
# GENERATE SINGLE EMBEDDING
# ============================================================

def generate_embedding(text: str) -> List[float]:
    """
    Generate a 3072-dimensional embedding for a single text.

    Args:
        text: Text to embed.

    Returns:
        List containing 3072 floating-point values.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot generate embedding for empty text."
        )

    try:

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config={
                "output_dimensionality": EMBEDDING_DIMENSION
            }
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini returned no embeddings."
            )

        embedding = response.embeddings[0].values

        if not embedding:
            raise RuntimeError(
                "Gemini returned an empty embedding."
            )

        # ----------------------------------------------------
        # Validate dimension
        # ----------------------------------------------------

        if len(embedding) != EMBEDDING_DIMENSION:

            raise RuntimeError(
                f"Unexpected embedding dimension: "
                f"{len(embedding)}. "
                f"Expected {EMBEDDING_DIMENSION}."
            )

        return list(embedding)

    except Exception as e:

        print("\n" + "=" * 80)
        print("EMBEDDING GENERATION ERROR")
        print("=" * 80)
        print(str(e))
        print("=" * 80 + "\n")

        raise


# ============================================================
# GENERATE MULTIPLE EMBEDDINGS
# ============================================================

def generate_embeddings(
    texts: List[str]
) -> List[List[float]]:
    """
    Generate embeddings for multiple text chunks.

    Args:
        texts: List of chunk texts.

    Returns:
        List of 3072-dimensional embedding vectors.
    """

    if not texts:
        return []

    embeddings = []

    total = len(texts)

    for index, text in enumerate(texts):

        print(
            f"Generating embedding "
            f"{index + 1}/{total}..."
        )

        embedding = generate_embedding(text)

        embeddings.append(embedding)

    return embeddings


# ============================================================
# VALIDATE EMBEDDING
# ============================================================

def validate_embedding(
    embedding: List[float]
) -> bool:
    """
    Validate that an embedding is compatible
    with the Supabase pgvector column.
    """

    if not isinstance(embedding, list):
        return False

    if len(embedding) != EMBEDDING_DIMENSION:
        return False

    if not all(
        isinstance(value, (int, float))
        for value in embedding
    ):
        return False

    return True