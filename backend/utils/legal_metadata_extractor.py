import re
from typing import Dict, Optional


# ============================================================
# BASIC CLEANING
# ============================================================

def clean_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    value = re.sub(r"\s+", " ", value)
    value = value.strip(" :-\n\t.,")

    return value if value else None


def normalize_text(text: str) -> str:
    """
    Normalize PDF-extracted text while preserving paragraph numbers.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove artificial page-number lines such as:
    # " 2"
    # " 3"
    # " 4"
    text = re.sub(r"\n\s*\d{1,2}\s*\n", "\n", text)

    # Collapse excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# ============================================================
# CASE NUMBER
# ============================================================

def extract_case_number(text: str) -> Optional[str]:

    # Pakistani SAO / appeal formats
    patterns = [
        r"\bSAO\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bC\.?R\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bW\.?P\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bC\.?P\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bR\.?F\.?A\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bR\.?S\.?A\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bF\.?A\.?O\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bI\.?C\.?A\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bCrl\.?\s*Appeal\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bCrl\.?\s*Misc\.?\s*No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if matches:
            # Remove duplicates while preserving order
            unique = list(dict.fromkeys(matches))

            return " & ".join(
                clean_value(x) for x in unique
            )

    return None


# ============================================================
# JUDGE
# ============================================================

def extract_judge(text: str) -> Optional[str]:

    patterns = [

        # Most reliable:
        # (IJAZ UL AHSAN) JUDGE
        r"\(\s*([A-Z][A-Z .'-]+)\s*\)\s*JUDGE\b",

        # IJAZ UL AHSAN JUDGE
        r"\b([A-Z][A-Z .'-]{2,80})\s+JUDGE\b",

        # Justice XYZ
        r"\bJUSTICE\s+([A-Z][A-Z .'-]{2,80})",

        # CORAM: JUSTICE XYZ
        r"\bCORAM\s*:\s*(?:MR\.?|MS\.?|MRS\.?)?\s*JUSTICE\s+([A-Z][A-Z .'-]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            judge = clean_value(match.group(1))

            if judge:

                # Remove accidental trailing words
                judge = re.sub(
                    r"\s+JUDGE$",
                    "",
                    judge,
                    flags=re.IGNORECASE
                )

                return judge

    return None


# ============================================================
# HEADER EXTRACTION
# ============================================================

def extract_header_lines(text: str):

    """
    Extract the beginning of the judgment.

    Example:

    SAO No.150 of 2009.
    SAO No.150 of 2009.
    Tehkedar Jehagir.
    Izat Fazeel etc.
    16.10.2009.
    Mian Faheem Altaf, Advocate.
    """

    lines = []

    for line in text.splitlines():

        line = clean_value(line)

        if line:
            lines.append(line)

    return lines[:20]


# ============================================================
# PETITIONER / APPELLANT
# ============================================================

def extract_petitioner(text: str) -> Optional[str]:

    # Explicit labels
    patterns = [

        r"\bPetitioner\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",

        r"\bAppellant\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",

        r"\bPetitioners?\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",

        r"\bAppellants?\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            value = clean_value(match.group(1))

            if value:
                return value

    # --------------------------------------------------------
    # Header fallback
    # --------------------------------------------------------
    #
    # This particular dataset contains:
    #
    # Tehkedar Jehagir.
    # Izat Fazeel etc.
    #
    # There is no "VERSUS" text in the extracted PDF.
    #
    # We therefore use the two lines following the case number
    # as candidate parties.
    #

    lines = extract_header_lines(text)

    case_index = None

    for i, line in enumerate(lines):

        if re.search(
            r"\b(?:SAO|C\.?R\.?|W\.?P\.?|C\.?P\.?|R\.?F\.?A\.?|R\.?S\.?A\.?)",
            line,
            re.IGNORECASE
        ):
            case_index = i
            break

    if case_index is not None:

        candidates = []

        for line in lines[case_index + 1:case_index + 7]:

            # Skip dates
            if re.fullmatch(
                r"\d{1,2}[./-]\d{1,2}[./-]\d{4}",
                line
            ):
                continue

            # Skip advocate lines
            if re.search(
                r"\bAdvocate\b|\bCounsel\b",
                line,
                re.IGNORECASE
            ):
                continue

            # Skip court/judge information
            if re.search(
                r"\bJUDGE\b|\bJUSTICE\b|\bCOURT\b",
                line,
                re.IGNORECASE
            ):
                continue

            # Avoid extremely long lines
            if len(line) <= 120:
                candidates.append(line)

        if len(candidates) >= 1:

            candidate = candidates[0]

            # Don't return generic words
            if candidate.lower() not in {
                "etc",
                "versus",
                "vs",
                "v"
            }:
                return clean_value(candidate)

    return None


# ============================================================
# RESPONDENT
# ============================================================

def extract_respondent(text: str) -> Optional[str]:

    # Explicit labels
    patterns = [

        r"\bRespondent\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",

        r"\bRespondents?\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",

        r"\bDefendant\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",

        r"\bDefendants?\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,120})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            value = clean_value(match.group(1))

            if value:
                return value

    # --------------------------------------------------------
    # Header fallback
    # --------------------------------------------------------

    lines = extract_header_lines(text)

    case_index = None

    for i, line in enumerate(lines):

        if re.search(
            r"\b(?:SAO|C\.?R\.?|W\.?P\.?|C\.?P\.?|R\.?F\.?A\.?|R\.?S\.?A\.?)",
            line,
            re.IGNORECASE
        ):
            case_index = i
            break

    if case_index is not None:

        candidates = []

        for line in lines[case_index + 1:case_index + 7]:

            if re.fullmatch(
                r"\d{1,2}[./-]\d{1,2}[./-]\d{4}",
                line
            ):
                continue

            if re.search(
                r"\bAdvocate\b|\bCounsel\b|\bJUDGE\b|\bJUSTICE\b|\bCOURT\b",
                line,
                re.IGNORECASE
            ):
                continue

            if len(line) <= 120:
                candidates.append(line)

        if len(candidates) >= 2:

            candidate = candidates[1]

            if candidate.lower() not in {
                "etc",
                "versus",
                "vs",
                "v"
            }:
                return clean_value(candidate)

    return None


# ============================================================
# COURT
# ============================================================

def extract_court(
    text: str,
    filename: Optional[str] = None
) -> Optional[str]:

    norm = re.sub(r"\s+", " ", text).upper()

    court_patterns = [

        (
            r"SUPREME COURT OF PAKISTAN",
            "Supreme Court of Pakistan"
        ),

        (
            r"LAHORE HIGH COURT",
            "Lahore High Court"
        ),

        (
            r"LAHORE HIGH COURT,?\s*LAHORE",
            "Lahore High Court"
        ),

        (
            r"LAHORE HIGH COURT AT LAHORE",
            "Lahore High Court"
        ),

        (
            r"HIGH COURT OF SINDH",
            "High Court of Sindh"
        ),

        (
            r"SINDH HIGH COURT",
            "High Court of Sindh"
        ),

        (
            r"ISLAMABAD HIGH COURT",
            "Islamabad High Court"
        ),

        (
            r"ISLAMABAD HIGH COURT OF ISLAMABAD",
            "Islamabad High Court"
        ),

        (
            r"PESHAWAR HIGH COURT",
            "Peshawar High Court"
        ),

        (
            r"FEDERAL SHARIAT COURT",
            "Federal Shariat Court"
        ),

        (
            r"BALOCHISTAN HIGH COURT",
            "Balochistan High Court"
        ),
    ]

    for pattern, court_name in court_patterns:

        if re.search(pattern, norm):

            return court_name

    # --------------------------------------------------------
    # Filename fallback
    # --------------------------------------------------------
    #
    # This document is:
    #
    # 2009LHC8.pdf
    #
    # LHC = Lahore High Court
    #

    if filename:

        filename_upper = filename.upper()

        if "LHC" in filename_upper:
            return "Lahore High Court"

        if "SHC" in filename_upper:
            return "High Court of Sindh"

        if "IHC" in filename_upper:
            return "Islamabad High Court"

        if "PHC" in filename_upper:
            return "Peshawar High Court"

        if "BHC" in filename_upper:
            return "Balochistan High Court"

        if "FSC" in filename_upper:
            return "Federal Shariat Court"

        if "SCP" in filename_upper or "SC" in filename_upper:
            return "Supreme Court of Pakistan"

    return None


# ============================================================
# JUDGMENT DATE
# ============================================================

def extract_judgment_date(text: str) -> Optional[str]:

    patterns = [

        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",

        r"\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+\d{4}\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            return clean_value(match.group(0))

    return None


# ============================================================
# CASE TYPE
# ============================================================

def extract_case_type(text: str) -> str:

    norm = re.sub(
        r"\s+",
        " ",
        text.lower()
    )

    # Check specific legal proceeding first
    if re.search(r"\bsao\s+no", norm):
        return "Second Appeal / Civil"

    if "civil revision" in norm:
        return "Civil Revision"

    if "writ petition" in norm:
        return "Constitutional Petition"

    if "criminal appeal" in norm:
        return "Criminal Appeal"

    if "constitutional petition" in norm:
        return "Constitutional Petition"

    # Subject matter
    if (
        "ejectment" in norm
        or "eviction" in norm
        or "tenant" in norm
        or "personal need of the landlord" in norm
    ):
        return "Civil - Landlord/Tenant"

    if (
        "murder" in norm
        or "qatl-e-amd" in norm
        or "302 ppc" in norm
    ):
        return "Criminal - Murder"

    if (
        "property dispute" in norm
        or "mutation" in norm
    ):
        return "Civil - Property"

    if (
        "divorce" in norm
        or "khula" in norm
        or "maintenance" in norm
    ):
        return "Family Law"

    return "Unknown"


# ============================================================
# NUMBERED PARAGRAPHS
# ============================================================

def extract_numbered_paragraphs(text: str) -> Dict[int, str]:

    """
    Extract legal judgment paragraphs.

    Handles PDF text such as:

    2. The appeals are directed...
    3. The suits were contested...
    4. The issue of default...
    """

    text = normalize_text(text)

    matches = list(
        re.finditer(
            r"(?:^|\n|\s)(\d{1,2})\.\s+",
            text
        )
    )

    paragraphs = {}

    for i, match in enumerate(matches):

        number = int(match.group(1))

        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        content = text[start:end]

        content = clean_value(content)

        if content:
            paragraphs[number] = content

    return paragraphs


# ============================================================
# IMPORTANT PARTS
# ============================================================

def extract_important_parts(text: str) -> Dict[str, str]:

    paragraphs = extract_numbered_paragraphs(text)

    result = {
        "facts": "",
        "issues": "",
        "evidence": "",
        "reasoning": "",
        "decision": "",
    }

    # --------------------------------------------------------
    # FACTS
    # --------------------------------------------------------

    fact_numbers = [
        2,
        3,
        4,
    ]

    result["facts"] = "\n\n".join(
        f"{number}. {paragraphs[number]}"
        for number in fact_numbers
        if number in paragraphs
    )

    # --------------------------------------------------------
    # ISSUES
    # --------------------------------------------------------

    issue_numbers = [
        5,
        6,
        8,
    ]

    result["issues"] = "\n\n".join(
        f"{number}. {paragraphs[number]}"
        for number in issue_numbers
        if number in paragraphs
    )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    evidence_numbers = [
        3,
        4,
        6,
        8,
    ]

    result["evidence"] = "\n\n".join(
        f"{number}. {paragraphs[number]}"
        for number in evidence_numbers
        if number in paragraphs
    )

    # --------------------------------------------------------
    # REASONING
    # --------------------------------------------------------

    reasoning_numbers = [
        7,
        8,
        9,
    ]

    result["reasoning"] = "\n\n".join(
        f"{number}. {paragraphs[number]}"
        for number in reasoning_numbers
        if number in paragraphs
    )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    if 10 in paragraphs:
        result["decision"] = (
            f"10. {paragraphs[10]}"
        )

    # --------------------------------------------------------
    # FALLBACK DECISION SEARCH
    # --------------------------------------------------------

    if not result["decision"]:

        decision_patterns = [
            r"[^.]{0,250}"
            r"(?:appeals?|petition|application)"
            r".{0,100}"
            r"(?:dismissed|allowed|disposed of|set aside)"
            r"[^.]{0,250}\.",
        ]

        for pattern in decision_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if match:
                result["decision"] = clean_value(
                    match.group(0)
                )
                break

    return result


# ============================================================
# COMPLETE METADATA EXTRACTION
# ============================================================

def extract_legal_metadata(
    text: str,
    filename: Optional[str] = None
) -> Dict:

    text = normalize_text(text)

    important_parts = extract_important_parts(text)

    metadata = {

        "case_number":
            extract_case_number(text),

        "judge_name":
            extract_judge(text),

        "petitioner_name":
            extract_petitioner(text),

        "respondent_name":
            extract_respondent(text),

        "court":
            extract_court(
                text,
                filename
            ),

        "judgment_date":
            extract_judgment_date(text),

        "case_type":
            extract_case_type(text),

        "important_parts":
            important_parts,
    }

    return metadata