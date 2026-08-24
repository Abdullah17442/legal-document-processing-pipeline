import sqlite3
import os


DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "legal_pipeline.db"
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    # ==================================================
    # DOCUMENTS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,

            pages INTEGER,
            characters INTEGER,

            extracted_text TEXT,

            -- Legal metadata
            case_number TEXT,
            case_title TEXT,
            judge_name TEXT,
            petitioner_name TEXT,
            respondent_name TEXT,
            court TEXT,
            judgment_date TEXT,
            case_type TEXT,

            -- Important parts of judgment
            facts TEXT,
            issues TEXT,
            evidence TEXT,
            reasoning TEXT,
            decision TEXT,

            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==================================================
    # MIGRATE EXISTING DATABASE
    # ==================================================

    cursor.execute("PRAGMA table_info(documents)")

    existing_columns = {
        column["name"]
        for column in cursor.fetchall()
    }

    metadata_columns = {

        "case_number": "TEXT",
        "case_title": "TEXT",
        "judge_name": "TEXT",
        "petitioner_name": "TEXT",
        "respondent_name": "TEXT",
        "court": "TEXT",
        "judgment_date": "TEXT",
        "case_type": "TEXT",

        "facts": "TEXT",
        "issues": "TEXT",
        "evidence": "TEXT",
        "reasoning": "TEXT",
        "decision": "TEXT",
    }

    for column_name, column_type in metadata_columns.items():

        if column_name not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE documents
                ADD COLUMN {column_name} {column_type}
                """
            )

    # ==================================================
    # CHUNKS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            document_id INTEGER NOT NULL,

            chunk_number INTEGER NOT NULL,

            chunk_text TEXT NOT NULL,

            char_start INTEGER,
            char_end INTEGER,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (document_id)
            REFERENCES documents(id)
            ON DELETE CASCADE
        )
    """)

    # ==================================================
    # MIGRATE CHUNKS TABLE
    # ==================================================

    cursor.execute("PRAGMA table_info(chunks)")

    existing_chunk_columns = {
        column["name"]
        for column in cursor.fetchall()
    }

    chunk_columns = {
        "char_start": "INTEGER",
        "char_end": "INTEGER",
    }

    for column_name, column_type in chunk_columns.items():

        if column_name not in existing_chunk_columns:

            cursor.execute(
                f"""
                ALTER TABLE chunks
                ADD COLUMN {column_name} {column_type}
                """
            )

    # ==================================================
    # SAVE CHANGES
    # ==================================================

    conn.commit()
    conn.close()