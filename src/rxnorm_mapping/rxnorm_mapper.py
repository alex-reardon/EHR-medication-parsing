"""
rxnorm_mapper.py
-----------------
Matches messy medication strings to RxNorm concepts and produces
formulation-aware canonical forms suitable for LEDD computation.

Output columns (per suffix):
  rxnorm_match      - matched RxNorm string
  rxcui             - RxNorm concept ID
  tty               - term type (BN, IN, MIN, ...)
  score             - fuzzy match score (0-100)
  drug_name_canonical - ingredient(s) from MIN (e.g. "carbidopa / levodopa")
  formulation       - extracted formulation tag (e.g. "ER", "CR", "IR", "patch")
  ledd_key          - (canonical + formulation) used to look up LEDD conversion factor
  parse_confidence  - "high" / "medium" / "low" based on score
"""

from __future__ import annotations
import logging
import re
import pandas as pd
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fuzzy score thresholds
CONFIDENCE_HIGH   = 92
CONFIDENCE_MEDIUM = 85   # also used as the minimum match threshold

# RxNorm term types used for matching candidates
MATCH_TTY   = {"IN", "MIN", "BN", "SBDF"}   # indexed in lookup table
RESOLVE_TTY = {"IN", "MIN", "BN", "SBD", "SCD", "SBDF", "SBDC"}  # loaded from RRF

# Formulation token → normalised tag
# Order matters: more specific patterns should come first.
FORMULATION_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\bER\b|\bXR\b|\bextended[- ]release\b|\bext(?:ended)?[- ]rel\b', re.I), "ER"),
    (re.compile(r'\bCR\b|\bcontrolled[- ]release\b', re.I),                               "CR"),
    (re.compile(r'\bSR\b|\bsustained[- ]release\b', re.I),                                "SR"),
    (re.compile(r'\bIR\b|\bimmediate[- ]release\b', re.I),                                "IR"),
    (re.compile(r'\bDR\b|\bdelayed[- ]release\b', re.I),                                  "DR"),
    (re.compile(r'\bODT\b|\borally disintegrating\b', re.I),                              "ODT"),
    (re.compile(r'\bpatch\b|\btransdermal\b', re.I),                                      "patch"),
    (re.compile(r'\binhaler?\b|\binhalation\b', re.I),                                    "inhaler"),
    (re.compile(r'\binjection\b|\binjectable\b|\binfusion\b', re.I),                      "injectable"),
    (re.compile(r'\bbead\b|\bmicrobead\b|\bcapsule\b', re.I),                             "bead_capsule"),
    (re.compile(r'\bsolution\b|\bliquid\b|\bsyrup\b', re.I),                             "liquid"),
    (re.compile(r'\bsublingual\b|\bbuccal\b', re.I),                                      "sublingual"),
]

# Tokens stripped when cleaning an SBDF string down to its ingredient core
_DOSE_FORM_STRIP = re.compile(
    r'\b(oral|tablet|capsule|solution|suspension|injection|patch|cream|gel|'
    r'ointment|powder|granule|syrup|drops?|spray|inhaler|extended|immediate|'
    r'delayed|modified|release|film|coated|chewable|effervescent|sublingual|'
    r'buccal|topical|ophthalmic|otic|nasal|rectal|vaginal|transdermal|'
    r'product|pill|bead|microbead)\b',
    re.I,
)
_BRACKET_STRIP   = re.compile(r'\[.*?\]')
_WHITESPACE_NORM = re.compile(r'\s{2,}')


# ---------------------------------------------------------------------------
# Formulation extraction (pure, no RxNorm needed)
# ---------------------------------------------------------------------------
def extract_formulation(text: str) -> str | None:
    """
    Return the first matching normalised formulation tag from *text*, or None.

    Checks the raw drug string (e.g. "Sinemet CR", "levodopa ER 100mg")
    *and* can also be called on the SBDF string when available.
    """
    for pattern, tag in FORMULATION_MAP:
        if pattern.search(text):
            return tag
    return None


# ---------------------------------------------------------------------------
# SBDF string helpers
# ---------------------------------------------------------------------------
def _clean_sbdf_to_ingredient_key(sbdf_str: str) -> str:
    """
    Strip bracket content and dose-form tokens from an SBDF string,
    returning a normalised ingredient key suitable for MIN matching.

    e.g. "carbidopa / levodopa oral tablet extended release [sinemet cr]"
         → "carbidopa / levodopa"
    """
    s = _BRACKET_STRIP.sub("", sbdf_str)
    s = _DOSE_FORM_STRIP.sub("", s)
    s = _WHITESPACE_NORM.sub(" ", s).strip(" /,")
    parts = [p.strip() for p in re.split(r'[/,]', s) if p.strip()]
    return " / ".join(sorted(parts))


def _sbdf_str_to_min(
    sbdf_str: str,
    min_str_set: set[str],
    min_str_list: list[str],
    threshold: int = 85,
) -> str | None:
    """
    Resolve an SBDF string to its MIN (multi-ingredient) string.
    Tries an exact key match first; falls back to fuzzy.
    """
    key = _clean_sbdf_to_ingredient_key(sbdf_str)
    if key in min_str_set:
        return key
    if not min_str_list:
        return None
    match, score, _ = process.extractOne(key, min_str_list, scorer=fuzz.token_sort_ratio)
    return match if score >= threshold else None


# ---------------------------------------------------------------------------
# RxNorm lookup-table construction
# ---------------------------------------------------------------------------
def _load_rrf(path: str) -> pd.DataFrame:
    cols = [
        "rxcui", "lat", "ts", "lui", "stt", "sui", "ispref",
        "rxaui", "saui", "scui", "sdui", "sab", "tty",
        "code", "str", "srl", "suppress", "cvf", "empty",
    ]
    df = pd.read_csv(path, sep="|", header=None, names=cols, dtype=str)
    #df = df[(df["lat"] == "ENG") & (df["suppress"] == "N")].copy() # FIXEM 
    df = df[df["suppress"] == "N"].copy()
    df["str_lower"] = df["str"].str.lower().str.strip()
    return df


def _load_rel(path: str) -> pd.DataFrame:
    cols = [
        "rxcui1", "rxaui1", "stype1", "rel", "rxcui2", "rxaui2", "stype2",
        "rela", "rui", "srui", "sab", "sl", "dir",
        "rg", "suppress", "cvf", "empty",
    ]
    df = pd.read_csv(path, sep="|", header=None, names=cols, dtype=str)
    return df[(df["sab"] == "RXNORM") & (df["suppress"] == "N")]


def _build_sbd_to_min(
    sbd_rxcuis: set,
    scd_rxcuis: set,
    min_rxcuis: set,
    min_rxcui_to_str: dict,
    rel: pd.DataFrame,
) -> dict:
    """SBD → SCD → MIN chain via RXNREL tradename_of / has_tradename edges."""
    fwd = (
        rel[
            (rel["rela"] == "tradename_of") &
            rel["rxcui1"].isin(sbd_rxcuis) &
            rel["rxcui2"].isin(scd_rxcuis)
        ][["rxcui1", "rxcui2"]].rename(columns={"rxcui1": "sbd", "rxcui2": "scd"})
    )
    rev = (
        rel[
            (rel["rela"] == "has_tradename") &
            rel["rxcui2"].isin(sbd_rxcuis) &
            rel["rxcui1"].isin(scd_rxcuis)
        ][["rxcui1", "rxcui2"]].rename(columns={"rxcui2": "sbd", "rxcui1": "scd"})
    )
    sbd_scd = pd.concat([fwd, rev]).drop_duplicates()

    scd_to_min = (
        rel[
            (rel["rela"] == "has_ingredient") &
            rel["rxcui1"].isin(scd_rxcuis) &
            rel["rxcui2"].isin(min_rxcuis)
        ][["rxcui1", "rxcui2"]].rename(columns={"rxcui1": "scd", "rxcui2": "min_rxcui"})
    )

    merged = (
        sbd_scd.merge(scd_to_min, on="scd", how="inner")[["sbd", "min_rxcui"]]
        .drop_duplicates("sbd")
    )
    return {
        row.sbd: min_rxcui_to_str[row.min_rxcui]
        for row in merged.itertuples()
        if row.min_rxcui in min_rxcui_to_str
    }


def _build_bn_to_min_and_sbdf(
    bn_rows: pd.DataFrame,
    sbdf_rows: pd.DataFrame,
    min_rxcui_to_str: dict,
    rel: pd.DataFrame,
    sbd_rxcuis: set,
    scd_rxcuis: set,
    min_rxcuis: set,
    sbdf_threshold: int = 85,
) -> tuple[dict, dict]:
    """
    Returns (bn_rxcui→min_str, bn_rxcui→sbdf_str).

    Resolution order:
      1. BN → SBD → SCD → MIN via RXNREL (most reliable)
      2. BN → SBDF via bracket match → strip → MIN (fallback)
    """
    min_str_set  = set(min_rxcui_to_str.values())
    min_str_list = list(min_str_set)

    # --- path 1: RXNREL chain BN→SBD→SCD→MIN ---
    bn_to_sbd = (
        rel[rel["rela"] == "tradename_of"][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui1": "sbd", "rxcui2": "bn"})
    )
    sbd_to_min_map = _build_sbd_to_min(
        sbd_rxcuis, scd_rxcuis, min_rxcuis, min_rxcui_to_str, rel
    )
    bn_to_min: dict[str, str] = {}
    for row in bn_to_sbd.itertuples():
        if row.sbd in sbd_to_min_map:
            bn_to_min.setdefault(row.bn, sbd_to_min_map[row.sbd])

    # --- path 2: bracket pattern BN→SBDF→MIN ---
    # Pre-index SBDF strings by their bracket content (e.g. "[sinemet cr]" → "sinemet cr")
    # so each BN lookup is O(1) instead of a full DataFrame scan.
    sbdf_bracket = (
        sbdf_rows["str_lower"]
        .str.extract(r'\[([^\]]+)\]', expand=False)
        .str.strip()
    )
    bracket_to_sbdf: dict[str, str] = (
        sbdf_rows.assign(bracket=sbdf_bracket)
        .dropna(subset=["bracket"])
        .drop_duplicates("bracket")
        .set_index("bracket")["str_lower"]
        .to_dict()
    )

    bn_to_sbdf: dict[str, str] = {}
    for _, bn_row in bn_rows.iterrows():
        bn_str   = str(bn_row["str_lower"]).strip()
        sbdf_str = bracket_to_sbdf.get(bn_str)
        if sbdf_str is None:
            continue
        bn_to_sbdf[bn_row["rxcui"]] = sbdf_str

        # only fill bn_to_min if RXNREL didn't already get it
        if bn_row["rxcui"] not in bn_to_min:
            min_str = _sbdf_str_to_min(sbdf_str, min_str_set, min_str_list, sbdf_threshold)
            if min_str:
                bn_to_min[bn_row["rxcui"]] = min_str

    return bn_to_min, bn_to_sbdf


def build_rxnorm_lookup_table(
    rrf_path: str,
    rxnrel_path: str,
) -> tuple[list[str], pd.DataFrame, dict, dict, dict]:
    """
    Parse RXNCONSO and RXNREL and build lookup structures.

    Returns
    -------
    candidate_terms   : list[str]   – lower-case strings for fuzzy matching
    lookup_table      : DataFrame   – str_lower → (rxcui, tty)
    min_lookup        : dict        – rxcui → MIN string (ingredient(s))
    sbdf_lookup       : dict        – rxcui → SBDF string (carries formulation info)
    formulation_lookup: dict        – rxcui → formulation tag (from SBDF or BN str)
    """
    rx  = _load_rrf(rrf_path)
    rel = _load_rel(rxnrel_path)

    rx_all = rx[rx["tty"].isin(RESOLVE_TTY)].copy()

    # --- candidate terms for fuzzy matching (BN, IN, MIN, SBDF) ---
    rx_match   = rx_all[rx_all["tty"].isin(MATCH_TTY)]
    lookup_tbl = (
        rx_match.drop_duplicates("str_lower")
        .set_index("str_lower")[["rxcui", "tty"]]
    )
    candidate_terms = lookup_tbl.index.tolist()

    # --- rxcui sets and MIN string map ---
    def _rxcui_set(tty: str) -> set:
        return set(rx_all[rx_all["tty"] == tty]["rxcui"].unique())

    min_rxcuis = _rxcui_set("MIN")
    scd_rxcuis = _rxcui_set("SCD")
    sbd_rxcuis = _rxcui_set("SBD")
    in_rxcuis  = _rxcui_set("IN")
    bn_rxcuis  = _rxcui_set("BN")

    min_rxcui_to_str: dict[str, str] = (
        rx_all[rx_all["tty"] == "MIN"]
        .drop_duplicates("rxcui")
        .set_index("rxcui")["str_lower"]
        .to_dict()
    )

    bn_rows   = rx_all[(rx_all["tty"] == "BN")  & (rx_all["sab"] == "RXNORM")][["rxcui", "str_lower"]].drop_duplicates("rxcui")
    sbdf_rows = rx_all[(rx_all["tty"] == "SBDF") & (rx_all["sab"] == "RXNORM")][["rxcui", "str_lower"]].drop_duplicates("rxcui")

    bn_to_min, bn_to_sbdf = _build_bn_to_min_and_sbdf(
        bn_rows, sbdf_rows, min_rxcui_to_str, rel,
        sbd_rxcuis, scd_rxcuis, min_rxcuis,
    )

    sbd_to_min = _build_sbd_to_min(
        sbd_rxcuis, scd_rxcuis, min_rxcuis, min_rxcui_to_str, rel
    )

    in_to_min = (
        rel[
            (rel["rela"] == "has_ingredient") &
            rel["rxcui1"].isin(in_rxcuis) &
            rel["rxcui2"].isin(min_rxcuis)
        ][["rxcui1", "rxcui2"]]
        .rename(columns={"rxcui1": "in_rxcui", "rxcui2": "min_rxcui"})
        .drop_duplicates("in_rxcui")
    )

    # --- assemble min_lookup with explicit priority ---
    # MIN → itself (highest trust)
    min_lookup: dict[str, str] = {**min_rxcui_to_str}
    # IN → MIN
    for row in in_to_min.itertuples():
        min_lookup.setdefault(row.in_rxcui, min_rxcui_to_str.get(row.min_rxcui))
    # SBD → MIN
    for rxcui, min_str in sbd_to_min.items():
        min_lookup.setdefault(rxcui, min_str)
    # BN → MIN
    for rxcui, min_str in bn_to_min.items():
        min_lookup.setdefault(rxcui, min_str)

    # --- sbdf_lookup: rxcui → raw SBDF string (preserves formulation text) ---
    sbdf_lookup: dict[str, str] = dict(bn_to_sbdf)

    # --- formulation_lookup: rxcui → formulation tag ---
    # Source priority: SBDF string > BN string itself > None
    formulation_lookup: dict[str, str] = {}

    for rxcui, sbdf_str in sbdf_lookup.items():
        tag = extract_formulation(sbdf_str)
        if tag:
            formulation_lookup[rxcui] = tag

    for _, bn_row in bn_rows.iterrows():
        rxcui = bn_row["rxcui"]
        if rxcui not in formulation_lookup:
            tag = extract_formulation(bn_row["str_lower"])
            if tag:
                formulation_lookup[rxcui] = tag

    return candidate_terms, lookup_tbl, min_lookup, sbdf_lookup, formulation_lookup


# ---------------------------------------------------------------------------
# Match helpers
# ---------------------------------------------------------------------------
def _score_to_confidence(score: float | None) -> str:
    if pd.isna(score) or score < CONFIDENCE_MEDIUM:
        return "low"
    if score >= CONFIDENCE_HIGH:
        return "high"
    return "medium"

_SEP_NORM = re.compile(r'\s*[/+&]\s*')

def _normalize_input(term: str) -> str:
    """Normalize separators so levodopa/carbidopa, levodopa + carbidopa,
    and levodopa / carbidopa all tokenize the same way."""
    return _SEP_NORM.sub(' ', term).strip()


def _match_single(
    term: str,
    candidate_terms: list[str],
    lookup_table: pd.DataFrame,
    threshold: int,
) -> tuple[str | None, str | None, str | None, float | None]:
    """Return (matched_term, rxcui, tty, score) for a single string."""
    term = _normalize_input(term)  
    matched, score, _ = process.extractOne(
        term, candidate_terms, scorer=fuzz.token_sort_ratio
    )
    if score < threshold:
        return None, None, None, None
    row = lookup_table.loc[matched]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    return matched, row["rxcui"], row["tty"], score


def match_rxnorm_term(
    input_term: str | list | tuple,
    candidate_terms: list[str],
    lookup_table: pd.DataFrame,
    threshold: int = CONFIDENCE_MEDIUM,
) -> tuple[str | None, str | None, str | None, float | None]:
    """
    Match *input_term* against RxNorm candidates.

    Accepts a string or a list/tuple of strings (takes best scoring match
    across all elements, with BN preferred over IN/MIN on equal scores
    since brand names carry formulation information).
    """
    if isinstance(input_term, (list, tuple)):
        best: tuple[str | None, str | None, str | None, float | None] = (None, None, None, None)
        for sub in input_term:
            if not isinstance(sub, str):
                continue
            candidate = _match_single(sub, candidate_terms, lookup_table, threshold)
            if candidate[3] is not None and (
                best[3] is None or
                _is_better_match(candidate, best)
            ):
                best = candidate
        return best

    if not isinstance(input_term, str):
        return None, None, None, None

    return _match_single(input_term, candidate_terms, lookup_table, threshold)


def _is_better_match(
    new: tuple,
    current: tuple,
) -> bool:
    """
    BN wins over IN/MIN at equal scores because it encodes formulation info.
    Otherwise higher score wins.
    """
    # tty priority: BN=0 (keeps formulation), IN=1, MIN=2
    priority = {"BN": 0, "IN": 1, "MIN": 2}
    p_new = priority.get(new[2], 99)
    p_cur = priority.get(current[2], 99)
    if p_new != p_cur:
        return p_new < p_cur
    return (new[3] or 0) > (current[3] or 0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_ledd_key(canonical: str | None, formulation: str | None) -> str | None:
    """
    Combine ingredient canonical name and formulation into the key used to
    look up the LEDD conversion factor table.

    e.g. ("carbidopa / levodopa", "ER") → "carbidopa/levodopa_ER"
         ("levodopa", None)              → "levodopa_IR"   (default to IR)
    """
    if canonical is None:
        return None
    base = canonical.replace(" / ", "/").replace(" ", "_").lower()
    tag  = formulation if formulation else "IR"
    return f"{base}_{tag}"


def apply_rxnorm_mapping(
    df: pd.DataFrame,
    input_col: str,
    rxnorm_rrf_path: str,
    rxnrel_rrf_path: str,
    suffix: str = "",
    match_threshold: int = CONFIDENCE_MEDIUM,
    lookup_tables: tuple | None = None,
) -> pd.DataFrame:
    """
    Map messy drug name strings in *input_col* to normalised RxNorm concepts.

    Parameters
    ----------
    df               : input DataFrame
    input_col        : column containing raw drug name strings (or lists of strings)
    rxnorm_rrf_path  : path to RXNCONSO.RRF
    rxnrel_rrf_path  : path to RXNREL.RRF
    suffix           : appended to all output column names (useful when mapping
                       multiple columns, e.g. "_med1", "_med2")
    match_threshold  : minimum fuzzy score to accept a match (default 85)
    lookup_tables    : pass the output of build_rxnorm_lookup_table() to avoid
                       rebuilding on repeated calls

    Output columns added
    --------------------
    rxnorm_match      matched RxNorm string
    rxcui             RxNorm concept ID
    tty               term type
    score             fuzzy match score
    drug_name_canonical  ingredient(s) from MIN chain
    formulation       extracted formulation tag (ER / CR / IR / patch / ...)
    ledd_key          canonical + formulation key for LEDD table lookup
    parse_confidence  high / medium / low
    """
    if lookup_tables is None:
        lookup_tables = build_rxnorm_lookup_table(rxnorm_rrf_path, rxnrel_rrf_path)

    candidate_terms, lookup_table, min_lookup, sbdf_lookup, formulation_lookup = lookup_tables

    def _hashable(v):
        return tuple(v) if isinstance(v, list) else v

    unique_vals = df[input_col].dropna().apply(_hashable).unique()

    cache: dict = {
        v: match_rxnorm_term(v, candidate_terms, lookup_table, match_threshold)
        for v in unique_vals
    }

    def _get(val, idx):
        return cache.get(_hashable(val), (None, None, None, None))[idx]

    s = suffix
    df[f"rxnorm_match{s}"] = df[input_col].map(lambda v: _get(v, 0))
    df[f"rxcui{s}"]        = df[input_col].map(lambda v: _get(v, 1))
    df[f"tty{s}"]          = df[input_col].map(lambda v: _get(v, 2))
    df[f"score{s}"]        = df[input_col].map(lambda v: _get(v, 3))


    def _resolve_canonical(row) -> str | None:
        rxcui = row[f"rxcui{s}"]
        if pd.isna(rxcui):
            return None
        return min_lookup.get(rxcui)

    def _resolve_formulation(row) -> str | None:
        rxcui = row[f"rxcui{s}"]
        if pd.isna(rxcui):
            return None
        # 1. Formulation pre-resolved from SBDF/BN during table build
        tag = formulation_lookup.get(rxcui)
        if tag:
            return tag
        # 2. Fall back: check the raw input string itself
        raw = row[input_col]
        if isinstance(raw, str):
            return extract_formulation(raw)
        if isinstance(raw, (list, tuple)):
            for item in raw:
                tag = extract_formulation(str(item))
                if tag:
                    return tag
        return None

    df[f"drug_name_canonical{s}"] = df.apply(_resolve_canonical,  axis=1)
    df[f"formulation{s}"]         = df.apply(_resolve_formulation, axis=1)
    df[f"ledd_key{s}"]            = df.apply(
        lambda row: build_ledd_key(
            row[f"drug_name_canonical{s}"],
            row[f"formulation{s}"],
        ),
        axis=1,
    )
    df[f"parse_confidence{s}"] = df[f"score{s}"].map(_score_to_confidence)

    mapped = df[f"rxnorm_match{s}"].notna().sum()
    total  = len(df)
    high   = (df[f"parse_confidence{s}"] == "high").sum()
    med    = (df[f"parse_confidence{s}"] == "medium").sum()
    low    = (df[f"parse_confidence{s}"] == "low").sum()
    logger.info(
        "RxNorm mapping complete: %d/%d rows matched (%.1f%%) | confidence — high: %d, medium: %d, low: %d",
        mapped, total, 100 * mapped / total, high, med, low
    )

    return df
