
import pandas as pd
from preprocessing.normalize_text import apply_text_normalization
from preprocessing.normalize_quantity import apply_quantity_normalization
from preprocessing.normalize_units import apply_normalize_units


# -------------------------------
# MAIN TEXT PREPROCESSING
# -------------------------------

def normalize_medication_text(df, raw_med_col, compiled_patterns) -> str:
    
    df = df.copy()
    # -----------------------------------------
    # BASIC CLEANING
    # -----------------------------------------

    df = apply_text_normalization(df, raw_med_col)
    quantity_patterns = compiled_patterns["quantity"]
    unit_patterns = compiled_patterns['unit']
    

    # -----------------------------------------
    # UNIT NORMALIZATION
    # -----------------------------------------

    if unit_patterns is not None:

        df = apply_normalize_units(
            df = df,
            unit_pattern=unit_patterns,
        )

    # -----------------------------------------
    # QUANTITY NORMALIZATION
    # -----------------------------------------

    if quantity_patterns is not None:
        df = apply_quantity_normalization(
            df=df,
            quantity_patterns=quantity_patterns
        )

    return df
