const params = new URLSearchParams(window.location.search);
const targetUrl = params.get('url');

if (targetUrl) {
    document.body.innerHTML = "Triggering reload for: " + targetUrl + "...";
    chrome.runtime.sendMessage({ action: "browse_or_reload", url: targetUrl }, (response) => {
        if (chrome.runtime.lastError) {
            document.body.innerHTML = "Error: " + chrome.runtime.lastError.message;
            console.error(chrome.runtime.lastError);
            return;
        }
        if (response && response.status === "not_found") {
            document.body.innerHTML = "Tab not found. Navigating to new tab...";
            window.location.href = targetUrl;
        } else {
            document.body.innerHTML = "Tab reloaded! Closing...";
            window.close();
        }
    });
} else {
    document.body.innerHTML = "No target URL provided.";
}
