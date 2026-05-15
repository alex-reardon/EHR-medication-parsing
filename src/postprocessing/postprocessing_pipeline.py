# postprocessing/postprocessing_pipeline.py

from postprocessing.extraction_cleanup import (
    clean_extraction_artifacts
)

from postprocessing.residual_number_extraction import (
    apply_residual_number_extraction
)


def clean_extracted_text(
    df,
    text_col="clean_text"
):

    """
    Post-extraction cleanup pipeline.

    Steps
    -----
    1. Remove extraction artifacts
    2. Extract residual/unmapped numbers
    3. Update cleaned text

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


    # -----------------------------------------------------
    # EXTRACT RESIDUAL NUMBERS
    # -----------------------------------------------------

    df = apply_residual_number_extraction(
        df,
        text_col=text_col
    )

    
    # -----------------------------------------------------
    # CLEAN EXTRACTION ARTIFACTS
    # -----------------------------------------------------

    df[text_col] = (
        df[text_col]
        .apply(clean_extraction_artifacts)
    )

    return df