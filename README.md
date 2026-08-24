# Legal Document Processing Pipeline

An automated legal document processing pipeline for extracting, cleaning, structuring, chunking, embedding, and storing Pakistani legal judgments.

## Overview

This project processes legal PDF documents through an automated pipeline and prepares them for downstream AI-powered legal research and retrieval systems.

The pipeline performs:

1. PDF document upload
2. PDF text extraction
3. Text cleaning and normalization
4. Legal metadata extraction using Google Gemini
5. Legal document chunking
6. Chunk embedding generation
7. Local SQLite storage
8. Supabase document storage
9. Supabase vector storage
10. Duplicate document detection using SHA-256 file hashing

## Architecture

```text
PDF Upload
    ↓
File Hashing
    ↓
Duplicate Detection
    ↓
PDF Text Extraction
    ↓
Text Cleaning
    ↓
LLM Metadata Extraction
    ↓
Document Chunking
    ↓
Embedding Generation
    ↓
Local SQLite Storage
    ↓
Supabase PostgreSQL + pgvector