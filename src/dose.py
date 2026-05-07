import re
import pandas as pd

NUM = r'\d+(?:\.\d+)?'
SEP = r'\s*[/\-]\s*'

def load_unit_pattern(path: str) -> str:
    """
    Load normalization dictionary and build unit regex pattern
    """

    rules_df = pd.read_csv(path)

    unit_rules = rules_df[rules_df["category"] == "unit"]

    # clean + sort longest first (important!)
    unit_values = (
        unit_rules["replacement"]
        .dropna()
        .astype(str)
        .str.lower()
        .sort_values(key=lambda x: x.str.len(), ascending=False)
        .unique()
        .tolist()
    )

    # build regex
    unit_pattern = r'(?:' + '|'.join(map(re.escape, unit_values)) + r')'
    return unit_pattern



def clean_text_whitespace(text: str) -> str:
    """Standardize spacing and strip trailing slashes."""
    if not isinstance(text, str): return text
    text = re.sub(r"[/\-.]\s*$", "", text)
    return re.sub(r"\s+", " ", text).strip()




def extract_dose_and_units(text: str, unit_pattern: str):
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return pd.Series([None, None, text])

    text = str(text).lower()

    doses = []
    units = []


    # -------------------------------
    # 1A. ratios WITH units ATTACHED (25mg/35mg/100mg)
    # -------------------------------
    ratio_unit_each_pattern = rf'(\d+(?:\.\d+)?\s*{unit_pattern}(?:\s*[/\-]\s*\d+(?:\.\d+)?\s*{unit_pattern})+)'
    ratio_unit_each_matches = re.findall(ratio_unit_each_pattern, text)

    for match in ratio_unit_each_matches:
        parts = re.split(r'\s*[/\-]\s*', match)

        for part in parts:
            m = re.match(rf'(\d+(?:\.\d+)?)\s*({unit_pattern})', part)
            if m:
                doses.append(float(m.group(1)))
                units.append(m.group(2))

    # remove from text
    text = re.sub(ratio_unit_each_pattern, '', text)


    # -------------------------------
    # 1B. ratios WITH units (25/100 mg) or 25-100 mg
    # -------------------------------
    ratio_pattern = rf'(\d+(?:\.\d+)?(?:\s*[/\-]\s*\d+(?:\.\d+)?)+)\s*({unit_pattern})'
    ratio_matches = re.findall(ratio_pattern, text)

    for ratio, unit in ratio_matches:
        parts = re.split(r'\s*[/\-]\s*', ratio)
        doses.extend([float(p) for p in parts])
        units.extend([unit] * len(parts))  # 🔥 duplicate unit for each dose

    text = re.sub(ratio_pattern, '', text)


    # -------------------------------
    # 1C. ratios WITHOUT units (25/100) OR (25-100)
    # -------------------------------
    ratio_no_unit_pattern = rf'\b\d+(?:\.\d+)?(?:\s*[/\-]\s*\d+(?:\.\d+)?)+\b(?!\s*{unit_pattern})'
    ratio_no_unit_matches = re.findall(ratio_no_unit_pattern, text)

    for ratio in ratio_no_unit_matches:
        parts = re.split(r'\s*[/\-]\s*', ratio)
        doses.extend([float(p) for p in parts])

    text = re.sub(ratio_no_unit_pattern, '', text)


    # -------------------------------
    # 2. standard doses (10 mg)
    # -------------------------------
    standard_pattern = rf'(\d+\.?\d*)\s*({unit_pattern})'
    matches = re.findall(standard_pattern, text)

    for num, unit in matches:
        doses.append(float(num))
        units.append(unit)


    # -------------------------------
    # 4. remove number + unit
    # -------------------------------
    clean_text = re.sub(standard_pattern, '', text)
    # -------------------------------
    # 5. remove standalone units
    # -------------------------------
    if unit_pattern:
        unit_only_pattern = rf'\b{unit_pattern}(?:/{unit_pattern})*\b'
        clean_text = re.sub(unit_only_pattern, '', clean_text)

    # -------------------------------
    # 6. normalize spacing
    # -------------------------------
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    clean_text = re.sub(r'[/-]', ' ', clean_text)

    
    return pd.Series([
        doses if doses else None,
        units,
        clean_text
    ])



def apply_dose_unit_extraction(df: pd.DataFrame, input_col: str, output_col : str, path: str):
    """
    Applies dose + unit extraction to dataframe
    """
    unit_pattern = load_unit_pattern(path)

    df[["dose", "units", output_col]] = df[input_col].apply(
        lambda x: extract_dose_and_units(x, unit_pattern)
    )
    df[output_col] = df[output_col].apply(clean_text_whitespace)
    # Metrics
    mapped = df["dose"].notna().sum()
    print(f"Dose Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")
    

    return df


