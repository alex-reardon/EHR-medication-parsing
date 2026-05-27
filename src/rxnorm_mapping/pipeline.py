import pandas as pd

from rxnorm_mapping.rxnorm_mapper import apply_rxnorm_mapping
from rxnorm_mapping.rxnorm_selector import apply_rxnorm_selector
from rxnorm_mapping.rxclass_mapper import apply_rxclass_mapping

def rxnorm_map(
    df,
    rrf_path):

    #FIXME if parenthetical text 
    
    df = apply_rxnorm_mapping(df, input_col = "parenthetical_text", rxnorm_rrf_path = rrf_path, suffix = "_parenthetical_text")
    df = apply_rxnorm_mapping(df, input_col = "clean_text", rxnorm_rrf_path = rrf_path, suffix = "_clean_text")
    df = apply_rxnorm_selector(df, suffix_parenthetical_text = "_parenthetical_text", suffix_clean_text = "_clean_text", out_cols=("best_rxnorm_match", "best_rxcui", "best_score", "best_tty"))
    df = apply_rxclass_mapping(df, rxcui_col="best_rxcui", out_col="rxclass_atc", rela_source="ATC")
    return df 

