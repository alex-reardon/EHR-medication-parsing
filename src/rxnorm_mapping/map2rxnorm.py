import pandas as pd
from rapidfuzz import process, fuzz
import re


# -------------------------------
# BUILD LOOKUP
# -------------------------------
def build_rxnorm_lookup(rrf_path: str):

    cols = [
        "rxcui", "lat", "ts", "lui", "stt", "sui", "ispref",
        "rxaui", "saui", "scui", "sdui", "sab", "tty",
        "code", "str", "srl", "suppress", "cvf", "empty"
    ]

    rx = pd.read_csv(rrf_path, sep="|", header=None, names=cols, dtype=str)

    rx = rx[(rx["lat"] == "ENG") & (rx["suppress"] == "N")]
    rx = rx[rx["tty"].isin(["IN", "MIN", "BN"])].copy()

    rx["str_lower"] = rx["str"].str.lower().str.strip()

    lookup = rx.drop_duplicates("str_lower").set_index("str_lower")[["rxcui", "tty"]]

    # MIN lookup by RXCUI
    min_lookup = (
        rx[rx["tty"] == "MIN"]
        .drop_duplicates("rxcui")
        .set_index("rxcui")["str_lower"]
        .to_dict()
    )

    rx_names = lookup.index.tolist()

    return rx_names, lookup, min_lookup


# -------------------------------
# PRIORITY FUNCTION
# -------------------------------
def better(new, best):
    priority = {"MIN": 0, "IN": 1, "BN": 2}

    if best[3] == -1:
        return True

    p_new = priority.get(new[2], 99)
    p_best = priority.get(best[2], 99)

    return (p_new < p_best) or (p_new == p_best and new[3] > best[3])


def normalize_term(term):
    if not isinstance(term, str):
        return term

    term = term.lower()
    term = term.replace("/", " ")   # 🔥 CRITICAL FIX
    term = term.replace("-", " ")
    term = re.sub(r"\s+", " ", term).strip()

    return term

# -------------------------------
# MATCH FUNCTION (handles lists)
# -------------------------------
def match_rxnorm(term, rx_names, lookup, threshold=85):

    # -------------------------------
    # CASE 1: list input
    # -------------------------------
    if isinstance(term, (list, tuple)):
        best = (None, None, None, -1)

        for t in term:
            if not isinstance(t, str):
                continue

            match, rxcui, tty, score = match_rxnorm(t, rx_names, lookup, threshold)

            if score is not None and better((match, rxcui, tty, score), best):
                best = (match, rxcui, tty, score)

        return best if best[3] >= threshold else (None, None, None, None)

    # -------------------------------
    # CASE 2: normal string
    # -------------------------------
    if not isinstance(term, str):
        return None, None, None, None

    match, score, _ = process.extractOne(
        normalize_term(term),
        rx_names,
        scorer=fuzz.token_sort_ratio
    )

    if score >= threshold:
        row = lookup.loc[match]

        # handle duplicate index
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        return match, row["rxcui"], row["tty"], score

    return None, None, None, None


# -------------------------------
# APPLY FUNCTION (handles lists safely)
# -------------------------------
def apply_rxnorm_mapping(
    df: pd.DataFrame,
    rrf_path: str,
    out : str,
    threshold: int = 85,
    col_str_name: str = None
) -> pd.DataFrame:

    rx_names, lookup, min_lookup = build_rxnorm_lookup(rrf_path)

    # -------------------------------
    # convert lists → tuples for hashing
    # -------------------------------
    def safe_key(x):
        return tuple(x) if isinstance(x, list) else x

    unique_vals = df["clean_text"].dropna().apply(safe_key).unique()

    # -------------------------------
    # build mapping
    # -------------------------------
    mapping = {
        val: match_rxnorm(val, rx_names, lookup, threshold)
        for val in unique_vals
    }

    # -------------------------------
    # apply mapping
    # -------------------------------
    df["rxnorm_match" + out] = df["clean_text"].map(lambda x: mapping.get(safe_key(x), (None, None, None, None))[0])
    df["rxcui" + out] = df["clean_text"].map(lambda x: mapping.get(safe_key(x), (None, None, None, None))[1])
    df["score" + out] = df["clean_text"].map(lambda x: mapping.get(safe_key(x), (None, None, None, None))[2])
    df["tty" + out] = df["clean_text"].map(lambda x: mapping.get(safe_key(x), (None, None, None, None))[3])

    # -------------------------------
    # add MIN concept if tty is BN/IN
    # -------------------------------
    def get_min_match(row):

        tty = row["tty" + out]
        rxcui = row["rxcui" + out]

        if tty in ["BN", "IN"]:

            return min_lookup.get(rxcui)

        return row["rxnorm_match" + out]

    df["MIN"] = df.apply(get_min_match, axis=1)

    
   # -------------------------------
    # ALWAYS remove parenthetical text
    # -------------------------------
    if "clean_text" == "paren_text" and col_str_name is not None:

        def clean_row(row):

            text = row[col_str_name + 'no_time']
            paren = row['paren_text']

            if not isinstance(text, str):
                return text

            # -------------------------------
            # CASE 1: list/tuple
            # -------------------------------
            if isinstance(paren, (list, tuple)):

                for p in paren:

                    if isinstance(p, str):

                        text = text.replace(f"({p})", "")

                return text

            # -------------------------------
            # CASE 2: single string
            # -------------------------------
            if isinstance(paren, str):

                return text.replace(f"({paren})", "")

            return text

        df[col_str_name + 'no_time'] = df.apply(
            clean_row,
            axis=1
        )

        # -------------------------------
        # cleanup
        # -------------------------------
        df[col_str_name + 'no_time'] = (
            df[col_str_name + 'no_time']
            .str.replace(r"[()]", "", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    # -------------------------------
    # metrics
    # -------------------------------
    mapped = df["rxnorm_match" + out].notna().sum()
    print(f"RXNorm Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df