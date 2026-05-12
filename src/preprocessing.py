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

    text = text.lower()

    # -----------------------------------------
    # normalize separators/spaces
    # -----------------------------------------
    text = re.sub(r'\s*/\s*', '/', text)
    text = re.sub(r'\s*-\s*', '-', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # ==========================================================
    # CASE 1
    # levodopa carbidopa 100/25mg
    # levodopa/carbidopa 100/25
    #
    # -> carbidopa/levodopa 25/100
    # ==========================================================
    pattern_reverse_pair = re.compile(
        r'''
        levodopa
        \s*
        (?:/|\s+)
        \s*
        carbidopa
        \s+
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*(?:mg)?
        ''',
        flags=re.I | re.X
    )

    def reverse_pair_repl(m):

        levo = m.group(1)
        carb = m.group(2)

        return f"carbidopa/levodopa {carb}/{levo}"

    text = pattern_reverse_pair.sub(reverse_pair_repl, text)

    # ==========================================================
    # CASE 2
    # carbidopa/levodopa/entacapone 25/100/200
    #
    # -> carbidopa/entacapone/levodopa 25/200/100
    # ==========================================================
    pattern_triple = re.compile(
        r'''
        carbidopa
        \s*[/\-]\s*
        levodopa
        \s*[/\-]\s*
        entacapone
        \s+
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*(?:mg)?
        ''',
        flags=re.I | re.X
    )

    def reorder_triple(m):

        carb = m.group(1)
        levo = m.group(2)
        enta = m.group(3)

        return (
            f"carbidopa/entacapone/levodopa "
            f"{carb}/{enta}/{levo}"
        )

    text = pattern_triple.sub(reorder_triple, text)

    # ==========================================================
    # CASE 3
    # levodopa/carbidopa/entacapone 100/25/200
    # levodopa carbidopa entacapone 100/25/200
    #
    # -> carbidopa/entacapone/levodopa 25/200/100
    # ==========================================================
    pattern_reverse_triple = re.compile(
        r'''
        levodopa
        \s*
        (?:/|\s+)
        \s*
        carbidopa
        \s*
        (?:/|\s+)
        \s*
        entacapone
        \s+
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*(?:mg)?
        ''',
        flags=re.I | re.X
    )

    def reverse_triple_repl(m):

        levo = m.group(1)
        carb = m.group(2)
        enta = m.group(3)

        return (
            f"carbidopa/entacapone/levodopa "
            f"{carb}/{enta}/{levo}"
        )

    text = pattern_reverse_triple.sub(reverse_triple_repl, text)

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