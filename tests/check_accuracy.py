import pandas as pd

"""
data = "PPMI"
col_str_name = "LEDTRT_"
"""

data = "ADNI"
col_str_name = "CMMED_"


"""
data = "simGPT"
col_str_name = "rx_note_"
"""

df_gold = pd.read_csv(data + '_evaluation_sample.csv')
df_pred = pd.read_csv('../data/' + data + '/output/out_' + data + '.csv')

df_eval = df_gold.merge(
    df_pred[[col_str_name + 'simulated', "frequency_per_day"]],
    on=col_str_name + 'simulated',
    how="left"
)



def within_tolerance(pred, true, tol=0.01):

    def try_float(x):
        try:
            return float(x)
        except:
            return x

    # normalize strings
    if isinstance(pred, str):
        pred_clean = pred.strip().lower()
    else:
        pred_clean = pred

    if isinstance(true, str):
        true_clean = true.strip().lower()
    else:
        true_clean = true

    # attempt numeric conversion
    pred_clean = try_float(pred_clean)
    true_clean = try_float(true_clean)

    # -------------------------------
    # both missing → correct
    # -------------------------------
    if pd.isna(pred_clean) and pd.isna(true_clean):
        return True

    # one missing → incorrect
    if pd.isna(pred_clean) or pd.isna(true_clean):
        return False

    # -------------------------------
    # BOTH STRINGS → exact match
    # -------------------------------
    if isinstance(pred_clean, str) and isinstance(true_clean, str):
        return pred_clean == true_clean

    # -------------------------------
    # ONE STRING, ONE NUMERIC → incorrect
    # -------------------------------
    if isinstance(pred_clean, str) or isinstance(true_clean, str):
        return False

    # -------------------------------
    # NUMERIC COMPARISON
    # -------------------------------
    return abs(pred_clean - true_clean) <= tol



df_eval["both_missing"] = (
    df_eval["expected_frequency_per_day"].isna() & df_eval["frequency_per_day"].isna()
)

df_eval["missed_prediction"] = (
    df_eval["expected_frequency_per_day"].notna() & df_eval["frequency_per_day"].isna()
)


df_eval["tolerance_match"] = df_eval.apply(
    lambda x: within_tolerance(x.frequency_per_day, x.expected_frequency_per_day),
    axis=1
)



tol_accuracy = df_eval["tolerance_match"].mean()
print(f"Tolerance accuracy: {tol_accuracy:.2%}")
print("Coverage:", df_eval["expected_frequency_per_day"].notna().mean())
print("Miss rate:", df_eval["missed_prediction"].mean())


both_missing = (
    df_eval["expected_frequency_per_day"].isna() & df_eval["frequency_per_day"].isna()
)

errors = df_eval[
    (~df_eval["tolerance_match"]) &
    ~(df_eval["expected_frequency_per_day"].isna() & df_eval["frequency_per_day"].isna())
]
errors.to_csv('/Users/emudr/Desktop/errors.csv')
