let id = document.getElementById('turb-input').value;
const dataurl = '/getiddata?id=' + id;
let Data = {
    datetime: [],
    actual: [],
    pre_actual: [],
    yd15: [],
    pre_yd15: []
};
let datetime = [];
let actual = [];
let pre_actual = [];
let yd15 = [];
let pre_yd15 = [];

const N = 96;
let start = 1;
let end = N;

let year_i = 0;
let year_list = ['2020', '2021', '2022']
let delta = 1;

let DATA = [];
let DATAper = [];
let titlename = [];
let valdata = [];
let myColor = ["#1089E7", "#F57474", "#56D0E3", "#F8B448", "#8B78F6"];
let i = 11;
let data = [];


(async function () {
    fetch(dataurl)
        .then(res => res.json())
        .then(res => {
            console.log(res)
            Data.datetime = res.DATATIME
            Data.actual = res.ACTUAL
            Data.pre_actual = res.PREACTUAL
            Data.yd15 = res.YD15
            Data.pre_yd15 = res.PREYD15

            datetime = Data.datetime.slice(0, N);
            // console.log('7777', datetime)
            actual = Data.actual.slice(0, N);
            pre_actual = Data.pre_actual.slice(0, N);
            yd15 = Data.yd15.slice(0, N);
            pre_yd15 = Data.pre_yd15.slice(0, N);

            preRightUp()
            preActual()
            preYd15()
            preLeftdown(id)
            preLeftup(id)


        }).catch(err => {
        console.error('axios请求错误' + err)
    })

})();

// 刷新数据的函数 - 全局实际功率倍增10%
(function () {
    for (let i = 0; i < Data.yd15.length; i++) {
        // Data.yd15[i] *= Data.yd15[i]<0 ? -1:1;
        // Data.actual[i] *= Data.actual[i]<0 ? -1:1;
        // while(Data.actual[i] <= Data.yd15[i]) {
        //     Data.actual[i] = 1.1 * Data.actual[i]
        //     Data.pre_actual[i] = 1.1 * Data.actual[i]
        // }
        Data.actual[i] = 1.1 * Data.actual[i]
    }
})();

// 各月份风场累计供电量 - 左上
function preLeftup(id) {

    let data2020 = [0, 0, 0, 0, 0, 0, 0, 0, 0];
    let data2021 = [];
    let data2022 = [];

    var myChart = echarts.init(document.querySelector(".bar .chart"), null, {renderer: 'svg'});

    const url = '/querypowersupply?id=' + id
    fetch(url)
        .then(res => res.json())
        .then(res => {

            for (let i = 0; i < 3; i++) {
                data2020.push(parseFloat(res.values[i]))
            }
            for (let i = 3; i < 15; i++) {
                data2021.push(parseFloat(res.values[i]))
            }
            for (let i = 15; i < 27; i++) {
                data2022.push(parseFloat(res.values[i]))
            }
            // console.log('供电量2020', data2020)
            // console.log('供电量2021', data2021)
            // console.log('供电量2022', data2022)
            // 实例化对象

            var datax = []
            for (let i = 1; i <= 12; i++) {
                datax.push(i + '月')
            }
            // 指定配置和数据
            var option = {
                color: ["#2f89cf"],
                tooltip: {
                    trigger: "axis",
                    axisPointer: {
                        // 坐标轴指示器，坐标轴触发有效
                        type: "shadow" // 默认为直线，可选为：'line' | 'shadow'
                    }
                },
                grid: {
                    left: "0%",
                    top: "10px",
                    right: "0%",
                    bottom: "4%",
                    containLabel: true
                },
                xAxis: [
                    {
                        type: "category",
                        data: datax,
                        axisTick: {
                            alignWithLabel: true
                        },
                        axisLabel: {
                            textStyle: {
                                color: "rgba(255,255,255,.6)",
                                fontSize: "12"
                            }
                        },
                        axisLine: {
                            show: false
                        }
                    }
                ],
                yAxis: [
                    {
                        type: "value",
                        axisLabel: {
                            textStyle: {
                                color: "rgba(255,255,255,.6)",
                                fontSize: "12"
                            }
                        },
                        axisLine: {
                            lineStyle: {
                                color: "rgba(255,255,255,.1)"
                                // width: 1,
                                // type: "solid"
                            }
                        },
                        splitLine: {
                            lineStyle: {
                                color: "rgba(255,255,255,.1)"
                            }
                        }
                    }
                ],
                series: [
                    {
                        name: "该月供电量",
                        type: "bar",
                        barWidth: "35%",
                        data: data2020,
                        itemStyle: {
                            barBorderRadius: 5
                        }
                    }
                ]
            };

            // 把配置给实例对象
            myChart.setOption(option);


            // 数据变化
            var dataAll = [
                {
                    year: "2020",
                    data: data2020
                },
                {
                    year: "2021",
                    data: data2021
                },
                {
                    year: "2022",
                    data: data2022
                }
            ];

            $(".bar h2 ").on("click", "a", function () {
                option.series[0].data = dataAll[$(this).index()].data;
                myChart.setOption(option);
            });

        }).catch(err => {
        console.error('axios请求错误' + err)
    });


    window.addEventListener("resize", function () {
        myChart.resize();
    });
}

// 每2秒执行1次刷新数据的函数 - 左上轮询2021和2022
setInterval(async function () {

}, 2000);

// 发电功率实时预测 - 左中
function preActual() {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".line .chart"), null, {renderer: 'svg'});

    // 2. 指定配置和数据
    var option = {
        color: ["#00f2f1", "#ed3f35"],
        tooltip: {
            // 通过坐标轴来触发
            trigger: "axis"
        },
        legend: {
            // 距离容器10%
            right: "10%",
            // 修饰图例文字的颜色
            textStyle: {
                color: "#4c9bfd"
            }
            // 如果series 里面设置了name，此时图例组件的data可以省略
            // data: ["邮件营销", "联盟广告"]
        },
        grid: {
            top: "20%",
            left: "3%",
            right: "4%",
            bottom: "3%",
            show: true,
            borderColor: "#012f4a",
            containLabel: true
        },

        xAxis: {
            type: "category",
            boundaryGap: false,
            data: datetime,
            // 去除刻度
            axisTick: {
                show: false
            },
            // 修饰刻度标签的颜色
            axisLabel: {
                color: "rgba(255,255,255,.7)"
            },
            // 去除x坐标轴的颜色
            axisLine: {
                show: false
            }
        },
        yAxis: {
            type: "value",
            // 去除刻度
            axisTick: {
                show: false
            },
            // 修饰刻度标签的颜色
            axisLabel: {
                color: "rgba(255,255,255,.7)"
            },
            // 修改y轴分割线的颜色
            splitLine: {
                lineStyle: {
                    color: "#012f4a"
                }
            }
        },
        series: [
            {
                name: "实际发电量",
                type: "line",
                stack: "发电量",
                // 是否让线条圆滑显示
                smooth: true,
                data: actual
            },
            {
                name: "发电量预测",
                type: "line",
                stack: "预测",
                smooth: true,
                data: pre_actual
            }
        ]
    };
    // 3. 把配置和数据给实例对象
    myChart.setOption(option);

    window.addEventListener("resize", function () {
        myChart.resize();
    });
};


// 风向统计 - 左下
function preLeftdown(id) {
    let winddirection = [];

    const url = '/get_winddirection?' + 'turbid=' + id
    fetch(url)
        .then(res => res.json())
        .then(res => {
            for (let i = 0; i < 8; i++) {
                winddirection.push(parseFloat(res.direction[i]))
            }
            // 1. 实例化对象
            var myChart = echarts.init(document.querySelector(".pie1  .chart"), null, {renderer: 'svg'});
            // 2. 指定配置项和数据
            var option = {
                legend: {
                    top: "90%",
                    itemWidth: 10,
                    itemHeight: 8,
                    textStyle: {
                        color: "rgba(255,255,255,.5)",
                        fontSize: "12"
                    }
                },
                tooltip: {
                    trigger: "item",
                    formatter: "{a} <br/>{b} : {c} ({d}%)"
                },
                grid: {
                    top: '10%'
                },
                // 注意颜色写的位置
                color: [
                    "#006cff",
                    "#60cda0",
                    "#ed8884",
                    "#ff9f7f",
                    "#0096ff",
                    "#9fe6b8",
                    "#32c5e9",
                    "#1d9dff"
                ],
                series: [
                    {
                        name: "风向",
                        type: "pie",
                        // 如果radius是百分比则必须加引号
                        radius: ["10%", "70%"],
                        center: ["50%", "45%"],
                        roseType: "radius",
                        data: [
                            {value: winddirection[0], name: "正北"},
                            {value: winddirection[1], name: "东北"},
                            {value: winddirection[2], name: "正东"},
                            {value: winddirection[3], name: "东南"},
                            {value: winddirection[4], name: "正南"},
                            {value: winddirection[5], name: "西南"},
                            {value: winddirection[6], name: "正西"},
                            {value: winddirection[7], name: "西北"}
                        ],
                        // 修饰饼形图文字相关的样式 label对象
                        label: {
                            fontSize: 10
                        },
                        // 修饰引导线样式
                        labelLine: {
                            // 连接到图形的线长度
                            length: 8,
                            // 连接到文字的线长度
                            length2: 8
                        }
                    }
                ]
            };

            // 3. 配置项和数据给我们的实例化对象
            myChart.setOption(option);
            // 4. 当我们浏览器缩放的时候，图表也等比例缩放
            window.addEventListener("resize", function () {
                // 让我们的图表调用 resize这个方法
                myChart.resize();
            });
        }).catch(err => {
        console.error('axios请求错误' + err)
    });
}

// 刷新数据的函数 - 左中 + 右中
async function update() {
    // ---------------------右上-------------------------
    await updateRU()
    // ---------------------左中+右中-------------------------
    var myChart = echarts.init(document.querySelector(".line .chart"), null, {renderer: 'svg'});
    var myChart1 = echarts.init(document.querySelector(".line1 .chart"), null, {renderer: 'svg'});

    let newoneDATATIME;
    let newonePREACTUAL;
    let newoneACTUAL;
    let newoneYD15;
    let newonePREYD15;
    let year;
    let month;
    let day;
    let hour;
    let minute;

    var nowid = document.getElementById('turb-input').value;
    if (nowid !== id) {
        //图重画
        id = nowid;
        preLeftdown(id);
        preLeftup(id);

        await fetch('/getiddata?id=' + id)
            .then(res => res.json())
            .then(res => {
                console.log('更换id', res)
                Data.datetime = res.DATATIME
                Data.actual = res.ACTUAL
                Data.pre_actual = res.PREACTUAL
                Data.yd15 = res.YD15
                Data.pre_yd15 = res.PREYD15

                datetime = Data.datetime.slice(0, N);
                actual = Data.actual.slice(0, N);
                pre_actual = Data.pre_actual.slice(0, N);
                yd15 = Data.yd15.slice(0, N);
                pre_yd15 = Data.pre_yd15.slice(0, N);

            }).catch(err => {
                console.error('axios请求错误' + err)
            })
    } else {
        const lasttime = datetime[N - 1]
        let nowdate = new Date(lasttime);
        // 获取当前时间的毫秒数
        let timestamp = nowdate.getTime();
        // 加上15分钟的毫秒数
        timestamp += 15 * 60 * 1000;
        // 设置新的时间
        nowdate.setTime(timestamp);
        // 获取年月日时分
        year = nowdate.getFullYear();
        month = nowdate.getMonth() + 1;
        day = nowdate.getDate();
        hour = nowdate.getHours();
        minute = nowdate.getMinutes();

        const url = '/queryonedatabyidandtime?id=' + id + '&&year=' + year.toString() + '&&month=' + month.toString() + '&&day=' + day.toString() + '&&hour=' + hour.toString() + '&&minute=' + minute.toString()
        // console.log(url)
        await fetch(url)
            .then(res => res.json())
            .then(res => {
                // console.log(res)
                newoneDATATIME = res.DATATIME
                newoneACTUAL = res.ACTUAL
                newonePREACTUAL = res.PREACTUAL
                newoneYD15 = res.YD15
                newonePREYD15 = res.PREYD15
                // console.log('newone', newoneDATATIME)

            }).catch(err => {
                console.error('axios请求错误' + err)
            });

        datetime = datetime.slice(1, N)
        datetime.push(newoneDATATIME)

        actual = actual.slice(1, N)
        actual.push(newoneACTUAL)

        pre_actual = pre_actual.slice(1, N)
        pre_actual.push(newonePREACTUAL)

        yd15 = yd15.slice(1, N)
        yd15.push(newoneYD15)

        pre_yd15 = pre_yd15.slice(1, N)
        pre_yd15.push(newonePREYD15)
    }

    const option = {
        color: ["#00f2f1", "#ed3f35"],
        tooltip: {
            // 通过坐标轴来触发
            trigger: "axis"
        },
        legend: {
            // 距离容器10%
            right: "10%",
            // 修饰图例文字的颜色
            textStyle: {
                color: "#4c9bfd"
            }
            // 如果series 里面设置了name，此时图例组件的data可以省略
            // data: ["邮件营销", "联盟广告"]
        },
        grid: {
            top: "20%",
            left: "3%",
            right: "4%",
            bottom: "3%",
            show: true,
            borderColor: "#012f4a",
            containLabel: true
        },

        xAxis: {
            type: "category",
            boundaryGap: false,
            data: datetime,
            // 去除刻度
            axisTick: {
                show: false
            },
            // 修饰刻度标签的颜色
            axisLabel: {
                color: "rgba(255,255,255,.7)"
            },
            // 去除x坐标轴的颜色
            axisLine: {
                show: false
            }
        },
        yAxis: {
            type: "value",
            // 去除刻度
            axisTick: {
                show: false
            },
            // 修饰刻度标签的颜色
            axisLabel: {
                color: "rgba(255,255,255,.7)"
            },
            // 修改y轴分割线的颜色
            splitLine: {
                lineStyle: {
                    color: "#012f4a"
                }
            }
        },
        series: [
            {
                name: "实际发电量",
                type: "line",
                stack: "发电量",
                // 是否让线条圆滑显示
                smooth: true,
                data: actual
            },
            {
                name: "发电量预测",
                type: "line",
                stack: "预测",
                smooth: true,
                data: pre_actual
            }
        ]
    };
    const option1 = {
        tooltip: {
            trigger: "axis",
            axisPointer: {
                lineStyle: {
                    color: "#dddc6b"
                }
            }
        },
        legend: {
            top: "0%",
            textStyle: {
                color: "rgba(255,255,255,.5)",
                fontSize: "12"
            }
        },
        grid: {
            left: "10",
            top: "30",
            right: "10",
            bottom: "10",
            containLabel: true
        },

        xAxis: [
            {
                type: "category",
                boundaryGap: false,
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.6)",
                        fontSize: 12
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.2)"
                    }
                },

                data: datetime
            },
            {
                axisPointer: {show: false},
                axisLine: {show: false},
                position: "bottom",
                offset: 20
            }
        ],

        yAxis: [
            {
                type: "value",
                axisTick: {show: false},
                axisLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.1)"
                    }
                },
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.6)",
                        fontSize: 12
                    }
                },

                splitLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.1)"
                    }
                }
            }
        ],
        series: [
            {
                name: "供电量",
                type: "line",
                smooth: true,
                symbol: "circle",
                symbolSize: 5,
                showSymbol: false,
                lineStyle: {
                    normal: {
                        color: "#0184d5",
                        width: 2
                    }
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(
                            0,
                            0,
                            0,
                            1,
                            [
                                {
                                    offset: 0,
                                    color: "rgba(1, 132, 213, 0.4)"
                                },
                                {
                                    offset: 0.8,
                                    color: "rgba(1, 132, 213, 0.1)"
                                }
                            ],
                            false
                        ),
                        shadowColor: "rgba(0, 0, 0, 0.1)"
                    }
                },
                itemStyle: {
                    normal: {
                        color: "#0184d5",
                        borderColor: "rgba(221, 220, 107, .1)",
                        borderWidth: 12
                    }
                },
                data: yd15
            },
            {
                name: "供电量预测",
                type: "line",
                smooth: true,
                symbol: "circle",
                symbolSize: 5,
                showSymbol: false,
                lineStyle: {
                    normal: {
                        color: "#00d887",
                        width: 2
                    }
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(
                            0,
                            0,
                            0,
                            1,
                            [
                                {
                                    offset: 0,
                                    color: "rgba(0, 216, 135, 0.4)"
                                },
                                {
                                    offset: 0.8,
                                    color: "rgba(0, 216, 135, 0.1)"
                                }
                            ],
                            false
                        ),
                        shadowColor: "rgba(0, 0, 0, 0.1)"
                    }
                },
                itemStyle: {
                    normal: {
                        color: "#00d887",
                        borderColor: "rgba(221, 220, 107, .1)",
                        borderWidth: 12
                    }
                },
                data: pre_yd15
            }
        ]
    };
    myChart.setOption(option);
    myChart1.setOption(option1);


    // ---------------------左上-------------------------
    if (year_i === year_list.length - 1) {
        year_i = 0;
    } else {
        year_i = year_i + 1;
    }
    // console.log('测试year_i', year_i);
    let yearLU = year_list[year_i]
    document.getElementById('year').innerHTML = yearLU
    document.getElementById(yearLU).click()


}

// 每秒执行1次刷新数据的函数 - 左中 + 右中
(async function () {
    setInterval(async function () {
        await update();
    }, 2000);
})();

// 每秒执行1次刷新数据的函数 - 中上 - 全风场累计供电量+全风场累计发电量
setInterval(function () {
    // const yd15_dom = document.getElementById('yd15');
    // const pre_yd15_dom = document.getElementById('pre_yd15');
    // yd15_dom.innerHTML = String(sum_yd15[end - N]);
    // pre_yd15_dom.innerHTML = String(sum_pre_yd15[end - N]);
    const datetime_dom = document.getElementById('datetime');
    currentDate = new Date();

    year = currentDate.getFullYear();  // 获取当前年份
    month = ('0' + (currentDate.getMonth() + 1)).slice(-2);  // 获取当前月份，并补零
    day = ('0' + currentDate.getDate()).slice(-2);  // 获取当前日期，并补零
    hours = ('0' + currentDate.getHours()).slice(-2);  // 获取当前小时，并补零
    minutes = ('0' + currentDate.getMinutes()).slice(-2);  // 获取当前分钟，并补零
    seconds = ('0' + currentDate.getSeconds()).slice(-2);  // 获取当前秒数，并补零

    formattedDate = year + '-' + month + '-' + day + ' ' + hours + ':' + minutes + ':' + seconds;

    // console.log(formattedDate);  // 输出格式化后的日期和时间

    datetime_dom.innerHTML = formattedDate
}, 1000);

// 风场累计供电量 - 右上
function preRightUp() {
    const sumURL = '/sum_by_turbid'
    fetch(sumURL)
        .then(res => res.json())
        .then(res => {
            // 基于准备好的dom，初始化echarts实例
            var myChart = echarts.init(document.querySelector(".bar1 .chart"), null, {renderer: 'svg'});

            let sum = 0;
            for (let i = 11; i <= 20; i++) {
                // console.log('测试sumby', res[i])
                var tmp = res[i] / 100000000.0
                DATA.push(parseFloat(tmp.toFixed(1)))
                sum += DATA[i - 11];
            }
            for (let i = 11; i <= 20; i++) {
                let tmp = DATA[i - 11] / sum * 100
                DATAper[i - 11] = parseFloat(tmp.toFixed(1));
            }
            // console.log('测试DATA', DATA)

            for (i = 11; i <= 15; i++) {
                titlename.push('Turb-' + i)
                let tmp = DATA[i - 11]
                valdata.push(tmp.toString() + 'M');
                data.push(DATAper[i - 11]);
            }

            option = {
                //图标位置
                grid: {
                    top: "10%",
                    left: "18%",
                    right: "15%",
                    bottom: "10%"
                },
                xAxis: {
                    show: false
                },
                yAxis: [
                    {
                        show: true,
                        data: titlename,
                        inverse: true,
                        axisLine: {
                            show: false
                        },
                        splitLine: {
                            show: false
                        },
                        axisTick: {
                            show: false
                        },
                        axisLabel: {
                            color: "#fff",

                            rich: {
                                lg: {
                                    backgroundColor: "#339911",
                                    color: "#fff",
                                    borderRadius: 15,
                                    // padding: 5,
                                    align: "center",
                                    width: 15,
                                    height: 15
                                }
                            }
                        }
                    },
                    {
                        show: true,
                        inverse: true,
                        data: valdata,
                        axisLabel: {
                            textStyle: {
                                fontSize: 12,
                                color: "#fff"
                            }
                        }
                    }
                ],
                series: [
                    {
                        name: "条",
                        type: "bar",
                        yAxisIndex: 0,
                        data: data,
                        barCategoryGap: 50,
                        barWidth: 10,
                        itemStyle: {
                            normal: {
                                barBorderRadius: 20,
                                color: function (params) {
                                    var num = myColor.length;
                                    return myColor[params.dataIndex % num];
                                }
                            }
                        },
                        label: {
                            normal: {
                                show: true,
                                position: "inside",
                                formatter: "{c}%"
                            }
                        }
                    },
                    {
                        name: "框",
                        type: "bar",
                        yAxisIndex: 1,
                        barCategoryGap: 50,
                        data: data,
                        barWidth: 15,
                        itemStyle: {
                            normal: {
                                color: 'none',
                                borderColor: "#00c1de",
                                borderWidth: 3,
                                barBorderRadius: 15
                            }
                        }
                    }
                ]
            };
            // 使用刚指定的配置项和数据显示图表。
            myChart.setOption(option);

            window.addEventListener("resize", function () {
                myChart.resize();
            });
        }).catch(err => {
        console.error('sumByTurb请求错误' + err)
    })

}

async function updateRU() {
    var myChart = echarts.init(document.querySelector(".bar1 .chart"), null, {renderer: 'svg'});

    titlename = titlename.slice(1, 5);
    titlename.push('Turb-' + i);
    valdata = valdata.slice(1, 5);
    var temp = DATA[i - 11]
    valdata.push(temp.toString() + 'M')
    data = data.slice(1, 5);
    data.push(DATAper[i - 11])
    let colort = myColor[0];
    myColor = myColor.slice(1, 5);
    myColor.push(colort)

    i += 1;
    if (i >= 21) {
        i = 10 + i % 20;
    }

    option = {
        //图标位置
        grid: {
            top: "10%",
            left: "18%",
            right: "15%",
            bottom: "10%"
        },
        xAxis: {
            show: false
        },
        yAxis: [
            {
                show: true,
                data: titlename,
                inverse: true,
                axisLine: {
                    show: false
                },
                splitLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: "#fff",

                    rich: {
                        lg: {
                            backgroundColor: "#339911",
                            color: "#fff",
                            borderRadius: 15,
                            // padding: 5,
                            align: "center",
                            width: 15,
                            height: 15
                        }
                    }
                }
            },
            {
                show: true,
                inverse: true,
                data: valdata,
                axisLabel: {
                    textStyle: {
                        fontSize: 12,
                        color: "#fff"
                    }
                }
            }
        ],
        series: [
            {
                name: "条",
                type: "bar",
                yAxisIndex: 0,
                data: data,
                barCategoryGap: 50,
                barWidth: 10,
                itemStyle: {
                    normal: {
                        barBorderRadius: 20,
                        color: function (params) {
                            var num = myColor.length;
                            return myColor[params.dataIndex % num];
                        }
                    }
                },
                label: {
                    normal: {
                        show: true,
                        position: "inside",
                        formatter: "{c}%"
                    }
                }
            },
            {
                name: "框",
                type: "bar",
                yAxisIndex: 1,
                barCategoryGap: 50,
                data: data,
                barWidth: 15,
                itemStyle: {
                    normal: {
                        color: 'none',
                        borderColor: "#00c1de",
                        borderWidth: 3,
                        barBorderRadius: 15
                    }
                }
            }
        ]
    };
    // 使用刚指定的配置项和数据显示图表。
    myChart.setOption(option);
}


// 供电功率实时预测 - 右中
function preYd15() {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".line1 .chart"), null, {renderer: 'svg'});

    option = {
        tooltip: {
            trigger: "axis",
            axisPointer: {
                lineStyle: {
                    color: "#dddc6b"
                }
            }
        },
        legend: {
            top: "0%",
            textStyle: {
                color: "rgba(255,255,255,.5)",
                fontSize: "12"
            }
        },
        grid: {
            left: "10",
            top: "30",
            right: "10",
            bottom: "10",
            containLabel: true
        },

        xAxis: [
            {
                type: "category",
                boundaryGap: false,
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.6)",
                        fontSize: 12
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.2)"
                    }
                },

                data: datetime
            },
            {
                axisPointer: {show: false},
                axisLine: {show: false},
                position: "bottom",
                offset: 20
            }
        ],

        yAxis: [
            {
                type: "value",
                axisTick: {show: false},
                axisLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.1)"
                    }
                },
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.6)",
                        fontSize: 12
                    }
                },

                splitLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.1)"
                    }
                }
            }
        ],
        series: [
            {
                name: "供电量",
                type: "line",
                smooth: true,
                symbol: "circle",
                symbolSize: 5,
                showSymbol: false,
                lineStyle: {
                    normal: {
                        color: "#0184d5",
                        width: 2
                    }
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(
                            0,
                            0,
                            0,
                            1,
                            [
                                {
                                    offset: 0,
                                    color: "rgba(1, 132, 213, 0.4)"
                                },
                                {
                                    offset: 0.8,
                                    color: "rgba(1, 132, 213, 0.1)"
                                }
                            ],
                            false
                        ),
                        shadowColor: "rgba(0, 0, 0, 0.1)"
                    }
                },
                itemStyle: {
                    normal: {
                        color: "#0184d5",
                        borderColor: "rgba(221, 220, 107, .1)",
                        borderWidth: 12
                    }
                },
                data: yd15
            },
            {
                name: "供电量预测",
                type: "line",
                smooth: true,
                symbol: "circle",
                symbolSize: 5,
                showSymbol: false,
                lineStyle: {
                    normal: {
                        color: "#00d887",
                        width: 2
                    }
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(
                            0,
                            0,
                            0,
                            1,
                            [
                                {
                                    offset: 0,
                                    color: "rgba(0, 216, 135, 0.4)"
                                },
                                {
                                    offset: 0.8,
                                    color: "rgba(0, 216, 135, 0.1)"
                                }
                            ],
                            false
                        ),
                        shadowColor: "rgba(0, 0, 0, 0.1)"
                    }
                },
                itemStyle: {
                    normal: {
                        color: "#00d887",
                        borderColor: "rgba(221, 220, 107, .1)",
                        borderWidth: 12
                    }
                },
                data: pre_yd15
            }
        ]
    };

    // 使用刚指定的配置项和数据显示图表。
    myChart.setOption(option);
    window.addEventListener("resize", function () {
        myChart.resize();
    });
};
// 风场地区分布 - 右下 - 静态
(async function () {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".pie .chart"), null, {renderer: 'svg'});

    option = {
        tooltip: {
            trigger: "item",
            formatter: "{a} <br/>{b}: {c} ({d}%)",
            position: function (p) {
                //其中p为当前鼠标的位置
                return [p[0] + 10, p[1] - 10];
            }
        },
        legend: {
            top: "90%",
            itemWidth: 10,
            itemHeight: 10,
            data: ["海南", "辽宁", "河北", "江苏", "黑龙江", "甘肃", "新疆", "内蒙古"],
            textStyle: {
                color: "rgba(255,255,255,.5)",
                fontSize: "12"
            }
        },
        series: [
            {
                name: "风场地区分布",
                type: "pie",
                center: ["50%", "42%"],
                radius: ["40%", "60%"],
                color: [
                    "#065aab",
                    "#066eab",
                    "#0682ab",
                    "#0696ab",
                    "#06a0ab",
                    "#06b4ab",
                    "#06c8ab",
                    "#06dcab",
                    "#06f0ab"
                ],
                label: {show: false},
                labelLine: {show: false},
                data: [
                    {value: 20, name: "海南"},
                    {value: 26, name: "辽宁"},
                    {value: 24, name: "河北"},
                    {value: 25, name: "江苏"},
                    {value: 20, name: "黑龙江"},
                    {value: 25, name: "甘肃"},
                    {value: 30, name: "新疆"},
                    {value: 42, name: "内蒙古"}
                ]
            }
        ]
    };

    // 使用刚指定的配置项和数据显示图表。
    myChart.setOption(option);
    window.addEventListener("resize", function () {
        myChart.resize();
    });
})();


