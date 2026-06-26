# postprocessing/extraction_cleanup.py

import re
import pandas as pd


def _clean_extraction_artifacts(text: str) -> str:

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
    # REMOVE UNKNOWN/UNK
    # -----------------------------------------

    text = re.sub(
        'unknown',
        '',
        text
    )


    text = re.sub(
        'unk',
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
    # NORMALIZE SEPARATORS
    # -----------------------------------------
    text = re.sub(
        r"\s*(?:\+|-|:|,)\s*",
        " ",
        text
    )


    # -----------------------------------------
    # REMOVE DOUBLE / REPEATED HYPHENS
    # ex: "- -"
    # -----------------------------------------

    text = re.sub(
        r'\s*/\s*/\s*',
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
    # REMOVE TRAILING NON-ALPHANUMERIC CHARS
    text = re.sub(
        r'[^a-zA-Z0-9]+$',
        '',
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



def apply_cleanup(df, text_col) : 
    df[text_col] = df[text_col].apply(lambda x: _clean_extraction_artifacts(x))
    return df

    