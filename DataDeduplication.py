import pandas as pd
# 去除重复值

def getcsv(df):
    df.drop_duplicates(subset=['DATATIME'], keep='first', inplace=True)
    return df

    # df = pd.read_csv('datatmp.csv', parse_dates=['DATATIME'], infer_datetime_format=True, dayfirst=True)
    # # print(df.columns)
    # # df.drop_duplicates(subset=['DATATIME'], keep='first', inplace=True)
    # data = []
    # for id in range(11, 21):
    #     data.append(df[df['TurbID'] == id])
    #
    # for i in range(10):
    #     print(i + 11)
    #     print(len(data[i]))
    #     data[i].drop_duplicates(subset=['DATATIME'], keep='first', inplace=True)
    #     print(len(data[i]))
    #
    # df_final = pd.concat(data)
    # return df_final
    # df_final.to_csv('去重版.csv', index=False)


