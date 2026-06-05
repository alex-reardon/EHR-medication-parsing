import pandas as pd
from daily_dose_calculation.calculate_daily_dose import apply_expand_dose_rows


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

    df = apply_expand_dose_rows(
        df,
        dose_col=dose_col,
        frequency_col=frequency_col,
        amount_col=amount_col,
        output_col=output_col
    )

    # count calculated cells across all output cols
    out_cols = [c for c in df.columns if c == output_col or c.startswith(f"{output_col}_")]
    total    = df[out_cols].notna().any(axis=1).sum()
    print(f"Dose Calculation Complete: {total}/{len(df)} rows calculated ({total/len(df):.2%})")

    return df