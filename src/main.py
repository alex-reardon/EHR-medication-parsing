

import pandas as pd
from pathlib import Path
from patterns.compile_normalization_patterns import build_normalization_pattern
from patterns.compile_frequency_patterns import build_frequency_pattern
from preprocessing.pipeline import normalize_medication_text
from extraction.pipeline import extract_medication_entities
from postprocessing.pipeline import clean_medication_text
from rxnorm_mapping.pipeline import rxnorm_map
from daily_dose_calculation.pipeline import calculate_total_daily_dose


ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "data"
TEMP_DIR   = Path.home() / "Desktop"
RXNORM_DIR = TEMP_DIR / "EHRdata" / "RxNorm_full_05042026" / "rrf"

norm_path = DATA_DIR / "normalization_dictionary.csv"
freq_path = DATA_DIR / "frequency_dictionary.csv"

def save_temp(df, name):
    df.to_csv(TEMP_DIR / f"{name}.csv")

def read_temp(name):
    return pd.read_csv(TEMP_DIR / f"{name}.csv")

# ## PPMI
# data = 'PPMI'
# col_str_name = "LEDTRT_"
# subid = 'PATNO'
# raw_med_col = col_str_name + 'simulated'
# df = pd.read_csv(DATA_DIR / "PPMI/simulated/LEDD_Concomitant_Medication_Log_simulated.csv")
# df = df[[raw_med_col, 'LEDD']]


# # ## ADNI
# data = "ADNI"
# col_str_name = 'CMMED_'
# subid = 'PTID'
# raw_med_col = col_str_name + 'simulated'
# df = pd.read_csv(DATA_DIR / "ADNI/simulated/RECCMEDS_25Mar2026_simulated.csv")
# df = df[[raw_med_col]]


# ## Simulated data
# data = "simGPT"
# col_str_name = "rx_note_"
# subid = ''
# raw_med_col = col_str_name + 'simulated'
# df = pd.read_csv(DATA_DIR / "simGPT/simulated/simGPT.csv")
# df = df[[raw_med_col]]


# ## EICU data
# data = "eicu"
# col_str_name = "drugname_"
# subid= "patientunitstayid"
# raw_med_col = "drugname"
# df = pd.read_csv(TEMP_DIR / "EHRdata" / "eicu_medication.csv")
# df = df.dropna(subset= ['drugname'])
# df = df.sample(n=2000, random_state=42) # FIXME DO ALL
# df = df[[raw_med_col]]

## PPMI Archived
data = "PPMI_archived"
col_str_name = "CMTRT_"
subid= "PATNO"
raw_med_col = col_str_name + 'simulated'
df = pd.read_csv(DATA_DIR / "PPMI_archived/simulated/Concomitant_Medications-Archived_05Jun2026_simulated_edited_part1.csv")
df = df[['PATNO', 'REC_ID', raw_med_col, 'CMDOSE', 'CMDOSU','LEDD']]



####
rxnorm_rrf_path = RXNORM_DIR / "RXNCONSO.RRF"
rxnrel_rrf_path = RXNORM_DIR / "RXNREL.RRF"
compiled_norm_patterns = build_normalization_pattern(path = norm_path)
compiled_freq_patterns = build_frequency_pattern(path = freq_path)
df = normalize_medication_text(df = df, raw_med_col = raw_med_col, compiled_patterns = compiled_norm_patterns)
df = extract_medication_entities(df = df, compiled_freq_patterns = compiled_freq_patterns,compiled_norm_patterns = compiled_norm_patterns)
df = clean_medication_text(df = df, text_col = "clean_text")
df = rxnorm_map(df, rxnorm_rrf_path, rxnrel_rrf_path)
# save_temp(df, 'df1')
# df = read_temp('df1')

df = calculate_total_daily_dose(
    df,
    dose_col="dose", #FIXME
    frequency_col="frequency_per_day",
    amount_col="amount",
)
df.to_csv(DATA_DIR / data / "output" / f"out_{data}.csv")




cols = [
    #subid,
    col_str_name + "simulated",
    'parsed', #FIXME
    'best_rxnorm_match',
    'best_tty',
    'best_sbdf',
    "release",
    "dose",
    "amount",
    "frequency_per_day",
    "dose_reordered",
    "LEDD"
]
df = df[cols]
df.to_csv(DATA_DIR / data / "output" / f"outtemp_{data}.csv")


# change output_col to clean_text_col
