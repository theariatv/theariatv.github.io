import os
import glob
import re

# Directory configuration
INPUT_DIR = "./channels"       # Directory containing the state .md files
OUTPUT_DIR = "."               # ROOT directory for the generated .m3u files

# Dictionary for automatic flag assignment
FLAG_MAP = {
    "United States": "🇺🇸", "Guyana": "🇬🇾", "Cyprus": "🇨🇾", "Türkyie": "🇹🇷", "Turkey": "🇹🇷",
    "Slovakia": "🇸🇰", "Japan": "🇯🇵", "Iceland": "🇮🇸", "Spain": "🇪🇸", "Columbia": "🇨🇴", "Colombia": "🇨🇴",
    "Argentina": "🇦🇷", "Australia": "🇦🇺", "Finland": "🇫🇮", "North Macedonia": "🇲🇰", "Germany": "🇩🇪",
    "Portugal": "🇵🇹", "Singapore": "🇸🇬", "Brazil": "🇧🇷", "Lithuania": "🇱🇹", "Philippines": "🇵🇭",
    "Poland": "🇵🇱", "Belarus": "🇧🇾", "Bulgaria": "🇧🇬", "Vietnam": "🇻🇳", "San Marino": "🇸🇲",
    "Norway": "🇳🇴", "Montenegro": "🇲🇪", "United Arab Emirates": "🇦🇪", "Israel": "🇮🇱", "Iran": "🇮🇷",
    "Mexico": "🇲🇽", "Albania": "🇦🇱", "Greece": "🇬🇷", "Slovenia": "🇸🇮", "North Korea": "🇰🇵",
    "Switzerland": "🇨🇭", "Bosnia and Herzegovina": "🇧🇦", "Serbia": "🇷🇸", "Vatican City": "🇻🇦",
    "Croatia": "🇭🇷", "Denmark": "🇩🇰", "Monaco": "🇲🇨", "Andorra": "🇦🇩", "Ukraine": "🇺🇦",
    "Austria": "🇦🇹", "New Zealand": "🇳🇿", "Moldova": "🇲🇩", "Russia": "🇷🇺", "Netherlands": "🇳🇱",
    "Estonia": "🇪🇪", "Italy": "🇮🇹", "Romania": "🇷🇴", "Chile": "🇨🇱", "France": "🇫🇷", "South Africa": "🇿🇦",
    "Georgia": "🇬🇪", "Belgium": "🇧🇪", "Costa Rica": "🇨🇷", "India": "🇮🇳", "United Kingdom": "🇬🇧",
    "Czech Republic": "🇨🇿", "Czechia": "🇨🇿", "Hungary": "🇭🇺", "China": "🇨🇳", "South Korea": "🇰🇷",
    "Sweden": "🇸🇪", "Faroe Islands": "🇫🇴", "Ireland": "🇮🇪", "Armenia": "🇦🇲", "Azerbaijan": "🇦🇿",
    "Luxembourg": "🇱🇺", "Jamaica": "🇯🇲", "Thailand": "🇹🇭", "Canada": "🇨🇦", "Latin America": "🌎",
    "International": "🌍", "Caribbean": "🏝️", "Africa": "🌍"
}

def ensure_directories():
    """Creates the output folder structure if it doesn't exist."""
    os.makedirs(os.path.join(OUTPUT_DIR, "stable"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "aria+"), exist_ok=True)

def apply_flag(name):
    """Appends a flag emoji to the state name if it's missing."""
    clean_name = name.strip()
    # Check if the name already ends with an emoji/flag or if it's in our map
    for country, flag in FLAG_MAP.items():
        if country.lower() == clean_name.lower():
            if flag not in clean_name:
                return f"{clean_name} {flag}"
            break
    return clean_name

def parse_md_files():
    ensure_directories()

    mega_aria = ["#EXTM3U\n"]
    mega_aria_plus = ["#EXTM3U\n"]

    # Dictionaries to temporarily group entries by state name for global alphabetical sorting
    mega_stable_dict = {}
    mega_unstable_dict = {}

    md_files = glob.glob(f"{INPUT_DIR}/*.md")

    if not md_files:
        print(f"Warning: No .md files found in '{INPUT_DIR}'.")
        return

    for file_path in md_files:
        raw_filename = os.path.basename(file_path).replace(".md", "")
        
        # Fallback state name in case the file has no heading
        state_name = raw_filename.replace("_", " ").title()
        
        state_stable = []
        state_unstable = []

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            # Extract custom title from markdown header
            if line.startswith("#") and not line.startswith("#EXT") and not "Kanály:" in line:
                clean_title = re.sub(r'^#+\s*', '', line).strip()
                if clean_title:
                    state_name = clean_title

            # Apply flag to the state name
            state_name = apply_flag(state_name)

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

                    # Fix for the &nbsp; issue - completely strip it out
                    epg_id = parts[5].replace("&nbsp;", "").strip()
                    stream_type = parts[6].lower().strip()

                    if not link:
                        continue

                    # Generate the M3U line with the properly formatted group-title (with flag)
                    m3u_entry = f'#EXTINF:-1 tvg-id="{epg_id}" tvg-logo="{logo}" group-title="{state_name}" tvg-status="{stream_type}",{channel_name}\n{link}\n'

                    if stream_type == "stable":
                        state_stable.append(m3u_entry)
                        state_unstable.append(m3u_entry)
                    elif stream_type == "unstable":
                        state_unstable.append(m3u_entry)
                    elif stream_type == "not-working":
                        state_unstable.append(m3u_entry)
                    else:
                        state_unstable.append(m3u_entry)

        # 1. Stable state playlist (saved in root /stable/)
        if state_stable:
            state_stable_file = os.path.join(OUTPUT_DIR, "stable", f"{raw_filename}.m3u")
            with open(state_stable_file, "w", encoding="utf-8") as out:
                out.write("#EXTM3U\n" + "".join(state_stable))
            
            # Store entries in the dictionary under the specific group/state name
            if state_name not in mega_stable_dict:
                mega_stable_dict[state_name] = []
            mega_stable_dict[state_name].extend(state_stable)

        # 2. Extended state playlist (saved in root /aria+/)
        if state_unstable:
            state_unstable_file = os.path.join(OUTPUT_DIR, "aria+", f"{raw_filename}.m3u")
            with open(state_unstable_file, "w", encoding="utf-8") as out:
                out.write("#EXTM3U\n" + "".join(state_unstable))
            
            # Store entries in the dictionary under the specific group/state name
            if state_name not in mega_unstable_dict:
                mega_unstable_dict[state_name] = []
            mega_unstable_dict[state_name].extend(state_unstable)

        print(f"Processed state: {state_name} (Stable: {len(state_stable)}, Total: {len(state_unstable)})")

    # Compile the final lists alphabetically sorted by state_name (which includes the flag)
    for sorted_state in sorted(mega_stable_dict.keys()):
        mega_aria.extend(mega_stable_dict[sorted_state])

    for sorted_state in sorted(mega_unstable_dict.keys()):
        mega_aria_plus.extend(mega_unstable_dict[sorted_state])

    # Save mega playlists directly to root
    with open(os.path.join(OUTPUT_DIR, "aria.m3u"), "w", encoding="utf-8") as out:
        out.writelines(mega_aria)

    with open(os.path.join(OUTPUT_DIR, "aria+.m3u"), "w", encoding="utf-8") as out:
        out.writelines(mega_aria_plus)

    print("\n--- DONE ---")
    print("Playlists generated in root directory (strictly sorted alphabetically by group-title).")

if __name__ == "__main__":
    parse_md_files()
