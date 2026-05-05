import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

#FIXME - change "release"

# -------------------------------
# LOAD TERMS FROM CSV
# -------------------------------

def load_release_pattern(path: str, category) -> str:
    """
    Load release dictionary and build unit regex pattern
    """

    rules_df = pd.read_csv(path)
    release_rules = rules_df[rules_df["category"] == category ]

    # clean + sort longest first
    release_values = (
        release_rules["replacement"]
        .dropna()
        .astype(str)
        .str.lower()
        .sort_values(key=lambda x: x.str.len(), ascending=False)
        .unique()
        .tolist()
    )

    # build regex
    release_pattern = r'\b(?:' + '|'.join(map(re.escape, release_values)) + r')\b'
    return release_pattern



# -------------------------------
# CORE FUNCTION
# -------------------------------
def extract_release(text: str, pattern : str) -> dict:

    if pd.isna(text):
        return pd.Series([None, text])


    text = str(text).lower()
    matches = list(dict.fromkeys(re.findall(pattern, text)))

    if matches:
        cleaned = re.sub(pattern, '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return pd.Series([matches, cleaned])

    return pd.Series([None, text])


def clean_text_whitespace(text: str) -> str:
    """Standardize spacing and strip trailing slashes."""
    if not isinstance(text, str): return text
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"/\s*$", "", text)


# -------------------------------
# APPLY TO DATAFRAME
# -------------------------------
def apply_category_extraction(
    df: pd.DataFrame,
    input_col: str ,
    output_col : str,
    category : str, 
    data_path: str = None
) -> pd.DataFrame:

    logger.info("Loading category term lists...")
    release_pattern = load_release_pattern(data_path, category)


    df[[category, output_col]] = df[input_col].apply(
        lambda x: extract_release(x, release_pattern)
    )

    df[output_col] = df[output_col].apply(clean_text_whitespace)

    # Metrics
    mapped = df[category].notna().sum()
    print(f"{category} Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df