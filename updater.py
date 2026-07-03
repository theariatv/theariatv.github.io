import os
import re

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

def apply_flag(name):
    """Appends a flag emoji to the state name if it's missing."""
    clean_name = name.strip()
    for country, flag in FLAG_MAP.items():
        if country.lower() == clean_name.lower():
            if flag not in clean_name:
                return f"{clean_name} {flag}"
            break
    return clean_name

def parse_m3u(file_path):
    """
    Reads the .m3u file and extracts data including 'group-title', 'tvg-logo', and 'tvg-id'.
    """
    channels = []
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found.")
        return channels

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_channel = {}
    
    group_pattern = re.compile(r'group-title="([^"]+)"')
    logo_pattern = re.compile(r'tvg-logo="([^"]+)"')
    id_pattern = re.compile(r'tvg-id="([^"]+)"')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTINF:"):
            parts = line.split(",")
            name = parts[-1].strip() if len(parts) > 1 else "Unknown Channel"
            
            match_group = group_pattern.search(line)
            match_logo = logo_pattern.search(line)
            match_id = id_pattern.search(line)
            
            state_raw = match_group.group(1).strip() if match_group else "Uncategorized"
            state = state_raw.replace("_", " ").title()
            
            logo = match_logo.group(1).strip() if match_logo else ""
            epg_id = match_id.group(1).replace("&nbsp;", "").strip() if match_id else ""
            
            current_channel = {
                'name': name,
                'state': state,
                'logo': logo,
                'epg_id': epg_id
            }
            
        elif not line.startswith("#"):
            if 'name' in current_channel:
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = {}

    return channels

def update_markdowns():
    # 1. Přečtení playlistů
    stable_channels = parse_m3u("aria.m3u")
    plus_channels = parse_m3u("aria+.m3u")
    
    # 2. Vytvoření rychlého setu URL adres, které jsou prokazatelně stable
    stable_urls = {ch['url'] for ch in stable_channels}
    
    # 3. Sloučení (pro případ, že by náhodou nějaký kanál byl v aria, ale chyběl v aria+)
    plus_urls = {ch['url'] for ch in plus_channels}
    all_channels = list(plus_channels)
    
    for ch in stable_channels:
        if ch['url'] not in plus_urls:
            all_channels.append(ch)
            
    # 4. Seskupení podle států do LISTŮ, aby se nesmazaly duplikáty s ohledem na stejný název!
    grouped_channels = {}
    for ch in all_channels:
        state = ch['state']
        if state not in grouped_channels:
            grouped_channels[state] = []
        grouped_channels[state].append(ch)

    os.makedirs("channels", exist_ok=True)

    # 5. Generování souborů
    for state, channels in grouped_channels.items():
        safe_filename = "".join([c if c.isalnum() else "_" for c in state])
        safe_filename = re.sub(r'_+', '_', safe_filename).strip('_')
        
        target_filename = f"{safe_filename}.md"
        
        # Chytré hledání existujícího souboru (ignoruje case-sensitivity)
        if os.path.exists("channels"):
            for existing_file in os.listdir("channels"):
                if existing_file.lower() == target_filename.lower():
                    target_filename = existing_file
                    break
        
        file_path = os.path.join("channels", target_filename)

        # Zachování existujícího nadpisu (kvůli ručně dělaným vlaječkám), jinak generujeme nový
        existing_title = ""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#'):
                        existing_title = line.strip()
                        break
                        
        if not existing_title:
            existing_title = f"# {apply_flag(state)}"

        # Zápis do MD
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{existing_title}\n\n")
            f.write("| # | Channel | Link | Logo | EPG id | Type |\n")
            f.write("|:-:|:-------:|:----:|:----:|:------:|:----:|\n")

            for i, ch in enumerate(channels, start=1):
                # Detekce typu pomocí rychlého vyhledávání v Setu URL
                c_type = "stable" if ch['url'] in stable_urls else "unstable"
                
                logo_col = f'<img height="20" src="{ch["logo"]}"/>' if ch["logo"] else ch['name']
                epg_id = ch['epg_id'] if ch['epg_id'] else "&nbsp;"
                
                f.write(f"| {i} | {ch['name']} | [>]({ch['url']}) | {logo_col} | {epg_id} | {c_type} |\n")
                
        print(f"Updated file: {file_path} ({len(channels)} channels)")

if __name__ == "__main__":
    print("Starting extraction and rebuilding MD files from M3U...")
    update_markdowns()
    print("All MD files have been successfully updated in the 'channels/' directory.")
