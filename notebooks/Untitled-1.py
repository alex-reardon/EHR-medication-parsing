from __future__ import annotations
import re
import pandas as pd

"""
ledd_mapping.py
---------------
Maps a cleaned medication DataFrame to LEDD conversion factors.

Matching priority (highest to lowest specificity):
  1. best_rxnorm_match + release  (e.g. carbidopa/levodopa + er)
  2. best_rxnorm_match + route    (e.g. levodopa + inh)
  3. best_rxnorm_match alone      (e.g. rasagiline)

Within each tier, longer best_rxnorm_match strings are tried first so that
"carbidopa / entacapone / levodopa" wins over "levodopa" on the same row.

Route matching is substring-based (data value contained in ledd table value
or vice versa) to handle partial strings like "inh" matching "inhalation".
"""



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(val) -> str | None:
    """Lowercase, strip whitespace and list brackets from a cell value."""
    if val is None or (isinstance(val, float)):
        return None
    s = str(val).strip().lower()
    # strip list formatting: ['er'] -> er
    s = re.sub(r"[\[\]']", "", s).strip()
    return s if s else None


def _route_match(data_route: str | None, table_route: str | None) -> bool:
    """
    Fuzzy substring route match.
    Passes if either string contains the other (handles 'inh' vs 'inhalation',
    'intestin' vs 'intestinal infusion', etc.).
    Returns True if both are None (neither has a route constraint).
    """
    if data_route is None and table_route is None:
        return True
    if data_route is None or table_route is None:
        return False
    return data_route in table_route or table_route in data_route


# ---------------------------------------------------------------------------
# Build lookup structures from the LEDD table
# ---------------------------------------------------------------------------

def _build_ledd_lookup(ledd_df: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Split the LEDD table into three pre-sorted lookup lists:
      tier1: rows that have best_rxnorm_match AND release
      tier2: rows that have best_rxnorm_match AND route
      tier3: rows that have best_rxnorm_match only (no release, no route)

    Each list is sorted descending by len(best_rxnorm_match) so longer/more
    specific drug names are matched first.
    """
    tier1, tier2, tier3 = [], [], []

    for _, row in ledd_df.iterrows():
        name    = _clean(row.get("best_rxnorm_match"))
        release = _clean(row.get("release"))
        route   = _clean(row.get("route"))
        factor  = row.get("ledd_conversion_factor")
        comt    = row.get("comt_modifier")
        drug_class = _clean(row.get("drug_class"))
        canonical  = _clean(row.get("drug_name_canonical"))

        if not name:
            continue

        entry = dict(
            name=name,
            release=release,
            route=route,
            factor=factor,
            comt=comt,
            drug_class=drug_class,
            canonical=canonical,
        )

        if release:
            tier1.append(entry)
        elif route:
            tier2.append(entry)
        else:
            tier3.append(entry)

    key = lambda e: len(e["name"])
    return (
        sorted(tier1, key=key, reverse=True),
        sorted(tier2, key=key, reverse=True),
        sorted(tier3, key=key, reverse=True),
    )


# ---------------------------------------------------------------------------
# Row-level matching
# ---------------------------------------------------------------------------

def _match_row(
    data_name: str | None,
    data_release: str | None,
    data_route: str | None,
    tier1: list[dict],
    tier2: list[dict],
    tier3: list[dict],
) -> dict | None:
    """
    Try tiers in order, return first matching entry or None.
    """
    if not data_name:
        return None

    # --- tier 1: name + release ---
    if data_release:
        for entry in tier1:
            if entry["name"] == data_name and entry["release"] == data_release:
                return entry

    # --- tier 2: name + route ---
    if data_route:
        for entry in tier2:
            if entry["name"] == data_name and _route_match(data_route, entry["route"]):
                return entry

    # --- tier 3: name only ---
    for entry in tier3:
        if entry["name"] == data_name:
            return entry

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_ledd_mapping(
    df: pd.DataFrame,
    ledd_csv_path: str,
    name_col: str    = "best_rxnorm_match",
    release_col: str = "release",
    route_col: str   = "route",
) -> pd.DataFrame:
    """
    Map each row in *df* to a LEDD conversion factor.

    Parameters
    ----------
    df            : cleaned medication DataFrame
    ledd_csv_path : path to ledd_conversion_factors.csv
    name_col      : column containing normalised drug name
    release_col   : column containing release modifier (er/ir/cr/...)
    route_col     : column containing route (oral/inh/sublingual/...)

    Columns added
    -------------
    ledd_drug_class       : drug class from LEDD table
    ledd_canonical        : canonical ingredient name from LEDD table
    ledd_conversion_factor: raw value from table (may be 'LDx0.33', 'CHECK', etc.)
    ledd_factor_numeric   : float conversion factor where parseable, else NaN
    ledd_comt_modifier    : COMT modifier value if applicable
    ledd_match_tier       : 1 / 2 / 3 — which tier matched (useful for QC)
    ledd_mapped           : bool — whether any match was found
    """
    ledd_df = pd.read_csv(ledd_csv_path, dtype=str)

    # normalise LEDD table values
    ledd_df["best_rxnorm_match"] = ledd_df["best_rxnorm_match"].str.lower().str.strip()
    ledd_df["release"]           = ledd_df["release"].str.lower().str.strip()
    ledd_df["route"]             = ledd_df["route"].str.lower().str.strip()

    tier1, tier2, tier3 = _build_ledd_lookup(ledd_df)

    results = []
    for _, row in df.iterrows():
        data_name    = _clean(row.get(name_col))
        data_release = _clean(row.get(release_col))
        data_route   = _clean(row.get(route_col))

        # try tier 1 first, then 2, then 3
        match = None
        tier_hit = None

        if data_release:
            for entry in tier1:
                if entry["name"] == data_name and entry["release"] == data_release:
                    match = entry
                    tier_hit = 1
                    break

        if match is None and data_route:
            for entry in tier2:
                if entry["name"] == data_name and _route_match(data_route, entry["route"]):
                    match = entry
                    tier_hit = 2
                    break

        if match is None:
            for entry in tier3:
                if entry["name"] == data_name:
                    match = entry
                    tier_hit = 3
                    break

        if match:
            factor_raw = str(match["factor"]).strip() if match["factor"] else None
            try:
                factor_num = float(factor_raw)
            except (TypeError, ValueError):
                factor_num = float("nan")

            results.append(dict(
                ledd_drug_class=match["drug_class"],
                ledd_canonical=match["canonical"],
                ledd_conversion_factor=factor_raw,
                ledd_factor_numeric=factor_num,
                ledd_comt_modifier=match["comt"],
                ledd_match_tier=tier_hit,
                ledd_mapped=True,
            ))
        else:
            results.append(dict(
                ledd_drug_class=None,
                ledd_canonical=None,
                ledd_conversion_factor=None,
                ledd_factor_numeric=float("nan"),
                ledd_comt_modifier=None,
                ledd_match_tier=None,
                ledd_mapped=False,
            ))

    result_df = pd.DataFrame(results, index=df.index)
    df = pd.concat([df, result_df], axis=1)

    mapped   = df["ledd_mapped"].sum()
    total    = len(df)
    t1 = (df["ledd_match_tier"] == 1).sum()
    t2 = (df["ledd_match_tier"] == 2).sum()
    t3 = (df["ledd_match_tier"] == 3).sum()
    unmapped = df[~df["ledd_mapped"]][name_col].dropna().unique()

    print(f"LEDD mapping: {mapped}/{total} rows mapped ({mapped/total:.1%})")
    print(f"  tier 1 (name+release): {t1}  |  tier 2 (name+route): {t2}  |  tier 3 (name only): {t3}")
    if len(unmapped):
        print(f"  unmapped drug names ({len(unmapped)}): {sorted(unmapped)}")

    return df


df = pd.read_csv('/Users/emudr/PPMI_LEDD/data/PPMI_archived/output/out_PPMI_archived.csv')



df = apply_ledd_mapping(
    df,
    ledd_csv_path="/Users/emudr/PPMI_LEDD/data/ledd_conversion_factors.csv",
    name_col="best_rxnorm_match",
    release_col="release",
    route_col="route",
)

# rows that matched but need manual review (COMT, CHECK, blank factors)
review = df[df["ledd_mapped"] & df["ledd_factor_numeric"].isna()]
df.to_csv('/Users/emudr/Desktop/temp.csv')