import pandas as pd
import re 
import numpy as np
import unicodedata 
import random


dir = '/Users/emudr/PPMI_LEDD/data/PPMI_archived/'
raw_file = 'raw/Concomitant_Medications-Archived_05Jun2026.csv'
df = pd.read_csv(dir + raw_file, low_memory = False)


daily_phrases = [
    "x per day",
    "times per day",
    "x a day",
    "a day", 
    "daily",
    "each day",
    "times every day",
    "times everyday",
    "x every day", 
    "per day",
    "per 24 hours",
    "every 24 hours"
]

form_phrases = [
    'pill', 
    'pills', 
    'capsule', 
    'capsules',
    'tab', 
    'tabs', 
    'softgel',
    'dose']


def add_phrase(df, col,  phrase_list):
    def _add(freq):
        if pd.isna(freq):
            return None
        return f"{float(freq)} {random.choice(phrase_list)}"

    df[col] = df[col].apply(_add)
    return df


# df = add_phrase(df, 'DM', daily_phrases)
# df = add_phrase(df, 'LEDDOSE', form_phrases) 


def combine_row(row):
    return " ".join(
        str(x) for x in row
        if pd.notna(x) and str(x).strip() != ""
    )

cols = ["CMTRT", "CMDOSE", "CMDOSU", "CMDOSFRQ"]
df = df[df['PD_MOTOR_MED'] == 1]
df["CMTRT_simulated"] = df[cols].apply(combine_row, axis=1)

col_reorder = ['REC_ID','PATNO','EVENT_ID', 'PAG_NAME', 'CMTRT_simulated', 'CMTRT', 'CMDOSE', 'CMDOSU', 'CMDOSFRQ', 'STARTDT', 'STOPDT',	'LEDD',	'ORIG_ENTRY', 'LAST_UPDATE', 'CMINDC']
df = df[col_reorder]
df.to_csv(dir + 'simulated/Concomitant_Medications-Archived_05Jun2026_simulated.csv')