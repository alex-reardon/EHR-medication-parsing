import pandas as pd
import numpy as np
import os



def flag_ledd_agreement(df, col_a="LEDD", col_b="levodopa_ledd", tolerance=0.1):
    """
    Returns rows where col_a and col_b disagree.
    - Numeric columns: compared within +/- tolerance using np.isclose
    - String columns: exact string match
    - Both null: treated as a match (excluded from mismatches)
    """
    df = df.copy()

    a = pd.to_numeric(df[col_a], errors="coerce")
    b = pd.to_numeric(df[col_b], errors="coerce")

    both_numeric = a.notna() & b.notna()
    both_null = df[col_a].isna() & df[col_b].isna()

    numeric_match = pd.Series(False, index=df.index)
    numeric_match[both_numeric] = np.isclose(
        a[both_numeric], b[both_numeric], atol=tolerance
    )

    string_match = df[col_a].astype(str) == df[col_b].astype(str)

    match = numeric_match | string_match | both_null
    mismatches = df[~match]

    n_total = len(df)
    n_match = match.sum()
    n_mismatch = len(mismatches)

    print(
        f"Agreement Check ({col_a} vs {col_b}):\n"
        f"  Total rows     : {n_total}\n"
        f"  Matching       : {n_match} ({n_match/n_total:.1%})\n"
        f"  Mismatching    : {n_mismatch} ({n_mismatch/n_total:.1%})\n"
        f"  Tolerance      : +/-{tolerance}\n"
    )

    return mismatches


# ── Load ──────────────────────────────────────────────────────────────────────
data = "PPMI_archived"
df = pd.read_csv(f"/Users/emudr/PPMI_LEDD/data/{data}/output/out_{data}.csv")

# ── Find mismatches ───────────────────────────────────────────────────────────
mismatches = flag_ledd_agreement(df, col_a="LEDD", col_b="levodopa_ledd", tolerance=0.1)
cols = [ "PATNO", "REC_ID", "CMTRT_simulated", 
"CMDOSE", "CMDOSU", 
"dose",  "token_order_flipped", "dose_reordered",
"clean_text", "best_rxnorm_match", "canonical_LEDD_med", "parsed",
 "amount", "release", "frequency_per_day","ledd_factor_numeric",
 "levodopa_ledd","LEDD", 
"residual_numbers", "residual_tokens"]
mismatches = mismatches[cols]
# ── Save ──────────────────────────────────────────────────────────────────────
desktop_path = os.path.expanduser("~/Desktop/ledd_mismatches.csv")
mismatches.to_csv(desktop_path, index=False)
print(f"Saved {len(mismatches)} mismatched rows to {desktop_path}")


janelt


import pandas as pd
import numpy as np
def flag_ledd_agreement(df, col_a="LEDD", col_b="levodopa_ledd", tolerance=0.1):
    df = df.copy()

    a = pd.to_numeric(df[col_a], errors="coerce")
    b = pd.to_numeric(df[col_b], errors="coerce")

    comparable = a.notna() & b.notna()
    diff = (a - b).abs()

    df["ledd_diff"] = diff.where(comparable)
    df["ledd_match"] = np.where(comparable, diff <= tolerance, np.nan)

    n_comparable = comparable.sum()
    n_match = (df["ledd_match"] == True).sum()
    print(
        f"LEDD Agreement Check: "
        f"{n_match}/{n_comparable} comparable rows match "
        f"within +/-{tolerance} "
        f"({n_match/n_comparable:.1%})" if n_comparable else
        "LEDD Agreement Check: no comparable rows"
    )

    # Filter to only rows where numeric cols disagree (or strings differ)
    numeric_mismatch = df["ledd_match"] == False

    string_cols = [c for c in df.columns if df[c].dtype == object and c not in [col_a, col_b]]
    string_mismatch = pd.Series(False, index=df.index)
    for c in string_cols:
        if c in df.columns:
            string_mismatch |= df[c].astype(str) != df[c].astype(str)  # placeholder — see note

    mismatches = df[numeric_mismatch]
    return mismatches


data = "PPMI_archived"
df = pd.read_csv('/Users/emudr/PPMI_LEDD/data/' + data + '/output/out_' + data + '.csv')

mismatches = df[df["LEDD"] != df["levodopa_ledd"]]
import os
desktop_path = os.path.expanduser("~/Desktop/ledd_mismatches.csv")
mismatches.to_csv(desktop_path, index=False)
print(f"Saved {len(mismatches)} mismatched rows to {desktop_path}")
janetl

mismatches = flag_ledd_agreement(df, col_a="LEDD", col_b="levodopa_ledd", tolerance=0.1)

import os
desktop_path = os.path.expanduser("~/Desktop/ledd_mismatches.csv")
mismatches.to_csv(desktop_path, index=False)
print(f"Saved {len(mismatches)} mismatched rows to {desktop_path}")