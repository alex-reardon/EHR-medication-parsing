from rxnorm_mapping.rxnorm_mapper import apply_rxnorm_mapping, build_rxnorm_lookup_table
from rxnorm_mapping.rxnorm_selector import apply_rxnorm_selector
from rxnorm_mapping.rxclass_mapper import apply_rxclass_mapping
from rxnorm_mapping.reorder_dose import apply_reorder_dose


def rxnorm_map(df, rxnorm_rrf_path, rxnrel_rrf_path):
    lookup_tables = build_rxnorm_lookup_table(rxnorm_rrf_path, rxnrel_rrf_path)
    df = apply_rxnorm_mapping(df, input_col="parenthetical_text", rxnorm_rrf_path=rxnorm_rrf_path, rxnrel_rrf_path=rxnrel_rrf_path, suffix="_parenthetical_text", lookup_tables=lookup_tables)
    df = apply_rxnorm_mapping(df, input_col="clean_text", rxnorm_rrf_path=rxnorm_rrf_path, rxnrel_rrf_path=rxnrel_rrf_path, suffix="_clean_text", lookup_tables=lookup_tables)
    df = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text", out_cols=("best_rxnorm_match", "best_rxcui", "best_score", "best_sbdf", "best_tty"))
    df = apply_rxclass_mapping(df, rxcui_col="best_rxcui", out_col="rxclass_atc", rela_source="ATC")
    df = apply_reorder_dose(df, input_col="parsed", match_col="best_rxnorm_match")
    return df

