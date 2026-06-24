import numpy as np



def create_canonical_ledd_col(df) :
    
    # initialize with best_rxnorm_match
    df["canonical_LEDD_med"] = df["best_rxnorm_match"]

    # brand -> canonical medication mapping
    ledd_map = {
        "madopar": "benserazide / levodopa",
        "clarium": "piribedil",
        "dopicar": "carbidopa / levodopa",
        "duodopa": "carbidopa / levodopa",
        "isicom": "carbidopa / levodopa",
        "levocomp": "carbidopa / levodopa",
        "levopar": "benserazide / levodopa",
        "neupro": "rotigotine",
        "requip": "ropinirole",
        "rytary": "carbidopa / levodopa",
        "sifrol": "pramipexole",
        "xadago": "safinamide",
        "melevedopa": "benserazide / levodopa",
    }

    # only fill where best_rxnorm_match is missing
    mask = (
        df["canonical_LEDD_med"].isna()
        | (df["canonical_LEDD_med"].astype(str).str.strip() == "")
    )

    for brand, med in ledd_map.items():
        brand_mask = (
            mask
            & df["clean_text"].fillna("").str.contains(brand, case=False, regex=False)
        )
        df.loc[brand_mask, "canonical_LEDD_med"] = med
    return df 


def apply_create_canonical_ledd_col(df) :
    df = create_canonical_ledd_col(df)
    return df 
