chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "browse_or_reload") {
        const targetUrl = request.url;
        
        chrome.tabs.query({}, (tabs) => {
            // Check if any tab matches the target URL (ignoring protocol/trailing slashes slightly if needed)
            const matchingTab = tabs.find(tab => tab.url && tab.url.split('#')[0].replace(/\/+$/, '') === targetUrl.split('#')[0].replace(/\/+$/, ''));
            
            if (matchingTab) {
                // Reload the existing tab and bring it to focus
                chrome.tabs.reload(matchingTab.id, { bypassCache: false }, () => {
                    chrome.tabs.update(matchingTab.id, { active: true }, () => {
                        chrome.windows.update(matchingTab.windowId, { focused: true }, () => {
                            sendResponse({ status: "reloaded", tabId: matchingTab.id });
                        });
                    });
                });
            } else {
                // No matching tab, signal back so the CLI can let gh browse handle it natively
                sendResponse({ status: "not_found" });
            }
        });
        return true; // Keep message channel open for async sendResponse
    }
});