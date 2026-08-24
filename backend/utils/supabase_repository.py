import os
import json

from dotenv import load_dotenv
from supabase import create_client, Client


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL environment variable is not set."
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY environment variable is not set."
    )


# ============================================================
# CONSTANTS
# ============================================================

EMBEDDING_DIMENSION = 3072


# ============================================================
# SUPABASE CLIENT
# ============================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# NORMALIZE EMBEDDING
# ============================================================

def normalize_embedding(embedding):

    if embedding is None:
        return None

    if isinstance(embedding, (list, tuple)):

        return [
            float(value)
            for value in embedding
        ]

    if isinstance(embedding, str):

        embedding = embedding.strip()

        if not embedding:
            return []

        # Try JSON format
        try:

            parsed = json.loads(
                embedding
            )

            if isinstance(parsed, list):

                return [
                    float(value)
                    for value in parsed
                ]

        except (json.JSONDecodeError, TypeError):
            pass

        # Try PostgreSQL vector format
        cleaned = (
            embedding
            .strip()
            .lstrip("[")
            .rstrip("]")
        )

        if not cleaned:
            return []

        return [
            float(value.strip())
            for value in cleaned.split(",")
        ]

    raise TypeError(
        f"Unsupported embedding type: "
        f"{type(embedding)}"
    )


# ============================================================
# VALIDATE EMBEDDING
# ============================================================

def validate_embedding(embedding):

    if embedding is None:

        raise ValueError(
            "Embedding cannot be None."
        )

    if not isinstance(
        embedding,
        (list, tuple)
    ):

        raise TypeError(
            "Embedding must be a list or tuple."
        )

    if len(embedding) != EMBEDDING_DIMENSION:

        raise ValueError(
            f"Expected "
            f"{EMBEDDING_DIMENSION}-dimensional "
            f"embedding, received {len(embedding)}."
        )

    return True


# ============================================================
# VALIDATE FILE HASH
# ============================================================

def validate_file_hash(file_hash):

    if file_hash is None:

        raise ValueError(
            "file_hash cannot be None."
        )

    if not isinstance(
        file_hash,
        str
    ):

        raise TypeError(
            "file_hash must be a string."
        )

    file_hash = file_hash.strip().lower()

    if len(file_hash) != 64:

        raise ValueError(
            "Invalid SHA-256 hash. "
            "Expected exactly 64 hexadecimal characters."
        )

    try:

        int(
            file_hash,
            16
        )

    except ValueError:

        raise ValueError(
            "Invalid SHA-256 hash. "
            "Hash must contain only hexadecimal characters."
        )

    return file_hash


# ============================================================
# GET DOCUMENT BY HASH
# ============================================================

def get_supabase_document_by_hash(file_hash):

    file_hash = validate_file_hash(
        file_hash
    )

    response = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "file_hash",
            file_hash
        )
        .limit(1)
        .execute()
    )

    if not response.data:

        return None

    return response.data[0]


# ============================================================
# SAVE DOCUMENT
# ============================================================

def save_supabase_document(
    filename,
    filepath,
    pages,
    characters,
    extracted_text,
    file_hash,
    case_number=None,
    case_title=None,
    judge_name=None,
    petitioner_name=None,
    respondent_name=None,
    court=None,
    judgment_date=None,
    case_type=None,
    facts=None,
    issues=None,
    evidence=None,
    reasoning=None,
    decision=None
):

    file_hash = validate_file_hash(
        file_hash
    )


    # ========================================================
    # DUPLICATE CHECK
    # ========================================================

    existing_document = (
        get_supabase_document_by_hash(
            file_hash
        )
    )

    if existing_document:

        raise ValueError(
            "Duplicate document detected. "
            f"Document ID: "
            f"{existing_document['id']}"
        )


    # ========================================================
    # DOCUMENT DATA
    # ========================================================

    data = {

        "filename": filename,

        "filepath": filepath,

        "pages": pages,

        "characters": characters,

        "extracted_text": extracted_text,

        "file_hash": file_hash,

        "case_number": case_number,

        "case_title": case_title,

        "judge_name": judge_name,

        "petitioner_name": petitioner_name,

        "respondent_name": respondent_name,

        "court": court,

        "judgment_date": judgment_date,

        "case_type": case_type,

        "facts": facts,

        "issues": issues,

        "evidence": evidence,

        "reasoning": reasoning,

        "decision": decision
    }


    # ========================================================
    # INSERT
    # ========================================================

    response = (
        supabase
        .table("documents")
        .insert(data)
        .execute()
    )


    if not response.data:

        raise RuntimeError(
            "Supabase did not return "
            "the inserted document."
        )


    inserted_document = response.data[0]


    # ========================================================
    # VERIFY
    # ========================================================

    inserted_hash = (
        inserted_document.get(
            "file_hash"
        )
    )

    if inserted_hash != file_hash:

        raise RuntimeError(
            "Supabase returned an unexpected "
            "file_hash."
        )


    print("\n" + "=" * 80)
    print("SUPABASE DOCUMENT INSERTED")
    print("=" * 80)

    print(
        f"Document ID: "
        f"{inserted_document['id']}"
    )

    print(
        f"Filename: "
        f"{inserted_document['filename']}"
    )

    print(
        f"File hash: "
        f"{inserted_hash}"
    )

    print("=" * 80 + "\n")


    return inserted_document["id"]


# ============================================================
# VERIFY SUPABASE DOCUMENT EXISTS
# ============================================================

def verify_supabase_document_exists(
    document_id
):

    response = (
        supabase
        .table("documents")
        .select("id")
        .eq(
            "id",
            document_id
        )
        .maybe_single()
        .execute()
    )

    return response.data is not None


# ============================================================
# SAVE SINGLE CHUNK
# ============================================================

def save_supabase_chunk(
    document_id,
    chunk_number,
    chunk_text,
    char_start=None,
    char_end=None,
    embedding=None
):

    # ========================================================
    # IMPORTANT:
    # Verify parent document first.
    # ========================================================

    if not verify_supabase_document_exists(
        document_id
    ):

        raise ValueError(
            f"Supabase document ID "
            f"{document_id} does not exist."
        )


    validate_embedding(
        embedding
    )


    data = {

        "document_id": document_id,

        "chunk_number": chunk_number,

        "chunk_text": chunk_text,

        "char_start": char_start,

        "char_end": char_end,

        "embedding": embedding
    }


    response = (
        supabase
        .table("chunks")
        .insert(data)
        .execute()
    )


    if not response.data:

        raise RuntimeError(
            "Supabase did not return "
            "the inserted chunk."
        )


    return response.data[0]["id"]


# ============================================================
# SAVE MULTIPLE CHUNKS
# ============================================================

def save_supabase_chunks(
    document_id,
    chunks,
    embeddings
):

    # ========================================================
    # VERIFY PARENT DOCUMENT
    # ========================================================

    if not verify_supabase_document_exists(
        document_id
    ):

        raise ValueError(
            f"Cannot save chunks. "
            f"Supabase document ID "
            f"{document_id} does not exist."
        )


    # ========================================================
    # VALIDATE COUNTS
    # ========================================================

    if len(chunks) != len(embeddings):

        raise ValueError(
            "Number of chunks and embeddings "
            "must match."
        )


    if not chunks:

        return []


    # ========================================================
    # PREPARE ROWS
    # ========================================================

    rows = []


    for chunk, embedding in zip(
        chunks,
        embeddings
    ):

        validate_embedding(
            embedding
        )


        rows.append({

            # IMPORTANT:
            # This MUST be the Supabase document ID.
            "document_id": document_id,

            "chunk_number": chunk[
                "chunk_index"
            ],

            "chunk_text": chunk[
                "text"
            ],

            "char_start": chunk.get(
                "char_start"
            ),

            "char_end": chunk.get(
                "char_end"
            ),

            "embedding": embedding
        })


    # ========================================================
    # INSERT
    # ========================================================

    response = (
        supabase
        .table("chunks")
        .insert(rows)
        .execute()
    )


    if not response.data:

        raise RuntimeError(
            "Supabase did not return "
            "the inserted chunks."
        )


    print(
        f"Successfully inserted "
        f"{len(response.data)} chunks "
        f"for Supabase document "
        f"{document_id}"
    )


    return [
        row["id"]
        for row in response.data
    ]


# ============================================================
# GET DOCUMENT
# ============================================================

def get_supabase_document(
    document_id
):

    response = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "id",
            document_id
        )
        .maybe_single()
        .execute()
    )

    return response.data


# ============================================================
# GET ALL DOCUMENTS
# ============================================================

def get_all_supabase_documents():

    response = (
        supabase
        .table("documents")
        .select("*")
        .order(
            "uploaded_at",
            desc=True
        )
        .execute()
    )

    return response.data


# ============================================================
# GET DOCUMENT CHUNKS
# ============================================================

def get_supabase_chunks(
    document_id
):

    response = (
        supabase
        .table("chunks")
        .select("*")
        .eq(
            "document_id",
            document_id
        )
        .order(
            "chunk_number",
            desc=False
        )
        .execute()
    )


    chunks = response.data


    for chunk in chunks:

        if (
            "embedding" in chunk
            and chunk["embedding"] is not None
        ):

            chunk["embedding"] = (
                normalize_embedding(
                    chunk["embedding"]
                )
            )


    return chunks


# ============================================================
# DELETE SUPABASE CHUNKS
# ============================================================

def delete_supabase_chunks(
    document_id
):

    response = (
        supabase
        .table("chunks")
        .delete()
        .eq(
            "document_id",
            document_id
        )
        .execute()
    )

    return response.data


# ============================================================
# DELETE SUPABASE DOCUMENT
# ============================================================

def delete_supabase_document(
    document_id
):

    response = (
        supabase
        .table("documents")
        .delete()
        .eq(
            "id",
            document_id
        )
        .execute()
    )

    return bool(
        response.data
    )


# ============================================================
# VECTOR SEARCH
# ============================================================

def search_similar_chunks(
    query_embedding,
    match_count=5
):

    validate_embedding(
        query_embedding
    )


    if match_count <= 0:

        raise ValueError(
            "match_count must be greater than 0."
        )


    response = supabase.rpc(
        "match_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": match_count
        }
    ).execute()


    return response.data