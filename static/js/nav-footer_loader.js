(async function nav_loader() {
    $(function () {
        $("#sidebar").load("/navigation.html");
    });
})();

(async function footer_loader() {
    $(function () {
        $("#footer-placeholder").load("/footer.html");
    });
})();
