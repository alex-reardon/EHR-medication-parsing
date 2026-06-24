

import pandas as pd
import os
os.chdir("/Users/emudr/PPMI_LEDD/data/PPMI_archived/output/")

df = pd.read_csv("out_PPMI_archived.csv")
print(df["parenthetical_text"].apply(lambda x: type(x)).value_counts())