import re
import pandas as pd
from rapidfuzz import process, fuzz


def _build_rxnorm_lookup_table(rrf_path: str, rxnrel_path: str):

    cols = [
        "rxcui", "lat", "ts", "lui", "stt", "sui", "ispref",
        "rxaui", "saui", "scui", "sdui", "sab", "tty",
        "code", "str", "srl", "suppress", "cvf", "empty"
    ]

    rx = pd.read_csv(rrf_path, sep="|", header=None, names=cols, dtype=str)
    rx = rx[(rx["lat"] == "ENG") & (rx["suppress"] == "N")]
    rx["str_lower"] = rx["str"].str.lower().str.strip()

    rx_all = rx[rx["tty"].isin(["IN", "MIN", "BN", "SBD", "SCD", "SBDF", "SBDC"])].copy()

    rx_match = rx_all[rx_all["tty"].isin(["IN", "MIN", "BN", "SBDF", "SCD", "SBD", "SBCD"])]
    lookup = rx_match.drop_duplicates("str_lower").set_index("str_lower")[["rxcui", "tty"]]
    rx_names = lookup.index.tolist()

    # --------------------------------------------------
    # Load RXNREL
    # --------------------------------------------------
    rel_cols = [
        "rxcui1", "rxaui1", "stype1",
        "rel", "rxcui2", "rxaui2", "stype2",
        "rela", "rui", "srui",
        "sab", "sl", "dir",
        "rg", "suppress", "cvf", "empty"
    ]
    rel = pd.read_csv(rxnrel_path, sep="|", header=None, names=rel_cols, dtype=str)
    rel = rel[(rel["sab"] == "RXNORM") & (rel["suppress"] == "N")]

    min_rxcuis = set(rx_all[rx_all["tty"] == "MIN"]["rxcui"].unique())
    scd_rxcuis = set(rx_all[rx_all["tty"] == "SCD"]["rxcui"].unique())
    sbd_rxcuis = set(rx_all[rx_all["tty"] == "SBD"]["rxcui"].unique())
    in_rxcuis  = set(rx_all[rx_all["tty"] == "IN"]["rxcui"].unique())

    min_rxcui_to_str = (
        rx_all[rx_all["tty"] == "MIN"]
        .drop_duplicates("rxcui")
        .set_index("rxcui")["str_lower"]
        .to_dict()
    )

    # --------------------------------------------------
    # RXNREL chain: SBD → SCD → MIN
    # --------------------------------------------------
    sbd_to_scd_forward = (
        rel[
            (rel["rela"] == "tradename_of") &
            rel["rxcui1"].isin(sbd_rxcuis) &
            rel["rxcui2"].isin(scd_rxcuis)
        ][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui1": "sbd", "rxcui2": "scd"})
    )
    sbd_to_scd_reverse = (
        rel[
            (rel["rela"] == "has_tradename") &
            rel["rxcui2"].isin(sbd_rxcuis) &
            rel["rxcui1"].isin(scd_rxcuis)
        ][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui2": "sbd", "rxcui1": "scd"})
    )
    sbd_scd_map = pd.concat([sbd_to_scd_forward, sbd_to_scd_reverse]).drop_duplicates()

    scd_to_min = (
        rel[
            (rel["rela"] == "has_ingredient") &
            rel["rxcui1"].isin(scd_rxcuis) &
            rel["rxcui2"].isin(min_rxcuis)
        ][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui1": "scd", "rxcui2": "min_rxcui"})
    )

    sbd_to_min = (
        sbd_scd_map
        .merge(scd_to_min, on="scd", how="inner")
        [["sbd", "min_rxcui"]]
        .drop_duplicates("sbd")
        .assign(min_str=lambda d: d["min_rxcui"].map(min_rxcui_to_str))
        .dropna(subset=["min_str"])
        .set_index("sbd")["min_str"]
        .to_dict()
    )

    # --------------------------------------------------
    # BN → SBDF via bracket matching
    # e.g. BN "stalevo" → SBDF "carbidopa / entacapone / levodopa oral tablet [stalevo]"
    # Strip bracket + dose form → MIN string
    # --------------------------------------------------
    DOSE_FORM_PATTERN = re.compile(
        r'\b(oral|tablet|capsule|solution|suspension|injection|patch|'
        r'cream|gel|ointment|powder|granule|syrup|drops?|spray|inhaler|'
        r'extended|immediate|delayed|modified|release|film|coated|'
        r'chewable|effervescent|sublingual|buccal|topical|ophthalmic|'
        r'otic|nasal|rectal|vaginal|transdermal|product|pill)\b',
        re.IGNORECASE
    )
    BRACKET_PATTERN = re.compile(r'\[.*?\]')

    def _sbdf_str_to_min(sbdf_str: str) -> str | None:
        s = BRACKET_PATTERN.sub("", sbdf_str).strip()
        s = DOSE_FORM_PATTERN.sub("", s).strip()
        parts = [p.strip() for p in re.split(r'[/,]', s) if p.strip()]
        ingredient_key = " / ".join(sorted(parts))
        if ingredient_key in min_rxcui_to_str.values():
            return ingredient_key
        min_strings = list(min_rxcui_to_str.values())
        if not min_strings:
            return None
        match, score, _ = process.extractOne(
            ingredient_key, min_strings, scorer=fuzz.token_sort_ratio
        )
        return match if score >= 85 else None

    bn_rows = rx_all[
        (rx_all["tty"] == "BN") & (rx_all["sab"] == "RXNORM")
    ][["rxcui", "str_lower"]].drop_duplicates("rxcui")

    sbdf_rows = rx_all[
        (rx_all["tty"] == "SBDF") & (rx_all["sab"] == "RXNORM")
    ][["rxcui", "str_lower"]].drop_duplicates("rxcui")

    # BN rxcui → SBDF str  (raw, before stripping)
    bn_to_sbdf_str = {}
    # BN rxcui → MIN str   (after stripping SBDF)
    bn_to_min_via_sbdf = {}

    for _, bn_row in bn_rows.iterrows():

        bn = str(bn_row["str_lower"]).strip()
        pattern = r"\[\s*" + re.escape(bn) + r"\s*\]"
        matches = sbdf_rows[sbdf_rows["str_lower"].str.contains(pattern, regex=True, na=False)]
        if not matches.empty:
            sbdf_str = matches.iloc[0]["str_lower"]
            bn_to_sbdf_str[bn_row["rxcui"]] = sbdf_str
            min_str = _sbdf_str_to_min(sbdf_str)
            if min_str:
                bn_to_min_via_sbdf[bn_row["rxcui"]] = min_str

    # --------------------------------------------------
    # BN → MIN via RXNREL (BN→SBD→SCD→MIN) for drugs that have edges
    # --------------------------------------------------
    bn_to_sbd_rel = (
        rel[rel["rela"] == "tradename_of"][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui1": "sbd", "rxcui2": "bn"})
    )
    bn_sbd_scd = (
        bn_to_sbd_rel
        .merge(sbd_scd_map, on="sbd", how="inner")
        .merge(scd_to_min, on="scd", how="inner")
    )

    # --------------------------------------------------
    # Final min_lookup
    # --------------------------------------------------
    min_lookup = {}

    # BN via RXNREL
    for _, row in bn_sbd_scd.drop_duplicates("bn").iterrows():
        min_str = min_rxcui_to_str.get(row["min_rxcui"])
        if min_str:
            min_lookup[row["bn"]] = min_str

    # BN via SBDF bracket fallback
    for rxcui, min_str in bn_to_min_via_sbdf.items():
        min_lookup.setdefault(rxcui, min_str)

    # SBD → MIN
    for rxcui, min_str in sbd_to_min.items():
        min_lookup.setdefault(rxcui, min_str)

    # IN → MIN
    in_to_min = (
        rel[
            (rel["rela"] == "has_ingredient") &
            rel["rxcui1"].isin(in_rxcuis) &
            rel["rxcui2"].isin(min_rxcuis)
        ][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui1": "in_rxcui", "rxcui2": "min_rxcui"})
        .drop_duplicates("in_rxcui")
    )
    for _, row in in_to_min.iterrows():
        min_lookup.setdefault(row["in_rxcui"], min_rxcui_to_str.get(row["min_rxcui"]))

    # MIN → itself
    for rxcui, min_str in min_rxcui_to_str.items():
        min_lookup.setdefault(rxcui, min_str)

    # --------------------------------------------------
    # SBDF lookup: rxcui → sbdf_str  (for new df column)
    # Covers BN→SBDF (via bracket) and SBD→SBDF (via RXNREL if available)
    # --------------------------------------------------
    sbdf_lookup = dict(bn_to_sbdf_str)  # BN rxcui → sbdf str

    print("stalevo MIN lookup  →", min_lookup.get("1372713"))
    print("stalevo SBDF lookup →", sbdf_lookup.get("1372713"))

    return rx_names, lookup, min_lookup, sbdf_lookup


# -------------------------------
# PRIORITY FUNCTION
# -------------------------------
def _compare_rxnorm_matches(candidate, current_best):
    priority = {"BN": 0, "MIN": 1, "IN": 2}

    if current_best[3] == -1:
        return True

    p_new = priority.get(candidate[2], 99)
    p_best = priority.get(current_best[2], 99)

    return (p_new < p_best) or (p_new == p_best and candidate[3] > current_best[3])


# -------------------------------
# MATCH FUNCTION (handles lists)
# -------------------------------
def _match_rxnorm_term(input_term, candidate_terms, rxnorm_lookup_table, threshold=85):

    if isinstance(input_term, (list, tuple)):
        best_match = (None, None, None, -1)
        for sub_term in input_term:
            if not isinstance(sub_term, str):
                continue
            matched_term, rxnorm_id, tty, similarity_score = _match_rxnorm_term(
                sub_term, candidate_terms, rxnorm_lookup_table, threshold
            )
            candidate_match = (matched_term, rxnorm_id, tty, similarity_score)
            if similarity_score is not None and _compare_rxnorm_matches(candidate_match, best_match):
                best_match = candidate_match
        return best_match if best_match[3] >= threshold else (None, None, None, None)

    if not isinstance(input_term, str):
        return None, None, None, None

    matched_term, similarity_score, _ignored_index = process.extractOne(
        input_term,
        candidate_terms,
        scorer=fuzz.token_sort_ratio
    )

    if similarity_score >= threshold:
        rxnorm_row = rxnorm_lookup_table.loc[matched_term]
        if isinstance(rxnorm_row, pd.DataFrame):
            rxnorm_row = rxnorm_row.iloc[0]
        return matched_term, rxnorm_row["rxcui"], rxnorm_row["tty"], similarity_score

    return None, None, None, None


# -------------------------------
# APPLY FUNCTION
# -------------------------------
def apply_rxnorm_mapping(
    df: pd.DataFrame,
    input_col: str,
    rxnorm_rrf_path: str,
    rxnrel_rrf_path: str,
    suffix: str,
    match_threshold: int = 85
) -> pd.DataFrame:

    rxnorm_candidate_terms, rxnorm_lookup_table, min_concept_lookup, sbdf_lookup = (
        _build_rxnorm_lookup_table(rxnorm_rrf_path, rxnrel_rrf_path)
    )

    def to_hashable_key(value):
        return tuple(value) if isinstance(value, list) else value

    unique_inputs = df[input_col].dropna().apply(to_hashable_key).unique()

    rxnorm_match_cache = {
        val: _match_rxnorm_term(val, rxnorm_candidate_terms, rxnorm_lookup_table, match_threshold)
        for val in unique_inputs
    }

    def _get(val, idx):
        return rxnorm_match_cache.get(to_hashable_key(val), (None, None, None, None))[idx]

    df["rxnorm_match" + suffix] = df[input_col].map(lambda v: _get(v, 0))
    df["rxcui"        + suffix] = df[input_col].map(lambda v: _get(v, 1))
    df["score"        + suffix] = df[input_col].map(lambda v: _get(v, 3))
    df["tty"          + suffix] = df[input_col].map(lambda v: _get(v, 2))

    def resolve_min_concept(row):
        rxcui = row["rxcui" + suffix]
        if pd.isna(rxcui):
            return None
        return min_concept_lookup.get(rxcui)

    def resolve_sbdf(row):
        rxcui = row["rxcui" + suffix]
        if pd.isna(rxcui):
            return None
        return sbdf_lookup.get(rxcui)

    df["MIN"  + suffix]  = df.apply(resolve_min_concept, axis=1)
    df["sbdf" + suffix]  = df.apply(resolve_sbdf, axis=1)

    mapped = df["rxnorm_match" + suffix].notna().sum()
    print(f"RXNorm Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df