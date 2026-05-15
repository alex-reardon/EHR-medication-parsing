import pandas as pd
import re


# ---------------------------------------------------
# APPLY NORMALIZATION RULES TO SINGLE TEXT
# ---------------------------------------------------

def apply_rules(
    text: str,
    compiled_rules: list,
) -> str:

    if pd.isna(text):
        return text

    text = str(text)

    for rule in compiled_rules:

        pattern = rule["pattern"]

        repl = rule["replacement"]

        repl = (
            ''
            if pd.isna(repl)
            or str(repl).strip() == ''
            else str(repl)
        )

        text = re.sub(
            pattern,
            repl,
            text,
        )

    # final whitespace cleanup
    text = re.sub(r"\s+", " ", text).strip()

    return text



# ---------------------------------------------------
# QUANTITY NORMALIZATION
# ---------------------------------------------------

def normalize_quantity(
    text: str,
    quantity_patterns: list,
) -> str:

    text = apply_rules(
        text=text,
        compiled_rules=quantity_patterns,
    )

    return text