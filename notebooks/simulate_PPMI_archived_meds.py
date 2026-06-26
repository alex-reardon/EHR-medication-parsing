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

def contains_number(text):
    """Check if a string contains any numeric digit."""
    return bool(re.search(r'\d', str(text))) if pd.notna(text) else False

def map_route_col(df):
    route_map = {
        1: "IV",
        2: "IM",
        3: "PO",
        4: "SC",
        5: "PR",
        6: "Sublingual",
        7: "Inhaled",
        8: "Topical",
        9 : np.nan
        
    }
    df["ROUTE"] = df["ROUTE"].map(route_map)
    return df



def combine_row(row):
    cmtrt = row["CMTRT"]
    cmdose = row["CMDOSE"]
    cmdosu = row["CMDOSU"]
    cmdosfrq = row["CMDOSFRQ"]
    cmroute = row["ROUTE"]

    parts = [cmtrt]  # always include CMTRT

    if contains_number(cmtrt):
        # CMTRT has embedded dose numbers
        if pd.notna(cmdosu) and str(cmdosu).strip().upper() == "MG":
            # unit is MG — skip CMDOSE and CMDOSU, only append frequency
            pass
        else:
            # unit is NOT MG — merge in CMDOSE and CMDOSU
            if pd.notna(cmdose) and str(cmdose).strip() != "":
                parts.append(str(cmdose))
            if pd.notna(cmdosu) and str(cmdosu).strip() != "":
                parts.append(str(cmdosu))
    else:
        # No embedded number — merge in CMDOSE and CMDOSU unconditionally
        if pd.notna(cmdose) and str(cmdose).strip() != "":
            parts.append(str(cmdose))
        if pd.notna(cmdosu) and str(cmdosu).strip() != "":
            parts.append(str(cmdosu))

    # Always append frequency if present
    if pd.notna(cmdosfrq) and str(cmdosfrq).strip() != "":
        parts.append(str(cmdosfrq))

    # Always append route if present
    if pd.notna(cmroute) and str(cmroute).strip() != "":
        parts.append(str(cmroute))

    return " ".join(parts)


cols = ["CMTRT", "CMDOSE", "CMDOSU", "CMDOSFRQ", "ROUTE"]
df = df[df['PD_MOTOR_MED'] == 1]
df = map_route_col(df)
df["CMTRT_simulated"] = df[cols].apply(combine_row, axis=1)

col_reorder = ['REC_ID','PATNO','EVENT_ID', 'PAG_NAME', 'CMTRT_simulated', 'CMTRT', 'CMDOSE', 'CMDOSU', 'CMDOSFRQ', 'ROUTE', 'STARTDT', 'STOPDT',	'LEDD',	'ORIG_ENTRY', 'LAST_UPDATE', 'CMINDC']
df = df[col_reorder]
df.to_csv(dir + 'simulated/Concomitant_Medications-Archived_05Jun2026_simulated.csv')


import pandas as pd
from pathlib import Path

base_dir = Path(r"C:\Users\emudr\PPMI_LEDD\data\PPMI_archived\simulated")
main_file = base_dir / "Concomitant_Medications-Archived_05Jun2026_simulated.csv"
update_file = base_dir / "CMTRT_simulated_edited_part1.csv"

# Read files
main_df = pd.read_csv(main_file)
update_df = pd.read_csv(update_file)


keys = ["PATNO", "REC_ID"]

main_cols_to_pull = [
    "EVENT_ID", "PAG_NAME", "CMTRT", "CMDOSE", "CMDOSU", "CMDOSFRQ","ROUTE", 
    "STARTDT", "STOPDT", "LEDD", "ORIG_ENTRY",
    "LAST_UPDATE", "CMINDC"
]


update_df = update_df.merge(
    main_df[keys + main_cols_to_pull],
    on=keys,
    how="left"
)

update_df = update_df.rename(
    columns={"CMTRT_simulated": "CMTRT_simulated_orig","CMTRT_simulated_edited": "CMTRT_simulated"}
)

# Set the same index on both so pandas knows how to align rows
main_df_indexed = main_df.set_index(keys)
update_df_indexed = update_df.set_index(keys)


# This overwrites values in main_df_indexed wherever update_df_indexed
# has non-null values for matching index (PATNO, REC_ID) and matching columns
main_df_indexed.update(update_df_indexed)

# Bring the keys back as columns
main_df_updated = main_df_indexed.reset_index()



## add in edited col
edited_col_df = update_df[['REC_ID', 'CMTRT_simulated_edited_TF']]
main_df_updated = pd.merge(main_df_updated, edited_col_df, how = 'left', on = 'REC_ID')



new_file = base_dir / "Concomitant_Medications-Archived_05Jun2026_simulated_edited_part1.csv"
# Overwrite original file
main_df_updated.to_csv(new_file, index=False)

print(f"Replaced {len(update_df):,} rows")
print(f"Final row count: {len(main_df_updated):,}")