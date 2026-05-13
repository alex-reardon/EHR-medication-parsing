import re
import pandas as pd
import logging
from functools import lru_cache
from collections import defaultdict
import numpy as np
logger = logging.getLogger(__name__)


# -------------------------------
# BUILD FEQUENCY RULES/REPLACEMENTS
# -------------------------------
def load_frequency_rules(
    path: str,
    category: str = None,
    use_priority: bool = False,
    priority: int = None
):
    """
    Load frequency rules with optional category filtering
    and optional priority filtering.

    Parameters
    ----------
    path : str
        Path to CSV

    category : str or list, optional
        Filter by df['category']

    use_priority : bool, default False
        Whether to filter by priority

    priority : int, optional
        Which priority to keep (e.g., 1 or 2)
        Required if use_priority=True

    Returns
    -------
    pd.DataFrame
    """

    df = pd.read_csv(path)

    # -------------------------------
    # FILTER BY CATEGORY
    # -------------------------------
    if category is not None and "category" in df.columns:
        if isinstance(category, list):
            df = df[df["category"].isin(category)].copy()
        else:
            df = df[df["category"] == category].copy()

    # -------------------------------
    # FILTER BY PRIORITY
    # -------------------------------
    if use_priority:
        if "priority" not in df.columns:
            raise ValueError("CSV does not contain a 'priority' column")

        df = df[df["priority"] == priority].copy()

    # -------------------------------
    # CLEAN
    # -------------------------------
    df = df.dropna(subset=["raw"]).copy()
    df["raw"] = df["raw"].astype(str)

    return df.reset_index(drop=True)




def has_existing_value(val):
    if val is None:
        return False
    if isinstance(val, float) and pd.isna(val):
        return False
    if isinstance(val, list) and len(val) == 0:
        return False
    return True



def extract_weekday_frequency(text):
    if pd.isna(text):
        return None

    text = str(text).lower()

    patterns = [
        r"\bmon(?:day)?\b",
        r"\btue(?:s|sday)?\b",
        r"\bwed(?:nesday)?\b",
        r"\bthu(?:rs|rsday)?\b",
        r"\bfri(?:day)?\b",
        r"\bsat(?:urday)?\b",
        r"\bsun(?:day)?\b",
    ]

    found = set()

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            found.add(pattern)  # avoids double counting

    count = len(found)

    return f"{count}x/week" if count > 0 else None




def apply_weekday_frequency(df, input_col, output_col):
    mask = df[output_col].isna() # FIXME

    df.loc[mask, output_col] = df.loc[mask, input_col].apply(
        extract_weekday_frequency
    )

    return df



# -------------------------------
# CORE FAST EXTRACTOR (CACHED)
# -------------------------------
def build_extractor(compiled_rules):
    
    @lru_cache(maxsize=20000)
    def extract(text):
        if text is None or (isinstance(text, float) and pd.isna(text)):
            return None, text

        text = str(text).lower()
        cleaned = text
        matches = []

        for pattern, replacement in compiled_rules:
            found = pattern.findall(cleaned)

            if found:
                matches.append(replacement)
                cleaned = pattern.sub("", cleaned)
                

        if matches:
            matches = list(dict.fromkeys(matches))  # dedupe
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return matches, cleaned

        return None, text

    return extract



# -------------------------------
# FAST APPLY FREQUENCY EXTRACTION FUNCTION
# -------------------------------
def apply_frequency_extraction_fast(
    df: pd.DataFrame,
    input_col: str,
    freq_rules: pd.DataFrame,
    output_col: str = "freq_raw"
):
    df = df.copy()

    # ensure column exists
    if output_col not in df.columns:
        df[output_col] = None
    

    # compile rules once
    compiled_rules = [
        (re.compile(row["raw"]), row["replacement"])
        for _, row in freq_rules.iterrows()
    ]

    extractor = build_extractor(compiled_rules)

    def process_row(row):
        text = row[input_col]
        existing = row[output_col]

        new_matches, cleaned = extractor(text)

        # nothing new found → keep existing
        if not new_matches:
            return pd.Series([existing, text])

        # normalize existing → list
        if has_existing_value(existing):
            existing = existing if isinstance(existing, list) else [existing]
            combined = list(dict.fromkeys(existing + new_matches))
        else:
            combined = new_matches

        return pd.Series([combined, cleaned])
    
    df[[output_col, input_col]] = df.apply(process_row, axis=1)
    
    df[input_col] = df[input_col].str.replace(r"/\s*$", "", regex=True).str.strip()
    return df




def normalize_freq(val):
    if isinstance(val, list):
        val = val[0] if val else None

    if isinstance(val, str):
        try:
            return float(val)
        except:
            return val  # keep non-numeric like "3x/week"

    return val



def build_timing_pattern_from_df(df):
    grouped = df_to_grouped_dict(df)

    patterns = {}

    for label, terms in grouped.items():
        processed_terms = []

        for term in terms:
            term = str(term).lower().strip()
            
            # remove any existing \b to prevent double wrapping
            term = term.replace(r"\b", "")

            processed_terms.append(term)

        pattern_str = r"\b(?:{})\b".format("|".join(processed_terms))

        patterns[label] = re.compile(pattern_str)

    return patterns



def extract_timing_frequency(text: str, timing_patterns: dict) -> int:
    if pd.isna(text):
        return None

    text = str(text).lower()

    matches = set()

    for label, pattern in timing_patterns.items():
        if pattern.search(text):
            matches.add(label)

    if len(matches) == 0:
        return None

    return len(matches)



def apply_timing_extraction(df, input_col, output_col, timing_patterns):
    df[output_col] = df[input_col].apply(
        lambda x: extract_timing_frequency(x, timing_patterns)
    )
    return df


def clean_numeric_freq(numeric_freq):
    
    # -------------------------------
    # CASE 1: list / array input
    # -------------------------------
    if isinstance(numeric_freq, (list, tuple, np.ndarray)):
        if len(numeric_freq) == 0:
            return None

        cleaned = []

        for val in numeric_freq:
            if pd.isna(val):
                continue
            try:
                cleaned.append(float(val))
            except:
                continue

        if not cleaned:
            return None

        # deduplicate (1.0 vs 1)
        cleaned = list(set(cleaned))

        return max(cleaned)  # or cleaned[0]

    # -------------------------------
    # CASE 2: scalar input
    # -------------------------------
    if pd.isna(numeric_freq):
        return None

    try:
        return float(numeric_freq)
    except:
        return None
    

    
def resolve_frequency(numeric_freq, timing_freq):
    
    # numeric always wins
    if pd.notna(numeric_freq):
        return numeric_freq

    # fallback to timing
    if pd.notna(timing_freq):
        return timing_freq

    return None






def remove_timing_terms(text, timing_patterns):
    if pd.isna(text):
        return text

    text = str(text).lower()

    for pattern in timing_patterns.values():
        text = pattern.sub("", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text



def df_to_grouped_dict(df, key_col="replacement", value_col="raw"):
    grouped = defaultdict(list)

    for _, row in df.iterrows():
        grouped[row[key_col]].append(str(row[value_col]))

    return dict(grouped)



def remove_prn_terms(text, prn_pattern):
    if pd.isna(text):
        return text

    text = str(text).lower()
    text = prn_pattern.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text





def extract_prn_flag(text, prn_pattern):
    if pd.isna(text):
        return False

    text = str(text).lower()
    return bool(prn_pattern.search(text))




def apply_prn_extraction(df, input_col, output_col, prn_pattern):
    df[output_col] = df[input_col].apply(
        lambda x: extract_prn_flag(x, prn_pattern)
    )
    return df



def build_pattern(df):
    terms = (
        df["raw"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.strip()
        .unique()
    )

    # 🔥 sort longest → shortest
    terms = sorted(terms, key=len, reverse=True)

    pattern = r"(?:{})".format("|".join(terms))
    return re.compile(pattern, flags=re.IGNORECASE)



def run_frequency_extraction_layered(
    df: pd.DataFrame,
    input_col: str,
    clean_med_name = None, 
    output_col: str = "freq_raw",
    path: str = None
) -> pd.DataFrame:

    df = df.copy()


    prn_df = load_frequency_rules(path, category = "prn", use_priority=False)
    prn_patterns = build_pattern(prn_df)
    print(prn_patterns)

    # -------------------------------
    # EXTRACT PRN
    # -------------------------------
    df = apply_prn_extraction(
        df,
        input_col=input_col, 
        output_col="is_prn",
        prn_pattern=prn_patterns
    )

    # -------------------------------
    # REMOVE PRN FROM TEXT
    # -------------------------------
    df[input_col] = df[input_col].apply(
        lambda x: remove_prn_terms(x, prn_patterns)
    )


    # -------------------------------
    # PASS 1: strict
    # -------------------------------
    rules_main = load_frequency_rules(path, category = "frequency", use_priority = True, priority=1)

    df = apply_frequency_extraction_fast(
        df=df,
        input_col=input_col,
        freq_rules=rules_main,
        output_col=output_col
    )

    # -------------------------------
    # PASS 2: fallback
    # -------------------------------
    rules_fallback = load_frequency_rules(path, category = "frequency", use_priority = True, priority=2)

    df = apply_frequency_extraction_fast(
        df=df,
        input_col=input_col,
        freq_rules=rules_fallback,
        output_col=output_col
    )

    # -------------------------------
    # WEEKDAY fallback
    # -------------------------------
    df = apply_weekday_frequency(df, input_col, output_col)

    df["freq_raw"] = df[output_col].apply(clean_numeric_freq)



   # PASS 3: timing extraction
    # -------------------------------
    timing_df = load_frequency_rules(path, category = "time_of_day", use_priority = False)
    timing_patterns = build_timing_pattern_from_df(timing_df)

    df = apply_timing_extraction(
        df,
        input_col=input_col,
        output_col="frequency_timing",
        timing_patterns=timing_patterns
    )

    df[clean_med_name] = df[input_col].apply(
    lambda x: remove_timing_terms(x, timing_patterns)
)


    # -------------------------------
    # PASS 4: resolve final frequency
    # -------------------------------
    df["freq_raw"] = df.apply(
        lambda row: resolve_frequency(
            row["freq_raw"],
            row["frequency_timing"]
        ),
        axis=1
    )


    # NORMALIZE 
    df["frequency_per_day"] = df["freq_raw"].apply(normalize_freq)
    df[clean_med_name] = df[clean_med_name].str.replace(r'\s*/\s*', '/', regex=True)
    # -------------------------------
    # METRICS
    # -------------------------------
    mapped = df["frequency_per_day"].notna().sum()
    print(f"Frequency Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df
  