from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

import os
import shutil


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# UTILS
# ============================================================

from utils.pdf_extractor import extract_text_from_pdf
from utils.text_cleaner import clean_text
from utils.chunker import chunk_text

from utils.embedding_generator import (
    generate_embedding,
    generate_embeddings
)

from utils.llm_metadata_extractor import (
    extract_llm_metadata
)

from utils.file_hash import calculate_file_hash


# ============================================================
# LOCAL DATABASE
# ============================================================

from database.connection import initialize_database

from database.document_repository import (
    save_document,
    get_document,
    get_all_documents,
    delete_document,
)


# ============================================================
# SUPABASE
# ============================================================

from utils.supabase_repository import (
    save_supabase_document,
    save_supabase_chunks,
    get_supabase_document,
    get_all_supabase_documents,
    get_supabase_chunks,
    delete_supabase_document,
    delete_supabase_chunks,
    get_supabase_document_by_hash,
    search_similar_chunks,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Legal Assistant Backend"
)


# ============================================================
# INITIALIZE LOCAL DATABASE
# ============================================================

initialize_database()


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# UPLOAD FOLDER
# ============================================================

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "success": True,
        "message": "Legal Assistant Backend Running"
    }


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    # ========================================================
    # STEP 0: VALIDATE FILE
    # ========================================================

    if not file.filename:

        return {
            "success": False,
            "message": "No filename provided."
        }


    if file.content_type != "application/pdf":

        return {
            "success": False,
            "message": "Only PDF files are allowed."
        }


    # ========================================================
    # STEP 1: CALCULATE SHA-256 FILE HASH
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 1: CALCULATING FILE HASH")
    print("=" * 80)

    try:

        file.file.seek(0)

        file_hash = calculate_file_hash(
            file.file
        )

    except Exception as e:

        print("FILE HASH ERROR")
        print(str(e))

        return {

            "success": False,

            "message": "Failed to calculate file hash.",

            "error": str(e)
        }


    print(
        f"SHA-256: {file_hash}"
    )

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 2: CHECK DUPLICATE IN SUPABASE
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 2: CHECKING FOR DUPLICATE DOCUMENT")
    print("=" * 80)

    try:

        existing_document = (
            get_supabase_document_by_hash(
                file_hash
            )
        )

    except Exception as e:

        print("DUPLICATE CHECK FAILED")
        print(str(e))

        return {

            "success": False,

            "message": (
                "Could not check whether "
                "the document already exists."
            ),

            "error": str(e)
        }


    # ========================================================
    # DUPLICATE FOUND
    # ========================================================

    if existing_document:

        print(
            "DUPLICATE DOCUMENT DETECTED"
        )

        print(
            f"Existing document ID: "
            f"{existing_document['id']}"
        )

        print(
            f"Existing filename: "
            f"{existing_document['filename']}"
        )

        print("=" * 80 + "\n")

        return {

            "success": False,

            "duplicate": True,

            "message": (
                "This document has already "
                "been uploaded."
            ),

            "existing_document_id": (
                existing_document["id"]
            ),

            "existing_filename": (
                existing_document["filename"]
            ),

            "file_hash": file_hash
        }


    print(
        "NO DUPLICATE FOUND."
    )

    print(
        "Continuing with document processing..."
    )

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 3: CREATE UNIQUE FILE PATH
    # ========================================================

    original_filename = file.filename

    base_name, extension = os.path.splitext(
        original_filename
    )

    safe_filename = (
        f"{base_name}_{file_hash[:12]}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )


    # ========================================================
    # STEP 4: SAVE PDF
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 4: SAVING PDF")
    print("=" * 80)

    try:

        # Hash calculation moves file pointer.
        # Reset it before copying.

        file.file.seek(0)

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        print("FILE SAVE ERROR")
        print(str(e))

        return {

            "success": False,

            "message": "Failed to save uploaded PDF.",

            "error": str(e)
        }


    print(
        f"Saved to: {file_path}"
    )

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 5: EXTRACT TEXT
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 5: EXTRACTING PDF TEXT")
    print("=" * 80)

    try:

        result = extract_text_from_pdf(
            file_path
        )

        extracted_text = result["text"]

    except Exception as e:

        print(
            "PDF TEXT EXTRACTION ERROR"
        )

        print(str(e))

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": "PDF text extraction failed.",

            "error": str(e)
        }


    print(
        f"Pages extracted: {result['pages']}"
    )

    print(
        f"Characters extracted: "
        f"{len(extracted_text)}"
    )

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 6: CLEAN TEXT
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 6: CLEANING TEXT")
    print("=" * 80)

    try:

        cleaned_text = clean_text(
            extracted_text
        )

    except Exception as e:

        print(
            "TEXT CLEANING ERROR"
        )

        print(str(e))

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": "Text cleaning failed.",

            "error": str(e)
        }


    print(
        f"Cleaned characters: "
        f"{len(cleaned_text)}"
    )

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 7: LLM LEGAL METADATA EXTRACTION
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 7: RUNNING LLM LEGAL METADATA EXTRACTION")
    print("=" * 80)

    try:

        metadata = extract_llm_metadata(
            cleaned_text
        )

    except Exception as e:

        print(
            "METADATA EXTRACTION ERROR"
        )

        print(str(e))

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": (
                "Legal metadata extraction failed."
            ),

            "error": str(e)
        }


    print("\nLLM METADATA RESULT:")
    print(metadata)

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 8: CREATE CHUNKS
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 8: CREATING CHUNKS")
    print("=" * 80)

    try:

        chunks = chunk_text(
            cleaned_text
        )

    except Exception as e:

        print(
            "CHUNKING ERROR"
        )

        print(str(e))

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": "Document chunking failed.",

            "error": str(e)
        }


    print(
        f"CHUNKS CREATED: {len(chunks)}"
    )

    print("=" * 80 + "\n")


    if not chunks:

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": "No chunks were generated."
        }


    # ========================================================
    # STEP 9: IMPORTANT PARTS
    # ========================================================

    important_parts = metadata.get(
        "important_parts",
        {}
    )


    # ========================================================
    # STEP 10: SAVE DOCUMENT TO LOCAL SQLITE
    # ========================================================
    #
    # IMPORTANT:
    #
    # SQLite is ONLY being used here for local testing /
    # local document management.
    #
    # We DO NOT save chunks to SQLite anymore.
    #
    # Supabase is the source of truth for chunks and embeddings.
    #
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 10: SAVING DOCUMENT TO LOCAL SQLITE")
    print("=" * 80)

    try:

        local_document_id = save_document(

            filename=original_filename,

            filepath=file_path,

            pages=result["pages"],

            characters=len(cleaned_text),

            extracted_text=cleaned_text,

            case_number=metadata.get(
                "case_number"
            ),

            case_title=metadata.get(
                "case_title"
            ),

            judge_name=metadata.get(
                "judge_name"
            ),

            petitioner_name=metadata.get(
                "petitioner_name"
            ),

            respondent_name=metadata.get(
                "respondent_name"
            ),

            court=metadata.get(
                "court"
            ),

            judgment_date=metadata.get(
                "judgment_date"
            ),

            case_type=metadata.get(
                "case_type"
            ),

            facts=important_parts.get(
                "facts"
            ),

            issues=important_parts.get(
                "issues"
            ),

            evidence=important_parts.get(
                "evidence"
            ),

            reasoning=important_parts.get(
                "reasoning"
            ),

            decision=important_parts.get(
                "decision"
            ),
        )

        print(
            f"Local document ID: "
            f"{local_document_id}"
        )

    except Exception as e:

        print(
            "LOCAL DOCUMENT STORAGE ERROR"
        )

        print(str(e))

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": (
                "Local document storage failed."
            ),

            "error": str(e)
        }

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 11: GENERATE EMBEDDINGS
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 11: GENERATING CHUNK EMBEDDINGS")
    print("=" * 80)

    try:

        chunk_texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = generate_embeddings(
            chunk_texts
        )

    except Exception as e:

        print(
            "EMBEDDING GENERATION ERROR"
        )

        print(str(e))

        # Cleanup local document

        try:

            delete_document(
                local_document_id
            )

        except Exception:
            pass

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": (
                "Embedding generation failed."
            ),

            "local_document_id": (
                local_document_id
            ),

            "error": str(e)
        }


    # ========================================================
    # VALIDATE EMBEDDINGS
    # ========================================================

    if len(embeddings) != len(chunks):

        print(
            "EMBEDDING COUNT MISMATCH"
        )

        try:

            delete_document(
                local_document_id
            )

        except Exception:
            pass

        if os.path.exists(file_path):

            os.remove(file_path)

        return {

            "success": False,

            "message": (
                "Number of embeddings does not "
                "match number of chunks."
            ),

            "chunks": len(chunks),

            "embeddings": len(embeddings)
        }


    # ========================================================
    # VALIDATE EMBEDDING DIMENSION
    # ========================================================

    if embeddings:

        embedding_dimension = len(
            embeddings[0]
        )

        if embedding_dimension != 3072:

            print(
                "INVALID EMBEDDING DIMENSION"
            )

            try:

                delete_document(
                    local_document_id
                )

            except Exception:
                pass

            if os.path.exists(file_path):

                os.remove(file_path)

            return {

                "success": False,

                "message": (
                    "Invalid embedding dimension."
                ),

                "expected_dimension": 3072,

                "actual_dimension": (
                    embedding_dimension
                )
            }

    else:

        embedding_dimension = 0


    print(
        f"Embeddings generated: "
        f"{len(embeddings)}"
    )

    print(
        f"Embedding dimension: "
        f"{embedding_dimension}"
    )

    print("=" * 80 + "\n")


    # ========================================================
    # STEP 12: SAVE DOCUMENT TO SUPABASE
    # ========================================================

    print("\n" + "=" * 80)
    print("STEP 12: SAVING DOCUMENT TO SUPABASE")
    print("=" * 80)

    supabase_document_id = None
    supabase_chunk_ids = []

    try:

        supabase_document_id = (
            save_supabase_document(

                filename=original_filename,

                filepath=file_path,

                pages=result["pages"],

                characters=len(cleaned_text),

                extracted_text=cleaned_text,

                file_hash=file_hash,

                case_number=metadata.get(
                    "case_number"
                ),

                case_title=metadata.get(
                    "case_title"
                ),

                judge_name=metadata.get(
                    "judge_name"
                ),

                petitioner_name=metadata.get(
                    "petitioner_name"
                ),

                respondent_name=metadata.get(
                    "respondent_name"
                ),

                court=metadata.get(
                    "court"
                ),

                judgment_date=metadata.get(
                    "judgment_date"
                ),

                case_type=metadata.get(
                    "case_type"
                ),

                facts=important_parts.get(
                    "facts"
                ),

                issues=important_parts.get(
                    "issues"
                ),

                evidence=important_parts.get(
                    "evidence"
                ),

                reasoning=important_parts.get(
                    "reasoning"
                ),

                decision=important_parts.get(
                    "decision"
                ),
            )
        )


        print(
            f"Supabase document ID: "
            f"{supabase_document_id}"
        )


        # ====================================================
        # STEP 13: SAVE CHUNKS + EMBEDDINGS TO SUPABASE
        # ====================================================
        #
        # CRITICAL:
        #
        # We use supabase_document_id here.
        #
        # NOT local_document_id.
        #
        # This fixes:
        #
        # chunks_document_id_fkey
        #
        # ====================================================

        print("\n" + "=" * 80)
        print("STEP 13: SAVING CHUNKS + EMBEDDINGS TO SUPABASE")
        print("=" * 80)

        supabase_chunk_ids = (
            save_supabase_chunks(

                document_id=supabase_document_id,

                chunks=chunks,

                embeddings=embeddings
            )
        )


        print(
            f"Supabase chunks saved: "
            f"{len(supabase_chunk_ids)}"
        )

        print("=" * 80 + "\n")


    except Exception as e:

        print("\n" + "=" * 80)
        print("SUPABASE STORAGE ERROR")
        print("=" * 80)

        print(str(e))

        print("=" * 80 + "\n")


        # ====================================================
        # CLEANUP SUPABASE DOCUMENT
        # ====================================================

        if supabase_document_id is not None:

            try:

                delete_supabase_chunks(
                    supabase_document_id
                )

            except Exception:
                pass

            try:

                delete_supabase_document(
                    supabase_document_id
                )

            except Exception:
                pass


        # ====================================================
        # CLEANUP LOCAL DOCUMENT
        # ====================================================

        try:

            delete_document(
                local_document_id
            )

        except Exception:
            pass


        # ====================================================
        # CLEANUP PDF
        # ====================================================

        if os.path.exists(file_path):

            try:

                os.remove(file_path)

            except Exception:
                pass


        return {

            "success": False,

            "message": (
                "Document processing completed, "
                "but Supabase storage failed."
            ),

            "local_document_id": (
                local_document_id
            ),

            "error": str(e)
        }


    # ========================================================
    # STEP 14: FINAL SUCCESS RESPONSE
    # ========================================================

    print("\n" + "=" * 80)
    print("DOCUMENT UPLOAD COMPLETED SUCCESSFULLY")
    print("=" * 80)

    print(
        f"Local document ID: "
        f"{local_document_id}"
    )

    print(
        f"Supabase document ID: "
        f"{supabase_document_id}"
    )

    print(
        f"Chunks: "
        f"{len(chunks)}"
    )

    print(
        f"Embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Embedding dimension: "
        f"{embedding_dimension}"
    )

    print("=" * 80 + "\n")


    return {

        "success": True,

        "duplicate": False,

        "message": (
            "PDF uploaded, cleaned, metadata extracted, "
            "chunked, embedded and stored successfully."
        ),

        # ----------------------------------------------------
        # IDS
        # ----------------------------------------------------

        "local_document_id": (
            local_document_id
        ),

        "supabase_document_id": (
            supabase_document_id
        ),

        # ----------------------------------------------------
        # HASH
        # ----------------------------------------------------

        "file_hash": file_hash,

        # ----------------------------------------------------
        # FILE
        # ----------------------------------------------------

        "filename": original_filename,

        "stored_filename": safe_filename,

        "pages": result["pages"],

        "characters": len(
            cleaned_text
        ),

        # ----------------------------------------------------
        # CHUNKS
        # ----------------------------------------------------

        "chunks": len(
            chunks
        ),

        "supabase_chunk_count": len(
            supabase_chunk_ids
        ),

        # ----------------------------------------------------
        # EMBEDDINGS
        # ----------------------------------------------------

        "embedding_count": len(
            embeddings
        ),

        "embedding_dimension": (
            embedding_dimension
        ),

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        "metadata": metadata,

        # ----------------------------------------------------
        # PREVIEW
        # ----------------------------------------------------

        "preview": cleaned_text[:500]
    }


# ============================================================
# GET ALL LOCAL DOCUMENTS
# ============================================================

@app.get("/documents")
async def list_documents():

    try:

        documents = get_all_documents()

        return {

            "success": True,

            "count": len(documents),

            "documents": [
                dict(document)
                for document in documents
            ]
        }

    except Exception as e:

        return {

            "success": False,

            "message": "Failed to get local documents.",

            "error": str(e)
        }


# ============================================================
# GET LOCAL DOCUMENT
# ============================================================

@app.get("/documents/{document_id}")
async def get_document_details(
    document_id: int
):

    document = get_document(
        document_id
    )

    if document is None:

        return {

            "success": False,

            "message": "Document not found."
        }

    return {

        "success": True,

        "document": dict(document)
    }


# ============================================================
# GET DOCUMENT METADATA
# ============================================================

@app.get(
    "/documents/{document_id}/metadata"
)
async def get_document_metadata(
    document_id: int
):

    document = get_document(
        document_id
    )

    if document is None:

        return {

            "success": False,

            "message": "Document not found."
        }

    return {

        "success": True,

        "document_id": document_id,

        "filename": document["filename"],

        "metadata": {

            "case_number": document[
                "case_number"
            ],

            "case_title": document[
                "case_title"
            ],

            "judge_name": document[
                "judge_name"
            ],

            "petitioner_name": document[
                "petitioner_name"
            ],

            "respondent_name": document[
                "respondent_name"
            ],

            "court": document[
                "court"
            ],

            "judgment_date": document[
                "judgment_date"
            ],

            "case_type": document[
                "case_type"
            ],

            "important_parts": {

                "facts": document[
                    "facts"
                ],

                "issues": document[
                    "issues"
                ],

                "evidence": document[
                    "evidence"
                ],

                "reasoning": document[
                    "reasoning"
                ],

                "decision": document[
                    "decision"
                ]
            }
        }
    }


# ============================================================
# GET RAW CLEANED TEXT
# ============================================================

@app.get(
    "/documents/{document_id}/raw-text"
)
async def get_raw_text(
    document_id: int
):

    document = get_document(
        document_id
    )

    if document is None:

        return {

            "success": False,

            "message": "Document not found."
        }

    return {

        "success": True,

        "document_id": document_id,

        "filename": document[
            "filename"
        ],

        "characters": document[
            "characters"
        ],

        "text": document[
            "extracted_text"
        ]
    }


# ============================================================
# DEBUG: RUN LLM METADATA AGAIN
# ============================================================

@app.get(
    "/documents/{document_id}/debug-metadata"
)
async def debug_metadata(
    document_id: int
):

    document = get_document(
        document_id
    )

    if document is None:

        return {

            "success": False,

            "message": "Document not found."
        }

    text = document[
        "extracted_text"
    ]

    try:

        metadata = extract_llm_metadata(
            text
        )

        return {

            "success": True,

            "document_id": document_id,

            "filename": document[
                "filename"
            ],

            "metadata": metadata,

            "text_preview": text[:3000]
        }

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Metadata extraction failed."
            ),

            "error": str(e)
        }


# ============================================================
# SUPABASE: GET DOCUMENT
# ============================================================

@app.get(
    "/supabase/documents/{document_id}"
)
async def get_supabase_document_api(
    document_id: int
):

    try:

        document = get_supabase_document(
            document_id
        )

        if document is None:

            return {

                "success": False,

                "message": (
                    "Supabase document not found."
                )
            }

        return {

            "success": True,

            "document": document
        }

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Failed to retrieve Supabase document."
            ),

            "error": str(e)
        }


# ============================================================
# SUPABASE: GET ALL DOCUMENTS
# ============================================================

@app.get(
    "/supabase/documents"
)
async def list_supabase_documents():

    try:

        documents = (
            get_all_supabase_documents()
        )

        return {

            "success": True,

            "count": len(documents),

            "documents": documents
        }

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Failed to retrieve Supabase documents."
            ),

            "error": str(e)
        }


# ============================================================
# SUPABASE: GET DOCUMENT CHUNKS
# ============================================================

@app.get(
    "/supabase/documents/{document_id}/chunks"
)
async def list_supabase_document_chunks(
    document_id: int
):

    try:

        document = get_supabase_document(
            document_id
        )

        if document is None:

            return {

                "success": False,

                "message": (
                    "Supabase document not found."
                )
            }

        chunks = get_supabase_chunks(
            document_id
        )

        return {

            "success": True,

            "document_id": document_id,

            "filename": document[
                "filename"
            ],

            "count": len(chunks),

            "chunks": chunks
        }

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Failed to retrieve Supabase chunks."
            ),

            "error": str(e)
        }


# ============================================================
# SUPABASE: VECTOR SEARCH
# ============================================================

@app.post(
    "/supabase/search"
)
async def supabase_vector_search(
    query: str,
    match_count: int = 5
):

    if not query or not query.strip():

        return {

            "success": False,

            "message": "Query cannot be empty."
        }

    try:

        # Generate embedding for user query

        query_embedding = generate_embedding(
            query.strip()
        )

        # Search Supabase vector database

        results = search_similar_chunks(
            query_embedding=query_embedding,

            match_count=match_count
        )

        return {

            "success": True,

            "query": query,

            "match_count": match_count,

            "results": results
        }

    except Exception as e:

        return {

            "success": False,

            "message": "Vector search failed.",

            "error": str(e)
        }


# ============================================================
# TEST EMBEDDING GENERATION
# ============================================================

@app.get(
    "/test-embedding"
)
async def test_embedding():

    test_text = (
        "This is a test sentence "
        "for embedding generation."
    )

    try:

        embedding = generate_embedding(
            test_text
        )

        return {

            "success": True,

            "text": test_text,

            "dimensions": len(
                embedding
            ),

            "embedding_preview": (
                embedding[:10]
            )
        }

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Embedding generation failed."
            ),

            "error": str(e)
        }


# ============================================================
# DELETE LOCAL DOCUMENT
# ============================================================

@app.delete(
    "/documents/{document_id}"
)
async def remove_document(
    document_id: int
):

    document = get_document(
        document_id
    )

    if document is None:

        return {

            "success": False,

            "message": "Document not found."
        }


    # ========================================================
    # DELETE PDF
    # ========================================================

    if os.path.exists(
        document["filepath"]
    ):

        try:

            os.remove(
                document["filepath"]
            )

        except Exception as e:

            print(
                "FILE DELETE ERROR:",
                str(e)
            )


    # ========================================================
    # DELETE LOCAL DATABASE RECORD
    # ========================================================

    try:

        deleted = delete_document(
            document_id
        )

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Failed to delete local document."
            ),

            "error": str(e)
        }


    if not deleted:

        return {

            "success": False,

            "message": (
                "Failed to delete local document."
            )
        }


    return {

        "success": True,

        "message": (
            "Local document deleted successfully."
        )
    }


# ============================================================
# DELETE SUPABASE DOCUMENT
# ============================================================

@app.delete(
    "/supabase/documents/{document_id}"
)
async def remove_supabase_document(
    document_id: int
):

    document = get_supabase_document(
        document_id
    )

    if document is None:

        return {

            "success": False,

            "message": (
                "Supabase document not found."
            )
        }


    try:

        # ====================================================
        # DELETE CHUNKS FIRST
        # ====================================================
        #
        # This is important if the database does not have
        # ON DELETE CASCADE configured.
        #
        # ====================================================

        try:

            delete_supabase_chunks(
                document_id
            )

        except Exception as e:

            print(
                "SUPABASE CHUNK DELETE ERROR:",
                str(e)
            )


        # ====================================================
        # DELETE DOCUMENT
        # ====================================================

        deleted = delete_supabase_document(
            document_id
        )


        return {

            "success": deleted,

            "message": (
                "Supabase document and its chunks "
                "deleted successfully."
                if deleted
                else
                "Failed to delete Supabase document."
            )
        }

    except Exception as e:

        return {

            "success": False,

            "message": (
                "Supabase deletion failed."
            ),

            "error": str(e)
        }