import pandas as pd


def getcsv(df):
    # 计算每一列的最小值和最大值
    min_val = df['WINDSPEED'].min()
    max_val = df['WINDSPEED'].max()
    # 对指定列进行最小-最大归一化
    df['WINDSPEED'] = (df['WINDSPEED'] - min_val) / (max_val - min_val)

    min_val = df['WINDDIRECTION'].min()
    max_val = df['WINDDIRECTION'].max()
    # 对指定列进行最小-最大归一化
    df['WINDDIRECTION'] = (df['WINDDIRECTION'] - min_val) / (max_val - min_val)

    min_val = df['TEMPERATURE'].min()
    max_val = df['TEMPERATURE'].max()
    # 对指定列进行最小-最大归一化
    df['TEMPERATURE'] = (df['TEMPERATURE'] - min_val) / (max_val - min_val)

    min_val = df['HUMIDITY'].min()
    max_val = df['HUMIDITY'].max()
    # 对指定列进行最小-最大归一化
    df['HUMIDITY'] = (df['HUMIDITY'] - min_val) / (max_val - min_val)

    min_val = df['PRESSURE'].min()
    max_val = df['PRESSURE'].max()
    # 对指定列进行最小-最大归一化
    df['PRESSURE'] = (df['PRESSURE'] - min_val) / (max_val - min_val)

    min_val = df['HUMIDITY'].min()
    max_val = df['HUMIDITY'].max()
    # 对指定列进行最小-最大归一化
    df['HUMIDITY'] = (df['HUMIDITY'] - min_val) / (max_val - min_val)

    return df

