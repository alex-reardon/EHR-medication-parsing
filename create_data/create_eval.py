import pandas as pd

data = 'ppmi'

df = pd.read_csv('/Users/emudr/PPMI_LEDD/data/' +data+ '/output/out_' + data +'.csv')
sample_df = (
    df.drop_duplicates()
      .sample(n=200, random_state=42)
)

sample_df.to_csv('/Users/emudr/PPMI_LEDD/data/' +data+ '/eval/eval_' + data + '.csv', index = False)

