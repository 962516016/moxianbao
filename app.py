import glob
import json
import os
import secrets
import shutil
import zipfile
from datetime import datetime, timedelta

import dtale
import joblib
import matplotlib.pyplot as plt
import matplotx
import numpy as np
import openai
import pandas as pd
import pymysqlpool
from flask import Flask, jsonify, request, send_file, render_template, session, redirect
from flask_cors import CORS
from lightgbm import LGBMRegressor, early_stopping
from matplotlib.ticker import MaxNLocator
from sklearn.model_selection import train_test_split

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# 上传的文件df格式
df_upload_file = pd.DataFrame({})
# 预测结果
res_datatime = []
res_windspeed = []
res_power = []

myhost = '0.0.0.0'
myport = 5446
report_port = 40000

api_list = {
    'upload_file': '0',
    'data_analyze': '1',
    'online_predict': '2',
    'gptapi_analyze': '3',
    'download_resfile': '4',
    'getmodel': '5',
}


def to_string(a, f):
    res = ""
    if f == 1:
        for i in range(min(len(a), 50)):
            res = res + str(round(a[i], 2)) + ","
    else:
        for i in range(min(len(a), 50)):
            res = res + a[i] + ","
    return res


# 配置数据库连接信息和连接池参数
DB_CONFIG = {
    'host': '140.143.125.244',
    'port': 3306,
    'user': 'ly',
    'password': 'longyuan',
    'database': 'longyuan',
}
# 创建 pymysqlpool 连接池
pool = pymysqlpool.ConnectionPool(size=5, pre_create_num=1, **DB_CONFIG)


# 计算文件夹中文件数量
def count_files_in_folder(folder_path):
    file_count = 0

    # 获取指定文件夹下的所有文件路径
    file_paths = glob.glob(os.path.join(folder_path, '*'))

    for path in file_paths:
        if os.path.isfile(path):  # 只计算文件数量，排除文件夹和子文件夹
            file_count += 1

    return file_count


# 获取路径下的所有文件，返回一个路径列表
def get_file_paths(directory):
    file_paths = []
    time_list = []
    for root, directories, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(file))
            t = os.path.getmtime(directory+'/'+file)
            # 将时间戳转换为datetime对象
            modified_datetime = datetime.fromtimestamp(t)
            # 格式化为年月日时分秒的格式
            formatted_time = modified_datetime.strftime("%Y-%m-%d %H:%M:%S")
            time_list.append(formatted_time)
    return file_paths, time_list


# 在数据库中查询数据
def query_pre_data(turbid, year, month, day, hour, length):
    connection = pool.get_connection()
    current_date = datetime(int(year), int(month), int(day), int(hour), 0, 0)
    previous_date = current_date - timedelta(hours=int(length))

    current_date = current_date.strftime("%y/%m/%d %H:%M")
    previous_date = previous_date.strftime("%y/%m/%d %H:%M")

    # print(previous_date)
    # print(current_date)

    cursor = connection.cursor()
    # 使用 SQL 查询语句从数据库中获取满足条件的数据

    sql = "SELECT DATATIME,ACTUAL,PREACTUAL,YD15,PREYD15 FROM data0 WHERE Turbid=%s AND STR_TO_DATE(DATATIME, '%%Y/%%m/%%d %%H:%%i') >= STR_TO_DATE(%s, '%%Y/%%m/%%d %%H:%%i') AND STR_TO_DATE(DATATIME, '%%Y/%%m/%%d %%H:%%i') <= STR_TO_DATE(%s, '%%Y/%%m/%%d %%H:%%i')"

    cursor.execute(sql, (turbid, previous_date, current_date))
    # 获取查询结果
    result = cursor.fetchall()
    # 关闭连接
    connection.close()
    cursor.close()
    return result


def sqlverifypassword(password):
    username = session['username']
    connection = pool.get_connection()
    cursor = connection.cursor()
    sql = "SELECT * FROM usertable WHERE username=%s AND password=%s"
    cursor.execute(sql, (username, password))
    result = cursor.fetchall()
    connection.close()
    cursor.close()
    if result:
        return True
    else:
        return False

def sqlchangepassword(password):
    username = session['username']
    connection = pool.get_connection()
    cursor = connection.cursor()
    sql = "UPDATE usertable SET password='%s' WHERE username='%s';" % (password, username)
    cursor.execute(sql)
    flg = cursor.rowcount
    print(flg)
    connection.commit()
    connection.close()
    cursor.close()
    if flg==1:
        return True
    else:
        return False



def query_winddirection_data(turbid):
    connection = pool.get_connection()
    cursor = connection.cursor()
    sql = "SELECT * FROM winddirection WHERE TurbID=%s"
    cursor.execute(sql, turbid)
    result = cursor.fetchall()
    connection.close()
    cursor.close()
    return result


def addUser(username, password):
    connection = pool.get_connection()
    cursor = connection.cursor()
    print(username)
    print(password)
    sql = 'INSERT IGNORE INTO usertable (username,password) VALUES (%s,%s)'
    cursor.execute(sql, (username, password))
    connection.commit()
    flg = cursor.rowcount
    print(flg)
    connection.close()
    cursor.close()
    if flg == 1:
        return True
    return False


def verify_user(username, password):
    if username == '':
        return False
    connection = pool.get_connection()
    # 创建游标对象
    cursor = connection.cursor()
    # 执行查询语句
    sql = "SELECT * FROM usertable WHERE username = %s AND password = %s"
    cursor.execute(sql, (username, password))
    # 获取查询结果
    result = cursor.fetchone()
    # 关闭游标和连接
    connection.close()
    cursor.close()
    # 根据查询结果返回验证结果
    if result:
        return True
    else:
        return False


# 添加日志
def addlog(username, operate_time, api, note=''):
    connection = pool.get_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO log (username, operate_time, api, note) VALUES (%s,%s,%s,%s);"
    cursor.execute(sql, (username, operate_time, api, note))
    connection.commit()
    flg = cursor.rowcount
    print(flg)
    connection.close()
    cursor.close()
    if flg == 1:
        return True
    return False


# 对上传的文件进行预测并返回
def upload_predict(data):
    null_count = data['YD15'].isnull().sum()
    model1 = joblib.load("usingmodels/model1.pkl")
    model2 = joblib.load("usingmodels/model2.pkl")
    df = data[-null_count:]
    data_new = df.copy()
    # 新建一列
    df['WINDSPEED2'] = df['WINDSPEED'] * np.cos(np.radians(df['WINDDIRECTION'].values))
    train = df[["WINDSPEED", "WINDSPEED2"]]
    output1 = model1.predict(train.values)
    output2 = model2.predict(train.values)
    data_new['YD15'] = output1
    data_new['ROUND(A.POWER,0)'] = output2
    global res_datatime
    global res_windspeed
    global res_power
    global df_upload_file
    res_datatime = data_new['DATATIME'].tolist()
    res_power = data_new['YD15'].tolist()
    res_windspeed = data_new['WINDSPEED'].tolist()
    df_upload_file[-null_count:] = data_new[-null_count:]
    return jsonify({
        'DATATIME': data_new['DATATIME'].values.tolist(),
        'PRE_POWER': data_new['ROUND(A.POWER,0)'].values.tolist(),
        'PRE_YD15': data_new['YD15'].values.tolist()
    })


# 给定一段时间预测接下来一段时间的值
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
    # print(data)
    result_list_datatime = [item[0] for item in data]
    result_list_actualpower = [float(item[1]) for item in data]
    result_list_preactual = [float(item[2]) for item in data]
    result_list_yd15 = [float(item[3]) for item in data]
    result_list_preyd15 = [float(item[4]) for item in data]
    # print(result_list)
    # 将查询结果处理为 JSON 格式
    result = jsonify({
        "DATETIME": result_list_datatime,
        "ROUND(A.POWER,0)": result_list_actualpower,
        "PRE_ROUND(A.POWER,0)": result_list_preactual,
        "YD15": result_list_yd15,
        "PRE_YD15": result_list_preyd15
    })
    return result


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


@app.route('/log')
def log():
    username = session.get('username')
    sdk = session.get('sdk')
    return render_template('log.html', username=username, log=log)


@app.route('/get_apicount', methods=['GET'])
def get_apicount():
    username = request.args.get('username')
    # data = query_apicount_data(username,)
    # res_list_apicount = list(data[0])
    res_list_apicount = []
    for key in api_list.keys():
        data = query_apicount_data(username, api_list[key])
        # print('getapicount中的返回'+key, data[0])
        res_list_apicount.append(data[0])
    result = jsonify({
        "cnt": len(api_list),
        "apicount": res_list_apicount
    })
    return result


# 获取他人使用offline程序跑出来的模型
@app.route('/getmodel', methods=['POST'])
def get_model():
    sdk = request.values.get('sdk')  # 这是sdk，可以从数据库中查出用户名，然后将日志表直接填了。
    currenttime = request.values.get('currenttime')
    file = request.files['file']
    cnt = count_files_in_folder('./getmodels')
    # 添加日志记录

    if cnt % 2 == 0:
        tmp = int(cnt / 2)
        file_name = "yd15_" + str(tmp + 1) + ".pkl"
    else:
        tmp = int(cnt / 2)
        file_name = "actualpower_" + str(tmp + 1) + ".pkl"
    file.save('./getmodels/' + file_name)  # 保存到指定位置
    return '文件上传成功！'


@app.route('/download_offine_soft')
def download_offine_soft():
    file_path = './offline_soft/龙源电力功率预测系统offline安装包.msi'  # 文件在服务器上的路径
    return send_file(file_path, as_attachment=True)

@app.route('/download_history_csv')
def download_history_csv():
    file_path = request.args.get('path')
    return send_file(file_path, as_attachment=True)



@app.route('/gptapi_analyze')
def analyze_wind_power():
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['gptapi_analyze'], note="AI分析")
    # 编辑prompt
    openai.api_key = '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'
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
         "content": "这是一列时间序列，" + to_string(res_datatime, 0) + "这是对应的风速列，" + to_string(res_windspeed,
                                                                                                       1) + "这是对应的功率列，" + to_string(
             res_power, 1) + "请结合时间分析一下风速对于功率的影响。"
                             "我需要你结合风速的变化，分析功率的变化情况，给出分析结果，比如某个时间到另一个时间内，风速发生了什么变化，功率又有什么变化，并分析原因，分析的透彻到底，一段话直接说明白，不用画图"},
    ]
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-0301',
        messages=messages,
        temperature=0,
    )
    print(messages)
    # 获取助手角色的回答
    assistant_response = response['choices'][0]['message']['content']
    return jsonify({'ans': assistant_response})


# 设置API密钥
API_KEY = 'your-api-key'


@app.route('/longyuanapi', methods=['POST'])
def api_predict():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    # 检查身份验证头部中是否包含正确的密钥
    if 'Authorization' not in request.headers or request.headers['Authorization'] != API_KEY:
        return jsonify({'error': 'Unauthorized'})
    file = request.files['file']
    # 检查文件类型是否为CSV
    if file.filename.endswith('.csv'):

        show = request.headers['show']
        train = request.headers['train']
        output = request.headers['output']

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


router_list = [
    '/',
    '/index',
    ''
]
static_list = [
    '/staic',

]


# @app.before_request
# def myredirect():
#     if not request.path in router_list+static_list:
#         username = request.args.get('username')
#         if not username:
#             print('测试username')
#             return redirect('/?error=请登录', code=302, )
#         else:
#             print('success')

@app.route('/')
def home():
    username = session.get('username')
    print(username)
    if not username is None:
        return redirect('/index')
    return redirect('/login')


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



@app.route('/offline')
def offline():
    username = session.get('username')
    # session.get('sdk')
    sdk = session.get('sdk')
    print('sdk是多少:', sdk)
    return render_template("offline.html", username=username, sdk=sdk)


@app.route('/newsdk')
def newsdk():
    sdk = secrets.token_hex(16).__str__()
    username = session.get('username')
    connection = pool.get_connection()
    cursor = connection.cursor()
    sql = "UPDATE usertable SET sdk='%s' WHERE username='%s';" % (sdk, username)
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
    # jsonify({'sdk': sdk})
    return redirect('/offline')
    # 将sdk和username对应起来加到数据库中


# @app.route('/getsdk')
def getsdk():
    username = session.get('username')
    connection = pool.get_connection()
    cursor = connection.cursor()
    sql = "SELECT sdk FROM usertable WHERE username='%s'" % username
    cursor.execute(sql)
    result = cursor.fetchone()
    if result is not None:
        session['sdk'] = result[0]
    else:
        del session['sdk']
    connection.close()
    cursor.close()
    return session.get('sdk')


def createfolder(username):
    path1 = 'userdata/%s/上传数据集' % username
    path2 = 'userdata/%s/下载结果文件' % username
    path3 = 'static/usertouxiang/%s' % username
    print('__________________________________')
    os.makedirs(path1, exist_ok=True)
    os.makedirs(path2, exist_ok=True)
    os.makedirs(path3, exist_ok=True)
    source_file = 'static/picture/touxiang.png'
    destination_file = path3 + '/touxiang.png'
    if os.path.exists(destination_file) == False:
        shutil.copy2(source_file, destination_file)


@app.route('/index', methods=['POST'])
def login_verify():
    username = request.form['username']
    password = request.form['password']
    print(username)
    print(password)
    flg = verify_user(username, password)
    if flg:
        session['username'] = username
        session['sdk'] = getsdk()
        sdk = session.get('sdk')
        # 为该用户建立需要的文件夹
        createfolder(username)
        return render_template("index.html", username=username, sdk=sdk)




    elif password == '':
        error = '密码不能为空'
        # redirect('/login')
        return render_template('login.html', error=error, username=username)
    else:
        error = '用户名或密码错误'
        # redirect('/login')
        return render_template('login.html', error=error, username=username)

@app.route('/index')
def to_index():
    username = session.get('username')
    if username == None:
        return redirect('/')
    return render_template('index.html', username=username)


@app.route('/admin')
def to_admin():
    username = session.get('username')
    if username == 'admin':
        return render_template('admin.html', username=username)
    else:
        return render_template('iderror.html')


@app.route('/api')
def to_api():
    username = session.get('username')
    return render_template('api.html', username=username)


@app.route('/predict')
def to_predict():
    username = session.get('username')
    return render_template('predict.html', username=username)
@app.route('/personalcenter')
def to_personalcenter():
    username = session.get('username')
    return render_template('personalcenter.html', username=username)

@app.route('/upload_file', methods=['POST'])
def get_file():
    if 'file' not in request.files:
        return '未选择文件', 400
    file = request.files['file']
    if file.filename == '':
        return '未选择文件', 400
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['upload_file'], note="上传数据文件")
    df = pd.read_csv(file)
    path = "userdata/%s/上传数据集" % session.get('username')
    cnt = count_files_in_folder(path)
    filename = '/in' + str(cnt+1) + '.csv'
    df.to_csv(path + filename, index=False)
    global df_upload_file
    df_upload_file = df
    return jsonify({})


@app.route('/data_analyze')
def data_analysis():
    # profile = ProfileReport(df_upload_file)
    # profile.to_file("templates/report.html")
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['data_analyze'], note="数据分析处理")
    name = '0001in.csv'
    df = pd.read_csv(name)
    dtale.show(df, host=myhost, port=report_port)
    return render_template('report.html')


# 前端获取文件，后端处理完，返回一段时间的预测值
@app.route('/online_predict')
def file_predict():
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['online_predict'], note="数据训练预测")
    tmp = upload_predict(df_upload_file)
    return tmp


@app.route('/download_resfile')
def download_resfile():
    now = datetime.now()
    operate_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # 添加日志
    addlog(username=session['username'], operate_time=operate_time, api=api_list['download_resfile'],
           note="下载预测结果")
    path = "userdata/%s/下载结果文件" % session.get('username')
    cnt = count_files_in_folder(path)
    file_name = '/res' + str(cnt + 1) + '.csv'
    file_path = path + file_name# 文件在服务器上的路径
    df_upload_file.to_csv(file_path, index=False)
    return send_file(file_path, download_name=file_name, as_attachment=True)


@app.route('/get_modelname')
def get_getmodels():
    usingmodels_list,tmp = get_file_paths('usingmodels')
    getmodels_list,tmp = get_file_paths('getmodels')
    return jsonify({
        'usingmodels': usingmodels_list,
        'getmodels': getmodels_list
    })

@app.route('/get_userfile')
def get_userfile():
    path1 = "userdata/%s/上传数据集" % session.get('username')
    path2 = "userdata/%s/下载结果文件" % session.get('username')
    uploadcsv_list,time1 = get_file_paths(path1)
    downloadcsv_list,time2 = get_file_paths(path2)
    print(time1)
    print(time2)
    return jsonify({
        'uploadcsv': uploadcsv_list,
        'uploadcsv_time': time1,
        'downloadcsv': downloadcsv_list,
        'downloadcsv_time': time2
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


# 注册界面
@app.route('/register')
def to_register():
    return render_template('register.html')


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


@app.route('/navigation.html')
def navigation():
    return render_template('navigation.html')


@app.route('/footer.html')
def footer():
    return render_template('footer.html')



@app.route('/verifypassword', methods=['POST'])
def verifypassword():
    password = request.form.get('password')
    if sqlverifypassword(password):#验证密码成功
        sdk = getsdk()
        if sdk == None:
            return '您还未申请sdk'
        else:
            return sdk
    else:
        return '密码错误'

@app.route('/changepassword', methods=['POST'])
def changepassword():
    password = request.form.get('password')
    if sqlchangepassword(password):
        return '修改成功'
    else:
        return '修改失败，请重试'


if __name__ == '__main__':
    app.run(debug=True, host=myhost, port=myport)
