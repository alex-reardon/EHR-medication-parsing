# postprocessing/extraction_cleanup.py

import re
import pandas as pd


def clean_extraction_artifacts(text: str) -> str:

    if pd.isna(text):
        return text

    # -----------------------------------------
    # REMOVE EMPTY PARENTHESES
    # -----------------------------------------

    text = re.sub(
        r'\(\s*\)',
        '',
        text
    )

    # -----------------------------------------
    # REMOVE DANGLING "/("
    # -----------------------------------------

    text = re.sub(
        r'/\s*\(',
        '',
        text
    )

    # -----------------------------------------
    # REMOVE DOUBLE / REPEATED HYPHENS
    # ex: "- -"
    # -----------------------------------------

    text = re.sub(
        r'\s*-\s*-\s*',
        ' ',
        text
    )

    # -----------------------------------------
    # REMOVE TRAILING SLASHES
    # -----------------------------------------

    text = re.sub(
        r'/\s*$',
        '',
        text
    )

    # -----------------------------------------
    # REMOVE TRAILING HYPHENS
    # -----------------------------------------

    text = re.sub(
        r'[\s/\-.–—−]+$',
        '',
        text
    )

    # -----------------------------------------
    # REMOVE TRAILING NON-ALPHANUMERIC CHARS
    text = re.sub(
        r'[^a-zA-Z0-9]+$',
        '',
        text
    )

    # -----------------------------------------
    # NORMALIZE SEPARATORS
    # -----------------------------------------
    text = re.sub(
        r"\s*(?:\+|/|-|and)\s*",
        "/",
        text
    )


    # -----------------------------------------
    # COLLAPSE WHITESPACE
    # -----------------------------------------

    text = re.sub(
        r'\s+',
        ' ',
        text
    ).strip()

    return text