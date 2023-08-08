// toggle-chats-btn按下 设置left-container可见
function toggle_settings_dialog() {
    if ($("#settings-dialog").css("display") === "none") {
        $("#api-key").val(config.apiKey);
        $("#user-id").val(config.userId);
        $("#password").val(config.password);

        let top = $(".content").offset().top;
        let left = $(".content").offset().left;
        let width = $(".content").width();
        let height = $(".content").height() + $(".input-area").height();
        $("#settings-dialog").css("top", top);
        $("#settings-dialog").css("left", left);
        $("#settings-dialog").css("width", width);
        $("#settings-dialog").css("height", height);
    } else {
        // 获取设置值
        console.log("关闭设置");
        let user_change_flag = false;
        if (config.userId !== $("#user-id").val() || config.password !== $("#password").val()) {
            user_change_flag = true;
        }
        config.apiKey = $("#api-key").val();
        config.userId = $("#user-id").val();
        config.password = $("#password").val();
        // 保存设置
        localStorage.setItem("config", JSON.stringify(config));
        if (user_change_flag) {
            // 刷新页面
            location.reload();
        }
    }
    $("#settings-dialog").toggle();
}

$(document).ready(function () {
    $("#toggle-chats-btn").click(function () {
        $(".left-container").toggle();
    });
    $("#toggle-setting-btn").click(function () {
        toggle_settings_dialog();
    });

});