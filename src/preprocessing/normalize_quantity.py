import logging
import pandas as pd
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# APPLY NORMALIZATION RULES TO SINGLE TEXT
# ---------------------------------------------------

def _apply_regex_replacement_rules(
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

def normalize_quantities(
    text: str,
    quantity_patterns: list,
) -> str:

    text = _apply_regex_replacement_rules(
        text=text,
        compiled_rules=quantity_patterns,
    )

    return text


def apply_quantity_normalization(
    df: pd.DataFrame,
    quantity_patterns: list = None
) -> pd.DataFrame:

    """
    Apply regex-based quantity normalization to a dataframe column.
    """

    df = df.copy()

    if quantity_patterns is None:
        return df

    df["clean_text"] = df["clean_text"].apply(
        lambda x: normalize_quantities(
            text=x,
            quantity_patterns=quantity_patterns
        )
    )

    # -------------------------------
    # METRICS
    # -------------------------------
    total = len(df)
    non_null = df["clean_text"].notna().sum()

    logger.info(
        "Quantity Normalization Complete: %d/%d rows processed (%.2f%%)",
        non_null, total, 100 * non_null / total
    )

    return df