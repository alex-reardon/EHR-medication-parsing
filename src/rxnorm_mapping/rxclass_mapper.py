import logging
import requests
import pandas as pd

logger = logging.getLogger(__name__)


def _fetch_rxclass_classes(
    rxcui,
    rela_source="ATC"
):
    """
    Map RXCUI -> drug class using RxClass API

    rela_source options:
        ATC
        MESHPA
        VA
        FMTSME
    """

    if pd.isna(rxcui):
        return None


    try:
        rxcui = str(int(float(rxcui)))
    except (ValueError, TypeError):
        return None

    url = (
        "https://rxnav.nlm.nih.gov/REST/"
        f"rxclass/class/byRxcui.json?rxcui={rxcui}"
    )

    try:

        r = requests.get(url, timeout=10)

        data = r.json()

        concepts = (
            data.get("rxclassDrugInfoList", {})
            .get("rxclassDrugInfo", [])
        )

        classes = []

        for c in concepts:

            source = c.get("relaSource")

            if source != rela_source:
                continue

            class_name = (
                c.get("rxclassMinConceptItem", {})
                .get("className")
            )

            if class_name:
                classes.append(class_name)

        # unique preserve order
        classes = list(dict.fromkeys(classes))

        if not classes:
            return None

        return "; ".join(classes)

    except Exception as e:

        logger.warning("RxClass API error for rxcui %s: %s", rxcui, e)

        return None


def apply_rxclass_mapping(
    df,
    rxcui_col="rxcui",
    out_col="rxclass_atc",
    rela_source="ATC"
):

    # cache unique rxcuis
    unique_rxcuis = df[rxcui_col].dropna().unique()

    mapping = {
        rxcui: _fetch_rxclass_classes(rxcui, rela_source)
        for rxcui in unique_rxcuis
    }

    df[out_col] = df[rxcui_col].map(mapping)

    return df

