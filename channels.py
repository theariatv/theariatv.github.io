import os
import glob
import re

# Directory configuration
INPUT_DIR = "./channels"       # Directory containing the state .md files
OUTPUT_DIR = "."               # ROOT directory for the generated .m3u files

def ensure_directories():
    """Creates the output folder structure if it doesn't exist."""
    os.makedirs(os.path.join(OUTPUT_DIR, "stable"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "aria+"), exist_ok=True)

def parse_md_files():
    ensure_directories()

    mega_aria = ["#EXTM3U\n"]
    mega_aria_plus = ["#EXTM3U\n"]

    md_files = glob.glob(f"{INPUT_DIR}/*.md")

    if not md_files:
        print(f"Warning: No .md files found in '{INPUT_DIR}'.")
        return

    for file_path in md_files:
        state_name = os.path.basename(file_path).replace(".md", "")
        
        state_stable = []
        state_unstable = []

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            if line.startswith("|") and not line.startswith("| # |") and not line.startswith("|:-"):
                parts = [p.strip() for p in line.split("|")]

                if len(parts) >= 7:
                    channel_name = parts[2].strip()
                    
                    link_raw = parts[3]
                    link_match = re.search(r'\((.*?)\)', link_raw)
                    link = link_match.group(1) if link_match else ""

                    logo_raw = parts[4]
                    logo_match = re.search(r'src="(.*?)"', logo_raw)
                    logo = logo_match.group(1) if logo_match else ""

                    epg_id = parts[5].strip()
                    stream_type = parts[6].lower().strip()

                    if not link:
                        continue

                    m3u_entry = f'#EXTINF:-1 tvg-id="{epg_id}" tvg-logo="{logo}" group-title="{state_name}",{channel_name}\n{link}\n'

                    if stream_type == "stable":
                        state_stable.append(m3u_entry)
                        state_unstable.append(m3u_entry)
                    elif stream_type == "unstable":
                        state_unstable.append(m3u_entry)
                    else:
                        state_unstable.append(m3u_entry)

        # 1. Stable state playlist (saved in root /stable/)
        if state_stable:
            state_stable_file = os.path.join(OUTPUT_DIR, "stable", f"{state_name}.m3u")
            with open(state_stable_file, "w", encoding="utf-8") as out:
                out.write("#EXTM3U\n" + "".join(state_stable))
            mega_aria.extend(state_stable)

        # 2. Extended state playlist (saved in root /aria+/)
        if state_unstable:
            state_unstable_file = os.path.join(OUTPUT_DIR, "aria+", f"{state_name}.m3u")
            with open(state_unstable_file, "w", encoding="utf-8") as out:
                out.write("#EXTM3U\n" + "".join(state_unstable))
            mega_aria_plus.extend(state_unstable)

        print(f"Processed state: {state_name} (Stable: {len(state_stable)}, Total: {len(state_unstable)})")

    # Save mega playlists directly to root
    with open(os.path.join(OUTPUT_DIR, "aria.m3u"), "w", encoding="utf-8") as out:
        out.writelines(mega_aria)

    with open(os.path.join(OUTPUT_DIR, "aria+.m3u"), "w", encoding="utf-8") as out:
        out.writelines(mega_aria_plus)

    print("\n--- DONE ---")
    print(f"Playlists generated in root directory.")

if __name__ == "__main__":
    parse_md_files()
