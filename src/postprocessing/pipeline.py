# postprocessing/postprocessing_pipeline.py
from postprocessing.residual_numbers import apply_residual_number_extraction
from postprocessing.cleanup import apply_cleanup



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
    df = apply_cleanup(
        df, 
        text_col = text_col
    )


    return df