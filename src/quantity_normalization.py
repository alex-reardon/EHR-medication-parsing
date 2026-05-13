import pandas as pd

# -------------------------------
# APPLY REPLACEMENTS
# -------------------------------
def apply_rules(df, compiled_rules):
    
    updated = df["clean_text"].astype(str).copy()

    for rule in compiled_rules:

        pattern = rule["pattern"]

        repl = rule["replacement"]

        repl = (
            ''
            if pd.isna(repl)
            or str(repl).strip() == ''
            else str(repl)
        )

        updated = updated.str.replace(
            pattern,
            repl,
            regex=True
        )

    updated = (
        updated
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    return updated


def apply_quantity_normalization(df, compiled_rules) : 
    df["clean_text"] = apply_rules(df, compiled_rules)
    return df 