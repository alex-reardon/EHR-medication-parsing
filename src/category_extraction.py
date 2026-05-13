import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# -------------------------------
# LOAD TERMS FROM CSV
# -------------------------------

def load_category_pattern(path: str, category) -> str:
    """
    Load category dictionary and build unit regex pattern
    """

    rules_df = pd.read_csv(path)
    category_rules = rules_df[rules_df["category"] == category ]

    # clean + sort longest first
    category_values = (
        category_rules["replacement"]
        .dropna()
        .astype(str)
        .str.lower()
        .sort_values(key=lambda x: x.str.len(), ascending=False)
        .unique()
        .tolist()
    )

    if not category_values:
        raise ValueError(f"No terms found for category: {category}")
    
    # build regex
    category_pattern = r'\b(?:' + '|'.join(map(re.escape, category_values)) + r')\b'
    return category_pattern



# -------------------------------
# CORE FUNCTION
# -------------------------------
def extract_category(text: str, pattern: str) -> pd.Series:
    if pd.isna(text):
        return pd.Series([None, text])

    text = str(text).lower()
    matches = re.findall(pattern, text)

    if matches:
        # flatten if regex ever returns tuples
        cleaned_matches = []
        for m in matches:
            if isinstance(m, tuple):
                cleaned_matches.extend([x for x in m if x])
            else:
                cleaned_matches.append(m)

        matches = list(dict.fromkeys(cleaned_matches))

        # remove matched terms + surrounding whitespace
        cleaned = re.sub(pattern, " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return pd.Series([matches, cleaned])

    return pd.Series([None, text])



def clean_text_whitespace(text: str) -> str:
    """Standardize spacing and strip trailing slashes."""
    if not isinstance(text, str): return text
    text = re.sub(r"/\s*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r'[^a-zA-Z0-9]+$', '', text)
    return text


# -------------------------------
# APPLY TO DATAFRAME
# -------------------------------
def apply_category_extraction(
    df: pd.DataFrame,
    category : str, 
    data_path: str = None
) -> pd.DataFrame:

    logger.info("Loading category term lists...")
    category_pattern = load_category_pattern(data_path, category)


    df[[category, "clean_text"]] = df["clean_text"].apply(
        lambda x: extract_category(x, category_pattern))

    df["clean_text"] = df["clean_text"].apply(clean_text_whitespace)
    df["clean_text"] = df["clean_text"].str.replace(r'\s*/\s*', '/', regex=True)

    # Metrics
    mapped = df[category].notna().sum()
    print(f"{category} Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df