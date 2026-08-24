from database.supabase_client import supabase
from utils.embedding_generator import generate_embedding


print("=" * 60)
print("SUPABASE EMBEDDING TEST")
print("=" * 60)


# ============================================================
# TEST TEXT
# ============================================================

text = """
The court considered whether the landlord had established
bonafide personal need for the premises.
"""


# ============================================================
# GENERATE EMBEDDING
# ============================================================

embedding = generate_embedding(text)


print("Embedding generated.")
print("Dimensions:", len(embedding))


# ============================================================
# VALIDATE DIMENSION
# ============================================================

if len(embedding) != 3072:

    raise ValueError(
        f"Expected 3072 dimensions, "
        f"got {len(embedding)}"
    )


print("Embedding dimension is correct: 3072")


# ============================================================
# INSERT CHUNK
# ============================================================

chunk = {

    "document_id": 1,

    "chunk_number": 0,

    "chunk_text": text,

    "char_start": 0,

    "char_end": len(text),

    "embedding": embedding
}


try:

    response = (
        supabase
        .table("chunks")
        .insert(chunk)
        .execute()
    )

    print("\nChunk + embedding inserted successfully.")

    print(response.data)

except Exception as e:

    print("\nEmbedding insertion FAILED.")

    print(str(e))