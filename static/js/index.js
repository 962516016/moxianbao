let id = document.getElementById('turb-input').value;

let firstdate = ['2021-11-01 00:00:00', '2021-11-01 00:00:00', '2021-04-02 00:00:00', '2021-04-02 00:00:00', '2021-04-02 00:00:00', '2020-10-02 00:00:00', '2021-04-02 00:00:00', '2022-01-02 00:00:00', '2022-01-01 00:00:00', '2020-10-01 00:00:00'];

dataurl = '/getiddata?id=' + id

let Data = {
    datetime: [],
    actual: [],
    pre_actual: [],
    yd15: [],
    pre_yd15: []
};

let sum_yd15 = [136080275, 136080367, 136080464, 136080565, 136080669, 136080770, 136080883, 136080966, 136081051, 136081152, 136081262, 136081356, 136081454, 136081538, 136081648, 136081764, 136081868, 136081952, 136082037, 136082133, 136082237, 136082332, 136082412, 136082492, 136082597, 136082682, 136082796, 136082913, 136083004, 136083111, 136083213, 136083318, 136083438, 136083539, 136083636, 136083733, 136083846, 136083941, 136084022, 136084108, 136084202, 136084289, 136084386, 136084498, 136084601, 136084701, 136084804, 136084896, 136084989, 136085101, 136085198, 136085293, 136085391, 136085505, 136085602, 136085711, 136085820, 136085913, 136086022, 136086132, 136086238, 136086357, 136086472, 136086557, 136086665, 136086777, 136086874, 136086981, 136087079, 136087174, 136087292, 136087387, 136087474, 136087579, 136087699, 136087783, 136087890, 136088004, 136088124, 136088206, 136088319, 136088418, 136088506, 136088611, 136088721, 136088823, 136088928, 136089046, 136089134, 136089222, 136089326, 136089407, 136089521, 136089612, 136089724, 136089842, 136089958];
let sum_pre_yd15 = [137281894, 137281894, 137281894, 137281894, 137281894, 137281894, 137281894, 137281894, 136081052, 136081136, 136081267, 136081356, 136081454, 136081575, 136081643, 136081764, 136081873, 136081956, 136082049, 136082124, 136082254, 136082353, 136082420, 136082521, 136082577, 136082705, 136082767, 136082903, 136083016, 136083101, 136083202, 136083328, 136083417, 136083554, 136083646, 136083750, 136083855, 136083945, 136084026, 136084123, 136084202, 136084294, 136084381, 136084501, 136084623, 136084714, 136084790, 136084928, 136084991, 136085086, 136085190, 136085292, 136085378, 136085511, 136085623, 136085716, 136085820, 136085926, 136086026, 136086116, 136086223, 136086333, 136086449, 136086596, 136086665, 136086790, 136086863, 136086982, 136087097, 136087201, 136087263, 136087381, 136087497, 136087598, 136087672, 136087821, 136087907, 136087996, 136088106, 136088245, 136088293, 136088412, 136088527, 136088625, 136088700, 136088832, 136088918, 136089026, 136089164, 136089255, 136089341, 136089412, 136089524, 136089642, 136089717, 136089849, 136089960];

let datetime = [];
let actual = [];
let pre_actual = [];
let yd15 = [];
let pre_yd15 = [];

const N = 96;
let start = 1;
let end = N;
const seconds = (Data.yd15.length - N);
console.log('起始', N, '个点', '循环用时', seconds, '秒');

let year_i = 0;
let year_list = ['2020', '2021', '2022']
let delta = 1;


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
            console.log('7777', datetime)
            actual = Data.actual.slice(0, N);
            pre_actual = Data.pre_actual.slice(0, N);
            yd15 = Data.yd15.slice(0, N);
            pre_yd15 = Data.pre_yd15.slice(0, N);

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

    var myChart = echarts.init(document.querySelector(".bar .chart"));

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
            console.log('供电量2020', data2020)
            console.log('供电量2021', data2021)
            console.log('供电量2022', data2022)
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
    if (year_i === year_list.length - 1) {
        year_i = 0;
    } else {
        year_i = year_i + 1;
    }
    console.log('测试year_i', year_i);
    let year = year_list[year_i]
    document.getElementById('year').innerHTML = year
    document.getElementById(year).click()
}, 2000);

// 发电功率实时预测 - 左中
function preActual() {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".line .chart"));

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
            var myChart = echarts.init(document.querySelector(".pie1  .chart"));
            // 2. 指定配置项和数据
            var option = {
                legend: {
                    top: "90%",
                    itemWidth: 10,
                    itemHeight: 10,
                    textStyle: {
                        color: "rgba(255,255,255,.5)",
                        fontSize: "12"
                    }
                },
                tooltip: {
                    trigger: "item",
                    formatter: "{a} <br/>{b} : {c} ({d}%)"
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
                        center: ["50%", "42%"],
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
                            length: 10,
                            // 连接到文字的线长度
                            length2: 10
                        }
                    }
                ]
            };

            // 3. 配置项和数据给我们的实例化对象
            myChart.setOption(option);

        }).catch(err => {
        console.error('axios请求错误' + err)
    });


    // 4. 当我们浏览器缩放的时候，图表也等比例缩放
    window.addEventListener("resize", function () {
        // 让我们的图表调用 resize这个方法
        myChart.resize();
    });
}

// 刷新数据的函数 - 左中 + 右中
async function update() {
    var myChart = echarts.init(document.querySelector(".line .chart"));
    var myChart1 = echarts.init(document.querySelector(".line1 .chart"));

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

    if (nowid === id) {
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

    } else {
        //图重画
        id = nowid;
        preLeftdown(id);
        preLeftup(id);
        nowtime = firstdate[parseInt(id)-11];
        let nowdate = new Date(nowtime);
        // 获取年月日时分
        year = nowdate.getFullYear();
        month = nowdate.getMonth() + 1;
        day = nowdate.getDate();
        hour = nowdate.getHours();
        minute = nowdate.getMinutes();
    }


    const url = '/queryonedatabyidandtime?id=' + id + '&&year=' + year.toString() + '&&month=' + month.toString() + '&&day=' + day.toString() + '&&hour=' + hour.toString() + '&&minute=' + minute.toString()
    console.log(url)
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


// 2. 指定配置和数据
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
// 3. 把配置和数据给实例对象
    myChart.setOption(option);
    myChart1.setOption(option1);
}


// 每秒执行1次刷新数据的函数 - 左中 + 右中
(async function () {
    setInterval(async function () {
        await update();
    }, 2000);
})();

// 每秒执行1次刷新数据的函数 - 中上 - 全风场累计供电量+全风场累计发电量
setInterval(function () {
    const yd15_dom = document.getElementById('yd15');
    const pre_yd15_dom = document.getElementById('pre_yd15');
    yd15_dom.innerHTML = String(sum_yd15[end - N]);
    pre_yd15_dom.innerHTML = String(sum_pre_yd15[end - N]);
}, 1000);


// 风场累计供电量 - 右上
(async function () {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".bar1 .chart"));

    var data = [11, 7, 19, 12, 51];
    var titlename = [];
    var valdata = ['2.8M', '2.0M', '4.8M', '3.1M', '13M'];
    var myColor = ["#1089E7", "#F57474", "#56D0E3", "#F8B448", "#8B78F6"];

    for (let i = 11; i <= 15; i++) {
        titlename.push('Turb-' + i)
    }
    option = {
        //图标位置
        grid: {
            top: "10%",
            left: "22%",
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
                data: [11, 7, 19, 12, 51],
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
})();

// 供电功率实时预测 - 右中
function preYd15() {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".line1 .chart"));

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
// 风场地区分布 - 右下
(async function () {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.querySelector(".pie .chart"));

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


