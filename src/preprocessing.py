import pandas as pd
import re
import unicodedata


# -------------------------------
# NORMALIZE TEXT
# -------------------------------
def normalize_text(text: str) -> str:
    if pd.isna(text):
        return text

    text = unicodedata.normalize("NFKC", str(text))
    text = str(text).lower()
    text = re.sub(r'\\', '/', text) #capture double //
    text = text.replace('[', '(').replace(']', ')')
    text = re.sub(r'[^a-z0-9\s\./\-%\(\)\+:,]',' ', text)
    text = re.sub(r'(?<!\d)\.(?!\d)', '', text) # only keep decimals if between two numbers 
    text = re.sub(r'\s+', ' ', text)# collapse whitespace
    text = re.sub(r'/+', '/', text) #capture double //
    text = re.sub(r'\s*/\s*', '/', text) # normalize ' / ' 
    text = re.sub(r'[–—−]', '-', text)
    return text



# -------------------------------
# MAIN PREPROCESS FUNCTION
# -------------------------------
def preprocess_medications(
    df: pd.DataFrame,
    raw_med_col: str
) -> pd.DataFrame:
    """
    Full preprocessing pipeline:
    1. (Optional) Normalize text 

    Args:
        df: input DataFrame
        text_col: source column

    """
    df = df.drop_duplicates().copy()
    df.loc[:, "clean_text"] = df[raw_med_col].apply(normalize_text)

    return df