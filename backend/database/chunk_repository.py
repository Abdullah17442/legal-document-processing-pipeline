from database.connection import get_connection


# ============================================================
# SAVE CHUNKS
# ============================================================

def save_chunks(document_id, chunks):
    """
    Save chunks to LOCAL SQLite database.

    IMPORTANT:
    This repository is ONLY for SQLite.

    It must NOT use Supabase.

    document_id must belong to the local SQLite
    documents table.
    """

    if not chunks:
        return []

    connection = get_connection()

    try:

        records = []

        for chunk in chunks:

            records.append(
                (
                    document_id,

                    chunk["chunk_index"],

                    chunk["text"],

                    chunk.get("char_start"),

                    chunk.get("char_end")
                )
            )

        cursor = connection.cursor()

        cursor.executemany(
            """
            INSERT INTO chunks (
                document_id,
                chunk_number,
                chunk_text,
                char_start,
                char_end
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            records
        )

        connection.commit()

        # ----------------------------------------------------
        # Return inserted chunks
        # ----------------------------------------------------

        inserted_chunks = []

        first_id = (
            cursor.lastrowid - len(records) + 1
        )

        for i, chunk in enumerate(chunks):

            inserted_chunks.append(
                {
                    "id": first_id + i,
                    "document_id": document_id,
                    "chunk_number": chunk["chunk_index"],
                    "chunk_text": chunk["text"],
                    "char_start": chunk.get("char_start"),
                    "char_end": chunk.get("char_end")
                }
            )

        return inserted_chunks

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# GET CHUNKS
# ============================================================

def get_chunks(document_id):
    """
    Get all chunks belonging to a local SQLite document.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                document_id,
                chunk_number,
                chunk_text,
                char_start,
                char_end,
                created_at
            FROM chunks
            WHERE document_id = ?
            ORDER BY chunk_number ASC
            """,
            (document_id,)
        )

        rows = cursor.fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# GET CHUNKS WITH EMBEDDINGS
# ============================================================

def get_chunks_with_embeddings(document_id):
    """
    Get chunks including embeddings from local SQLite.

    This function assumes the local chunks table has
    an embedding column.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM chunks
            WHERE document_id = ?
            ORDER BY chunk_number ASC
            """,
            (document_id,)
        )

        rows = cursor.fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# DELETE CHUNKS
# ============================================================

def delete_chunks(document_id):
    """
    Delete all chunks belonging to a local SQLite document.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM chunks
            WHERE document_id = ?
            """,
            (document_id,)
        )

        deleted_count = cursor.rowcount

        connection.commit()

        return deleted_count > 0

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()