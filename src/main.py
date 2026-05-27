import pandas as pd
from patterns.compile_normalization_patterns import build_normalization_pattern
from patterns.compile_frequency_patterns import build_frequency_pattern
from preprocessing.pipeline import normalize_medication_text
from extraction.pipeline import extract_medication_entities
from postprocessing.pipeline import clean_medication_text
from rxnorm_mapping.pipeline import rxnorm_map #change to canonicalization



import os
os.chdir("/Users/emudr/PPMI_LEDD/src")
norm_path = "../data/normalization_dictionary.csv"
freq_path = "../data/frequency_dictionary.csv"
outdir = '/Users/emudr/Desktop/'


## PPMI
data = 'PPMI'
col_str_name = "LEDTRT_"
subid = 'PATNO'
raw_med_col = col_str_name + 'simulated'
df = pd.read_csv("../data/PPMI/simulated/LEDD_Concomitant_Medication_Log_simulated.csv")
df = df[[raw_med_col]]


# # ## ADNI
# data = "ADNI"
# col_str_name = 'CMMED_'
# subid = 'PTID'
# raw_med_col = col_str_name + 'simulated'
# df = pd.read_csv("../data/ADNI/simulated/RECCMEDS_25Mar2026_simulated.csv")
# df = df[[raw_med_col]]


# ## Simulated data 
# data = "simGPT"
# col_str_name = "rx_note_" 
# subid = ''
# raw_med_col = col_str_name + 'simulated'
# df = pd.read_csv("../data/simGPT/simulated/simGPT.csv")
# df = df[[raw_med_col]]


# ## EICU data 
# data = "eicu"
# col_str_name = "drugname_"
# subid= "patientunitstayid"
# raw_med_col = "drugname"
# df = pd.read_csv("/Users/emudr/Desktop/EHRdata/eicu_medication.csv")
# df = df.dropna(subset= ['drugname'])
# df = df.sample(n=2000, random_state=42) # FIXME DO ALL
# df = df[[raw_med_col]]




####
rrf_path="/Users/emudr/Desktop/EHRdata/rrf/RXNCONSO.RRF"
compiled_norm_patterns = build_normalization_pattern(path = norm_path)
compiled_freq_patterns = build_frequency_pattern(path = freq_path)
df = normalize_medication_text(df = df, raw_med_col = raw_med_col, compiled_patterns = compiled_norm_patterns)
df = extract_medication_entities(df = df, compiled_freq_patterns = compiled_freq_patterns,compiled_norm_patterns = compiled_norm_patterns)
df = clean_medication_text(df = df, text_col = "clean_text")
df = rxnorm_map(df, rrf_path)
df.to_csv('../data/' + data + '/output/out_' + data + '.csv')
janetl




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

