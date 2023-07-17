import dtale
import pandas as pd

name = '0001in.csv'
df = pd.read_csv(name)
dtale.show(df).open_browser()

