
# from src.rxnorm_mapping import apply_rxnorm_mapping
# from src.pick_best_rxnorm import pick_best_rxnorm
# from src.reorder_dose import reorder_combo_doses
# from src.get_drug_class import apply_rxclass_mapping
import pandas as pd
from preprocessing.preprocessing_pipeline import preprocess_medication_dataframe
from patterns.compile_normalization_patterns import build_normalization_pattern
from patterns.compile_frequency_patterns import build_frequency_pattern
from extraction.extraction_pipeline import extract_medication_entities
from postprocessing.postprocessing_pipeline import clean_extracted_text
from rxnorm_mapping.rxnorm_pipeline import rxnorm_map




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

df = preprocess_medication_dataframe(df=df, raw_med_col = raw_med_col, compiled_patterns = compiled_norm_patterns)
df = extract_medication_entities(df = df, compiled_freq_patterns = compiled_freq_patterns,compiled_norm_patterns = compiled_norm_patterns)
df = clean_extracted_text(df=df, text_col="clean_text")
df = rxnorm_map(df, rrf_path, out = "1")
df.to_csv(outdir + 'p.csv')
janetl






df = apply_rxnorm_mapping(df, input_col= "paren_text", rrf_path="/Users/emudr/Desktop/EHRdata/RXNCONSO.RRF", out1 = "rxmatch0", out2 = "rxcui0", out3 = "score0", out4 = 'tty0', col_str_name = col_str_name)
df = apply_rxnorm_mapping(df, input_col= col_str_name + "no_time", rrf_path="/Users/emudr/Desktop/EHRdata/RXNCONSO.RRF", out1 = "rxmatch1", out2 = "rxcui1", out3 = "score1", out4 = 'tty1')
df = pick_best_rxnorm(df, col_str_name)
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

