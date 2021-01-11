

function remove_stream(url, target_selector) {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onload = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const target = $(target_selector)
                target.fadeOut("slow", function () {
                    target.remove();
                })
            } else {
                console.log(xhr.statusText);
            }
        }
    }

    xhr.send(null);

}

function initPopover() {
    $("[data-toggle='popover']").popover(
        {
            trigger: "focus",
            html: true,
            offset: "100",
            sanitize: false
        });
}

function refresh(url) {
    $("[data-toggle='popover']").popover("dispose");
    $(".modal").modal("hide");
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onload = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const content = $(".content");
                content.html(xhr.responseText)
                initPopover();
            } else {
                console.log(xhr.statusText);
            }
        } else {
            return 0;
        }
    }

    xhr.send(null);
}
