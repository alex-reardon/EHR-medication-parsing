# extraction/extraction_pipeline.py

import pandas as pd

from extraction.dose_extraction import extract_dose

from extraction.frequency_extraction import extract_frequency

from extraction.formulation_extraction import extract_formulation

from extraction.prn_extraction import extract_prn

from extraction.medication_category_extraction import extract_medication_category

from extraction.parenthetical_extraction import (extract_parenthetical)


# ---------------------------------------------------
# MAIN EXTRACTION PIPELINE
# ---------------------------------------------------

def extract_medication_entities(
    df: pd.DataFrame,
    compiled_freq_patterns: dict,
    compiled_norm_patterns : dict
) -> pd.DataFrame:
    """
    Run all extraction modules on medication text.

    Args:
        df:
            input dataframe

        compiled_patterns:
            dictionary of compiled regex rules

        text_col:
            source text column

    Returns:
        dataframe with extracted entities
    """

    df = df.copy()


    # ---------------------------------------------------
    # LOAD PATTERNS
    # ---------------------------------------------------



    formulation_patterns = compiled_norm_patterns["form"]

    release_patterns = compiled_norm_patterns["release"]
    
    prn_patterns = compiled_freq_patterns["prn"]

    frequency_patterns = compiled_freq_patterns

    dose_patterns = compiled_norm_patterns['unit']

    route_patterns = compiled_norm_patterns['route']

    device_patterns = compiled_norm_patterns['device']

    timing_patterns = compiled_norm_patterns['time_of_day']


    # ---------------------------------------------------
    # FORMULATION EXTRACTION
    # ---------------------------------------------------

    df = extract_formulation(
        df=df,
        compiled_rules = formulation_patterns,
    )


    # ---------------------------------------------------
    # RELEASE EXTRACTION
    # ---------------------------------------------------
    df = extract_medication_category(
        df=df,
        compiled_rules = release_patterns,
        category = 'release'
    )


    # ---------------------------------------------------
    # PRN EXTRACTION
    # ---------------------------------------------------
    df = extract_prn(
        df=df,
        compiled_rules = prn_patterns
    )


    # ---------------------------------------------------
    # FREQUENCY EXTRACTION
    # ---------------------------------------------------

    df = extract_frequency(
        df=df,
        compiled_rules=frequency_patterns
    )


    # ---------------------------------------------------
    # DOSE EXTRACTION
    # ---------------------------------------------------
    df = extract_dose(
        df=df, 
        compiled_rules = dose_patterns
    )


    # ---------------------------------------------------
    # ROUTE EXTRACTION
    # ---------------------------------------------------
    df = extract_medication_category(
        df=df,
        compiled_rules = route_patterns,
        category = 'route'
    )

    # ---------------------------------------------------
    # Device EXTRACTION
    # ---------------------------------------------------
    df = extract_medication_category(
        df=df,
        compiled_rules = device_patterns,
        category = 'device'
    )

    # ---------------------------------------------------
    # Timing EXTRACTION
    # ---------------------------------------------------
    df = extract_medication_category(
        df=df,
        compiled_rules = timing_patterns,
        category = 'time_of_day'
    )


    # ---------------------------------------------------
    # Parentheses EXTRACTION
    # ---------------------------------------------------
    df = extract_parenthetical(df)


    return df