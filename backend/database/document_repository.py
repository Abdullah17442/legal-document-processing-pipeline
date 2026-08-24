import sqlite3

from database.connection import get_connection


# ============================================================
# SAVE DOCUMENT
# ============================================================

def save_document(
    filename,
    filepath,
    pages,
    characters,
    extracted_text,

    # Legal metadata
    case_number=None,
    case_title=None,
    judge_name=None,
    petitioner_name=None,
    respondent_name=None,
    court=None,
    judgment_date=None,
    case_type=None,

    # Important parts
    facts=None,
    issues=None,
    evidence=None,
    reasoning=None,
    decision=None
):
    """
    Save a document to the LOCAL SQLite database.

    This function must NOT write to Supabase.

    Returns:
        int: Local SQLite document ID
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO documents (
                filename,
                filepath,
                pages,
                characters,
                extracted_text,
                case_number,
                case_title,
                judge_name,
                petitioner_name,
                respondent_name,
                court,
                judgment_date,
                case_type,
                facts,
                issues,
                evidence,
                reasoning,
                decision
            )
            VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,
            (
                filename,
                filepath,
                pages,
                characters,
                extracted_text,

                case_number,
                case_title,
                judge_name,
                petitioner_name,
                respondent_name,
                court,
                judgment_date,
                case_type,

                facts,
                issues,
                evidence,
                reasoning,
                decision
            )
        )

        conn.commit()

        document_id = cursor.lastrowid

        return document_id

    finally:

        conn.close()


# ============================================================
# GET DOCUMENT
# ============================================================

def get_document(document_id):
    """
    Retrieve a document from LOCAL SQLite.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,)
        )

        row = cursor.fetchone()

        return row

    finally:

        conn.close()


# ============================================================
# GET ALL DOCUMENTS
# ============================================================

def get_all_documents():
    """
    Retrieve all documents from LOCAL SQLite.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM documents
            ORDER BY uploaded_at DESC
            """
        )

        rows = cursor.fetchall()

        return rows

    finally:

        conn.close()


# ============================================================
# DELETE DOCUMENT
# ============================================================

def delete_document(document_id):
    """
    Delete a document from LOCAL SQLite.

    Associated local chunks should be removed
    according to the database relationship/schema.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM documents
            WHERE id = ?
            """,
            (document_id,)
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()