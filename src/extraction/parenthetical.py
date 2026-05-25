# category_extraction/parenthetical_extraction.py

import re
import pandas as pd


# ---------------------------------------------------------
# EXTRACT PARENTHETICAL TEXT
# ---------------------------------------------------------

PAREN_PATTERN = r'\((.*?)\)'


def extract_parenthetical(text):

    """
    Extract text inside parentheses.

    Examples
    --------
    aspirin (baby)
        -> ["baby"]

    stalevo (carbidopa/levodopa/entacapone)
        -> ["carbidopa/levodopa/entacapone"]

    sinemet (cr)
        -> ["cr"]
    """

    parsed = {
        "parenthetical_text": [],
        "clean_text": text
    }

    if pd.isna(text) or text == "":
        return parsed

    working = str(text)

    # -----------------------------------------------------
    # FIND MATCHES
    # -----------------------------------------------------

    matches = re.findall(
        PAREN_PATTERN,
        working
    )

    for match in matches:

        match = match.strip()

        if match:

            parsed["parenthetical_text"].append({

                "text": match,

                "raw": f"({match})"
            })

    # -----------------------------------------------------
    # REMOVE PARENTHETICAL TEXT
    # -----------------------------------------------------

    working = re.sub(
        PAREN_PATTERN,
        ' ',
        working
    )

    # -----------------------------------------------------
    # COLLAPSE WHITESPACE
    # -----------------------------------------------------

    working = re.sub(
        r'\s+',
        ' ',
        working
    ).strip()

    parsed["clean_text"] = working

    return parsed


# ---------------------------------------------------------
# APPLY TO DATAFRAME
# ---------------------------------------------------------

def apply_parenthetical_extraction(
    df,
    text_col="clean_text"
):

    df = df.copy()

    # -----------------------------------------------------
    # PARSE
    # -----------------------------------------------------

    df["parsed_parenthetical"] = df[text_col].apply(
        extract_parenthetical
    )

    # -----------------------------------------------------
    # EXTRACT TEXT VALUES
    # -----------------------------------------------------

    df["parenthetical_text"] = (
        df["parsed_parenthetical"]
        .apply(
            lambda x:
            [p["text"] for p in x["parenthetical_text"]]
            if x["parenthetical_text"]
            else None
        )
    )

    # -----------------------------------------------------
    # UPDATE CLEAN TEXT
    # -----------------------------------------------------

    df[text_col] = (
        df["parsed_parenthetical"]
        .apply(lambda x: x["clean_text"])
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    mapped = df["parenthetical_text"].notna().sum()

    print(
        f"Parenthetical Extraction: "
        f"{mapped}/{len(df)} "
        f"({mapped/len(df):.1%})"
    )

    return df