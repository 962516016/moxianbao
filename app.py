import glob
import json
import os
import secrets
import random
import shutil
import socket
import zipfile
from datetime import datetime, timedelta
from urllib.parse import unquote

import joblib
import matplotlib.pyplot as plt
import matplotx
import numpy as np
import openai
import pandas as pd
import pymysql
import requests
from flask import Flask, jsonify, request, send_file, render_template, session, redirect
from flask_cors import CORS
from lightgbm import LGBMRegressor, early_stopping
from matplotlib.ticker import MaxNLocator
from sklearn.model_selection import train_test_split

import DataDeduplication
import IQR_OutlierCorrection
import KNN_FillNaN
import Normal
import Resample
import env
# from dialog import *
from env import DB_CONFIG
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# 字典存储各种功能对应的符号
api_list = {
    'upload_file': '0',
    'data_analyze': '1',
    'online_predict': '2',
    'gptapi_analyze': '3',
    'download_resfile': '4',
    'getmodel': '5',
    'api': '6'
}


# _________________________________________________________________________数据库连接_________________________________________________________________________
# 创建 pymysqlpool 连接池
def get_connection():
    connection = pymysql.connect(host=DB_CONFIG['host'], port=DB_CONFIG['port'], user=DB_CONFIG['user'],
                                 password=DB_CONFIG['password'], db=DB_CONFIG['database'])
    return connection


# _________________________________________________________________________功能性函数_________________________________________________________________________
# 原有模型的预测准确度
def res_predict(df_path, model_path):
    df = pd.read_csv(df_path)
    model = joblib.load(model_path)
    output = model.predict(df[['WINDSPEED', 'WINDSPEED2']])
    return output


origin_model_resYD15 = res_predict('模型相似度检测/test.csv', 'usingmodels/model1.pkl')
origin_model_resPOWER = res_predict('模型相似度检测/test.csv', 'usingmodels/model2.pkl')


def getMAE(ndarray1, ndarray2):
    diff = np.abs(ndarray1 - ndarray2)
    mae = np.mean(diff)
    return mae


# 得到相似度
def getSimilarity(a):
    if a > 2000:
        a = 2000
    a = 2000 - a
    a = a / 2000
    a = a * 0.4 + 0.5
    return a


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
        return ip


def yd15addmodel(df):
    folder_path = './usingmodels'
    file_names = os.listdir(folder_path)
    cnt_yd15 = 0
    output = None
    for file_name in file_names:
        if file_name == 'model1.pkl' or file_name == 'model2.pkl' or file_name[0] == 'a':
            continue
        else:
            cnt_yd15 = cnt_yd15 + 1
            modelpath = folder_path + '/' + file_name
            tmpmodel = joblib.load(modelpath)
            if output is None:
                output = tmpmodel.predict(df[["WINDSPEED", "WINDSPEED2"]].values)
            else:
                output = output + tmpmodel.predict(df[["WINDSPEED", "WINDSPEED2"]].values)
    if output is None:
        return None
    return output * 0.2 / cnt_yd15


def actualaddmodel(df):
    folder_path = './usingmodels'
    file_names = os.listdir(folder_path)
    cnt_actual = 0
    output = None
    for file_name in file_names:
        if file_name == 'model1.pkl' or file_name == 'model2.pkl' or file_name[0] == 'y':
            continue
        else:
            cnt_actual = cnt_actual + 1
            modelpath = folder_path + '/' + file_name
            tmpmodel = joblib.load(modelpath)
            if output is None:
                output = tmpmodel.predict(df[["WINDSPEED", "WINDSPEED2"]].values)
            else:
                output = output + tmpmodel.predict(df[["WINDSPEED", "WINDSPEED2"]].values)
    if output is None:
        return None
    return output * 0.2 / cnt_actual


# 对两个csv文件进行训练和预测
def train(path1, path2):
    df1 = pd.read_csv(path1)
    df2 = pd.read_csv(path2)

    datatimelist = df2['DATATIME'].values

    # 预测YD15
    X_train1 = df1[["WINDSPEED", "WINDSPEED2"]]
    y_train1 = df1[["YD15"]]
    X_test1 = df2[["WINDSPEED", "WINDSPEED2"]]
    # gbm
    x_train, x_test, y_train, y_test = train_test_split(X_train1, y_train1, test_size=0.2)
    gbm1 = LGBMRegressor(objective="regression", learning_rate=0.005, n_estimators=1000, n_jobs=-1)
    gbm1 = gbm1.fit(x_train, y_train, eval_set=[(x_test, y_test)], eval_metric="rmse",
                    callbacks=[early_stopping(stopping_rounds=1000)])
    y_pred15 = gbm1.predict(X_test1)
    # print('y_pred15', y_pred15 * 0.9)
    # print(df2['PREYD15'].values * 0.1)
    output1 = df2['PREYD15'].values * 0.7 + y_pred15 * 0.3
    output1_new = yd15addmodel(X_test1)
    if output1_new is not None:
        output1 = output1 * 0.8 + output1_new

    # 预测POWER
    X_train2 = df1[["WINDSPEED", "WINDSPEED2"]]
    y_train2 = df1[["ROUND(A.POWER,0)"]]
    X_test2 = df2[["WINDSPEED", "WINDSPEED2"]]
    # gbm
    x_train, x_test, y_train, y_test = train_test_split(X_train2, y_train2, test_size=0.2)
    gbm2 = LGBMRegressor(objective="regression", learning_rate=0.005, n_estimators=1000, n_jobs=-1)
    gbm2 = gbm2.fit(x_train, y_train, eval_set=[(x_test, y_test)], eval_metric="rmse",
                    callbacks=[early_stopping(stopping_rounds=1000)])
    POWER = gbm2.predict(X_test2)

    output2 = POWER * 0.3 + df2['PREACTUAL'].values * 0.7
    output2_new = yd15addmodel(X_test1)
    if output2_new is not None:
        output2 = output2 * 0.8 + output2_new

    return [datatimelist.tolist(), output1.tolist(), output2.tolist(), df2['YD15'].values.tolist(),
            df2['ACTUAL'].values.tolist()]


def train2(path1, path2):
    df2 = pd.read_csv(path2)
    datatimelist = df2['DATATIME'].values
    return [datatimelist.tolist(), df2['YD15'].values.tolist(),
            df2['ACTUAL'].values.tolist()]


# 对一个数据集进行预测功率
def upload_predict(data):
    null_count = data['YD15'].isnull().sum()
    session['null_count'] = str(null_count)
    model1 = joblib.load("usingmodels/model1.pkl")
    model2 = joblib.load("usingmodels/model2.pkl")
    df = data[-null_count:]
    data_new = df.copy()
    # 新建一列
    df['WINDSPEED2'] = df['WINDSPEED'] * np.cos(np.radians(df['WINDDIRECTION'].values))
    train = df[["WINDSPEED", "WINDSPEED2"]]
    output1 = model1.predict(train.values)
    output2 = model2.predict(train.values)

    output1_new = yd15addmodel(train)
    output2_new = actualaddmodel(train)

    if output1_new is None:
        data_new['YD15'] = output1
    else:
        data_new['YD15'] = output1 * 0.8 + output1_new

    if output2_new is None:
        data_new['ROUND(A.POWER,0)'] = output2
    else:
        data_new['ROUND(A.POWER,0)'] = output2 * 0.8 + output2_new
    data[-null_count:] = data_new
    path = 'userdata/%s/当前结果文件/tmp.csv' % session.get('username')
    data.to_csv(path, index=False)

    return jsonify({
        'DATATIME': data_new['DATATIME'].values.tolist(),
        'PRE_POWER': np.round(data_new['ROUND(A.POWER,0)'].values, decimals=2).tolist(),
        'PRE_YD15': np.round(data_new['YD15'].values, decimals=2).tolist()
    })


# 登录时创建文件夹
def createfolder(username):
    path1 = 'userdata/%s/上传数据集' % username
    path2 = 'userdata/%s/下载结果文件' % username
    path3 = 'static/usertouxiang/%s' % username
    path4 = 'userdata/%s/当前上传数据集' % username
    path5 = 'userdata/%s/当前结果文件' % username
    os.makedirs(path1, exist_ok=True)
    os.makedirs(path2, exist_ok=True)
    os.makedirs(path3, exist_ok=True)
    os.makedirs(path4, exist_ok=True)
    os.makedirs(path5, exist_ok=True)
    source_file = 'static/picture/touxiang.png'
    destination_file = path3 + '/touxiang.png'
    if os.path.exists(destination_file) == False:
        shutil.copy2(source_file, destination_file)


def to_string(a, f):
    res = ""
    if f == 1:
        for i in range(min(len(a), 50)):
            res = res + str(round(a[i], 2)) + ","
    else:
        for i in range(min(len(a), 50)):
            res = res + a[i] + ","
    return res


# 计算文件夹中文件数量
def count_files_in_folder(folder_path):
    file_count = 0
    # 获取指定文件夹下的所有文件路径
    file_paths = glob.glob(os.path.join(folder_path, '*'))
    for path in file_paths:
        if os.path.isfile(path):  # 只计算文件数量，排除文件夹和子文件夹
            file_count += 1
    return file_count


# 获取路径下的所有文件，返回两个列表，文件名列表，修改时间列表，按修改时间排序
def get_file_paths(directory):
    file_paths = []
    time_list = []
    list = []
    for root, directories, files in os.walk(directory):
        for file in files:
            # file_paths.append(os.path.join(file))
            t = os.path.getmtime(directory + '/' + file)
            # 将时间戳转换为datetime对象
            modified_datetime = datetime.fromtimestamp(t)
            # 格式化为年月日时分秒的格式
            formatted_time = modified_datetime.strftime("%Y-%m-%d %H:%M:%S")
            # time_list.append(formatted_time)
            list.append([os.path.join(file), formatted_time])
    sorted_list = sorted(list, key=lambda x: x[1])
    for i in range(len(sorted_list)):
        file_paths.append(sorted_list[i][0])
        time_list.append(sorted_list[i][1])
    return file_paths, time_list


# _________________________________________________________________________数据库SQL语句_________________________________________________________________________

# 查询供电量
def querypowersupply(id):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "select month,value from powersupply where TurbID = '%s';" % id
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    result_list = [[], []]
    for item in result:
        for i in range(2):
            result_list[i].append(item[i])
    return result_list


# 查询某个id的供发电功率及预测
def queryiddata(id):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "select DATATIME,ACTUAL,PREACTUAL,YD15,PREYD15 from datatmp where TurbID = '%s' LIMIT 96;" % id
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    result_list = [[], [], [], [], []]
    for item in result:
        for i in range(5):
            result_list[i].append(item[i])
    return result_list


def queryonedatabyidandtime(id, year, month, day, hour, minute):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "select DATATIME,ACTUAL,PREACTUAL,YD15,PREYD15 from datatmp where TurbID = '%s' and year = '%s' and month = '%s' and day = '%s' and hour = '%s' and minute = '%s';" % (
        id, year, month, day, hour, minute)
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    result_list = [[], [], [], [], []]
    for item in result:
        for i in range(5):
            result_list[i].append(item[i])
    return result_list


# 给密钥到期时间增加time个月份
def addsdktimemonth(username, time):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "UPDATE usertable SET time = DATE_ADD(time, INTERVAL %s MONTH) WHERE username = '%s';" % (time, username)
    print(sql)
    cursor.execute(sql)
    connection.commit()
    flg = cursor.rowcount
    cursor.close()
    connection.close()
    if flg == 1:
        return True
    else:
        return False


# 查询密钥对应的用户名
def query_sdk_username(sdk):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "select username from usertable where sdk = '%s';" % sdk
    cursor.execute(sql)
    res = cursor.fetchall()
    print(res[0][0])
    cursor.close()
    connection.close()
    if res:
        return res[0]
    return 'false'


# 主图数据查询
def query_pre_data(turbid, year, month, day, hour, length):
    connection = get_connection()
    current_date = datetime(int(year), int(month), int(day), int(hour), 0, 0)
    previous_date = current_date - timedelta(days=int(length))
    current_date = current_date.strftime("%y-%m-%d %H:%M")
    previous_date = previous_date.strftime("%y-%m-%d %H:%M")
    cursor = connection.cursor()
    # 使用 SQL 查询语句从数据库中获取满足条件的数据
    sql = "SELECT DATATIME,WINDSPEED,WINDSPEED2,ACTUAL,YD15 FROM datatmp WHERE TurbID=%s AND STR_TO_DATE(DATATIME, " \
          "'%%Y-%%m-%%d %%H:%%i') >= STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i') AND STR_TO_DATE(DATATIME, '%%Y-%%m-%%d " \
          "%%H:%%i') <= STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i')"
    cursor.execute(sql, (turbid, previous_date, current_date))
    # 获取查询结果
    result = cursor.fetchall()
    result_list = [[], [], [], [], []]
    for item in result:
        for i in range(5):
            result_list[i].append(item[i])
    # 关闭连接
    cursor.close()
    connection.close()
    df = pd.DataFrame({
        'DATATIME': result_list[0],
        'WINDSPEED': result_list[1],
        'WINDSPEED2': result_list[2],
        'ROUND(A.POWER,0)': result_list[3],
        'YD15': result_list[4],
    })
    path = 'userdata/%s/train.csv' % session.get('username')
    df.to_csv(path, index=False)
    return [result_list[0], result_list[3], result_list[4]]


def query_preinput_data(turbid, year, month, day, hour, length):
    connection = get_connection()
    current_date = datetime(int(year), int(month), int(day), int(hour), 0, 0)
    following_date = current_date + timedelta(hours=int(length))
    current_date = current_date.strftime("%y-%m-%d %H:%M")
    following_date = following_date.strftime("%y-%m-%d %H:%M")
    cursor = connection.cursor()
    # 使用 SQL 查询语句从数据库中获取满足条件的数据
    sql = "SELECT DATATIME,WINDSPEED,WINDSPEED2,ACTUAL,PREACTUAL,YD15,PREYD15 FROM datatmp WHERE TurbID=%s AND STR_TO_DATE(DATATIME, " \
          "'%%Y-%%m-%%d %%H:%%i') > STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i') AND STR_TO_DATE(DATATIME, '%%Y-%%m-%%d " \
          "%%H:%%i') <= STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i')"
    cursor.execute(sql, (turbid, current_date, following_date))
    # 获取查询结果
    result = cursor.fetchall()
    result_list = [[], [], [], [], [], [], []]
    for item in result:
        for i in range(7):
            result_list[i].append(item[i])
    df = pd.DataFrame({
        'DATATIME': result_list[0],
        'WINDSPEED': result_list[1],
        'WINDSPEED2': result_list[2],
        'ACTUAL': result_list[3],
        'PREACTUAL': result_list[4],
        'YD15': result_list[5],
        'PREYD15': result_list[6]
    })

    path = 'userdata/%s/predict.csv' % session.get('username')
    df.to_csv(path, index=False)
    # 关闭连接
    cursor.close()
    connection.close()
    if result:
        return True
    return False


def query_range(turbid, year, month, day, hour, length):
    connection = get_connection()
    current_date = datetime(int(year), int(month), int(day), int(hour), 0, 0)
    following_date = current_date + timedelta(hours=int(length))
    current_date = current_date.strftime("%y-%m-%d %H:%M")
    following_date = following_date.strftime("%y-%m-%d %H:%M")
    cursor = connection.cursor()
    # 使用 SQL 查询语句从数据库中获取满足条件的数据

    cursor.execute(sql, (turbid, current_date, following_date))
    # 获取查询结果
    result = cursor.fetchall()
    result_list = [[], [], [], [], [], [], []]
    for item in result:
        for i in range(7):
            result_list[i].append(item[i])
    df = pd.DataFrame({
        'DATATIME': result_list[0],
        'WINDSPEED': result_list[1],
        'WINDSPEED2': result_list[2],
        'ACTUAL': result_list[3],
        'PREACTUAL': result_list[4],
        'YD15': result_list[5],
        'PREYD15': result_list[6]
    })

    path = 'userdata/%s/predict.csv' % session.get('username')
    df.to_csv(path, index=False)
    # 关闭连接
    cursor.close()
    connection.close()
    if result:
        return True
    return False


# 验证用户名密码
def sqlverifypassword(password):
    username = session.get('username')
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT * FROM usertable WHERE username=%s AND password=%s"
    cursor.execute(sql, (username, password))
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    if result:
        return True
    else:
        return False


# 修改用户表中用户密码
def sqlchangepassword(password):
    username = session['username']
    connection = get_connection()
    cursor = connection.cursor()
    sql = "UPDATE usertable SET password='%s' WHERE username='%s';" % (password, username)
    cursor.execute(sql)
    flg = cursor.rowcount
    print(flg)
    connection.commit()
    cursor.close()
    connection.close()
    if flg == 1:
        return True
    else:
        return False


# 查询风向数据
def query_winddirection_data(turbid):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT * FROM winddirection WHERE TurbID=%s"
    cursor.execute(sql, turbid)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


# 查询某用户的功能分布（功能调用次数分布）
def query_apicount_data(username, api):
    if username == 'admin':
        sql = "SELECT COUNT(*) FROM log WHERE api='%s'" % api
    else:
        sql = "SELECT COUNT(*) FROM log WHERE username='%s' and api='%s'" % (username, api)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


# 查询某个用户某天内调用功能分布（使用时段分析）
def query_timeapicount_data(username, year, month, day):
    if month < 10:
        month = '0' + str(month)
    else:
        month = str(month)
    if day < 10:
        day = '0' + str(day)
    else:
        day = str(day)
    date = str(year) + '-' + month + '-' + day + '%'
    if username == 'admin':
        sql = "SELECT api,COUNT(*) AS count FROM log WHERE operate_time LIKE '%s' GROUP BY api" % date
    else:
        sql = "SELECT api,COUNT(*) AS count FROM log WHERE username='%s' and operate_time LIKE '%s' GROUP BY api" % (
            username, date)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    apimap = {int(item[0]): item[1] for item in result}
    countlist = []
    for i in range(7):
        if i in apimap.keys():
            countlist.append(apimap.get(i))
        else:
            countlist.append(0)
    return countlist


# 获取日志（日志操作记录）
def query_apilist_data(username):
    if username == 'admin':
        sql = "SELECT username,operate_time,api,note FROM log ORDER BY operate_time desc "
    else:
        sql = "SELECT username,operate_time,api,note FROM log WHERE username='%s' ORDER BY operate_time desc " % username
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


# 新增用户（注册）
def addUser(username, password):
    connection = get_connection()
    cursor = connection.cursor()
    sql = 'INSERT IGNORE INTO usertable (username,password) VALUES (%s,%s)'
    cursor.execute(sql, (username, password))
    connection.commit()
    flg = cursor.rowcount
    cursor.close()
    connection.close()
    if flg == 1:
        return True
    return False


# 验证用户名密码
def verify_user(username, password):
    print('->', username, password)
    if username == '':
        return False
    connection = get_connection()

    # 创建游标对象
    cursor = connection.cursor()
    # 执行查询语句
    sql = "SELECT password FROM usertable WHERE username = '%s'" % username
    print(sql)
    cursor.execute(sql)
    # 获取查询结果
    result = cursor.fetchone()
    # 关闭游标和连接
    cursor.close()
    connection.close()
    # 根据查询结果返回验证结果
    print("测试0801", result)
    print('login->', result)
    if result[0] == password:
        return True
    else:
        return False


# 添加日志
def addlog(username, operate_time, api, note=''):
    connection = get_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO log (username, operate_time, api, note) VALUES (%s,%s,%s,%s);"
    cursor.execute(sql, (username, operate_time, api, note))
    connection.commit()
    flg = cursor.rowcount
    print(flg)
    cursor.close()
    connection.close()
    if flg == 1:
        return True
    return False


# 更新当前用户的sdk
def updatesdk():
    username = session.get('username')
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT sdk FROM usertable WHERE username='%s'" % username
    cursor.execute(sql)
    result = cursor.fetchone()

    if result is not None:
        if result[0] is not None:
            session['sdk'] = result[0]


def updatesdktime():
    username = session.get('username')
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT time FROM usertable WHERE username='%s'" % username
    cursor.execute(sql)
    result = cursor.fetchone()

    if result is not None:
        if result[0] is not None:
            session['sdktime'] = result[0].strftime("%Y年%m月%d日 %H:%M:%S")

    cursor.close()
    connection.close()
    return session.get('sdk')


# _________________________________________________________________________注册登录退出_______________________________________________________________________

pathNoneCheckList = ['/index', '/visual', '/predict', '/offline', '/api', '/admin', '/log_admin', '/personalcenter',
                     '/log']


# 路由安全性过滤与检查
# @app.before_request
# def check_login():
#     path = request.path
#     username = session.get('username')
#     if path in pathNoneCheckList and username is None:
#         print('测试', path, username)
#         return redirect('/login')
#     return


# 注册界面
@app.route('/register')
def to_register():
    return render_template('register.html')


# 提交注册信息并进行注册
@app.route('/register_submit', methods=['POST'])
def register_submit():
    data = request.get_json()
    data = json.dumps(data)
    print(data)
    json_data = json.loads(data)

    username = json_data['username']
    password = json_data['password']
    repassword = json_data['repassword']

    if repassword != password:
        return '两次密码不一致！'
    else:
        if addUser(username, password):
            return '注册成功,点此登录'
        else:
            return '注册失败,请重试！'


# 登录界面
@app.route('/login')
def login():
    return render_template("login.html")


# 退出界面
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# 登录验证
@app.route('/index', methods=['POST'])
def login_verify():
    username = request.form['username']
    password = request.form['password']
    flg = verify_user(username, password)
    if flg:
        session['username'] = username
        updatesdk()
        updatesdktime()

        # 为该用户建立需要的文件夹
        createfolder(username)

        # 为该用户创建ai对话账户
        print('我在创建ai用户')
        url1 = 'http://' + get_host_ip() + ':5445/createUser?username=' + username
        requests.get(url1)

        if username == 'admin':
            return redirect('/admin')
        else:
            return render_template("index.html", username=username, sdk=session.get('sdk'))
    elif password == '':
        error = '密码不能为空'
        # redirect('/login')
        return render_template('login.html', error=error, username=username)
    else:
        print('error')
        error = '用户名或密码错误'
        # redirect('/login')
        return render_template('login.html', error=error, username=username)


# _________________________________________________________________________主页_________________________________________________________________________

# 跳转到主页，如果未登录跳转登录界面
@app.route('/')
def home():
    return redirect('/login')


# 获取一定时间范围内的数据作为训练数据（主图左）
@app.route('/predict_value', methods=['GET'])
def predict_value():
    # 获取前端传递的查询参数
    turbid = request.args.get('turbid')
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    hour = request.args.get('hour')
    length = request.args.get('length')

    # 查询数据库中满足条件的数据
    data = query_pre_data(turbid, year, month, day, hour, length)
    print(data[0])
    # 将查询结果处理为 JSON 格式
    result = jsonify({
        "DATETIME": data[0],
        "ROUND(A.POWER,0)": data[1],
        "YD15": data[2],
    })
    return result


@app.route('/train_predict', methods=['GET'])
def train_predict():
    # 获取前端传递的查询参数
    turbid = request.args.get('turbid')
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    hour = request.args.get('hour')
    length = request.args.get('length')

    flg = query_preinput_data(turbid, year, month, day, hour, length)

    if flg:
        path = "userdata/%s/" % session.get('username')
        path1 = path + 'train.csv'
        path2 = path + 'predict.csv'
        res_list = train(path1, path2)
        print('__', res_list)
        return jsonify({
            "DATATIME": res_list[0],
            "PREYD15": res_list[1],
            "PREACTUAL": res_list[2],
            'YD15': res_list[3],
            "ACTUAL": res_list[4]
        })
    else:
        return jsonify({'error': 'error'})


@app.route('/rangeAccess', methods=['GET'])
def range_access():
    # 获取前端传递的查询参数
    turbid = request.args.get('turbid')
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    hour = request.args.get('hour')
    length = request.args.get('length')

    flg = query_preinput_data(turbid, year, month, day, hour, length)

    if flg:
        path = "userdata/%s/" % session.get('username')
        path1 = path + 'train.csv'
        path2 = path + 'predict.csv'
        res_list = train(path1, path2)
        print('__', res_list)
        return jsonify({
            "DATATIME": res_list[0],
            "PREYD15": res_list[1],
            "PREACTUAL": res_list[2],
            'YD15': res_list[3],
            "ACTUAL": res_list[4]
        })
    else:
        return jsonify({'error': 'error'})


@app.route('/train_predict2', methods=['GET'])
def train_predict2():
    # 获取前端传递的查询参数
    turbid = request.args.get('turbid')
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    hour = request.args.get('hour')
    length = request.args.get('length')

    flg = query_preinput_data(turbid, year, month, day, hour, length)

    if flg:
        path = "userdata/%s/" % session.get('username')
        path1 = path + 'train.csv'
        path2 = path + 'predict.csv'
        res_list = train2(path1, path2)
        print('__', res_list)
        return jsonify({
            "DATATIME": res_list[0],
            'YD15': res_list[1],
            "ACTUAL": res_list[2]
        })
    else:
        return jsonify({'error': 'error'})


# 获取风向数据（风向玫瑰图）
@app.route('/get_winddirection', methods=['GET'])
def get_winddirection():
    # 获取前端传递的查询参数
    turbid = request.args.get('turbid')
    data = query_winddirection_data(turbid)
    res_list_direction = list(data[0])
    # 将查询结果处理为 JSON 格式
    result = jsonify({
        "direction": res_list_direction
    })
    # print(res_list_direction)
    return result


# 跳转主页
@app.route('/index')
def to_index():
    username = session.get('username')
    return render_template('index.html', username=username)


# _________________________________________________________________________可视化大屏_____________________________________________________________________

# 跳转可视化大屏
@app.route('/visual')
def visual():
    username = session.get('username')
    return render_template('visual.html', username=username)


# 根据id读取供发电功率及预测功率
@app.route('/getiddata', methods=['GET'])
def getiddata():
    id = request.args.get('id')
    list = queryiddata(id)
    print('test', list[0][0])
    return jsonify({
        'DATATIME': list[0],
        'ACTUAL': list[1],
        'PREACTUAL': list[2],
        'YD15': list[3],
        'PREYD15': list[4]
    })


# 根据id和日期读取供发电功率及预测功率
@app.route('/queryonedatabyidandtime', methods=['GET'])
def getonedatabyidandtime():
    id = request.args.get('id')
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    hour = request.args.get('hour')
    minute = request.args.get('minute')
    list = queryonedatabyidandtime(id, year, month, day, hour, minute)
    # print(list)
    return jsonify({
        'DATATIME': list[0][0],
        'ACTUAL': list[1][0],
        'PREACTUAL': list[2][0],
        'YD15': list[3][0],
        'PREYD15': list[4][0]
    })


# 根据id获取不同月份的供电量
@app.route('/querypowersupply', methods=['GET'])
def getpowersupply():
    id = request.args.get('id')
    print('__________>>', id)
    list = querypowersupply(id)
    print(list)
    return jsonify({
        'month': list[0],
        'values': list[1],
    })


# _________________________________________________________________________在线预测_______________________________________________________________________

# 跳转在线预测界面
@app.route('/predict')
def to_predict():
    username = session.get('username')
    return render_template('predict.html', username=username)


# 上传文件
@app.route('/upload_file', methods=['POST'])
def get_file():
    username = session.get('username')
    if 'file' not in request.files:
        return '未选择文件', 400
    file = request.files['file']
    if file.filename == '':
        return '未选择文件', 400
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=username, operate_time=operate_time, api=api_list['upload_file'], note="上传数据文件")
    df = pd.read_csv(file)
    path = "userdata/%s/上传数据集" % username
    cnt = count_files_in_folder(path)
    filename = '/in' + str(cnt + 1) + '.csv'
    df.to_csv(path + filename, index=False)
    path = 'userdata/%s/当前上传数据集/tmp.csv' % username
    df.to_csv(path, index=False)

    return jsonify({})


# 数据分析
@app.route('/data_analyze', methods=['GET'])
def data_analysis():
    select = request.args.get('select')
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    csvid = '1'
    tmp_path = 'userdata/%s/当前上传数据集/tmp.csv' % session.get('username')
    df = pd.read_csv(tmp_path)
    turbid = df['TurbID'].iloc[0]
    if turbid == 1:
        csvid = '1'
    else :
        csvid = '2'
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['data_analyze'], note="数据分析处理")
    print(csvid+'_report'+select+'.html')
    return render_template('/report/'+csvid+'_report'+select+'.html')
    # return render_template('1_report0000.html')



# 对上传的文件进行预测并返回（功率预测）
@app.route('/online_predict')
def file_predict():
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['online_predict'], note="数据训练预测")
    path = 'userdata/%s/当前上传数据集/tmp.csv' % session.get('username')
    df = pd.read_csv(path)
    tmp = upload_predict(df)
    return tmp


# chatgpt分析
@app.route('/gptapi_analyze')
def analyze_wind_power():
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['gptapi_analyze'], note="AI分析")
    # 编辑prompt
    # openai.api_key = GPT_API
    # openai.api_base = "https://chat-api.leyoubaloy.xyz/v1"
    # send a ChatCompletion request to GPT
    path = 'userdata/%s/当前结果文件/tmp.csv' % session.get('username')

    try:
        df = pd.read_csv(path)
        # 在这里处理文件读取成功后的逻辑
        cnt = session.get('null_count')
        if cnt is None:
            cnt = 50
        else:
            cnt = int(cnt)
        res_datatime = df[-cnt:]['DATATIME'].tolist()
        res_windspeed = df[-cnt:]['WINDSPEED'].tolist()
        res_power = df[-cnt:]['YD15'].tolist()

        return jsonify({
            'datatime': to_string(res_datatime, 0),
            'windspeed': to_string(res_windspeed, 1),
            'power': to_string(res_power, 1)
        })
    except FileNotFoundError:
        # 文件不存在的处理逻辑
        return jsonify({
            'error': 'error'
        })

    # messages = [
    #     {"role": "system",
    #      "content": "我希望你扮演一个数据分析师的角色。作为数据分析师，你有深厚的数学和统计知识，并且擅长使用各种数据分析工具和编" +
    #                 "程语言来解析数据。你对风电数据非常熟悉，包括功率、风速与时间的关系。你的职责是分析这些数据，并提供关于可能原因和" +
    #                 "潜在风险的解释。作为数据分析师，你会仔细研究风电数据中功率、风速和时间之间的关系。你会运用统计方法分析数据的趋势和" +
    #                 "模式，以确定功率和风速之间的关联程度。你会考虑不同的时间段和季节对风电发电量的影响，并尝试找出任何异常或异常行为。在" +
    #                 "分析风电数据时，你会注意到一些可能的原因和潜在的风险。作为数据分析师，你的职责还包括向相关团队和管理层提供分析结果和建议。"},
    #     {"role": "user",
    #      "content": "这是一列时间序列，" + to_string(res_datatime, 0) + "这是对应的风速列，" + to_string(res_windspeed,
    #                                                                                                    1) + "这是对应的功率列，" + to_string(
    #          res_power, 1) +
    #                 "请结合时间分析一下风速对于功率的影响。"
    #                 "我需要你结合风速的变化，分析功率的变化情况，给出分析结果，比如某个时间到另一个时间内，风速发生了什么变化，功率又有什么变化，并分析原因，分析的透彻到底，一段话直接说明白，不用画图"},
    # ]
    # response = openai.ChatCompletion.create(
    #     model='gpt-3.5-turbo-0301',
    #     messages=messages,
    #     temperature=0,
    # )
    # print(messages)
    # 获取助手角色的回答
    # assistant_response = response['choices'][0]['message']['content']


# 下载结果文件
@app.route('/download_resfile')
def download_resfile():
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['download_resfile'],
           note="下载预测结果")
    path = "userdata/%s/下载结果文件/" % session.get('username')
    cnt = count_files_in_folder(path)
    file_name = 'res' + str(cnt + 1) + '.csv'
    file_path = path + file_name  # 文件在服务器上的路径

    tmp_path = 'userdata/%s/当前结果文件/tmp.csv' % session.get('username')
    df = pd.read_csv(tmp_path)
    df.to_csv(file_path, index=False)

    return send_file(file_path, download_name=file_name, as_attachment=True)


@app.route('/dialog')
def dialog():
    username = session.get('username')
    print('测试dialog获取ip', 'http://' + get_host_ip() + ":5445/")
    return render_template('dialog.html', username=username, baseURL='http://' + get_host_ip() + ":5445/")


###
# _________________________________________________________________________离线应用_________________________________________________________________________
###
#

###
# _________________________________________________________________________离线应用_________________________________________________________________________

# 跳转离线应用界面
@app.route('/offline')
def offline():
    username = session.get('username')
    # session.get('sdk')
    sdk = session.get('sdk')
    # print('sdk是多少:', sdk)
    return render_template("offline.html", username=username, sdk=sdk)


# 下载离线应用安装包
@app.route('/download_offine_soft')
def download_offine_soft():
    file_path = './offline_soft/风电功率预测系统油专特供版offline.msi'  # 文件在服务器上的路径
    return send_file(file_path, as_attachment=True)


# 将sdk和username对应起来加到数据库中（在离线应用界面申请sdk）
@app.route('/newsdk_offline')
def newsdkoffline():
    sdk = secrets.token_hex(16).__str__()
    username = session.get('username')

    connection = get_connection()
    cursor = connection.cursor()
    time = datetime.now() + timedelta(days=31)
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    sql = "UPDATE usertable SET sdk='%s',time='%s' WHERE username='%s';" % (sdk, time, username)
    cursor.execute(sql)
    flg = cursor.rowcount
    print(flg)
    connection.commit()
    connection.close()
    cursor.close()
    if flg == 0:
        sdk = None
    print('申请sdk测试', sdk)
    session['sdk'] = sdk
    session['sdktime'] = time
    # jsonify({'sdk': sdk})
    return redirect('/offline')


# _________________________________________________________________________API使用文档_______________________________________________________________________

# 跳转API使用文档界面
@app.route('/api')
def to_api():
    username = session.get('username')
    sdk = session.get('sdk')
    return render_template('api.html', username=username, sdk=sdk)


# 将sdk和username对应起来加到数据库中（在api文档界面申请sdk）
@app.route('/newsdk_api')
def newsdkapi():
    sdk = secrets.token_hex(16).__str__()
    username = session.get('username')
    connection = get_connection()
    cursor = connection.cursor()
    time = datetime.now() + timedelta(days=31)
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    sql = "UPDATE usertable SET sdk='%s',time='%s' WHERE username='%s';" % (sdk, time, username)
    print(sql)
    cursor.execute(sql)
    flg = cursor.rowcount
    print(flg)
    connection.commit()
    connection.close()
    cursor.close()
    if flg == 0:
        sdk = None
    print('申请sdk测试', sdk)
    session['sdk'] = sdk
    session['sdktime'] = time

    # jsonify({'sdk': sdk})
    return redirect('/api')


# _________________________________________________________________________windpower风电API_______________________________________________________________________

@app.route('/windpowerapisavepredictfile', methods=['POST'])
def api_predict():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    # 检查身份验证头部中是否包含正确的密钥
    if 'Authorization' not in request.headers or query_sdk_username(request.headers['Authorization']) == 'false':
        return jsonify({'error': '您的密钥未被授权，请更换密钥'})
    else:
        addlog(username=query_sdk_username(request.headers['Authorization']),
               operate_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), api=api_list['api'], note='API调用')

    file = request.files['file']
    # 检查文件类型是否为CSV
    if file.filename.endswith('.csv'):
        show = request.headers['figure']
        train = request.headers['train']
        output = request.headers['file']

        # 保存上传的文件
        file.save(file.filename)
        # 读取CSV文件
        df = pd.read_csv(file.filename)
        # 在此处进行预测操作，可根据自己的需求使用适当的模型或算法
        res_file = pd.DataFrame({})
        if train == 'True':
            null_count = df['YD15'].isnull().sum()
            cnt = null_count
            data_new = df.copy()
            df = df.fillna(0)
            # 新建一列
            df['WINDSPEED2'] = df['WINDSPEED'] * np.cos(np.radians(df['WINDDIRECTION'].values))
            # 预测YD15
            X_train1 = df[["WINDSPEED", "WINDSPEED2"]][:-null_count]
            y_train1 = df[["YD15"]][:-null_count]
            X_test1 = df[["WINDSPEED", "WINDSPEED2"]][-null_count:]
            # gbm
            x_train, x_test, y_train, y_test = train_test_split(X_train1, y_train1, test_size=0.2)
            gbm1 = LGBMRegressor(objective="regression", learning_rate=0.005, n_estimators=1000, n_jobs=-1)
            gbm1 = gbm1.fit(x_train, y_train, eval_set=[(x_test, y_test)], eval_metric="rmse",
                            callbacks=[early_stopping(stopping_rounds=1000)])
            y_pred15 = gbm1.predict(X_test1.values)
            output1 = y_pred15
            # 预测POWER
            X_train2 = df[["WINDSPEED", "WINDSPEED2"]][:-null_count]
            y_train2 = df[["ROUND(A.POWER,0)"]][:-null_count]
            X_test2 = df[["WINDSPEED", "WINDSPEED2"]][-null_count:]
            # gbm
            x_train, x_test, y_train, y_test = train_test_split(X_train2, y_train2, test_size=0.2)
            gbm2 = LGBMRegressor(objective="regression", learning_rate=0.005, n_estimators=1000, n_jobs=-1)
            gbm2 = gbm2.fit(x_train, y_train, eval_set=[(x_test, y_test)], eval_metric="rmse",
                            callbacks=[early_stopping(stopping_rounds=1000)])
            POWER = gbm2.predict(X_test2.values)
            output2 = POWER
            data_new['YD15'][-null_count:] = output1
            data_new['ROUND(A.POWER,0)'][-null_count:] = output2
            res_file = data_new
        else:
            model1 = joblib.load("usingmodels/model1.pkl")
            model2 = joblib.load("usingmodels/model2.pkl")
            null_count = df['YD15'].isnull().sum()
            cnt = null_count
            data_new = df.copy()
            # 新建一列
            df['WINDSPEED2'] = df['WINDSPEED'] * np.cos(np.radians(df['WINDDIRECTION'].values))
            train = df[["WINDSPEED", "WINDSPEED2"]]
            output1 = model1.predict(train.values)
            output2 = model2.predict(train.values)
            data_new['YD15'] = output1
            data_new['ROUND(A.POWER,0)'] = output2
            res_file = data_new
        # 假设预测结果为新的DataFrame对象
        predictions = res_file
        if show == 'True':
            plt.clf()
            df = res_file
            # 在图形上绘制示例图形
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
            plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
            x = df['DATATIME'][-cnt:].tolist()
            y1 = df['YD15'][-cnt:].tolist()
            y2 = df['ROUND(A.POWER,0)'][-cnt:].tolist()
            # mpl_style(dark=False)
            with plt.style.context(matplotx.styles.pitaya_smoothie['light']):
                fig = plt.figure(figsize=(10, 4))
                plt.plot(x, y1, label='YD15')
                plt.plot(x, y2, label='ROUND(A.POWER,0)')
                plt.xlabel('日期')
                plt.ylabel('功率')
                plt.title('预测结果')
                plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=5))
                plt.legend()
                fig.savefig('res_picture.png')

        # 生成预测后的CSV文件
        if output == 'True':
            output_filename = 'predictions.csv'
            predictions.to_csv(output_filename, index=False)

        if output == 'True' and show == 'False':
            return send_file('predictions.csv', as_attachment=True)
        elif output == 'False' and show == 'True':
            return send_file('res_picture.png', as_attachment=True)
        else:
            # 打包文件和图片
            files_to_compress = ['predictions.csv', 'res_picture.png']
            # 压缩后的ZIP文件路径
            zip_file_path = 'res.zip'
            # 创建一个ZIP文件并将文件添加到其中
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file in files_to_compress:
                    zipf.write(file)
            return send_file(zip_file_path, as_attachment=True)


@app.route('/windpowerapiprocessingdata', methods=['POST'])
def api_processingdata():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    # 检查身份验证头部中是否包含正确的密钥
    if 'Authorization' not in request.headers or query_sdk_username(request.headers['Authorization']) == 'false':
        return jsonify({'error': '您的密钥未被授权，请更换密钥'})
    else:
        addlog(username=query_sdk_username(request.headers['Authorization']),
               operate_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), api=api_list['api'], note='API调用')

    file = request.files['file']
    # 检查文件类型是否为CSV
    if file.filename.endswith('.csv'):
        fill = request.headers['fill']
        outlier = request.headers['outlier']
        normal = request.headers['normal']
        resample = request.headers['resample']
        deduplication = request.headers['deduplication']

        # 保存上传的文件
        file.save(file.filename)
        # 读取CSV文件
        df = pd.read_csv(file.filename)

        if fill == 'True':
            df = KNN_FillNaN.getcsv(df)
        if outlier == 'True':
            df = IQR_OutlierCorrection.getcsv(df)
        if resample == 'True':
            df = Resample.getcsv(df)
        if deduplication == 'True':
            df = DataDeduplication.getcsv(df)
        if normal == 'True':
            df = Normal.getcsv(df)

        df.to_csv('processed_dataset.csv', index=False)
        return send_file('processed_dataset.csv', as_attachment=True)


@app.route('/windpowerapiaianalysis', methods=['POST'])
def api_aianalysis():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    # 检查身份验证头部中是否包含正确的密钥
    if 'Authorization' not in request.headers or query_sdk_username(request.headers['Authorization']) == 'false':
        return jsonify({'error': '您的密钥未被授权，请更换密钥'})
    else:
        addlog(username=query_sdk_username(request.headers['Authorization']),
               operate_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), api=api_list['api'], note='API调用')

    file = request.files['file']
    # 检查文件类型是否为CSV
    if file.filename.endswith('.csv'):
        ai = request.headers['ai']

        # 保存上传的文件
        file.save(file.filename)
        # 读取CSV文件
        df = pd.read_csv(file.filename)

        if ai == 'True':
            res_datatime = df[-172:]['DATATIME'].tolist()
            res_windspeed = df[-172:]['WINDSPEED'].tolist()
            res_power = df[-172:]['YD15'].tolist()

            # 编辑prompt
            openai.api_key = env.GPT_API
            openai.api_base = "https://chat-api.leyoubaloy.xyz/v1"
            # send a ChatCompletion request to GPT
            messages = [
                {"role": "system",
                 "content": "我希望你扮演一个数据分析师的角色。作为数据分析师，你有深厚的数学和统计知识，并且擅长使用各种数据分析工具和编" +
                            "程语言来解析数据。你对风电数据非常熟悉，包括功率、风速与时间的关系。你的职责是分析这些数据，并提供关于可能原因和" +
                            "潜在风险的解释。作为数据分析师，你会仔细研究风电数据中功率、风速和时间之间的关系。你会运用统计方法分析数据的趋势和" +
                            "模式，以确定功率和风速之间的关联程度。你会考虑不同的时间段和季节对风电发电量的影响，并尝试找出任何异常或异常行为。在" +
                            "分析风电数据时，你会注意到一些可能的原因和潜在的风险。作为数据分析师，你的职责还包括向相关团队和管理层提供分析结果和建议。"},
                {"role": "user",
                 "content": "这是一列时间序列，" + to_string(res_datatime, 0) + "这是对应的风速列，" + to_string(
                     res_windspeed,
                     1) + "这是对应的功率列，" + to_string(
                     res_power, 1) + "请结合时间分析一下风速对于功率的影响。"
                                     "我需要你结合风速的变化，分析功率的变化情况，给出分析结果，比如某个时间到另一个时间内，风速发生了什么变化，功率又有什么变化，并分析原因，分析的透彻到底，大约200个汉字，一段话直接说明白，不用画图"},
            ]
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-0301',
                messages=messages,
                temperature=0,
            )
            print(messages)
            # 获取助手角色的回答
            assistant_response = response['choices'][0]['message']['content']
        return jsonify({
            'ans': assistant_response
        })


# _________________________________________________________________________管理员管理模型界面_______________________________________________________________________

# 跳转模型管理
@app.route('/admin')
def to_admin():
    username = session.get('username')
    if username == 'admin':
        return render_template('admin.html', username=username)
    else:
        return render_template('iderror.html')


# 获取模型列表
@app.route('/get_modelname')
def get_getmodels():
    usingmodels_list, tmp = get_file_paths('usingmodels')
    getmodels_list, tmp = get_file_paths('getmodels')
    return jsonify({
        'usingmodels': usingmodels_list,
        'getmodels': getmodels_list
    })


# 把模型从左移到右
@app.route('/add_models_to_pool', methods=['POST'])
def addmodels():
    filenames = request.get_json()
    path_root = 'getmodels/'
    path_pool = 'usingmodels/'
    for i in range(len(filenames)):
        print(path_root + filenames[i])
        print(path_pool + filenames[i])
        shutil.move(path_root + filenames[i], path_pool + filenames[i])
    return 'ok'


# 直接删除模型
@app.route('/delete_models', methods=['POST'])
def deletemodels():
    filenames = request.get_json()
    path_root = 'getmodels/'
    for i in range(len(filenames)):
        os.remove(path_root + filenames[i])
    return 'ok'


# 模型从右移到左
@app.route('/remove_models_from_pool', methods=['POST'])
def removemodels():
    filenames = request.get_json()
    path_root = 'getmodels/'
    path_pool = 'usingmodels/'
    for i in range(len(filenames)):
        print(path_root + filenames[i])
        print(path_pool + filenames[i])
        shutil.move(path_pool + filenames[i], path_root + filenames[i])
    return 'ok'


# _________________________________________________________________________日志____________________________________________________________________________

# 用户日志界面跳转
@app.route('/log')
def log():
    username = session.get('username')
    return render_template('log.html', username=username, log=log)


# 管理员日志界面跳转
@app.route('/log_admin')
def adminlog():
    username = session.get('username')
    return render_template('log_admin.html', username=username, log=log)


# 获取日志列表
@app.route('/get_log')
def get_loglist():
    username = session.get('username')
    reslog = query_apilist_data(username)
    res = []
    for item in reslog:
        res.append(list(item))
    return jsonify({
        'cnt': len(res),
        'log': res
    })


# 向前端返回（功能调用次数分布）数据
@app.route('/get_apicount', methods=['GET'])
def get_apicount():
    username = request.args.get('username')
    # data = query_apicount_data(username,)
    # res_list_apicount = list(data[0])
    res_list_apicount = []
    apilist = ['上传数据', '数据分析', '预测功率', 'AI分析', '下载结果', '上传模型', 'API调用']
    for key in api_list.keys():
        data = query_apicount_data(username, api_list[key])
        res_list_apicount.append(data[0][0])
    result = jsonify({
        "cnt": len(api_list),
        "apicount": res_list_apicount,
        "apilist": apilist
    })
    return result


# 向前端返回（使用时段分析）数据
@app.route('/get_timeapicount')
def get_timeapicount():
    username = request.args.get('username')
    daydata = []
    for i in range(1, 32):
        api_list = query_timeapicount_data(username, 2023, 8, i)
        daydata.append(api_list)
    result = jsonify({
        "daydata": daydata
    })
    return result


# _________________________________________________________________________个人中心_________________________________________________________________________

# 跳转个人中心界面
@app.route('/personalcenter', methods=['GET'])
def to_personalcenter():
    username = session.get('username')
    return render_template('personalcenter.html', username=username, key_amount=session.get('sdktime'))


# 前往个人中心查看密钥查看sdk
@app.route('/check_sdk')
def check_sdk():
    username = session.get('username')
    sdk = session.get('sdk')
    return render_template('personalcenter.html', username=username, check=sdk, key_amount=session.get('sdktime'))


# 点击（查看）密钥
@app.route('/verifypassword', methods=['POST'])
def verifypassword():
    password = request.form.get('password')
    print('___________', password)
    if sqlverifypassword(password):  # 验证密码成功
        sdk = session.get('sdk')
        if sdk is None:
            print('您还未申请sdk!')
            return '您还未申请sdk!'
        else:
            print(sdk)
            return sdk
    else:
        print('密码错误!')
        return '密码错误!'


# 修改密码
@app.route('/changepassword', methods=['POST'])
def changepassword():
    password = request.form.get('password')
    if sqlchangepassword(password):
        return '修改成功'
    else:
        return '修改失败，请重试'



# 将续费时长添加
@app.route('/sdktimeadd', methods=['GET'])
def sdktimeadd():
    time = request.args.get('time')
    print('月份数', time)
    username = session.get('username')
    flg = addsdktimemonth(username, time)
    if flg:
        updatesdktime()
        return jsonify({
            "result": 'success'})
    else:
        return jsonify({
            "result": 'failed'})


# 更换头像
@app.route('/changetx', methods=['POST'])
def changetx():
    if 'image' not in request.files:
        return "No image uploaded", 400
    file = request.files['image']
    path = "static/usertouxiang/%s/touxiang.png" % session.get('username')
    file.save(path)  # 将图片保存到指定路径
    return "Image uploaded successfully"


# 获取用户文件列表
@app.route('/get_userfile')
def get_userfile():
    path1 = "userdata/%s/上传数据集" % session.get('username')
    path2 = "userdata/%s/下载结果文件" % session.get('username')
    uploadcsv_list, time1 = get_file_paths(path1)
    downloadcsv_list, time2 = get_file_paths(path2)
    return jsonify({
        'uploadcsv': uploadcsv_list,
        'uploadcsv_time': time1,
        'downloadcsv': downloadcsv_list,
        'downloadcsv_time': time2
    })


# （个人中心）界面下载历史文件
@app.route('/download_history_csv')
def download_history_csv():
    file_path = request.args.get('path')
    return send_file(file_path, as_attachment=True)


# _________________________________________________________________________离线app_________________________________________________________________________

# 获取他人使用offline程序跑出来的模型
@app.route('/getmodel', methods=['POST'])
def get_model():
    file = request.files['file']
    file.save('模型相似度检测/tmp.pkl')  # 保存到指定位置
    model = joblib.load('模型相似度检测/tmp.pkl')
    df = pd.read_csv('模型相似度检测/test.csv')
    output = model.predict(df[['WINDSPEED', 'WINDSPEED2']])
    # print(output)
    cnt = count_files_in_folder('./getmodels')
    if cnt % 2 == 0:
        tmp = int(cnt / 2)
        mae = getMAE(output, origin_model_resYD15)
        s = getSimilarity(mae)
        s = round(s * 100000, 0) + random.randrange(100, 300)
        s = int(s)

        file_name = "yd15_" + str(tmp + 1) + '_' + str(s) + ".pkl"
    else:
        tmp = int(cnt / 2)
        mae = getMAE(output, origin_model_resPOWER)
        s = getSimilarity(mae)
        s = round(s * 100000, 0) + random.randrange(100, 300)
        s = int(s)
        file_name = "actualpower_" + str(tmp + 1) + '_' + str(s) + ".pkl"

    # 源文件路径
    source_folder = '模型相似度检测'
    source_file = 'tmp.pkl'
    source_path = os.path.join(source_folder, source_file)

    # 目标文件夹路径
    target_folder = 'getmodels'
    target_file = file_name
    target_path = os.path.join(target_folder, target_file)

    # 剪切文件并修改名称
    shutil.copyfile(source_path, target_path)
    return '文件上传成功！'


router_list = [
    '/',
    '/index',
    ''
]
static_list = [
    '/staic',

]


# _________________________________________________________________________大屏_________________________________________________________________________

@app.route('/sum_by_turbid', methods=['GET'])
def sum_by_turbid():
    # connection = get_connection()  # 从连接池获取连接
    # cursor = connection.cursor()
    #
    # try:
    #     # 执行查询语句
    #     cursor.execute("SELECT turbid, SUM(yd15) AS sum_yd15 FROM datatmp GROUP BY TurbID")
    #     result = cursor.fetchall()
    #     resDict = {item[0]: item[1] for item in result}
    #     print('sum:', resDict)
    #
    #     # 返回 JSON 格式的结果
    #       return jsonify(resDict)
    # finally:
    #     cursor.close()
    #     # release(connection)  # 将连接释放回连接池
    return jsonify({
        "11": 875243253.858176,
        "12": 831182995.9716837,
        "13": 1137271137.9981165,
        "14": 621854739.6179744,
        "15": 1962467735.8125446,
        "16": 2256899187.198111,
        "17": 1101151908.2103438,
        "18": 198365430.37620512,
        "19": 1390901559.3073874,
        "20": 495908518.4166046
    })


# _________________________________________________________________________导航栏foot_________________________________________________________________________
@app.route('/navigation.html')
def navigation():
    username = session.get('username')
    return render_template('navigation.html', username=username)


@app.route('/footer.html')
def footer():
    username = session.get('username')
    return render_template('footer.html', username=username)


# ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
myhost = '0.0.0.0'
myport = 5446
report_port = 40000

if __name__ == '__main__':
    # print(render_template('footer.html').__str__())
    app.run(debug=True, host=myhost, port=myport)
