import pandas as pd
from rapidfuzz import process, fuzz


# -------------------------------
# BUILD LOOKUP
# -------------------------------
def _build_rxnorm_lookup_table(rrf_path: str):

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
def _compare_rxnorm_matches(candidate, current_best):
    priority = {"MIN": 0, "IN": 1, "BN": 2}

    if current_best[3] == -1:
        return True

    p_new = priority.get(candidate[2], 99)
    p_best = priority.get(current_best[2], 99)

    return (p_new < p_best) or (p_new == p_best and candidate[3] > current_best[3])




# -------------------------------
# MATCH FUNCTION (handles lists)
# -------------------------------
def _match_rxnorm_term(input_term, candidate_terms, rxnorm_lookup_table, threshold=85):

    # -------------------------------
    # CASE 1: list input
    # -------------------------------
    if isinstance(input_term, (list, tuple)):
        best_match = (None, None, None, -1)

        for sub_term in input_term:
            if not isinstance(sub_term, str):
                continue

            matched_term, rxnorm_id, tty, similarity_score = _match_rxnorm_term(sub_term, candidate_terms, rxnorm_lookup_table, threshold)
            candidate_match = (matched_term, rxnorm_id, tty, similarity_score)

            if similarity_score is not None and _compare_rxnorm_matches(candidate_match, best_match):
                best_match = candidate_match

        return best_match if best_match[3] >= threshold else (None, None, None, None)

    # -------------------------------
    # CASE 2: normal string
    # -------------------------------
    if not isinstance(input_term, str):
        return None, None, None, None

    matched_term, similarity_score, _ignored_index = process.extractOne(
        input_term,
        candidate_terms,
        scorer=fuzz.token_sort_ratio
    )

    if similarity_score >= threshold:
        rxnorm_row = rxnorm_lookup_table.loc[matched_term]

        # handle duplicate index
        if isinstance(rxnorm_row, pd.DataFrame):
            rxnorm_row = rxnorm_row.iloc[0]

        return matched_term, rxnorm_row["rxcui"], rxnorm_row["tty"], similarity_score

    return None, None, None, None


# -------------------------------
# APPLY FUNCTION (handles lists safely)
# -------------------------------
def apply_rxnorm_mapping(
    df: pd.DataFrame,
    input_col : str, 
    rxnorm_rrf_path: str,
    suffix : str,
    match_threshold: int = 85,
    base_text_col: str = None
) -> pd.DataFrame:

    rxnorm_candidate_terms, rxnorm_lookup_table, min_concept_lookup = _build_rxnorm_lookup_table(rxnorm_rrf_path) # FIXME remove rxnorm_lookup table

    # -------------------------------
    # convert lists → tuples for hashing
    # -------------------------------
    def to_hashable_key(value):
        return tuple(value) if isinstance(value, list) else value

    unique_inputs = df[input_col].dropna().apply(to_hashable_key).unique()

    # -------------------------------
    # build mapping
    # -------------------------------
    rxnorm_match_cache = {
        val: _match_rxnorm_term(val, rxnorm_candidate_terms, rxnorm_lookup_table, match_threshold)
        for val in unique_inputs
    }

    # -------------------------------
    # apply mapping
    # -------------------------------
    df["rxnorm_match" + suffix] = df[input_col].map(lambda input_value: rxnorm_match_cache.get(to_hashable_key(input_value), (None, None, None, None))[0])
    df["rxcui" + suffix] = df[input_col].map(lambda input_value: rxnorm_match_cache.get(to_hashable_key(input_value), (None, None, None, None))[1])
    df["score" + suffix] = df[input_col].map(lambda input_value: rxnorm_match_cache.get(to_hashable_key(input_value), (None, None, None, None))[3])
    df["tty" + suffix] = df[input_col].map(lambda input_value: rxnorm_match_cache.get(to_hashable_key(input_value), (None, None, None, None))[2])

    # -------------------------------
    # add MIN concept if tty is BN/IN
    # -------------------------------
    def resolve_min_concept(rxnorm_row):

        tty = rxnorm_row["tty" + suffix]
        rxcui = rxnorm_row["rxcui" + suffix]

        if tty in ["BN", "IN"]:

            return min_concept_lookup.get(rxcui)

        return rxnorm_row["rxnorm_match" + suffix]

    df["MIN" + suffix] = df.apply(resolve_min_concept, axis=1)


    # -------------------------------
    # metrics
    # -------------------------------
    mapped = df["rxnorm_match" + suffix].notna().sum()
    print(f"RXNorm Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df