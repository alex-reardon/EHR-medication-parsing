import pandas as pd


def sample_rows(df: pd.DataFrame, n: int = 200, seed: int = 42) -> pd.DataFrame:
    if df is None or len(df) == 0:
        raise ValueError("DataFrame is empty")

    n = min(n, len(df))
    sample = df.sample(n=n, random_state=seed).copy()
    print(f"Sampled {len(sample)} rows out of {len(df)}")
    return sample


"""
dataset = 'PPMI_'
outdir = '/Users/emudr/Desktop/'
df = pd.read_csv("../data/PPMI/simulated/LEDD_Concomitant_Medication_Log_simulated.csv")
df = df.drop_duplicates(subset=["LEDTRT_simulated"])
"""

'''
dataset= 'ADNI_'
outdir = '/Users/emudr/Desktop/'
df = pd.read_csv("../data/ADNI/simulated/RECCMEDS_25Mar2026_simulated.csv")
df = df.drop_duplicates(subset=["CMMED_simulated"])
'''

dataset = 'simGPT_'
outdir = '/Users/emudr/Desktop/'
df = pd.read_csv("../data/simGPT/simGPT.csv")
df = df.drop_duplicates(subset = ["rx_note"])


df_sample = sample_rows(df, n=200)
df_sample = df_sample.reset_index(drop=True)
df_sample["eval_id"] = df_sample.index
df_sample.to_csv(outdir + dataset + "evaluation_sample.csv", index=False)