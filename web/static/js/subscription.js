const CLIENT_ID = '730753288588-kkl69e0vqvng4324v2ab87rp2g71jeqm.apps.googleusercontent.com';
const REDIRECT_URI = 'https://youtube.dplab.biz/api/youtube_callback';
const API_URL = "https://www.googleapis.com/youtube/v3/subscriptions";

const fragmentString = location.hash.substring(1);
const params = {};
let regex = /([^&=]+)=([^&]*)/g, m;
while (m = regex.exec(fragmentString)) {
    params[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
}


function ajax(pageToken, list) {
    $.ajax({
        type: "GET",
        async: true,
        url: API_URL,
        headers: {
            Authorization: `Bearer ${params["access_token"]}`
        },
        data: {
            part: "snippet",
            mine: true,
            maxResults: 50,
            pageToken: pageToken
        },
    })
        .done((data, textStatus, jqXHR) => {
            data["items"].forEach(item => {
                list.push({
                    channel_id: item["snippet"]["channelId"],
                    title: item["snippet"]["title"],
                    desc: item["snippet"]["description"],
                    thumb: item["snippet"]["thumbnails"]["high"]
                })
            })
            if (data["nextPageToken"]) {
                ajax(data["nextPageToken"], list)
            } else {
                pageToken = null
                sendToServer(list)
                window.location = "https://youtube.dplab.biz"
            }
        })
        .fail((e) => {
            oauth2SignIn();
            pageToken = null;
        })


}

function getSubscriptions(next) {
    const params = JSON.parse(localStorage.getItem('yt-params'));
    if (params && params['access_token']) {
        let pageToken = "";
        const channel_list = [];
        ajax(pageToken, channel_list)
    } else {
        oauth2SignIn();
    }
}

/*
 * Create form to request access token from Google's OAuth 2.0 server.
 */
function oauth2SignIn() {
    // Google's OAuth 2.0 endpoint for requesting an access token
    const oauth2Endpoint = 'https://accounts.google.com/o/oauth2/v2/auth';

    // Create element to open OAuth 2.0 endpoint in new window.
    const form = document.createElement('form');
    form.setAttribute('method', 'GET'); // Send as a GET request.
    form.setAttribute('action', oauth2Endpoint);

    // Parameters to pass to OAuth 2.0 endpoint.
    const params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'https://www.googleapis.com/auth/youtube.readonly',
        'state': '1',
        'include_granted_scopes': 'true',
        'response_type': 'token'
    };

    // Add form parameters as hidden input values.
    for (let p in params) {
        const input = document.createElement('input');
        input.setAttribute('type', 'hidden');
        input.setAttribute('name', p);
        input.setAttribute('value', params[p]);
        form.appendChild(input);
    }

    // Add form to page and submit it to open the OAuth 2.0 endpoint.
    document.body.appendChild(form);
    form.submit();
}

function getCookie(key) {
    const cookies = document.cookie.split(";")
    let v = null;
    cookies.forEach(cookie => {
        const cookieKV = cookie.split("=")
        if (cookieKV[0].trim() === key) {
            v = cookieKV[1]
        }
    })
    return v
}

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method))
}

function csrfPrep() {
    $.ajaxSetup({
        beforeSend: (xhr, settings) => {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
            }
        }
    })
}

function sendToServer(data) {
    const url = "/api/register_subscription"

    csrfPrep()
    $.post(url, {channelList: JSON.stringify(data)}, (res) => {
        console.log(res)
    }, "json")
}
