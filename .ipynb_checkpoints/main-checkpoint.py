from src.preprocessing import preprocess_medications
from src.frequency import apply_frequency_extraction
from src.dose import apply_dose_unit_extraction
from src.formulation import apply_formulation_extraction
from src.medication_extraction import apply_medication_extraction
import pandas as pd
data_path = "data/normalization_dictionary.csv"
outdir = '/Users/emudr/Desktop/'


## PPMI
df = pd.read_csv("data/PPMI/raw/LEDD_Concomitant_Medication_Log.csv")
df = df[['LEDTRT']]
df = preprocess_medications(df, input_col = 'LEDTRT', output_col = 'LEDTRT_normalized', replacement_path = data_path)
df =  apply_frequency_extraction(df,  input_col = 'LEDTRT_normalized', output_col = 'freq', path = 'data/normalization_dictionary.csv')
df = apply_dose_unit_extraction(df, input_col = 'LEDTRT_normalized', path = 'data/normalization_dictionary.csv')
df = apply_formulation_extraction(df, input_col = "LEDTRT_normalized", output_col = "release", release_path = 'data/normalization_dictionary.csv')
df.to_csv(outdir + 'ppmiprep.csv')

janetl

'''
## ADNI
outdir = '/Users/emudr/Desktop/'
data_path = 'data/'
df = pd.read_csv("data/ADNI/simulated/RECCMEDS_25Mar2026_simulated.csv")
df = df[['PTID', 'CMMED_simulated']]
df = preprocess_medications(df, input_col = 'CMMED_simulated', output_col = 'CMMED_normalized', replacement_path = 'data/ADNI/normalization_dictionary.csv')
df =  apply_frequency_extraction(df,  input_col = 'CMMED_normalized', output_col = 'freq', path = 'data/normalization_dictionary.csv')
df = apply_dose_unit_extraction(df, input_col = 'CMMED_normalized', path = 'data/normalization_dictionary.csv')
df.to_csv(outdir + 'check.csv')
df = apply_formulation_extraction(df, input_col = "CMMED_normalized", output_col = "release", release_path = 'data/normalization_dictionary.csv')
df.to_csv(outdir + 'prep.csv')
'''

## Simulated data 
outdir = '/Users/emudr/Desktop/'
data_path = 'data/'
df = pd.read_csv("data/simGPT/simGPT.csv")
df = preprocess_medications(df, input_col = 'rx_note', output_col = 'rx_note_normalized', replacement_path = 'data/normalization_dictionary.csv')
df =  apply_frequency_extraction(df,  input_col = 'rx_note_normalized', output_col = 'freq', path = 'data/normalization_dictionary.csv')
df = apply_dose_unit_extraction(df, input_col = 'rx_note_normalized', path = 'data/normalization_dictionary.csv')
df = apply_formulation_extraction(df, input_col = "rx_note_normalized", output_col = "release", release_path = 'data/normalization_dictionary.csv')
df.to_csv(outdir + 'simprep.csv')
