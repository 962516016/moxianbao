from sklearn.impute import KNNImputer
import pandas as pd
# df = pd.read_csv('重采样并线性插值版.csv')
# df['TurbID'].fillna(method='ffill', inplace=True)


def getcsv(df):
    df['TurbID'].fillna(method='ffill', inplace=True)
    df = df.reset_index()
    dfcopy = df.copy()
    dfcopy1 = df.copy()
    dfcopy = dfcopy.drop('DATATIME', axis=1)
    dfcopy = dfcopy.drop('TurbID', axis=1)
    imputer = KNNImputer(n_neighbors=5, weights='uniform')
    df = pd.DataFrame(imputer.fit_transform(dfcopy), columns=dfcopy.columns)
    df['DATATIME'] = dfcopy1['DATATIME']
    df['TurbID'] = dfcopy1['TurbID']
    df = df[['TurbID','DATATIME',"WINDSPEED","PREPOWER","WINDDIRECTION","TEMPERATURE","HUMIDITY","PRESSURE","ROUND(A.WS,1)","ROUND(A.POWER,0)","YD15"]]
    return df



