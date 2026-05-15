import pandas as pd
import requests
from time import sleep


def match_rxnorm_api(term, threshold=80):
    """
    Call RxNorm API approximate match
    Returns: (normalized_name, rxcui, score, url)
    """

    if not isinstance(term, str) or term.strip() == "":
        return None, None, None, None

    try:
        # --- approximate match ---
        url = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
        params = {"term": term, "maxEntries": 1}

        res = requests.get(url, params=params).json()

        candidate = res.get("approximateGroup", {}).get("candidate", [])
        if not candidate:
            return None, None, None, None

        candidate = candidate[0]
        rxcui = candidate.get("rxcui")
        score = int(candidate.get("score", 0))

        if score < threshold:
            return None, None, score, None

        # --- get normalized name ---
        prop_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
        prop_res = requests.get(prop_url).json()

        name = prop_res.get("properties", {}).get("name")

        # --- build URL ---
        rxnav_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}"

        return name, rxcui, score, rxnav_url

    except Exception:
        return None, None, None, None


def apply_rxnorm_mapping_api(
    df: pd.DataFrame,
    input_col: str,
    threshold: int = 80,
    out_name: str = "rxnorm_name",
    out_rxcui: str = "rxcui",
    out_score: str = "rx_score",
    out_url: str = "rx_url"
) -> pd.DataFrame:

    unique_vals = df[input_col].dropna().unique()

    mapping = {}

    for i, val in enumerate(unique_vals):
        mapping[val] = match_rxnorm_api(val, threshold)

        # ⚠️ avoid hammering API
        sleep(0.05)

        if i % 100 == 0:
            print(f"Processed {i}/{len(unique_vals)}")

    df[out_name] = df[input_col].map(lambda x: mapping.get(x, (None, None, None, None))[0])
    df[out_rxcui] = df[input_col].map(lambda x: mapping.get(x, (None, None, None, None))[1])
    df[out_score] = df[input_col].map(lambda x: mapping.get(x, (None, None, None, None))[2])
    df[out_url] = df[input_col].map(lambda x: mapping.get(x, (None, None, None, None))[3])

    mapped = df[out_name].notna().sum()
    print(f"RXNorm API Mapping Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df