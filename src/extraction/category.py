import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def _extract_category(
    text,
    compiled_rules
):

    if pd.isna(text):
        return pd.Series([
            None,
            text
        ])

    text = str(text).lower()
    cleaned = text
    matches = []
    raw_matches = []

    # -----------------------------------------------------
    # APPLY RULES
    # -----------------------------------------------------
    for rule in compiled_rules:
        pattern = rule["pattern"]
        replacement = rule["replacement"]
        found = list(
            pattern.finditer(cleaned)
        )
        
        if not found:
            continue

        # ---------------------------------------------
        # STORE CANONICAL MAPPING
        # ---------------------------------------------
        matches.append(
            replacement
        )
        # ---------------------------------------------
        # STORE RAW MATCHES
        # ---------------------------------------------
        raw_matches.extend([
            m.group(0)
            for m in found
        ])
        # ---------------------------------------------
        # REMOVE MATCHES
        # ---------------------------------------------
        cleaned = pattern.sub(
            " ",
            cleaned
        )

    # -----------------------------------------------------
    # DEDUPE
    # -----------------------------------------------------
    if matches:
        matches = list(
            dict.fromkeys(matches)
        )

        raw_matches = list(
            dict.fromkeys(raw_matches)
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned
        ).strip()

        return pd.Series([
            matches,
            raw_matches,
            cleaned
        ])

    return pd.Series([
        None,
        None,
        text
    ])



def apply_category_extraction(df, category, compiled_rules):
    df = df.copy()
    df[[f"{category}", f"{category}_source", "clean_text"]] = df["clean_text"].apply(
        lambda x: _extract_category(x, compiled_rules)
    )
    return df