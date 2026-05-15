
import pandas as pd
from preprocessing.text_cleaning import normalize_text
from preprocessing.quantity_normalization import normalize_quantity
from preprocessing.unit_normalization import normalize_units



# -------------------------------
# MAIN TEXT PREPROCESSING
# -------------------------------

def preprocess_medication_text(text: str, quantity_patterns : list = None, unit_patterns : list = None) -> str:

    if pd.isna(text):
        return text

    # -----------------------------------------
    # BASIC CLEANING
    # -----------------------------------------

    text = normalize_text(text)


    # -----------------------------------------
    # UNIT NORMALIZATION
    # -----------------------------------------

    if unit_patterns is not None:

        text = normalize_units(
            text=text,
            unit_pattern=unit_patterns,
        )

    # -----------------------------------------
    # QUANTITY NORMALIZATION
    # -----------------------------------------

    if quantity_patterns is not None:

        text = normalize_quantity(
            text=text,
            quantity_patterns=quantity_patterns,
        )


    return text



# -------------------------------
# DATAFRAME WRAPPER
# -------------------------------

def preprocess_medication_dataframe(
    df: pd.DataFrame,
    raw_med_col: str, 
    compiled_patterns : dict
) -> pd.DataFrame:

    df = df.drop_duplicates().copy()

    # -----------------------------------------
    # LOAD COMPILED RULES
    # -----------------------------------------

    quantity_patterns = compiled_patterns["quantity"]
    unit_patterns = compiled_patterns['unit']

    # -----------------------------------------
    # RUN PREPROCESSING
    # -----------------------------------------

    df["clean_text"] = (
        df[raw_med_col]
        .apply(
            lambda x: preprocess_medication_text(
                text=x,
                quantity_patterns=quantity_patterns,
                unit_patterns = unit_patterns
            )
        )
    )

    return df