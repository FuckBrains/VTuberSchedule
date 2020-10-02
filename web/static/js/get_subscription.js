function getSubscription(URL) {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", URL, true)
    xhr.onload = function (e) {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log("Getting Subscriptions was Completed")
                location.reload();
            } else {
                console.error(xhr.statusText);
            }
        }
    }
    xhr.onerror = function (e) {
        console.error(xhr.statusText);
    }
    xhr.send(null);
}