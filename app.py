import glob
import os
import openai
import numpy as np
import pandas as pd
import pymysqlpool
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file, render_template
from flask_cors import CORS
from lightgbm import LGBMRegressor, early_stopping
from sklearn.model_selection import train_test_split


app = Flask(__name__)
CORS(app)

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



# 在数据库中查询数据
def query_data(turbid, year, month, day, hour, length):
    connection = pool.get_connection()
    current_date = datetime(int(year), int(month), int(day), int(hour), 0, 0)
    previous_date = current_date - timedelta(hours=int(length))

    current_date = current_date.strftime("%y/%m/%d %H:%M")
    previous_date = previous_date.strftime("%y/%m/%d %H:%M")


    print(previous_date)
    print(current_date)

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


# 对上传的文件进行预测并返回
def upload_predict(data):
    df = data
    data_new = df.copy()
    data_new = data_new[-172:]
    df = df.fillna(0)
    # 新建一列
    df['WINDSPEED2'] = df['WINDSPEED'] * np.cos(np.radians(df['WINDDIRECTION'].values))
    # 预测YD15
    X_train1 = df[["WINDSPEED", "WINDSPEED2"]][:-172]
    y_train1 = df[["YD15"]][:-172]
    X_test1 = df[["WINDSPEED", "WINDSPEED2"]][-172:]
    # gbm
    x_train, x_test, y_train, y_test = train_test_split(X_train1, y_train1, test_size=0.2)
    gbm1 = LGBMRegressor(objective="regression", learning_rate=0.005, n_estimators=1000, n_jobs=-1)
    gbm1 = gbm1.fit(x_train, y_train, eval_set=[(x_test, y_test)], eval_metric="rmse",
                    callbacks=[early_stopping(stopping_rounds=1000)])
    y_pred15 = gbm1.predict(X_test1.values)
    output1 = y_pred15
    # 预测POWER
    X_train2 = df[["WINDSPEED", "WINDSPEED2"]][:-172]
    y_train2 = df[["ROUND(A.POWER,0)"]][:-172]
    X_test2 = df[["WINDSPEED", "WINDSPEED2"]][-172:]
    # gbm
    x_train, x_test, y_train, y_test = train_test_split(X_train2, y_train2, test_size=0.2)
    gbm2 = LGBMRegressor(objective="regression", learning_rate=0.005, n_estimators=1000, n_jobs=-1)
    gbm2 = gbm2.fit(x_train, y_train, eval_set=[(x_test, y_test)], eval_metric="rmse",
                    callbacks=[early_stopping(stopping_rounds=1000)])
    POWER = gbm2.predict(X_test2.values)
    output2 = POWER
    data_new['PREYD15'] = output1
    data_new['PREACTUAL'] = output2
    data_new = data_new[['DATATIME', 'PREACTUAL', 'PREYD15']]
    return jsonify({
        'DATATIME': data_new['DATATIME'].values.tolist(),
        'PREACTUAL': data_new['PREACTUAL'].values.tolist(),
        'PREYD15': data_new['PREYD15'].values.tolist()
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
    data = query_data(turbid, year, month, day, hour, length)
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
        "ROUND(A.POWER,0)":result_list_actualpower,
        "PRE_ROUND(A.POWER,0)":result_list_actualpower,
        "YD15":result_list_yd15,
        "PRE_YD15": result_list_preyd15
    })
    return result


# 前端获取文件，后端处理完，返回一段时间的预测值
@app.route('/upload', methods=['POST'])
def file_predict():
    if 'file' not in request.files:
        return '未选择文件', 400

    file = request.files['file']
    if file.filename == '':
        return '未选择文件', 400
    df = pd.read_csv(file)
    return upload_predict(df)


# 获取他人使用offline程序跑出来的模型
@app.route('/getmodel', methods=['POST'])
def get_model():
    file = request.files['file']
    cnt = count_files_in_folder('./getmodels')
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
    file_path = './offline_soft/龙源电力功率预测系统油专特供offline_v0.0.3.exe'  # 文件在服务器上的路径
    return send_file(file_path, as_attachment=True)


@app.route('/gptapi_analyze', methods=['POST'])
def analyze_wind_power():
    # 从请求中获取上传的CSV文件
    file = request.files['file']
    # 读取数据集
    dataset = pd.read_csv(file)
    # 编辑prompt
    openai.api_key = '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'
    openai.api_base = "https://chat-api.leyoubaloy.xyz/v1"
    # send a ChatCompletion request to GPT
    messages = [
        {"role": "system",
         "content": "我希望你扮演一个数据分析师的角色。作为数据分析师，你有深厚的数学和统计知识，并且擅长使用各种数据分析工具和编"+
                    "程语言来解析数据。你对风电数据非常熟悉，包括功率、风速与时间的关系。你的职责是分析这些数据，并提供关于可能原因和"+
                    "潜在风险的解释。作为数据分析师，你会仔细研究风电数据中功率、风速和时间之间的关系。你会运用统计方法分析数据的趋势和"+
                    "模式，以确定功率和风速之间的关联程度。你会考虑不同的时间段和季节对风电发电量的影响，并尝试找出任何异常或异常行为。在"+
                    "分析风电数据时，你会注意到一些可能的原因和潜在的风险。例如，你可能会发现在某些时间段内，风速较低导致功率下降，这可能"+
                    "是由于气候条件或设备故障所致。另外，你还可能观察到功率波动较大的情况，这可能是由于风速变化剧烈或设备运行问题引起的。作"+
                    "为数据分析师，你的职责还包括编写详细的报告，向相关团队和管理层提供分析结果和建议。你会使用图表、图形和数据可视化工具"+
                    "来有效传达你的分析结果，并解释可能的原因和潜在风险。请注意，作为一个角色扮演的AI，我会尽力扮演数据分析师的角色，但我"+
                    "的回答仅基于模型训练时的数据，并不能保证分析的准确性。在实际情况中，建议您寻求专业的数据分析师进行详细的数据分析和解释。"},
        {"role": "user",
         "content": f"我已经上传了数据集，文件名为: {file.filename}。"
                    f"我需要你结合风速(WINDSPEED)的变化，分析功率(YD15)的变化情况，给出分析结果，分析的透彻到底，一段话直接说明白，不用画图"},
    ]
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=0,
    )
    # 获取助手角色的回答
    assistant_response = response['choices'][0]['message']['content']
    return jsonify(msg='执行成功', response=assistant_response), 200


# 设置API密钥
API_KEY = 'your-api-key'


@app.route('/test', methods=['POST'])
def predict1():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    # 检查身份验证头部中是否包含正确的密钥
    if 'Authorization' not in request.headers or request.headers['Authorization'] != API_KEY:
        return jsonify({'error': 'Unauthorized'})

    file = request.files['file']

    # 检查文件类型是否为CSV
    if file.filename.endswith('.csv'):
        # 保存上传的文件
        file.save(file.filename)

        # 读取CSV文件
        data = pd.read_csv(file.filename)

        # 在此处进行预测操作，可根据自己的需求使用适当的模型或算法

        # 假设预测结果为新的DataFrame对象
        predictions = 预测(data)

        # 生成预测后的CSV文件
        output_filename = 'predictions.csv'
        predictions.to_csv(output_filename, index=False)

        return jsonify({'success': True, 'output_filename': output_filename})

    else:
        return jsonify({'error': 'Invalid file format, only CSV files are allowed'})

@app.route('/')
def home():
    return render_template("login.html")


@app.route('/index', methods=['POST'])
def login_verify():
    username = request.form['username']
    password = request.form['password']

    if username == 'user' and password == 'user':
        return render_template("index.html")
    elif username == 'admin' and password == 'admin':
        return render_template("index.html")
    else:
        error = '用户名或密码错误'
        return render_template('login.html', error=error)

@app.route('/offline')
def offline():
    return render_template("offline.html")

@app.route('/index')
def to_index():
    return render_template('index.html')

@app.route('/admin')
def to_admin():
    return render_template('basic-table.html')

@app.route('/api')
def to_api():
    return render_template('api.html')


@app.route('/predict')
def to_predict():
    return render_template('predict.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5446)
