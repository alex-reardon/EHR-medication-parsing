# extraction/extraction_pipeline.py

import pandas as pd

from rxnorm_mapping.map2rxnorm import apply_rxnorm_mapping




def rxnorm_map(
    df,
    rrf_path, 
    out):
    
    df = apply_rxnorm_mapping(df, rrf_path, out)
    return df 
    
