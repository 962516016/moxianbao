hljs.initHighlightingOnLoad();
// 设置marked
marked.marked.setOptions({
    renderer: new marked.Renderer(),
    highlight: function (code) {
        return hljs.highlightAuto(code).value;
    },
    pedantic: false,
    gfm: true,
    tables: true,
    breaks: false,
    sanitize: false,
    smartLists: true,
    smartypants: false,
    xhtml: false
});

function createHeaders() {
    return {
        "password": config.password,
        "api-key": config.apiKey,
        "user-id": encodeURIComponent(config.userId)
    };
}

// 当鼠标移动到 bubble-left时显示复制按钮
$(document).on("mouseover", ".bubble-left", function () {
    let copyBtn = $("#menu");
    let copyBtnItem = $("#copy-btn");
    let offset = $(this).offset();
    // 右上角显示
    $("#resend-btn").hide();
    copyBtnItem.show();
    copyBtn.css("display", "block");
    copyBtn.css("top", offset.top);
    copyBtn.css("left", offset.left + $(this).width() - copyBtnItem.width() + 10);
    // 设置复制内容
    copyBtnItem.attr("data-clipboard-text", $(this).text());
});
// 移出bubble-left和菜单按钮时才恢复
$(document).on("mouseleave", ".bubble-left", function () {
    // 若进入了菜单按钮 不关闭
    if (event.toElement.className === "menu-btn") {
        return;
    } else {
        $("#menu").css("display", "none");
    }
});
$(document).on("mouseleave", "#menu", function () {
    $("#menu").css("display", "none");
});
$(document).on("click", "#copy-btn", function () {
    let clipboard = new ClipboardJS('#copy-btn');
    clipboard.on('success', function (e) {
        console.log(e);
        // 将显示字符更改为复制成功，一秒后改回
        $("#copy-btn").text("复制成功");
        setTimeout(function () {
            $("#copy-btn").text("复制");
        }, 2000);
    });
    clipboard.on('error', function (e) {
        console.log(e);
    });
    // 光标回归
    $("#textarea").focus();
});

// 当鼠标移动到 bubble-right时显示重发按钮
$(document).on("mouseover", ".bubble-right", function () {
    let menu = $("#menu");
    let resendBtn = $("#resend-btn");
    let offset = $(this).offset();
    // 右上角显示
    $("#copy-btn").hide();
    resendBtn.show();
    menu.css("display", "block");
    menu.css("top", offset.top);
    menu.css("left", offset.left + $(this).width() - resendBtn.width() + 10);
    // 设置复制内容
    resendBtn.attr("data-clipboard-text", $(this).text());
});
// 移出bubble-right和菜单按钮时才恢复
$(document).on("mouseleave", ".bubble-right", function () {
    // 若进入了菜单按钮 不关闭
    if (event.toElement.className === "menu-btn") {
        return;
    } else {
        $("#menu").css("display", "none");
    }
});
$(document).on("mouseleave", "#menu", function () { // 移出菜单按钮
    $("#menu").css("display", "none");
});
$(document).on("click", "#resend-btn", function () {
    // 渲染到输入框
    let text = $(this).attr("data-clipboard-text");
    $("#textarea").val(text);
    // 模拟点击事件
    $("#send-btn").click();
    // 光标回归
    $("#textarea").focus();
});
$(document).on("mousewheel DOMMouseScroll", function (e) {
    // 当鼠标滚动时，隐藏菜单
    $("#menu").css("display", "none");
});

$("#userDictFileDownload").click(function () {
    // 弹出选择框，选项有两个，覆盖或合并
    let all = confirm("是否需要下载所有用户记录？\n下载所有用户记录需要管理员密码，点击取消将下载个人记录");
    let adminPassword = undefined;
    if (all) {
        adminPassword = prompt("请输入管理员密码");
        if (adminPassword === null) {
            return;
        }
        console.log("下载所有用户记录");
    } else {
        console.log("下载个人记录");
    }
    let headers = createHeaders();
    headers["admin-password"] = adminPassword;
    headers["cache-control"] = "no-cache"
    $.ajax({
        url: "/downloadUserDictFile",
        type: "Get",
        headers: headers,
        xhrFields: {        // 必要，不能设置为blob，不然将数据乱码，因为blob是高级封装，不是原始数据
            responseType: "arraybuffer"
        },
        success: function (data, status, xhr) {
            // 判断若不是文件
            if (xhr.getResponseHeader('Content-Type') !== "application/octet-stream") {
                console.log("不是文件");
                alert(data);
                return;
            }

            let filename = "";
            let contentDisposition = xhr.getResponseHeader('Content-Disposition');
            if (contentDisposition && contentDisposition.indexOf('attachment') !== -1) {
                let filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                let matches = filenameRegex.exec(contentDisposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            let binaryData = [];
            binaryData.push(data);
            let url = window.URL.createObjectURL(new Blob(binaryData, {type: "application/octet-stream"})); // 将二进制流转换为 URL 对象
            let a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.setAttribute("download", filename);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            a = null;
        }
    });
});
$("#userDictFileUpload").change(function () {
    let file = this.files[0];
    let formData = new FormData();
    formData.append("file", file);
    let all = confirm("是否需要合并所有用户记录？\n合并所有用户记录需要管理员密码，点击取消将合并个人记录");
    let adminPassword = undefined;
    if (all) {
        adminPassword = prompt("请输入管理员密码");
        if (adminPassword === null) {
            return;
        }
        console.log("下载所有用户记录");
    } else {
        console.log("下载个人记录");
    }
    let headers = createHeaders();
    headers["admin-password"] = adminPassword;
    headers["cache-control"] = "no-cache"
    $.ajax({
        url: "/uploadUserDictFile",
        type: "POST",
        headers: headers,
        data: formData,
        processData: false,
        contentType: false,
        success: function (data) {
            alert(data);
            window.location.reload();
        }
    });
});


MathJax.Hub.Config({        // 公式配置
    showProcessingMessages: false, //关闭js加载过程信息
    messageStyle: "none", //不显示信息
    jax: ["input/TeX", "output/HTML-CSS"],
    tex2jax: {
        inlineMath: [["$", "$"], ["\\(", "\\)"]], //行内公式选择符
        displayMath: [["$$", "$$"], ["\\[", "\\]"]], //段内公式选择符
        skipTags: ["script", "noscript", "style", "textarea", "pre", "code", "a"] //避开某些标签
    },
    "HTML-CSS": {
        availableFonts: ["STIX", "TeX"], //可选字体
        showMathMenu: false //关闭右击菜单显示
    }
});


window.onload = function () {     //页面加载完成后，自动将光标定位至输入框
    document.getElementById('textarea').focus();
}

let newchat = $("#newchat");

function renderHeadInfo() {
    if (chats.length === 0) {   // 未登陆或授权
        $(".head-chat-name").text("未授权");
        $(".head-chat-info").text("当前浏览器未绑定用户或访问密码错误");
    } else {
        $(".head-chat-name").text(getSelectedChatInfo().name);
        // 判断 messages_of_chats 中是否存在selectedChatId
        if (messages_of_chats[selectedChatId] === undefined) {
            messages_of_chats[selectedChatId] = [];
        }
        $(".head-chat-info").text("共有" + messages_of_chats[selectedChatId].length + "条消息");
    }
}

function generateUUID() {
    let uuid = '', i, random
    for (i = 0; i < 32; i++) {
        random = Math.random() * 16 | 0
        if (i === 8 || i === 12 || i === 16 || i === 20) {
            uuid += '-'
        }
        uuid += (i === 12 ? 4 : (i === 16 ? (random & 3 | 8) : random)).toString(16)
    }
    return uuid
}

// getMode();
function generateChatInfo(id) {
    return {
        "id": id,
        "name": "默认对话",
        "selected": true,
        "mode": "continuous",
        "memory_summarize": "你是一个AI助手",
        "last_summarize_index": 0
    };
}

let selectedChatId = generateUUID();
let config = {
    "userId": null, "password": null, "apiKey": null, "chat_context_number": 5,
    "model_config": {"model": "gpt-3.5-turbo", "temperature": 0.9, "max_tokens": 2000}
};
let model_config = {"model": "gpt-3.5-turbo", "temperature": 0.9, "max_tokens": 2000};
let chats = [generateChatInfo(selectedChatId)];
let messages_of_chats = {[selectedChatId]: []};
if (localStorage.getItem("chats") !== null) {
    chats = JSON.parse(localStorage.getItem("chats"));
} else {
    localStorage.setItem("chats", JSON.stringify(chats));
}
if (localStorage.getItem("config") !== null) {
    config = JSON.parse(localStorage.getItem("config"));
} else {
    localStorage.setItem("config", JSON.stringify(config));
}
if (localStorage.getItem("messages_of_chats") !== null) {
    messages_of_chats = JSON.parse(localStorage.getItem("messages_of_chats"));
} else {
    localStorage.setItem("messages_of_chats", JSON.stringify(messages_of_chats));
}
selectedChatId = getSelectedId();


function loadChats() {
    console.log("start load chats");
    let headers = createHeaders();
    $.ajax({
        url: "/loadChats",
        type: "Get",
        headers: headers,
        dataType: "json",
        success: function (data) {
            console.log(data);
            if (data.code === 200) {
                chats = data.data;
                localStorage.setItem("chats", JSON.stringify(chats));
            }
            let html = "";
            for (let i = 0; i < chats.length; i++) {
                console.log(chats[i].name)
                console.log(chats[i].selected)
                if (chats[i].selected === true) {
                    selectedChatId = chats[i].id;
                    if (chats[i]["mode"] === "normal") {
                        $("#chmod-btn").text("当前为普通对话");
                    } else {
                        $("#chmod-btn").text("当前为连续对话");
                    }
                }
                html += '<div class="chat" id=' + chats[i].id + ' data-name=' + chats[i].name + ' data-selected=' + chats[i].selected + ' data-messages_total=' + chats[i].messages_total + '>' + chats[i].name + '</div>';
            }
            if (chats.length === 0) {     // 表示是未绑定用户状态
                $("#del-btn").hide();
                $("#chmod-btn").hide();
                $(".chat-list").hide();
            } else {
                $(".chat-list").append(html);
                $(".chat-list").append(newchat);
                // 将选中的selectedChat添加selected属性
                $("#" + selectedChatId).addClass("selected");
                if ($("#" + selectedChatId).data('name') !== '默认对话') {
                    $("#del-btn").html("删除对话");
                } else {
                    $("#del-btn").html("删除聊天记录");
                }
            }
            renderHeadInfo();
        }
    })
}

loadChats();

$("#newchat").click(function () {
    console.log("请输入会话名称");
    let name = prompt("请输入会话名称");
    if (name === null) {
        return;
    }
    $.ajax({
        url: "/newChat",
        type: "Get",
        headers: createHeaders(),
        dataType: "json",
        data: {
            "name": name,
            "time": get_time_str(new Date()),
            "chat_id": generateUUID()
        },
        success: function (data) {
            console.log(data);
            if (data.code === 200 || data.code === 201) {
                let html = '<div class="chat" id=' + data.data.id + ' data-name=' + data.data.name + ' data-selected=' + data.data.selected + ' data-messages_total=' + data.data.messages_total + '>' + data.data.name + '</div>';
                // newchat.remove();
                $(".chat-list").append(html);
                $(".chat-list").append(newchat);
                $("#" + selectedChatId).removeClass("selected");
                selectedChatId = data.data.id;
                $("#" + selectedChatId).addClass("selected");
                $("#del-btn").html("删除对话");
                $('.content').empty();
                let chat_info = generateChatInfo(selectedChatId);
                chat_info["name"] = name;
                chats.push(chat_info);
                if (chat_info["mode"] === "normal") {
                    $("#chmod-btn").text("当前为普通对话");
                } else {
                    $("#chmod-btn").text("当前为连续对话");
                }
                messages_of_chats[selectedChatId] = [];
                localStorage.setItem("chats", JSON.stringify(chats));
                loadHistory();
                renderHeadInfo();
            }
        }
    })
})


$(".chat-list").on('click', '.chat', function () {
    let id = this.id;
    let click = this;
    console.log(id);
    $.ajax({
        url: "/selectChat",
        type: "Get",
        headers: createHeaders(),
        dataType: "json",
        data: {     // get 方法时 data放置于路径 ?id=
            "id": id
        },
        success: function (data) {
            console.log(data);
            if (data.code === 200 || data.code === 201) {
                let chat_info = getSelectedChatInfo();
                chat_info["selected"] = false;
                $("#" + selectedChatId).removeClass("selected");
                selectedChatId = id;
                $(click).addClass("selected");
                $('.content').empty();
                if ($("#" + selectedChatId).data('name') !== '默认对话') {
                    $("#del-btn").html("删除对话");
                } else {
                    $("#del-btn").html("删除聊天记录");
                }
                chat_info = getSelectedChatInfo();
                chat_info["selected"] = true;
                if (chat_info["mode"] === "normal") {
                    $("#chmod-btn").text("当前为普通对话");
                } else {
                    $("#chmod-btn").text("当前为连续对话");
                }
                localStorage.setItem("chats", JSON.stringify(chats));
                if (messages_of_chats[selectedChatId] === undefined) {
                    messages_of_chats[selectedChatId] = [];
                }
                loadHistory();
                renderHeadInfo();
            }
        }
    })
})

function loadHistory() {
    console.log("start load history");
    if (messages_of_chats[selectedChatId] === undefined) {
        messages_of_chats[selectedChatId] = [];
    }
    $.ajax({
        url: "/loadHistory",
        type: "Get",
        headers: createHeaders(),
        dataType: "json",
        data: {
            "message_total": messages_of_chats[selectedChatId].length,
        },
        success: function (data) {
            console.log(data);
            let messages = [];
            if (data.code === 200) {   //200 时使用云端给的
                messages = data.data;
                messages_of_chats = {};
                messages_of_chats[selectedChatId] = data.data;
            } else if (data.code === 201) {                // 201时使用浏览器本地的
                if (messages_of_chats[selectedChatId].length === 0) {
                    messages_of_chats[selectedChatId] = data.data;
                }
                console.log('loadHistory' + 201);
                messages = messages_of_chats[selectedChatId];
            }
            localStorage.setItem("messages_of_chats", JSON.stringify(messages_of_chats));
            var html = "";
            for (var i = 0; i < messages.length; i++) {
                if (messages[i].role === "user") {
                    html += '<div class="item item-right"><div class="bubble bubble-right">' + messages[i].content + '</div><div class="avatar"><img src="./static/people.jpg" /></div></div>';
                } else if (messages[i].role === "assistant") {
                    html += '<div class="item item-left"><div class="avatar"><img src="./static/chatgpt.png" /></div><div class="bubble bubble-left markdown">' + marked.marked(messages[i].content) + '</div></div>';
                } else if (messages[i].role === "web-system") {
                    html += '<div class="item item-center"><span>' + messages[i].content + '</span></div>';
                }
            }
            $(".content").append(html);
            MathJax.Hub.Queue(["Typeset", MathJax.Hub, $(".content").get()]);   // 异步转换 放入队列中
            $(".content").scrollTop($(".content")[0].scrollHeight);

            let preList = $(".markdown pre");
            preList.each(function () {
                let btn = $("<span class=\"code-copy-btn\" onclick='codeCopy(this)'>复制代码</span>");
                btn.prependTo($(this));
            });
            renderHeadInfo();
        }
    });
}

loadHistory();

function codeCopy(obj) {

    let btn = $(obj);
    console.log("复制代码");
    btn.text("");
    let code = btn.parent().text();
    btn.text("复制代码");

    // 使用 Clipboard.js 复制文本
    let clipboard = new ClipboardJS(obj, {
        text: function () {
            return code;
        }
    });

    // 显示复制结果
    clipboard.on('success', function (e) {
        console.log("复制成功");
        btn.text("复制成功");
        setTimeout(function () {
            btn.text("复制代码");
        }, 1000);
    });
    clipboard.on('error', function (e) {
        console.log("复制失败");
        btn.text("复制失败");
        setTimeout(function () {
            btn.text("复制代码");
        }, 1000);
    });
}

let returnMessageAjax = null;

function get_time_str(time) {
    let year = time.getFullYear(); //得到年份
    let month = time.getMonth() + 1;//得到月份
    let date = time.getDate();//得到日期
    let hour = time.getHours();//得到小时
    if (hour < 10) hour = "0" + hour;
    let minu = time.getMinutes();//得到分钟
    if (minu < 10) minu = "0" + minu;
    return year + "年" + month + "月" + date + "日 " + hour + ":" + minu
}

let last_time = 0

function getSelectedChatInfo() {
    for (let i = 0; i < chats.length; i++) {
        if (chats[i].id === selectedChatId) {
            return chats[i];
        }
    }
    return {};
}

function getSelectedId() {
    for (let i = 0; i < chats.length; i++) {
        if (chats[i].selected === true) {
            return chats[i].id;
        }
    }
}

$("#send-btn").click(function () {
    console.log("click")
    var text = $("#textarea").val();
    console.log("text");
    console.log(text);
    if (text == "") {
        alert("请输入内容");
        return;
    }
    let html = ''
    let send_time = new Date();
    let send_time_str = get_time_str(send_time);
    let display_time = false;
    if (send_time.getTime() - last_time > 1000 * 60 * 5) {
        // 以'%Y年%#m月%#d日 %H:%M'格式显示时间
        html += '<div class="item item-center"><span>' + get_time_str(send_time) + '</span></div>';
        last_time = send_time.getTime();
        display_time = true;

    }
    html += '<div class="item item-right"><div class="bubble bubble-right markdown">' + marked.marked(text) + '</div><div class="avatar"><img src="./static/people.jpg" /></div></div>';
    $(".content").append(html);
    $("#textarea").val("");
    $(".content").scrollTop($(".content")[0].scrollHeight);
    if (text.startsWith('new:')) send_time_str = get_time_str(send_time)
    let chat_item = $('<div class="item item-left"><div class="avatar"><img src="./static/chatgpt.png" /></div><div class="bubble bubble-left markdown">正在等待回复</div></div>')
    $(".content").append(chat_item);
    $(".content").scrollTop($(".content")[0].scrollHeight);
    let get_times = 0;
    messages_of_chats[selectedChatId].push({
        "role": "user",
        "content": text,
        "send_time": send_time_str,
        "display_time": display_time
    });
    renderHeadInfo();
    let start_index = 0;
    let get_total = 0;
    for (let i = messages_of_chats[selectedChatId].length - 1; i >= 1; i--) {
        let role = messages_of_chats[selectedChatId][i].role;
        if (role === "user" || role === "assistant") {
            start_index = i;
            get_total += 1;
            if (get_total === config.chat_context_number) {
                // TODO 当用户按下切换按钮时，重新开始计数
                break;      // 获得上下文起始位置 start_index
            }
        }
    }

    let message_contexts = [];
    let chat_info = getSelectedChatInfo();
    if ("mode" in chat_info && chat_info["mode"] !== "normal") {
        if ("memory_summarize" in chat_info) {
            message_contexts = [{
                "role": "system",
                "content": "历史聊天记录前情提要总结：" + chat_info.memory_summarize
            }];
        }
        for (let i = start_index; i < messages_of_chats[selectedChatId].length; i++) {
            let role = messages_of_chats[selectedChatId][i].role;
            if (role === "user" || role === "assistant") {
                message_contexts.push(messages_of_chats[selectedChatId][i]);
            }
        }
    } else {
        message_contexts = [messages_of_chats[selectedChatId][messages_of_chats[selectedChatId].length - 1]];
    }

    let request_data = {
        "messages": message_contexts,
        "max_tokens": config.model_config.max_tokens || 2000,
        "model": config.model_config.model || "gpt-3.5-turbo",
        "temperature": config.model_config.temperature || 0.9,
        "stream": true,
        "continues_chat": true,
        "chat_id": selectedChatId,
        "save_message": true,
    };
    console.log("[Request]");
    console.log(request_data);
    let response_text = "";
    let headers = createHeaders();
    headers["Content-Type"] = "application/json";
    let index = 0;
    let codeBacktickNum = 0;
    returnMessageAjax = $.ajax({
        url: "/returnMessage",
        headers: headers,
        data: JSON.stringify(request_data),
        type: "Post",
        dataType: "text",
        xhrFields: {
            onprogress: function (e) {
                let response = e.currentTarget.response;
                if (response.slice(index).includes("`")) {
                    if (response.slice(index).includes("```")) {
                        codeBacktickNum += 1;
                        index = response.length;
                    }
                    console.log("codeBacktickNum: " + codeBacktickNum);
                } else {
                    index = response.length;
                }
                if (codeBacktickNum % 2 === 1) {
                    response += "\n```"
                }
                response_text = response;
                // console.log(response);
                if (response.includes("url_redirect")) {
                    let response_json = JSON.parse(response.trim());
                    let url_redirect = response_json["url_redirect"];
                    // 判断user_id非空
                    if (response_json.hasOwnProperty("user_id") && response_json["user_id"] !== "") {
                        config.userId = response_json["user_id"];
                        localStorage.setItem("config", JSON.stringify(config));
                    }
                    window.location.href = url_redirect;

                } else {
                    get_times += 1;
                    if (get_times === 2) {
                        $("#stop-btn").show();
                    }
                    let div = document.createElement('div');
                    div.innerHTML = marked.marked(response);
                    MathJax.Hub.Typeset(div);
                    chat_item.find(".bubble").empty();
                    chat_item.find(".bubble").append(div);
                    $(".content").scrollTop($(".content")[0].scrollHeight);
                }
            },
            onload: function (e) {
                $("#stop-btn").hide();
            }
        },
        timeout: 1000 * 60 * 2,
        complete: function (XMLHttpRequest, status, e) {
            if (status === 'timeout') {
                alert("请求超时");
            }
            $("#stop-btn").hide();
            let btn = $("<span class=\"code-copy-btn\" onclick='codeCopy(this)'>复制代码</span>");
            btn.prependTo(chat_item.find(".bubble").find("pre"));

            messages_of_chats[selectedChatId].push({
                "role": "assistant",
                "content": response_text,
                "send_time": get_time_str(new Date()),
                "display_time": false
            });
            localStorage.setItem("messages_of_chats", JSON.stringify(messages_of_chats));
            // getSummarize();
            renderHeadInfo();
        }
    });
});

function getSummarize() {
    // TODO 暂不使用
    let summarize = "";
    let chat_info = getSelectedChatInfo();
    if ("mode" in chat_info && chat_info["mode"] === "normal") {  // 如果非连续对话模式，不进行总结
        return;
    }
    if ("memory_summarize" in chat_info) {
        summarize = chat_info.memory_summarize;
    } else {
        chat_info["memory_summarize"] = "";
    }
    let message_contexts = [{"role": "system", "content": "历史聊天记录前情提要总结：" + summarize}];
    let start_index = 0;
    if ("last_summarize_index" in chat_info) {
        start_index = chat_info["last_summarize_index"] + 1;
    } else {
        chat_info["last_summarize_index"] = 0;
    }
    let end_index = messages_of_chats[selectedChatId].length - config.chat_context_number + 1;
    if (end_index - start_index > 5) {  // 过长截断
        start_index = end_index - 5;
    }
    if (start_index < 1) {
        start_index = 1;
    }
    for (let i = start_index; i < end_index; i++) {
        let role = messages_of_chats[selectedChatId][i].role;
        if (role === "user" || role === "assistant") {
            message_contexts.push(messages_of_chats[selectedChatId][i]);
        }
    }
    if (message_contexts.length === 1) {       // 如果没有需要总结的内容，直接返回
        return;
    }
    message_contexts.push({
        "role": "system",
        "content": "简要总结一下你和用户的对话，用作后续的上下文提示 prompt，控制在 50 字以内",
        "send_time": get_time_str(new Date()),
        "display_time": false
    })
    let request_data = {
        "messages": message_contexts,
        "max_tokens": 2000,
        "model": "gpt-3.5-turbo",
        "temperature": 0.9,
        "stream": true,
        "continues_chat": true,
        "chat_id": selectedChatId,
        "save_message": false,
    };
    console.log("[Memory Request]");
    console.log(request_data);
    let response_text = "";
    let headers = createHeaders();
    headers["Content-Type"] = "application/json";
    $.ajax({
        url: "/returnMessage",
        headers: headers,
        data: JSON.stringify(request_data),
        type: "Post",
        dataType: "text",
        xhrFields: {
            onprogress: function (e) {
                response_text = e.currentTarget.response;
                console.log(response_text);
            },
        },
        complete: function (XMLHttpRequest, status, e) {
            if (status === 'timeout') {
                alert("请求超时");
            }
            chat_info["memory_summarize"] = response_text;
            chat_info["last_summarize_index"] = end_index - 1;
            console.log("[Memory Response]");
            console.log(response_text);
        }
    })
    // 改为fetch获取
    // let decoder = new TextDecoder("utf-8");
    // fetch("/returnMessage", {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json",
    //     "user-id": config.userId,
    //     "password": config.password,
    //     "api-key": config.apiKey
    //   },
    //   body: JSON.stringify(request_data),
    // }).then((response) => {
    //   if (!response.ok) {
    //     throw new Error("Network response was not ok");
    //   }
    //   const reader = response.body.getReader();
    //   let responseText = '';
    //   return readStream();
//
    //   function readStream() {
    //     return reader.read().then(({ done, value }) => {
    //       if (done) {
    //         console.log(responseText);
    //         chat_info["memory_summarize"] = responseText;
    //         chat_info["last_summarize_index"] = end_index -1;
    //         return;
    //       }
    //       responseText += decoder.decode(value);
    //       console.log(responseText);
    //       return readStream();
    //     });
    //   }
//
    // }).catch((error) => {
    //   alert("Fetch API request failed with error:", error);
    // })


}

$("#stop-btn").click(function () {
    // 停止returnMessage请求
    if (returnMessageAjax != null) {

        returnMessageAjax.abort();
        returnMessageAjax = null;
    }
    $("#stop-btn").hide();
});
$("#textarea").keydown(function (e) {
    if (e.keyCode === 13 && !e.shiftKey) {
        e.preventDefault();
        $("#send-btn").click();
    }
});
$('#del-btn').click(function () {
    // 弹窗提醒是否确认删除
    if (confirm("确认删除所有聊天记录吗？非默认对话时将会直接删除该对话")) {
        $.get("/deleteHistory", function (data) {
            console.log(data);
        });
        let chat_info = getSelectedChatInfo();
        if (chat_info.name === "默认对话") {
            messages_of_chats[selectedChatId] = []
        } else {
            delete messages_of_chats[selectedChatId];
        }
        selectedChatId = chats[0].id;
        chats[0].selected = true;
        localStorage.setItem("messages_of_chats", JSON.stringify(messages_of_chats));
        localStorage.setItem("chats", JSON.stringify(chats));
        window.location.reload()
    }
});
$('#chmod-btn').click(function () {
    let chat_info = getSelectedChatInfo();
    if (!("mode" in chat_info)) {
        chat_info["mode"] = "continuous";
    }
    let display_content = "";
    if (chat_info["mode"] === "normal") {
        chat_info["mode"] = "continuous";
        display_content = "切换为连续对话";
        $("#chmod-btn").text("当前为连续对话");
    } else {
        chat_info["mode"] = "normal";
        display_content = "切换为普通对话";
        $("#chmod-btn").text("当前为普通对话");
    }

    var html = '<div class="item item-center"><span>' + display_content + '</span></div>'
    $(".content").append(html);
    $(".content").scrollTop($(".content")[0].scrollHeight);
});