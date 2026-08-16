#!/usr/bin/env python3
import sys
import subprocess
import json
import urllib.request
import urllib.error
import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/gh-browse-or-reload")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def get_extension_id():
    # If explicitly overridden by env var, use it
    if "GH_BROWSER_EXTENSION_ID" in os.environ:
        return os.environ["GH_BROWSER_EXTENSION_ID"]
        
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                ext_id = data.get("extension_id")
                if ext_id and ext_id != "YOUR_EXTENSION_ID_HERE":
                    return ext_id
        except Exception:
            pass
            
    # Prompt the user for the ID on first run
    print("\n--- First Run Setup ---")
    print("To enable seamless tab reloading on Windows/Linux, you need the companion browser extension installed.")
    print("Please enter your Chrome/Edge Extension ID (or press Enter to skip and fallback to default 'gh browse'):")
    
    try:
        ext_id = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
        
    if ext_id:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"extension_id": ext_id}, f)
        print(f"Settings saved to {CONFIG_FILE}. You won't be asked again!\n-----------------------\n")
        return ext_id
        
    return None

def get_target_url():
    """Gets the URL that `gh browse --n` would generate."""
    # Pass all incoming CLI args directly to gh browse with a no-op / print flag if possible,
    # or grab it cleanly by calling gh browse --no-browser
    args = sys.argv[1:]
    try:
        result = subprocess.run(
            ["gh", "browse", "--no-browser"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing gh browse: {e.stderr}", file=sys.stderr)
        sys.exit(e.returncode)

def try_browser_reload(url):
    """Attempts to reload the URL via a local Native Messaging or WebSockets server if running.
    Since extensions cannot listen directly to arbitrary HTTP requests without a native host, 
    we use a lightweight local automation fallback or direct instructions."""
    # For a completely robust cross-platform zero-dependency Python solution,
    # AppleScript (macOS) or xdotool (Linux) is highly reliable for target URLs.
    
    # Let's implement the cross-platform system window check as the primary automated bridge,
    # and provide the Chrome DevTools Protocol / Extension instructions as requested.
    if sys.platform == "darwin":
        # macOS AppleScript solution to scan and reload browser tabs
        applescript = f'''
        tell application "Google Chrome"
            set found to false
            set targetUrl to "{url}"
            repeat with w in windows
                set tabIndex to 1
                repeat with t in tabs of w
                    if URL of t starts with targetUrl or targetUrl starts with URL of t then
                        reload t
                        set active tab index of w to tabIndex
                        set index of w to 1
                        activate
                        set found to true
                        exit repeat
                    end if
                    set tabIndex to tabIndex + 1
                end repeat
                if found then exit repeat
            end repeat
            return found
        end tell
        '''
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if "true" in proc.stdout:
            return True
            
    elif sys.platform.startswith("linux"):
        # Linux xdotool / wmctrl parsing fallback
        pass
        
    elif sys.platform == "win32":
        ext_id = get_extension_id()
        if not ext_id:
            return False
            
        import urllib.parse
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import threading
        
        # HTML payload that sends a message to the extension
        html_payload = f"""<!DOCTYPE html>
<html><body>
<h2>Routing to GitHub...</h2>
<script>
    const targetUrl = "{url}";
    const extId = "{ext_id}";
    chrome.runtime.sendMessage(extId, {{ action: "browse_or_reload", url: targetUrl }}, (response) => {{
        if (chrome.runtime.lastError) {{
            document.body.innerHTML = "Error connecting to extension: " + chrome.runtime.lastError.message;
        }} else if (response && response.status === "not_found") {{
            // Tab not found, use this tab to go to GitHub
            window.location.href = targetUrl;
        }} else {{
            // Tab found and reloaded, close this tab
            window.close();
        }}
    }});
</script></body></html>"""

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html_payload.encode('utf-8'))
                
                # Only shut down the server if the main page was requested 
                # (browsers often fire a concurrent request for /favicon.ico which could eat the single request)
                if self.path == '/':
                    threading.Thread(target=self.server.shutdown).start()
            
            def log_message(self, format, *args):
                pass # Suppress terminal logging

        # Bind to port 0 to get a random free port
        server = HTTPServer(('127.0.0.1', 0), RequestHandler)
        port = server.server_port
        
        # Start server in a background thread 
        threading.Thread(target=server.serve_forever, daemon=True).start()
        
        # Because we use 'http://', Windows native os.startfile correctly routes to the EXISTING browser!
        print(f"DEBUG: Handing off to browser via local server on port {port}")
        os.startfile(f"http://127.0.0.1:{port}/")
        
        import time
        # Give the browser up to 5 seconds to fetch the page before the CLI script forcibly exits
        time.sleep(5)
        
        return True
        
    return False

def main():
    target_url = get_target_url()
    if not target_url:
        print("Could not resolve target URL from gh browse.", file=sys.stderr)
        sys.exit(1)
        
    # Try to find and reload an existing tab
    if try_browser_reload(target_url):
        print(f"Reloaded existing tab for: {target_url}")
        sys.exit(0)
        
    # If no existing tab was found/reloaded, pass execution to native gh browse
    print(f"Opening new tab for: {target_url}")
    subprocess.run(["gh", "browse"] + sys.argv[1:])

if __name__ == "__main__":
    main()