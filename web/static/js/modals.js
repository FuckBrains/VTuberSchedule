function moveToFreechat(ele, selector, api_url) {
    const target = $(selector);
    const obj = $(ele);
    const video_id = target.find("a").attr("href").replace("https://www.youtube.com/watch?v=", "");
    if (obj.is(":checked")) { // checked
        target.fadeOut("slow", function () {
            target.insertAfter($('#freechat_streams').find("[class*=yt-freechat]").last());
        })
        set_is_freechat(video_id, api_url, 1);

        const svg = target.find("svg");
        const content = svg.attr("data-content").replace('"checkbox"', '"checkbox" checked');
        svg.attr("data-content", content);
        $('[data-toggle="popover"]').popover("hide");
    } else { // uncheck
        target.fadeOut("slow", function () {
            target.insertAfter($('#upcoming_streams').find("[class*=yt-upcoming]").last());
        })
        set_is_freechat(video_id, api_url, 0);

        const svg = target.find("svg");
        const content = svg.attr("data-content").replace('checked', '');
        target.find("svg").attr("data-content", content);
        $('[data-toggle="popover"]').popover("hide");
    }
}

function set_is_freechat(video_id, api_url, set_to) {
    // set_to: 0 -> set to not freechat, 1 -> set to freechat
    if (set_to !== 0 && set_to !== 1) {
        console.log("Invalid param v=" + video_id + "  to: " + set_to);
        return;
    }
    const xhr = new XMLHttpRequest();
    xhr.open("GET", api_url + "?v=" + video_id + "&to=" + set_to, true);
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
            if (xhr.status !== 200) {
                console.log(xhr.statusText);
            }
        }
    }
    xhr.send(null);
}

function remove_modal(modal_selector, target_selector, api_url) {
    const modal = $(modal_selector);
    modal.modal();
    const target = $(target_selector);
    const video_id = target.find("a").attr("href").replace("https://www.youtube.com/watch?v=", "");

    // Footer削除しCardをModalに表示
    const fixed = target.children().clone(true);
    fixed.find(".card-footer").remove();
    $(modal_selector).find(".modal-body").html(
        fixed
    );

    // 削除ボタンのonclickに追加
    const remove_btn = modal.find(".remove-btn");
    const url = api_url + "?v=" + video_id;
    remove_btn.attr("onclick", `remove_stream('${url}', '${target_selector}')`);

}

function notify_modal(modal, api_url, video_id) {
    modal.modal();
    modal.find(".modal-body").html("<div class='text-center'><i class=\"fas fa-spinner fa-pulse text-center mx-auto\"></i></div>")


    $.get(api_url, {videoId: video_id}, function (res) {
        modal.find(".modal-body").html(res)
    })
}

function send_notify_settings(form, url) {
    const params = form.serialize()
    $.getJSON(url, params, (json)=>{
        if (!json.status) {
            console.error(json.errors)
        }
    })
}
