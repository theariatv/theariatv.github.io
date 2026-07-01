import os
import glob
import re

# Directory configuration
INPUT_DIR = "./channels"       # Directory containing the state .md files
OUTPUT_DIR = "./main"          # Output directory for the generated .m3u files

def ensure_directories():
    """Creates the output folder structure if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "stable"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "aria+"), exist_ok=True)

def parse_md_files():
    ensure_directories()

    # Containers for the mega playlists
    mega_aria = ["#EXTM3U\n"]
    mega_aria_plus = ["#EXTM3U\n"]

    # Find all .md files in the input directory
    md_files = glob.glob(f"{INPUT_DIR}/*.md")

    if not md_files:
        print(f"Warning: No .md files found in '{INPUT_DIR}'.")
        return

    for file_path in md_files:
        state_name = os.path.basename(file_path).replace(".md", "")
        
        # Containers for the specific state
        state_stable = []
        state_unstable = []

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            # Process only table rows, skipping headers and separators
            if line.startswith("|") and not line.startswith("| # |") and not line.startswith("|:-"):
                parts = [p.strip() for p in line.split("|")]

                # Expect at least 7 elements (due to splitting by | at the start and end of the row)
                if len(parts) >= 7:
                    channel_name = parts[2].strip()
                    
                    # Extract URL from the [>](url) format
                    link_raw = parts[3]
                    link_match = re.search(r'\((.*?)\)', link_raw)
                    link = link_match.group(1) if link_match else ""

                    # Extract logo from the <img src="url"/> format
                    logo_raw = parts[4]
                    logo_match = re.search(r'src="(.*?)"', logo_raw)
                    logo = logo_match.group(1) if logo_match else ""

                    epg_id = parts[5].strip()
                    stream_type = parts[6].lower().strip() # 'stable' or 'unstable'

                    if not link:
                        continue # Skip the line if there is no link

                    # Construct the standard M3U line
                    m3u_entry = f'#EXTINF:-1 tvg-id="{epg_id}" tvg-logo="{logo}" group-title="{state_name}",{channel_name}\n{link}\n'

                    # Sort by stream type
                    if stream_type == "stable":
                        # Stable streams go to both versions (aria and aria+)
                        state_stable.append(m3u_entry)
                        state_unstable.append(m3u_entry)
                    elif stream_type == "unstable":
                        # Unstable/Xtream streams go ONLY to aria+
                        state_unstable.append(m3u_entry)
                    else:
                        # Fallback if someone makes a typo in .md (treated as unstable)
                        state_unstable.append(m3u_entry)

        # --- WRITE PLAYLISTS FOR THE SPECIFIC STATE ---
        
        # 1. Stable state playlist (saved in /main/stable/)
        if state_stable:
            state_stable_file = os.path.join(OUTPUT_DIR, "stable", f"{state_name}.m3u")
            with open(state_stable_file, "w", encoding="utf-8") as out:
                out.write("#EXTM3U\n" + "".join(state_stable))
            # Add to the global stable mega playlist
            mega_aria.extend(state_stable)

        # 2. Extended state playlist (saved in /main/aria+/)
        if state_unstable:
            # Saved with identical state name, differentiated by the parent folder
            state_unstable_file = os.path.join(OUTPUT_DIR, "aria+", f"{state_name}.m3u")
            with open(state_unstable_file, "w", encoding="utf-8") as out:
                out.write("#EXTM3U\n" + "".join(state_unstable))
            # Add to the global extended mega playlist
            mega_aria_plus.extend(state_unstable)

        print(f"Processed state: {state_name} (Stable: {len(state_stable)}, Total: {len(state_unstable)})")

    # --- WRITE MEGA PLAYLISTS ---
    
    # Save the stable mega playlist (main/aria.m3u)
    with open(os.path.join(OUTPUT_DIR, "aria.m3u"), "w", encoding="utf-8") as out:
        out.writelines(mega_aria)

    # Save the complete mega playlist (main/aria+.m3u)
    with open(os.path.join(OUTPUT_DIR, "aria+.m3u"), "w", encoding="utf-8") as out:
        out.writelines(mega_aria_plus)

    print("\n--- DONE ---")
    print(f"Stable mega playlist: {os.path.join(OUTPUT_DIR, 'aria.m3u')}")
    print(f"Extended mega playlist: {os.path.join(OUTPUT_DIR, 'aria+.m3u')}")

if __name__ == "__main__":
    parse_md_files()
