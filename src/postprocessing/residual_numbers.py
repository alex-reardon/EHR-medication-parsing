# postprocessing/residual_number_extraction.py
import re
import pandas as pd


# ---------------------------------------------------------
# EXTRACT RESIDUAL / UNMAPPED NUMBERS
# ---------------------------------------------------------

NUMBER_PATTERN = r'\b-?\d+(?:\.\d+)?\b'


def _extract_residual_numbers(text):

    """
    Extract leftover standalone numbers that were not
    captured during dose extraction.

    Examples
    --------
    aspirin 81
        -> residual_numbers = [81]

    morphine -1
        -> residual_numbers = [-1]

    trazodone 0.5
        -> residual_numbers = [0.5]
    """

    if pd.isna(text):
        return {
            "residual_numbers": None,
            "clean_text": text
        }

    working = str(text)

    # -----------------------------------------------------
    # FIND MATCHES
    # -----------------------------------------------------

    matches = re.findall(
        NUMBER_PATTERN,
        working
    )

    parsed_numbers = []

    for m in matches:

        try:

            val = float(m)

            parsed_numbers.append(
                int(val)
                if val.is_integer()
                else val
            )

        except ValueError:

            parsed_numbers.append(m)

    # -----------------------------------------------------
    # REMOVE NUMBERS
    # -----------------------------------------------------

    working = re.sub(
        NUMBER_PATTERN,
        ' ',
        working
    )

    # -----------------------------------------------------
    # REMOVE LEFTOVER HYPHENS
    # ex:
    # morphine -1
    # morphine -
    # -----------------------------------------------------

    working = re.sub(
        r'\s*-\s*',
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

    return {

        "residual_numbers":
            parsed_numbers
            if parsed_numbers
            else None,

        "clean_text":
            working
    }


# ---------------------------------------------------------
# WRAPPER
# ---------------------------------------------------------

def apply_residual_number_extraction(
    df,
    text_col="clean_text"
):

    """
    Apply residual number extraction to dataframe.

    Parameters
    ----------
    df : pd.DataFrame

    text_col : str
        Column containing cleaned medication text

    Returns
    -------
    pd.DataFrame
    """

    df = df.copy()

    parsed = df[text_col].apply(
        _extract_residual_numbers
    )

    # -----------------------------------------------------
    # STORE NUMBERS
    # -----------------------------------------------------

    df["residual_numbers"] = parsed.apply(
        lambda x: x["residual_numbers"]
    )

    # -----------------------------------------------------
    # UPDATE CLEAN TEXT
    # -----------------------------------------------------

    df[text_col] = parsed.apply(
        lambda x: x["clean_text"]
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    mapped = df["residual_numbers"].notna().sum()

    print(
        f"Residual Number Extraction: "
        f"{mapped}/{len(df)} "
        f"({mapped/len(df):.1%})"
    )

    return df