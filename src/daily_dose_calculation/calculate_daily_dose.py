import re
import pandas as pd
import ast


def parse_dose_values(dose_raw):
    """
    Extract all numeric values from a dose string.
    ['81 mg']         → [81.0]
    ['25/100mg']      → [25.0, 100.0]
    ['25,100,10 mg']  → [25.0, 100.0, 10.0]
    """
    if isinstance(dose_raw, list):
        dose_raw = dose_raw[0] if dose_raw else ""
    if not isinstance(dose_raw, str):
        return [None]

    numbers = re.findall(r'\d+(?:\.\d+)?', dose_raw)
    return [float(n) for n in numbers] if numbers else [None]



def parse_amount(amount_raw):
    if isinstance(amount_raw, list): 
        amount_raw = amount_raw[0] if amount_raw else None
        
    if pd.isna(amount_raw):
        return None

    # convert "[1.5]" -> [1.5]
    if isinstance(amount_raw, str):
        try:
            parsed = ast.literal_eval(amount_raw)
            if isinstance(parsed, list):
                amount_raw = parsed
        except Exception:
            pass

    if isinstance(amount_raw, list):
        amount_raw = amount_raw[0] if amount_raw else None

    try:
        return float(amount_raw)
    except (TypeError, ValueError):
        return 1.0




def apply_expand_dose_rows(df, dose_col, frequency_col, amount_col, output_col="total_dose_per_day"):
    """
    For single-value doses, adds one output column.
    For multi-value doses like ['25/100mg'], adds one column per component:
        total_dose_per_day_1, total_dose_per_day_2, ...
    All rows get the same column set (NaN where not applicable).
    """
    rows = []

    # First pass: find the max number of dose components across all rows
    # so we know how many columns to create
    max_components = 1
    for _, row in df.iterrows():
        vals = parse_dose_values(row[dose_col])
        max_components = max(max_components, len([v for v in vals if v is not None]))

    # Build column names
    if max_components == 1:
        col_names = [output_col]
    else:
        col_names = [f"{output_col}_{i+1}" for i in range(max_components)]


    for _, row in df.iterrows():
        dose_values = parse_dose_values(row[dose_col])
        amount      = parse_amount(row[amount_col])

        # FIXME
        #FIXME if 
        if pd.isna(amount):
            amount= 1.0
        

        try:
            freq = float(row[frequency_col])
        except (TypeError, ValueError):
            freq = None

        new_row = row.to_dict()

        for i, col_name in enumerate(col_names):
            if i < len(dose_values) and dose_values[i] is not None and freq is not None:
                new_row[col_name] = dose_values[i] * freq * amount
            else:
                new_row[col_name] = None

        rows.append(new_row)

    return pd.DataFrame(rows).reset_index(drop=True)