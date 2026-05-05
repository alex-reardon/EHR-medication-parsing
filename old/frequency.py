import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def apply_frequency_extraction(df: pd.DataFrame, input_col: str, output_col: str = "freq", path: str = None):
    """
    Extract frequency terms from a column using replacement rules.

    Args:
        path: path to normalization_dictionary.csv
        df: input dataframe
        input_col: column to process
        output_col: name of frequency column (default = 'freq')

    Returns:
        df with:
            - new freq column
            - cleaned input_col (frequency removed)
    """

    # -------------------------------
    # LOAD RULES
    # -------------------------------
    rules_df = pd.read_csv(path)
    freq_rules = rules_df[rules_df["category"] == "freq"]

    # sort longest first (prevents partial matches)
    freq_rules = freq_rules.sort_values(
        by="replacement",
        key=lambda x: x.str.len(),
        ascending=False
    )

    # build regex pattern
    pattern = r'\b(?:' + '|'.join(map(re.escape, freq_rules["replacement"])) + r')\b'

    # -------------------------------
    # ROW FUNCTION
    # -------------------------------
    def extract_freq(text):
        if pd.isna(text):
            return pd.Series([None, text])

        text = str(text).lower()

        # find + deduplicate
        matches = list(dict.fromkeys(re.findall(pattern, text)))

        if matches:
            cleaned = re.sub(pattern, '', text)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            return pd.Series([matches, cleaned])

        return pd.Series([None, text])

    # -------------------------------
    # APPLY
    # -------------------------------
    df[[output_col, input_col]] = df[input_col].apply(extract_freq)

    logger.info(f"Frequency extraction applied to column: {input_col}")

    return df












'''
########################################### delete below?
# -------------------------------
# CORE FUNCTION
# -------------------------------
def extract_frequency(text: str) -> dict:
    """
    Extract medication amount and frequency from free text.

    Returns:
        {
            "amount": int or None,
            "frequency": int or None,
            "med_no_frequency": str
        }
    """

    if pd.isna(text):
        return {
            "amount": None,
            "frequency": None,
            "med_no_frequency": text
        }

    text = str(text).lower()
    clean_text = text

    amount = None
    frequency = None

    # -------------------------------
    # pattern 1: "2 tabs tid"
    # -------------------------------
    pattern = r'(\d+)\s*(pill|pills|tab|tabs|tablet|tablets)\s*(tid|bid|qid|qd)'
    match = re.search(pattern, text)

    if match:
        amount = int(match.group(1))

        freq_map = {
            "tid": 3,
            "bid": 2,
            "qid": 4,
            "qd": 1
        }

        frequency = freq_map.get(match.group(3))
        clean_text = re.sub(pattern, '', clean_text)

    # -------------------------------
    # pattern 2: "x 8"
    # -------------------------------
    elif re.search(r'\bx\s*(\d+)', text):
        match = re.search(r'\bx\s*(\d+)', text)
        amount = 1
        frequency = int(match.group(1))
        clean_text = re.sub(r'\bx\s*\d+', '', clean_text)

    # -------------------------------
    # pattern 3: "8 tabs daily"
    # -------------------------------
    elif re.search(r'(\d+)\s*(tabs?|tablets?)?\s*(per\s*)?(day|daily)', text):
        match = re.search(r'(\d+)\s*(tabs?|tablets?)?\s*(per\s*)?(day|daily)', text)
        amount = int(match.group(1))
        frequency = 1
        clean_text = re.sub(r'(\d+)\s*(tabs?|tablets?)?\s*(per\s*)?(day|daily)', '', clean_text)

    # -------------------------------
    # pattern 4: "24 hours"
    # -------------------------------
    elif re.search(r'(\d+)\s*hours?', text):
        match = re.search(r'(\d+)\s*hours?', text)
        hours = int(match.group(1))

        if hours == 24:
            amount = 1
            frequency = 1
            clean_text = re.sub(r'\d+\s*hours?', '', clean_text)

    # -------------------------------
    # standalone frequency terms
    # -------------------------------
    if frequency is None:

        if re.search(r'\btid\b', text):
            amount = amount or 1
            frequency = 3
            clean_text = re.sub(r'\btid\b', '', clean_text)

        elif re.search(r'\bbid\b', text):
            amount = amount or 1
            frequency = 2
            clean_text = re.sub(r'\bbid\b', '', clean_text)

        elif re.search(r'\bqid\b', text):
            amount = amount or 1
            frequency = 4
            clean_text = re.sub(r'\bqid\b', '', clean_text)

        elif re.search(r'\bqd\b|\bdaily\b', text):
            amount = amount or 1
            frequency = 1
            clean_text = re.sub(r'\bqd\b|\bdaily\b', '', clean_text)

    # -------------------------------
    # cleanup
    # -------------------------------
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return {
        "amount": amount,
        "frequency": frequency,
        "med_no_frequency" : clean_text
    }


# -------------------------------
# APPLY TO DATAFRAME
# -------------------------------
def apply_frequency_extraction(
    df: pd.DataFrame,
    input_col: str, 
    output_col : str, 
) -> pd.DataFrame:
    """
    Apply frequency extraction to a dataframe column.
    """

    logger.info("Starting frequency extraction...")

    freq_df = df[input_col].apply(extract_frequency).apply(pd.Series)

    # rename outputs
    freq_df = freq_df.rename(columns={
        "med_no_frequency": output_col
    })

    df = pd.concat([df, freq_df], axis=1)

    logger.info("Frequency extraction complete")

    return df
'''
