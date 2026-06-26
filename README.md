# EHR Medication Parsing Pipeline

Parsing canonical medication name, dose, release, formulation, etc. from free-text concomitant medication entries in clinical research datasets (PPMI, ADNI, eICU, simulated).

---

## Pipeline overview (`src/main.py`)

```
Raw medication text
       │
       ▼
1. Preprocessing        normalize_medication_text()
       │                  - Basic text cleaning (lowercasing, punctuation)
       │                  - Unit normalization  (e.g. "milligrams" → "mg")
       │                  - Quantity normalization  (e.g. "one" → 1)
       ▼
2. Extraction           extract_medication_entities()
       │                  - Formulation  (tablet, capsule, patch, …)
       │                  - Release type  (immediate, extended, …)
       │                  - PRN / as-needed flag
       │                  - Frequency per day
       │                  - Dose value(s)
       │                  - Route, device, timing, meal relation
       │                  - Parenthetical text (e.g. brand names in parentheses)
       ▼
3. Postprocessing       clean_medication_text()
       │                  - Strip extraction artifacts from clean_text
       │                  - Flag residual unmapped numbers
       ▼
4. RxNorm mapping       rxnorm_map()
       │                  - Map clean_text and parenthetical_text to RxNorm CUIs
       │                  - Select best match (best_rxnorm_match, best_sbdf, best_tty)
       │                  - Append ATC drug class via RxClass
       ▼
5. Daily dose calc      calculate_total_daily_dose()
       │                  - Canonicalize medication name for LEDD lookup
       │                  - Detect and fix ingredient order in combo drugs
       │                    (e.g. carbidopa/levodopa vs levodopa/carbidopa)
       │                  - Expand multi-strength doses into separate rows
       │                    (e.g. "25/100 mg" → row for 25 mg + row for 100 mg)
       │                  - Compute daily_dose = dose × frequency_per_day × amount
       │                  - Merge LEDD conversion factors from ledd_conversion_factors.csv
       │                  - Compute levodopa_ledd = total_levodopa_daily_dose × factor
       ▼
Output CSVs
  data/<dataset>/output/out_<dataset>.csv       ← full output
```

---

## Supported datasets

| Dataset | ID column | Raw medication column | 
|---|---|---|---|
| PPMI archived | `PATNO` | `CMTRT_simulated` | 
| PPMI | `PATNO` | `LEDTRT_simulated` |
| ADNI | `PTID` | `CMMED_simulated` |
| simGPT | — | `rx_note_simulated` | 
| eICU | `patientunitstayid` | `drugname` |



## Key input files

| File | Purpose |
|---|---|
| `data/normalization_dictionary.csv` | Regex rules for text/unit/quantity normalization |
| `data/frequency_dictionary.csv` | Regex rules for frequency parsing |
| `data/ledd_conversion_factors.csv` | LEDD conversion factors by drug and release type |

---

## Key output columns

| Column | Description |
|---|---|
| `clean_text` | Normalized medication text after extraction |
| `best_rxnorm_match` | Best-matched RxNorm drug name |
| `best_sbdf` | RxNorm SBDF concept (drug + form + dose) |
| `canonical_LEDD_med` | Standardized name used for LEDD factor lookup |
| `release` | Release type (IR / ER / CR / …) |
| `dose` | Extracted dose string (may contain multiple values) |
| `dose_reordered` | Dose reordered to match LEDD ingredient order |
| `frequency_per_day` | Numeric doses per day |
| `amount` | Number of units taken per dose |
| `daily_dose_1/2/3` | Per-component daily dose (mg/day) |
| `ledd_conversion_factor` | Lookup factor for this drug/release combination |
| `levodopa_ledd` | Final LEDD value (mg levodopa equivalent/day) |
| `LEDD` | Ground-truth LEDD from source data (for validation) |
