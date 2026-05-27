# extraction/extraction_pipeline.py
import pandas as pd
from extraction.formulation import apply_formulation_extraction
from extraction.category import apply_category_extraction
from extraction.prn_frequency import apply_prn_extraction
from extraction.dose import apply_dose_extraction
from extraction.frequency import apply_frequency_extraction
from extraction.parenthetical import apply_parenthetical_extraction


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
    meal_patterns = compiled_norm_patterns['meal_relation']

    # ---------------------------------------------------
    # FORMULATION EXTRACTION
    # ---------------------------------------------------
    df = apply_formulation_extraction(
        df=df,
        compiled_rules = formulation_patterns,
    )


    # ---------------------------------------------------
    # RELEASE EXTRACTION
    # ---------------------------------------------------
    df = apply_category_extraction(
        df=df,
        compiled_rules = release_patterns,
        category = 'release'
    )


    # ---------------------------------------------------
    # PRN EXTRACTION
    # ---------------------------------------------------
    df = apply_prn_extraction(
        df=df,
        compiled_rules = prn_patterns
    )


    # ---------------------------------------------------
    # FREQUENCY EXTRACTION
    # ---------------------------------------------------

    df = apply_frequency_extraction(
        df=df,
        compiled_rules=frequency_patterns
    )


    # ---------------------------------------------------
    # DOSE EXTRACTION
    # ---------------------------------------------------
    df = apply_dose_extraction(
        df=df, 
        compiled_rules = dose_patterns
    )


    # ---------------------------------------------------
    # ROUTE EXTRACTION
    # ---------------------------------------------------
    df = apply_category_extraction(
        df=df,
        compiled_rules = route_patterns,
        category = 'route'
    )

    # ---------------------------------------------------
    # Device EXTRACTION
    # ---------------------------------------------------
    df = apply_category_extraction(
        df=df,
        compiled_rules = device_patterns,
        category = 'device'
    )

    # ---------------------------------------------------
    # Timing EXTRACTION
    # ---------------------------------------------------
    df = apply_category_extraction(
        df=df,
        compiled_rules = timing_patterns,
        category = 'time_of_day'
    )



    # ---------------------------------------------------
    # MEAL: RELATION EXTRACTION
    # ---------------------------------------------------
    df = apply_category_extraction(
        df=df,
        compiled_rules = meal_patterns,
        category = 'meal_relation'
    )


    # ---------------------------------------------------
    # Parentheses EXTRACTION
    # ---------------------------------------------------
    df = apply_parenthetical_extraction(df)


    return df