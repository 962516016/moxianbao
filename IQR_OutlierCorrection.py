import pandas as pd

def replace_outliers_with_mean(df, cols, threshold=3):
    """
    将离群值替换为平均值

    参数:
    df: 输入的DataFrame数据集
    cols: 需要处理离群值的列名列表
    threshold: 离群值的阈值，默认为3，表示超过平均值三倍标准差的值为离群值

    返回:
    替换离群值后的DataFrame
    """
    for col in cols:
        mean = df[col].mean()
        std = df[col].std()
        outliers = (df[col] - mean).abs() > threshold * std
        df.loc[outliers, col] = mean

    return df



def getcsv(df):
    # 处理windspeed的离群点
    df.loc[df["WINDSPEED"] >= 30, "WINDSPEED"] = pd.NA
    df['WINDSPEED'].fillna(method='ffill', inplace=True)
    cols = ['PREPOWER', 'TEMPERATURE', 'HUMIDITY', 'PRESSURE', 'ROUND(A.WS,1)', 'ROUND(A.POWER,0)', 'YD15']
    df1 = replace_outliers_with_mean(df, cols)

    df = df1[['TurbID', 'DATATIME', 'WINDSPEED', 'PREPOWER',
              'WINDDIRECTION', 'TEMPERATURE', 'HUMIDITY', 'PRESSURE', 'ROUND(A.WS,1)', 'ROUND(A.POWER,0)', 'YD15']]

    return df

