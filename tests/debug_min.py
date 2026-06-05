"""
stalevo_debug.py  —  run this standalone to trace the BN→SBD→SCD→MIN chain
for Stalevo (rxcui 1372713) using your local RRF files.
"""

import pandas as pd

RXNCONSO = "/Users/emudr/Desktop/EHRdata/RxNorm_full_05042026/rrf/RXNCONSO.RRF"
RXNREL   = "/Users/emudr/Desktop/EHRdata/RxNorm_full_05042026/rrf/RXNREL.RRF"

import os
print(os.path.getsize("/Users/emudr/Desktop/EHRdata/RxNorm_full_05042026/rrf/RXNREL.RRF"))
jaentl


cols = [
    "rxcui","lat","ts","lui","stt","sui","ispref","rxaui",
    "saui","scui","sdui","sab","tty","code","str","srl","suppress","cvf","empty"
]
rx = pd.read_csv(RXNCONSO, sep="|", header=None, names=cols, dtype=str)
rx["str_lower"] = rx["str"].str.lower().str.strip()

rel_cols = [
    "rxcui1","rxaui1","stype1","rel","rxcui2","rxaui2","stype2",
    "rela","rui","srui","sab","sl","dir","rg","suppress","cvf","empty"
]
rel = pd.read_csv(RXNREL, sep="|", header=None, names=rel_cols, dtype=str)
rel_rx = rel[(rel["sab"] == "RXNORM") & (rel["suppress"] == "N")]

# 1. What do the Stalevo SBD strings actually look like lowercased?
sbd_stalevo = rx[
    (rx["tty"] == "SBD") &
    (rx["sab"] == "RXNORM") &
    (rx["str"].str.lower().str.contains("stalevo", na=False))
]
print("=== Stalevo SBD str_lower values ===")
for s in sbd_stalevo["str_lower"].tolist():
    print(repr(s))

# 2. Does the bracket match actually work?
print("\n=== Bracket match test ===")
print("Looking for strings ending with: '[stalevo]'")
matches = rx[rx["str_lower"].str.endswith("[stalevo]")]
print(f"Found {len(matches)} matches")
print(matches[["rxcui","tty","sab","str_lower"]].to_string())

# 3. What RXNREL edges do those SBD rxcuis (404551 etc) actually have?
stalevo_sbd_rxcuis = ["404551", "404552", "404553", "730992", "810087", "810094"]
print("\n=== RXNREL edges for known Stalevo SBDs ===")
edges = rel_rx[
    rel_rx["rxcui1"].isin(stalevo_sbd_rxcuis) |
    rel_rx["rxcui2"].isin(stalevo_sbd_rxcuis)
]
print(edges[["rxcui1","rela","rxcui2"]].head(30).to_string() if not edges.empty else "  (none)")

# 4. What MIN rxcuis exist at all?
min_rows = rx[(rx["tty"] == "MIN") & (rx["sab"] == "RXNORM") & (rx["suppress"] == "N")]
print(f"\n=== MIN count: {len(min_rows)} ===")
print(min_rows[["rxcui","str"]].head(10).to_string())