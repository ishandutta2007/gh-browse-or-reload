#!/usr/bin/env python3
import sys
import subprocess
import json
import urllib.request
import urllib.error
import os

# Fetch the Extension ID from environment variables
EXTENSION_ID = os.environ.get("GH_BROWSER_EXTENSION_ID", "YOUR_EXTENSION_ID_HERE")
def get_target_url():
    """Gets the URL that `gh browse --n` would generate."""
    # Pass all incoming CLI args directly to gh browse with a no-op / print flag if possible,
    # or grab it cleanly by calling gh browse --no-browser
    args = sys.argv[1:]
    try:
        result = subprocess.run(
            ["gh", "browse", "--no-browser"] + args,
            capture_code=True,
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