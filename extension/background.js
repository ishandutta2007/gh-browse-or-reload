chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
    if (request.action === "browse_or_reload") {
        const targetUrl = request.url;
        
        chrome.tabs.query({}, (tabs) => {
            // Normalize URLs by removing hashes, query parameters, and trailing slashes
            const normalizeUrl = (u) => u.split('#')[0].split('?')[0].replace(/\/+$/, '');
            const normalizedTarget = normalizeUrl(targetUrl);
            
            // Check if any tab matches the target URL or is a subpage of it (e.g. /tree/main)
            const matchingTab = tabs.find(tab => tab.url && normalizeUrl(tab.url).startsWith(normalizedTarget));
            
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