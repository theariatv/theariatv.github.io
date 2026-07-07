import os
import glob
import re
import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_DIR = "./channels"

def check_url(url):
    """
    Check if the URL is accessible.
    Returns True if stream seems alive (or requires auth), False if definitely dead/timeout.
    """
    if not url.startswith('http'):
        return True # Assume working for rtmp://, udp://, etc.
        
    # Ignore SSL certificate errors for IPTV streams
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # Use a standard player User-Agent
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'VLC/3.0.16 LibVLC/3.0.16'}
        )
        
        # urlopen only reads headers, it doesn't download the body unless we call .read()
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            return True
            
    except urllib.error.HTTPError as e:
        # If server responds with 401, 403, 405 etc., the server is up and stream might be valid but protected/needs GET
        if e.code in [401, 403, 405, 400]:
            return True
        # 404 Not Found, 500 Internal Server Error, 502, 503 are considered dead
        return False
    except Exception as e:
        # Timeout, URLError (DNS/connection refused), etc.
        return False

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    to_check = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith("|") and not line_stripped.startswith("| # |") and not line_stripped.startswith("|:-"):
            parts = line.split("|")
            if len(parts) >= 7:
                link_raw = parts[3]
                link_match = re.search(r'\((.*?)\)', link_raw)
                link = link_match.group(1) if link_match else ""
                
                if link:
                    current_type = parts[6].strip()
                    to_check.append((i, link, current_type, parts))

    if not to_check:
        return

    results = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = {executor.submit(check_url, item[1]): item for item in to_check}
        for future in as_completed(future_to_url):
            item = future_to_url[future]
            try:
                is_working = future.result()
                results[item[0]] = (is_working, item)
            except Exception:
                results[item[0]] = (False, item)

    for line_idx in sorted(results.keys()):
        is_working, item = results[line_idx]
        current_type = item[2]
        parts = item[3]
        
        new_type = current_type
        if is_working and current_type == "not-working":
            new_type = "unstable"
        elif not is_working and current_type != "not-working":
            new_type = "not-working"
            
        if new_type != current_type:
            parts[6] = f" {new_type} "
            lines[line_idx] = "|".join(parts)
            modified = True

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Updated: {os.path.basename(file_path)}")
        
    return modified

def main():
    print("Starting stream checker...")
    md_files = glob.glob(f"{INPUT_DIR}/*.md")
    if not md_files:
        print(f"No .md files found in {INPUT_DIR}")
        return
        
    any_modified = False
    for file_path in md_files:
        if process_file(file_path):
            any_modified = True
            
    print("Done checking streams.")
    
    if any_modified:
        print("Changes detected. Regenerating M3U and MD files...")
        os.system("python3 channels.py")
        os.system("python3 updater.py")
        print("Pipeline complete.")

if __name__ == "__main__":
    main()
