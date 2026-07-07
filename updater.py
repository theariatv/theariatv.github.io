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
    "International": "🌍", "Caribbean": "🏝️", "Africa": "🌍", "Aria Web Channels": "📺"
}

def apply_flag(name):
    """Přidá správnou vlajku k čistému názvu státu."""
    clean_name = name.strip()
    for country, flag in FLAG_MAP.items():
        if country.lower() == clean_name.lower():
            if flag not in clean_name:
                return f"{clean_name} {flag}"
            break
    return clean_name

def clean_state_name(raw_name):
    """
    Agresivně vyčistí název státu ze zdrojového M3U.
    Smaže emoji a speciální znaky, aby se předešlo duplikátům (např. 'Slovakia' vs 'Slovakia 🇸🇰').
    """
    name = raw_name.replace("_", " ")
    # Ponechá pouze písmena, číslice, mezery, pomlčky a apostrofy (emoji budou smazána)
    name = re.sub(r'[^\w\s\-\'&]', '', name)
    # Odstraní přebytečné mezery, které mohly vzniknout po smazání emoji
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title()

def parse_m3u(file_path):
    """
    Načte .m3u soubor a extrahuje data včetně EPG, Loga a Skupiny.
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
    status_pattern = re.compile(r'tvg-status="([^"]+)"')

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
            match_status = status_pattern.search(line)
            
            # Vyčištění názvu skupiny od případných emoji z M3U
            state_raw = match_group.group(1).strip() if match_group else "Uncategorized"
            state = clean_state_name(state_raw)
            
            logo = match_logo.group(1).strip() if match_logo else ""
            epg_id = match_id.group(1).replace("&nbsp;", "").strip() if match_id else ""
            status = match_status.group(1).strip() if match_status else ""
            
            current_channel = {
                'name': name,
                'state': state,
                'logo': logo,
                'epg_id': epg_id,
                'status': status
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
            
    # 4. Seskupení podle čistých názvů států (zabrání duplikátům!)
    grouped_channels = {}
    for ch in all_channels:
        state = ch['state']
        if state not in grouped_channels:
            grouped_channels[state] = []
        grouped_channels[state].append(ch)

    os.makedirs("channels", exist_ok=True)

    # 5. Generování MD souborů
    for state, channels in grouped_channels.items():
        safe_filename_base = "".join([c if c.isalnum() else "_" for c in state])
        safe_filename_base = re.sub(r'_+', '_', safe_filename_base).strip('_')
        
        target_filename = f"{safe_filename_base}.md"
        
        # Chytré hledání existujícího souboru (ignoruje case-sensitivity)
        if os.path.exists("channels"):
            for existing_file in os.listdir("channels"):
                if existing_file.lower() == target_filename.lower():
                    target_filename = existing_file
                    break
        
        file_path = os.path.join("channels", target_filename)

        # Vždy vynutíme konzistentní nadpis se správnou vlajkou
        final_title = f"# {apply_flag(state)}"

        # Zápis do MD
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{final_title}\n\n")
            f.write("| # | Channel | Link | Logo | EPG id | Type |\n")
            f.write("|:-:|:-------:|:----:|:----:|:------:|:----:|\n")

            for i, ch in enumerate(channels, start=1):
                # Detekce typu pomocí rychlého vyhledávání v Setu URL
                if ch.get('status') == 'not-working':
                    c_type = "not-working"
                elif ch['url'] in stable_urls:
                    c_type = "stable"
                else:
                    c_type = "unstable"
                
                logo_col = f'<img height="20" src="{ch["logo"]}"/>' if ch["logo"] else ch['name']
                epg_id = ch['epg_id'] if ch['epg_id'] else "&nbsp;"
                
                f.write(f"| {i} | {ch['name']} | [>]({ch['url']}) | {logo_col} | {epg_id} | {c_type} |\n")
                
        print(f"Updated file: {file_path} ({len(channels)} channels)")

if __name__ == "__main__":
    print("Starting extraction and rebuilding MD files from M3U...")
    update_markdowns()
    print("All MD files have been successfully updated in the 'channels/' directory.")
