import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)


# =========================================================
# BUILD PRN PATTERN
# =========================================================
def _build_prn_regex(
    compiled_rules
):
    """
    Build one compiled PRN regex
    from compiled rule objects.
    """

    terms = [
        rule["pattern_raw"]
        for rule in compiled_rules
        if pd.notna(
            rule["pattern_raw"]
        )
    ]

    # -----------------------------------------------------
    # DEDUPE + LONGEST FIRST
    # -----------------------------------------------------
    terms = sorted(
        list(dict.fromkeys(terms)),
        key=len,
        reverse=True
    )

    pattern = r"(?:{})".format(
        "|".join(terms)
    )

    return re.compile(
        pattern,
        flags=re.IGNORECASE
    )


# =========================================================
# EXTRACT PRN
# =========================================================
def extract_prn(
    text,
    prn_pattern
):
    """
    Extract PRN matches and
    remove them from text.
    """

    if pd.isna(text):
        return pd.Series([False, None, text ])
    text = str(text).lower()

    # -----------------------------------------------------
    # FIND MATCHES
    # -----------------------------------------------------
    found = list(
        prn_pattern.finditer(text)
    )

    # -----------------------------------------------------
    # NO MATCHES
    # -----------------------------------------------------
    if not found:

        return pd.Series([False, None, text])

    # -----------------------------------------------------
    # RAW MATCHES
    # -----------------------------------------------------
    raw_matches = list(
        dict.fromkeys([
            m.group(0)
            for m in found
        ])
    )

    # -----------------------------------------------------
    # REMOVE PRN TERMS
    # -----------------------------------------------------
    cleaned = prn_pattern.sub(
        " ",
        text
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    ).strip()

    return pd.Series([
        True,
        raw_matches,
        cleaned
    ])


# =========================================================
# APPLY PRN EXTRACTION
# =========================================================
def apply_prn_extraction(
    df,
    compiled_rules
):
    """
    Extract:
    - is_prn
    - prn_raw

    and update clean_text.
    """
    df = df.copy()

    # -----------------------------------------------------
    # BUILD PATTERN
    # -----------------------------------------------------
    prn_pattern = _build_prn_regex(
        compiled_rules
    )

    # -----------------------------------------------------
    # APPLY EXTRACTION
    # -----------------------------------------------------
    df[[
        "is_prn",
        "prn_raw",
        "clean_text"
    ]] = df["clean_text"].apply(
        lambda x: extract_prn(
            x,
            prn_pattern
        )
    )

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------
    df["clean_text"] = (
        df["clean_text"]
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    mapped = df["is_prn"].sum()

    logger.info(
        "PRN Extraction Complete: %d/%d rows mapped (%.2f%%)",
        mapped, len(df), 100 * mapped / len(df)
    )

    return df