from src.preprocessing import preprocess_medications
from src.frequency import run_frequency_extraction_layered
from src.dose import apply_dose_unit_extraction
from src.category_extraction import apply_category_extraction
from src.formulation import apply_extract_amount_and_form
from src.rxnorm_mapping import apply_rxnorm_mapping
from src.pick_best_rxnorm import pick_best_rxnorm
from src.reorder_dose import reorder_combo_doses
from src.get_drug_class import apply_rxclass_mapping
import pandas as pd

norm_path = "data/normalization_dictionary.csv"
freq_path = "data/frequency_dictionary.csv"
outdir = '/Users/emudr/Desktop/'


'''
## PPMI
data = 'PPMI'
col_str_name = "LEDTRT_"
df = pd.read_csv("data/PPMI/simulated/LEDD_Concomitant_Medication_Log_simulated.csv")
subid = 'PATNO'
start_col = col_str_name + 'simulated'
'''


## ADNI
data = "ADNI"
col_str_name = 'CMMED_'
df = pd.read_csv("data/ADNI/simulated/RECCMEDS_25Mar2026_simulated.csv")
subid = 'PTID'
start_col = col_str_name + 'simulated'


'''
## Simulated data 
data = "simGPT"
col_str_name = "rx_note_" 
df = pd.read_csv("data/simGPT/simulated/simGPT.csv")
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




df = preprocess_medications(df, input_col = start_col, output_col = col_str_name + 'normalized', replacement_path = norm_path)
df = apply_extract_amount_and_form(df, input_col = col_str_name + "normalized", output_col = col_str_name + 'no_form' , path = norm_path) 
df = apply_category_extraction(df, input_col = col_str_name + "no_form", output_col = col_str_name + "no_release", category = "release" , data_path = norm_path)
df = run_frequency_extraction_layered(df,  input_col = col_str_name + 'no_release', clean_med_name = col_str_name + 'normalized_no_frequency', output_col = 'frequency_per_day', path = freq_path)
df = apply_dose_unit_extraction(df, input_col = col_str_name + 'normalized_no_frequency', output_col = col_str_name + "no_dose_unit", path = norm_path)
df.to_csv(outdir + 'alex.csv')
df = apply_category_extraction(df, input_col = col_str_name + "no_dose_unit", output_col = col_str_name + "no_route", category = "route" , data_path = norm_path)
df = apply_category_extraction(df, input_col = col_str_name + "no_route", output_col = col_str_name + "no_device", category = "device" , data_path = norm_path) 
df = apply_category_extraction(df, input_col = col_str_name + "no_device", output_col = col_str_name + "no_time", category = "time_of_day" , data_path = norm_path)


df["numbers"] = df[col_str_name + "no_time"].str.findall(r"\d+(?:\.\d+)?")
df[col_str_name + "no_time"] = df[col_str_name + "no_time"].str.replace(r"\d+(?:\.\d+)?", "", regex=True)
df[col_str_name + "no_time"] = df[col_str_name + "no_time"].str.replace(r'/\s*$', '', regex=True) # remove trailing '/'
df["paren_text"] = df[col_str_name + "no_time"].str.findall(r"\(([^)]*)\)")    


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

