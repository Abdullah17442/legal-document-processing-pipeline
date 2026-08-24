import os

from dotenv import load_dotenv
from supabase import create_client, Client


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is not set in .env"
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY is not set in .env"
    )


# ============================================================
# CREATE SUPABASE CLIENT
# ============================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)