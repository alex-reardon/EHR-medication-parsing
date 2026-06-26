import numpy as np



def create_canonical_ledd_col(df) :
    
    # initialize with best_rxnorm_match
    df["canonical_LEDD_med"] = df["best_rxnorm_match"]

    # brand -> canonical medication mapping
    brand2ing = {
          "madopar": "levodopa / benserazide" ,
          "nacom" : "levodopa / carbidopa",
          "melevedopa": "levodopa / benserazide",
          "isicom" : "levodopa / carbidopa" 
    }

    mask = (
        df["canonical_LEDD_med"].isna()
        | (df["canonical_LEDD_med"].astype(str).str.strip() == "")
    )
    
    for brand, med in brand2ing.items():
        brand_mask = (mask & df["parsed"].fillna("").str.contains(brand, case=False, regex=False))
        df.loc[brand_mask, "parsed"] = med

    ledd_map = {
        "levodopa / benserazide": "benserazide / levodopa" ,
        "levodopa / carbidopa" : "carbidopa / levodopa", 
        "clarium": "piribedil",
        "dopicar": "carbidopa / levodopa",
        "duodopa": "carbidopa / levodopa",
        "levocomp": "carbidopa / levodopa",
        "levopar": "benserazide / levodopa",
        "neupro": "rotigotine",
        "requip": "ropinirole",
        "rytary": "carbidopa / levodopa",
        "sifrol": "pramipexole",
        "xadago": "safinamide", 
        "pk merz" : "amantadine" 
    }

    # only fill where best_rxnorm_match is missing
    mask = (
        df["canonical_LEDD_med"].isna()
        | (df["canonical_LEDD_med"].astype(str).str.strip() == "")
    )

    for brand, med in ledd_map.items():
        brand_mask = (
            mask
            & df["parsed"].fillna("").str.contains(brand, case=False, regex=False)
        )
        df.loc[brand_mask, "canonical_LEDD_med"] = med
    return df 


def apply_create_canonical_ledd_col(df) :
    df = create_canonical_ledd_col(df)
    return df 
