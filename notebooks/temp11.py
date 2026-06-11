import pandas as pd

# Read the CSV
df = pd.read_csv(
    "/Users/emudr/Downloads/Concomitant_Medications_LEDD_corrected_final.csv"
)

# Filter rows where LEDD_valid == 1
df_valid = df[df["LEDD_VALID"] == 1].copy()

# Check result
print(f"Rows with LEDD_valid == 1: {len(df_valid)}")
print(df_valid.head())


df_valid.to_csv(
    "/Users/emudr/Downloads/Concomitant_Medications_LEDD_valid_only.csv",
    index=False
)