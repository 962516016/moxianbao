import pandas as pd


def getcsv(df):



    df = df.set_index('DATATIME')
    df.index = pd.to_datetime(df.index)

    # 重采样+线性插值
    df = df.resample('15T').asfreq()
    df.interpolate(method='linear', limit_direction='both').reset_index()

    df = df.reset_index()
    return df
    # df_final.to_csv('重采样并线性插值版.csv', index=True)


