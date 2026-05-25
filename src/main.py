import pandas as pd
from patterns.compile_normalization_patterns import build_normalization_pattern
from patterns.compile_frequency_patterns import build_frequency_pattern
from preprocessing.pipeline import normalize_medication
from extraction.pipeline import extract_medication_entities
from postprocessing.pipeline import clean_extracted_text
from rxnorm_mapping.pipeline import rxnorm_map



import os
os.chdir("/Users/emudr/PPMI_LEDD/src")


norm_path = "../data/normalization_dictionary.csv"
freq_path = "../data/frequency_dictionary.csv"
outdir = '/Users/emudr/Desktop/'


# ## PPMI
# data = 'PPMI'
# col_str_name = "LEDTRT_"
# df = pd.read_csv("../data/PPMI/simulated/LEDD_Concomitant_Medication_Log_simulated.csv")
# subid = 'PATNO'
# raw_med_col = col_str_name + 'simulated'
# df = df[[raw_med_col]]


## ADNI
data = "ADNI"
col_str_name = 'CMMED_'
df = pd.read_csv("../data/ADNI/simulated/RECCMEDS_25Mar2026_simulated.csv")
subid = 'PTID'
raw_med_col = col_str_name + 'simulated'
df = df[[raw_med_col]]
# data_path = (
#     ROOT /
#     "data" /
#     "ADNI" /
#     "simulated" /
#     "RECCMEDS_25Mar2026_simulated.csv"
# )


'''
## Simulated data 
data = "simGPT"
col_str_name = "rx_note_" 
df = pd.read_csv("../data/simGPT/simulated/simGPT.csv")
subid = ''
start_col = col_str_name + 'simulated'
'''

'''
## EICU data 
data = "eicu"
col_str_name = "drugname_"
df = pd.read_csv("/Users/emudr/Desktop/EHRdata/eicu_medication.csv")
subid= "patientunitstayid"
start_col = "drugname"
df = df.dropna(subset= ['drugname'])
df = df.sample(n=2000, random_state=42) # FIXME DO ALL
'''

####
rrf_path="/Users/emudr/Desktop/EHRdata/RXNCONSO.RRF"
compiled_norm_patterns = build_normalization_pattern(path = norm_path)
compiled_freq_patterns = build_frequency_pattern(path = freq_path)

df = normalize_medication(df = df, raw_med_col = raw_med_col, compiled_patterns = compiled_norm_patterns)
df = extract_medication_entities(df = df, compiled_freq_patterns = compiled_freq_patterns,compiled_norm_patterns = compiled_norm_patterns)
df = clean_extracted_text(df=df, text_col = "clean_text")
df = rxnorm_map(df, rrf_path)
df.to_csv(outdir + 'p.csv')
janetl





df = apply_rxclass_mapping(df, rxcui_col="rxcui", out_col="drug_class", rela_source="ATC")
df = reorder_combo_doses(df=df, dose_col='dose', rxmatch_col='rxmatch', med_string_col='final', out_col='dose_reordered', threshold=85)

mapped = len(df[df['rxmatch'].notna()])
print(f"FINAL {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")


cols = [
    #subid,
    col_str_name + "simulated",
    col_str_name + "normalized",
    'final', 
    'rxmatch', 
    "amount",
    "form",
    "release",
    "is_prn",
    "frequency_per_day",
    "dose_reordered",
    "route",
    'MIN', 
    "time_of_day",
    "numbers",
    'rxcui', 
    'score', 
    'tty', 
    'drug_class',
]
df = df[cols]
df.to_csv('data/' + data + '/output/out_' + data + '.csv')


# change output_col to clean_text_col

