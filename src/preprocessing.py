import pandas as pd
import re
import unicodedata
from typing import Optional, Dict


# -------------------------------
# NORMALIZE TEXT
# -------------------------------
def normalize_text(text: str) -> str:
    if pd.isna(text):
        return text

    text = str(text).lower()
    #text = re.sub(r'-', '/', text) # normalize hyphens
    text = re.sub(r'(?<=\d),\s*(?=\d)', '.', text) # convert commas between numbers → decimals # FIXME
    text = re.sub(r'\\', '/', text) #capture double //
    text = text.replace('[', '(').replace(']', ')')
    text = re.sub(r'[^a-z0-9\s\./\-%\(\)]', ' ', text)
    text = re.sub(r'\(', ' (', text)
    text = re.sub(r'(?<!\d)\.(?!\d)', '', text) # only keep decimals if between two numbers 
    text = re.sub(r'\s+', ' ', text)# collapse whitespace
    text = re.sub(r'/+', '/', text) #capture double //

    return unicodedata.normalize("NFKC", text.strip())


# -------------------------------
# LOAD REPLACEMENTS
# -------------------------------
def load_replacements(path: str = None) -> dict:
    """
    Load regex replacement rules from CSV.
    Returns empty dict if no path provided.
    """

    if path is None:
        return {}

    df = pd.read_csv(path, keep_default_na=False)
    df = df.fillna("")
    return dict(zip(df["raw"], df["replacement"]))



# -------------------------------
# APPLY REPLACEMENTS
# -------------------------------
def apply_replacements(df, col, replacements):
    """
    Apply regex replacements to a dataframe column.
    Applies longest patterns first.
    """

    if not replacements:
        return df[col]

    updated = df[col].astype(str).copy()

    # sort patterns longest → shortest
    sorted_patterns = sorted(
        replacements.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for pattern, repl in sorted_patterns:
        repl = '' if pd.isna(repl) or str(repl).strip() == '' else repl
        updated = updated.str.replace(pattern, repl, regex=True)

    return updated




def normalize_combo(text):
    if not isinstance(text, str):
        return text

    text_lower = text.lower()

    # normalize slashes spacing (helps matching)
    text_clean = re.sub(r'\s*/\s*', ' / ', text_lower)

    # map aliases → canonical
    drug_map = {
        "levodopa": "levodopa",
        "levocomp": "levodopa",
        "carbidopa": "carbidopa",
        "entacapone": "entacapone"
    }

    drugs = "|".join(drug_map.keys())

    # -------------------------------
    # extract (drug, dose) pairs BOTH directions
    # -------------------------------
    pattern = re.compile(
        rf"(?:"
        rf"({drugs})\s*(\d+\.?\d*)"        # drug → number
        rf"|"
        rf"(\d+\.?\d*)\s*({drugs})"        # number → drug
        rf")"
    )

    matches = list(pattern.finditer(text_clean))

    if not matches:
        return text

    dose_map = {}
    spans = []

    for m in matches:
        spans.append(m.span())

        if m.group(1) and m.group(2):
            drug = drug_map[m.group(1)]
            dose = m.group(2)
        elif m.group(3) and m.group(4):
            drug = drug_map[m.group(4)]
            dose = m.group(3)
        else:
            continue

        dose_map[drug] = dose

    # require at least carbidopa + levodopa
    if "carbidopa" in dose_map and "levodopa" in dose_map:
        carb = dose_map["carbidopa"]
        levo = dose_map["levodopa"]
        enta = dose_map.get("entacapone")

        if enta:
            normalized = f"carbidopa/entacapone/levodopa {carb}/{enta}/{levo}"
        else:
            normalized = f"carbidopa/levodopa {carb}/{levo}"

        # replace ONLY the span covering all matches
        start = min(s[0] for s in spans)
        end = max(s[1] for s in spans)

        return text[:start] + normalized + text[end:]

    return text




# -------------------------------
# MAIN PREPROCESS FUNCTION
# -------------------------------
def preprocess_medications(
    df: pd.DataFrame,
    input_col: str,
    output_col : str,
    replacement_path : str = None
) -> pd.DataFrame:
    """
    Full preprocessing pipeline:
    1. (Optional) Normalize text 

    Args:
        df: input DataFrame
        text_col: source column

    """
    df = df.drop_duplicates().copy()
    df.loc[:, output_col] = df[input_col].apply(normalize_text)
    replacements = load_replacements(replacement_path)

    df[output_col] = apply_replacements(df, output_col, replacements)
    df[output_col] = df[output_col].apply(normalize_combo)
    df["paren_text"] = df[output_col].str.findall(r"\(([^)]*)\)")    
    #df[output_col] = df[output_col].str.replace("/", " ", regex=False)

    return df