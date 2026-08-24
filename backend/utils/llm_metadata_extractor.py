import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# GEMINI API KEY
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY was not found in the .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "gemini-3.5-flash-lite"


# ============================================================
# METADATA SCHEMA
# ============================================================

class LegalMetadata(BaseModel):

    case_number: Optional[str] = Field(
        default=None,
        description=(
            "Official case, appeal, petition, revision, "
            "reference or suit number exactly as stated "
            "in the judgment."
        )
    )

    case_title: Optional[str] = Field(
        default=None,
        description=(
            "Official title or heading of the case, usually "
            "containing the names of the parties."
        )
    )

    judge_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of the judge or judges who authored or "
            "delivered the current judgment."
        )
    )

    petitioner_name: Optional[str] = Field(
        default=None,
        description=(
            "Actual name of the petitioner, appellant, "
            "plaintiff or party initiating the proceeding."
        )
    )

    respondent_name: Optional[str] = Field(
        default=None,
        description=(
            "Actual name of the respondent, defendant or "
            "opposing party."
        )
    )

    court: Optional[str] = Field(
        default=None,
        description=(
            "Name of the court that issued the current "
            "judgment or order."
        )
    )

    judgment_date: Optional[str] = Field(
        default=None,
        description=(
            "Date on which the current judgment or order "
            "was delivered."
        )
    )

    case_type: Optional[str] = Field(
        default=None,
        description=(
            "Specific proceeding type, such as Civil Appeal, "
            "Second Appeal, SAO, Civil Revision, Writ Petition, "
            "Constitutional Petition, Criminal Appeal, etc."
        )
    )

    facts: Optional[str] = Field(
        default=None,
        description=(
            "Concise factual background of the current case."
        )
    )

    issues: Optional[str] = Field(
        default=None,
        description=(
            "Main legal or factual questions/issues "
            "determined by the court."
        )
    )

    evidence: Optional[str] = Field(
        default=None,
        description=(
            "Important witnesses, documents, exhibits, "
            "testimony or other evidence considered."
        )
    )

    reasoning: Optional[str] = Field(
        default=None,
        description=(
            "The court's reasoning and legal analysis "
            "supporting its conclusion."
        )
    )

    decision: Optional[str] = Field(
        default=None,
        description=(
            "Final decision/order of the current court."
        )
    )


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are a legal-document metadata extraction system
specialized in Pakistani judgments and court orders.

Extract structured information ONLY from the supplied
judgment text.

CRITICAL RULES:

1. NEVER use the filename to determine metadata.

2. Identify the court from the actual judgment text.

3. Identify the case number from the actual judgment.

4. Identify the official case title from the actual
   judgment heading or party description.

5. Identify the actual parties.

6. Do NOT confuse lawyers with parties.

7. Do NOT confuse lawyers with judges.

8. Do NOT confuse witnesses with parties.

9. Do NOT use judges mentioned in cited cases as the
   current judge.

10. The judge must be the judge who authored or delivered
    the CURRENT judgment.

11. The judgment date must be the date of the CURRENT
    judgment, not a date belonging to a lower court.

12. Identify the specific proceeding type from the document.

13. If multiple case numbers exist, identify the primary
    proceeding being decided.

14. Important parts must come ONLY from the supplied text.

15. Facts describe what happened in the dispute.

16. Issues describe the legal/factual questions before
    the court.

17. Evidence describes important witnesses, documents,
    exhibits and testimony.

18. Reasoning explains why the court reached its decision.

19. Decision describes the final order/outcome.

20. NEVER invent information.

21. If a field cannot reliably be determined from the
    document, return null.

22. Preserve names as they appear in the judgment.

23. Focus on the CURRENT judgment rather than information
    from cited or earlier cases.

24. Pay special attention to:
    - case heading
    - first pages
    - coram/judge section
    - party descriptions
    - concluding paragraphs
    - signature section

25. For Pakistani judgments, party labels may vary.
    Examples include:
    - petitioner
    - appellant
    - plaintiff
    - complainant
    - applicant
    - respondent
    - defendant
    - accused

26. If the document uses "appellant" instead of
    "petitioner", put the actual appellant's name in
    petitioner_name.

27. If the document uses "plaintiff" instead of
    "petitioner", put the actual plaintiff's name in
    petitioner_name.

28. If the document uses "defendant" instead of
    "respondent", put the actual defendant's name in
    respondent_name.

29. Do not return role labels such as "Petitioner",
    "Appellant", "Respondent" or "Defendant" as names.
"""


# ============================================================
# EMPTY RESULT
# ============================================================

def empty_metadata():

    return {
        "case_number": None,
        "case_title": None,
        "judge_name": None,
        "petitioner_name": None,
        "respondent_name": None,
        "court": None,
        "judgment_date": None,
        "case_type": None,

        "important_parts": {
            "facts": None,
            "issues": None,
            "evidence": None,
            "reasoning": None,
            "decision": None
        }
    }


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_llm_metadata(text: str) -> dict:

    if not text or not text.strip():

        return empty_metadata()


    # ========================================================
    # DOCUMENT SIZE
    # ========================================================

    MAX_CHARS = 40000


    if len(text) > MAX_CHARS:

        beginning = text[:25000]

        ending = text[-15000:]

        text_for_extraction = (
            beginning
            + "\n\n"
            + "[MIDDLE OF DOCUMENT OMITTED]\n\n"
            + ending
        )

    else:

        text_for_extraction = text


    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
{SYSTEM_INSTRUCTION}

Extract the following Pakistani legal judgment.

==============================
JUDGMENT TEXT
==============================

{text_for_extraction}

==============================
END JUDGMENT TEXT
==============================

Return ONLY the requested structured metadata.

Do not use the filename.

Do not guess.

If the court, party name or another field cannot be
established from the text, return null.
"""


    try:

        # ====================================================
        # GEMINI REQUEST
        # ====================================================

        response = client.models.generate_content(

            model=MODEL_NAME,

            contents=prompt,

            config={
                "response_mime_type": "application/json",
                "response_json_schema": (
                    LegalMetadata.model_json_schema()
                )
            }
        )


        # ====================================================
        # VALIDATE RESPONSE
        # ====================================================

        metadata = LegalMetadata.model_validate_json(
            response.text
        )


        # ====================================================
        # RETURN NORMALIZED FORMAT
        # ====================================================

        return {

            "case_number":
                metadata.case_number,

            "case_title":
                metadata.case_title,

            "judge_name":
                metadata.judge_name,

            "petitioner_name":
                metadata.petitioner_name,

            "respondent_name":
                metadata.respondent_name,

            "court":
                metadata.court,

            "judgment_date":
                metadata.judgment_date,

            "case_type":
                metadata.case_type,

            "important_parts": {

                "facts":
                    metadata.facts,

                "issues":
                    metadata.issues,

                "evidence":
                    metadata.evidence,

                "reasoning":
                    metadata.reasoning,

                "decision":
                    metadata.decision
            }
        }


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print("\n" + "=" * 80)

        print("LLM METADATA EXTRACTION ERROR")

        print("=" * 80)

        print(str(e))

        print("=" * 80 + "\n")


        result = empty_metadata()

        result["error"] = str(e)

        return result