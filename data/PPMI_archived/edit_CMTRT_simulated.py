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