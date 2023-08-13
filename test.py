# import dtale
# import pandas as pd
#
# name = '0001in.csv'
# df = pd.read_csv(name)
# dtale.show(df).open_browser()

from dataprep.datasets import load_dataset, get_dataset_names
from dataprep.eda import create_report


print('测试', get_dataset_names())

df = load_dataset('covid19')
create_report(df).show_browser()
print('done')