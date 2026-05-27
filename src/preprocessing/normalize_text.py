import pandas as pd
import re
import unicodedata




# -------------------------------
# BASIC TEXT NORMALIZATION
# -------------------------------
def _normalize_unicode_text(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text))


def _normalize_case(text: str) -> str:
    return text.lower()


def _normalize_symbols(text : str) -> str:
    text = re.sub(r'\\', '/', text) #capture double //
    text = text.replace('[', '(').replace(']', ')')
    text = re.sub(r'/+', '/', text) #capture double //
    text = re.sub(r'\s*/\s*', '/', text) # normalize ' / ' 
    text = re.sub(r'[–—−]', '-', text)
    return text


def _remove_invalid_characters(text : str) -> str:
    text = re.sub(r'[^a-z0-9\s\./\-%\(\)\+:,]',' ', text)
    return text


def _remove_spurious_periods(text: str) -> str:
    text = re.sub(r'(?<!\d)\.(?!\d)', '', text) # only keep decimals if between two numbers 
    return text


def _normalize_whitespace(text : str) -> str:
    text = re.sub(r'\s+', ' ', text)# collapse whitespace
    return text


def _remove_and(text:str) -> str:
    text = re.sub(r'\band\b','', text)
    return text




def normalize_text(text: str) -> str:
    if pd.isna(text):
    
        return text

    text = str(text)

    # unicode
    text = _normalize_unicode_text(text)

    # lowercase
    text = _normalize_case(text)

    # normalize symbols 
    text = _normalize_symbols(text)

    # normalize invalid characters
    text = _remove_invalid_characters(text)

    # remove
    text = _remove_spurious_periods(text)

    # whitespace
    text = _normalize_whitespace(text)

    #and
    text = _remove_and(text)

    return text



def apply_text_normalization(
    df: pd.DataFrame,
    raw_med_col :str, 
) -> pd.DataFrame:

    """
    Apply full text normalization pipeline to a dataframe column.
    """

    df = df.copy().drop_duplicates()

    df["clean_text"] = df[raw_med_col].apply(normalize_text)

    # -------------------------------
    # METRICS
    # -------------------------------
    total = len(df)
    non_null = df["clean_text"].notna().sum()

    print(
        f"Text Normalization Complete: "
        f"{non_null}/{total} rows processed "
        f"({non_null/total:.2%})"
    )

    return df