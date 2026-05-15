# preprocessing/unit_normalization.py

import re
import pandas as pd



# ---------------------------------------------------
# APPLY UNIT NORMALIZATION RULES
# ---------------------------------------------------

def normalize_units(
    text: str,
    unit_pattern: list,
) -> str:
    """
    Normalize unit variants before extraction.

    Examples:
        5 milligrams -> 5mg
        5 mcg -> 5mcg
        5 micrograms -> 5mcg
    """

    if pd.isna(text):
        return text

    text = str(text)

    for rule in unit_pattern:

        pattern = rule["pattern_raw"]

        replacement = rule["replacement"]

        # -----------------------------------------
        # REGEX OBJECT SUPPORT
        # -----------------------------------------

        if hasattr(pattern, "pattern"):

            pattern = pattern.pattern

        # -----------------------------------------
        # SUBSTITUTE
        # -----------------------------------------

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    # -----------------------------------------
    # CLEANUP WHITESPACE
    # -----------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text