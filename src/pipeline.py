from preprocessing.pipeline import normalize_medication_text
from extraction.pipeline import extract_medication_entities
from postprocessing.pipeline import clean_medication_text
from rxnorm_mapping.pipeline import rxnorm_map
#from daily_dose_calculation.pipeline import calculate_total_daily_dose


def run_pipeline(
    df,
    raw_med_col,
    compiled_norm_patterns,
    compiled_freq_patterns,
    rxnorm_rrf_path,
    rxnrel_rrf_path,
):
    """
    Run the complete medication processing pipeline.
    """

    # Normalize text
    df = normalize_medication_text(
        df=df,
        raw_med_col=raw_med_col,
        compiled_patterns=compiled_norm_patterns,
    )

    # Extract structured entities
    df = extract_medication_entities(
        df=df,
        compiled_freq_patterns=compiled_freq_patterns,
        compiled_norm_patterns=compiled_norm_patterns,
    )

    # Clean residual text
    df = clean_medication_text(
        df=df,
        text_col="clean_text",
    )

    # Map medications to RxNorm
    df = rxnorm_map(
        df,
        rxnorm_rrf_path,
        rxnrel_rrf_path,
    )

    # # Calculate total daily dose
    # df = calculate_total_daily_dose(
    #     df,
    #     dose_col="dose",
    #     frequency_col="frequency_per_day",
    #     amount_col="amount",
    # )

    return df