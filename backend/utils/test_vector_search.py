"""
Test Supabase pgvector semantic search.

Run from backend directory:

    python -m utils.test_vector_search
"""

from utils.embedding_generator import generate_embedding
from utils.supabase_repository import search_similar_chunks


# ============================================================
# TEST CONFIGURATION
# ============================================================

TEST_QUERY = (
    "What was the court's decision regarding the eviction "
    "of the tenants?"
)

MATCH_COUNT = 5


# ============================================================
# TEST VECTOR SEARCH
# ============================================================

def test_vector_search():

    print("\n" + "=" * 80)
    print("SUPABASE VECTOR SEARCH TEST")
    print("=" * 80)

    # --------------------------------------------------------
    # STEP 1: Generate query embedding
    # --------------------------------------------------------

    print("\n[1] Generating query embedding...")

    query_embedding = generate_embedding(
        TEST_QUERY
    )

    print(
        f"Query embedding dimension: "
        f"{len(query_embedding)}"
    )

    assert len(query_embedding) == 3072

    print("Embedding generation passed.")

    # --------------------------------------------------------
    # STEP 2: Perform vector search
    # --------------------------------------------------------

    print("\n[2] Searching Supabase pgvector...")

    results = search_similar_chunks(
        query_embedding=query_embedding,
        match_count=MATCH_COUNT
    )

    print(
        f"Results returned: {len(results)}"
    )

    assert results is not None

    # --------------------------------------------------------
    # STEP 3: Verify results
    # --------------------------------------------------------

    if not results:

        print("\nNo results returned.")

        print(
            "\nMake sure your Supabase chunks table "
            "contains embedded chunks."
        )

        return

    print("\nVector search returned results.")

    # --------------------------------------------------------
    # STEP 4: Display results
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("SEARCH RESULTS")
    print("-" * 80)

    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nResult #{index}"
        )

        print(
            f"Chunk ID: "
            f"{result.get('id')}"
        )

        print(
            f"Document ID: "
            f"{result.get('document_id')}"
        )

        print(
            f"Chunk Number: "
            f"{result.get('chunk_number')}"
        )

        # Different RPC implementations may
        # return similarity under different names.

        similarity = result.get(
            "similarity"
        )

        if similarity is not None:

            print(
                f"Similarity: "
                f"{similarity}"
            )

        chunk_text = result.get(
            "chunk_text",
            ""
        )

        print(
            f"Text Preview: "
            f"{chunk_text[:500]}"
        )

    # --------------------------------------------------------
    # STEP 5: Basic validation
    # --------------------------------------------------------

    first_result = results[0]

    assert "id" in first_result
    assert "document_id" in first_result
    assert "chunk_text" in first_result

    print("\n" + "-" * 80)
    print("VECTOR SEARCH VALIDATION PASSED")
    print("-" * 80)

    print("\nQuery:")
    print(TEST_QUERY)

    print(
        f"\nTop result chunk ID: "
        f"{first_result['id']}"
    )

    print(
        f"Top result document ID: "
        f"{first_result['document_id']}"
    )

    print("\n" + "=" * 80)
    print("VECTOR SEARCH TEST PASSED")
    print("=" * 80)


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":

    test_vector_search()