import pandas as pd
from daily_dose_calculation.check_reordered import apply_order_flipped # ingredient order detection (creates TF )
from daily_dose_calculation.reorder_dose import apply_dose_reorder # if above is TRUE flip 

from daily_dose_calculation.calculate_daily_dose import apply_expand_dose_rows # freq*amt*dose for each dose (ex 25/100mg)
from daily_dose_calculation.create_canonical_ledd_col import apply_create_canonical_ledd_col # create canonical med col name 

from daily_dose_calculation.ledd_mapping import apply_ledd_mapping # merge conversion factor col to df 
from daily_dose_calculation.calculate_ledd import apply_levodopa_ledd # calclulate levedopa equivalent daily dose (total levodopa daily dose * conversion factor)



def calculate_total_daily_dose(
    df: pd.DataFrame,
    dose_col: str,
    frequency_col: str,
    amount_col: str,
    output_col: str = "daily_dose"
) -> pd.DataFrame:
    """
    Wrapper for expand_dose_rows.
    
    Expands multi-value doses into separate rows and computes:
        total_dose_per_day = dose × frequency_per_day × amount

    Parameters
    ----------
    df            : input DataFrame
    dose_col      : column containing dose strings e.g. ['81 mg'], ['25/100mg']
    frequency_col : column containing numeric frequency per day e.g. 1, 3, 4
    amount_col    : column containing amount taken e.g. [1], [2]
    output_col    : name for the output column (default: 'total_dose_per_day')

    Returns
    -------
    DataFrame with one row per dose component and a total_dose_per_day column.
    """



    required = [dose_col, frequency_col, amount_col]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()    
    
    
    # Create canonical LEDD med col 
    df = apply_create_canonical_ledd_col(df)
    print(df.columns)


    df = apply_order_flipped(df, input_col='parsed', match_col='canonical_LEDD_med')

    df = apply_dose_reorder(df, dose_col = 'dose', input_col = 'parsed', matched_col = 'canonical_LEDD_med')

    df = apply_expand_dose_rows(
        df,
        dose_col='dose_reordered',
        frequency_col=frequency_col,
        amount_col=amount_col,
        output_col=output_col
    )

    # count calculated cells across all output cols
    out_cols = [c for c in df.columns if c == output_col or c.startswith(f"{output_col}_")]
    total    = df[out_cols].notna().any(axis=1).sum()
    print(f"Dose Calculation Complete: {total}/{len(df)} rows calculated ({total/len(df):.2%})")

    df = apply_ledd_mapping(
        df,
        ledd_csv_path="/Users/emudr/PPMI_LEDD/data/ledd_conversion_factors.csv",
        name_col="canonical_LEDD_med",
        release_col="release",
        route_col="route"
    )

    df = apply_levodopa_ledd(df, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3"))
    ld_mask = df["ledd_conversion_factor"].astype(str).str.contains(r"LD x ", na=False)
    df.loc[ld_mask, "levodopa_ledd"] = df.loc[ld_mask, "ledd_conversion_factor"]

    return df 


