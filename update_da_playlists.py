import os
import re

def parse_m3u(file_path, stream_type):
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
            
            state = match_group.group(1).strip() if match_group else "Uncategorized"
            logo = match_logo.group(1).strip() if match_logo else ""
            epg_id = match_id.group(1).strip() if match_id else "&nbsp;"
            
            current_channel['name'] = name
            current_channel['state'] = state
            current_channel['logo'] = logo
            current_channel['epg_id'] = epg_id
            current_channel['type'] = stream_type
            
        elif not line.startswith("#"):
            if 'name' in current_channel:
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = {}

    return channels

def parse_existing_markdown(file_path):
    """
    Reads an existing markdown file and extracts its title and channel records.
    This prevents overwriting manual user edits.
    """
    title = ""
    existing_channels = {}
    
    if not os.path.exists(file_path):
        return title, existing_channels

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Capture the custom heading (e.g., "# Czech Republic 🇨🇿")
            if line.startswith('#') and not title:
                title = line
                
            # Parse the table rows (skip headers)
            elif line.startswith('|') and not ':-:' in line and not '| # |' in line:
                parts = [p.strip() for p in line.split('|')]
                
                # Check if it's a valid row with exactly 8 pipe separations 
                # (empty start, num, name, link, logo, epg, type, empty end)
                if len(parts) >= 8:
                    name = parts[2]
                    
                    # Safely extract the raw URL from the markdown link syntax [>](url)
                    url_match = re.search(r'\[.*?\]\((.*?)\)', parts[3])
                    url = url_match.group(1) if url_match else parts[3]
                    
                    logo_col = parts[4]
                    epg_id = parts[5]
                    c_type = parts[6]
                    
                    # Store existing records
                    existing_channels[name] = {
                        'url': url,
                        'logo_col': logo_col,
                        'epg_id': epg_id,
                        'type': c_type
                    }
                    
    return title, existing_channels

def generate_markdown_by_state(stable_channels, unstable_channels, output_dir="channels"):
    """
    Merges parsed M3U channels with existing markdown files without losing manual edits.
    """
    all_channels = stable_channels + unstable_channels
    grouped_channels = {}

    # Group by state with Title Case normalization
    for ch in all_channels:
        state = ch['state'].strip().title()
        if state not in grouped_channels:
            grouped_channels[state] = []
        grouped_channels[state].append(ch)

    os.makedirs(output_dir, exist_ok=True)

    # Merge and generate files
    for state, channels in grouped_channels.items():
        # Vytvoření bezpečného názvu bez vynucení malých písmen přes .lower()
        safe_filename_base = "".join([c if c.isalnum() else "_" for c in state])
        safe_filename_base = re.sub(r'_+', '_', safe_filename_base).strip('_')
        
        target_filename = f"{safe_filename_base}.md"
        
        # Chytré hledání: Zkontroluje složku bez ohledu na velikost písmen
        if os.path.exists(output_dir):
            for existing_file in os.listdir(output_dir):
                if existing_file.lower() == target_filename.lower():
                    target_filename = existing_file
                    break
        
        file_path = os.path.join(output_dir, target_filename)

        # Load existing data to avoid destruction of manual edits
        existing_title, existing_channels = parse_existing_markdown(file_path)
        
        # Keep custom title if it exists, otherwise generate a default one
        if not existing_title:
            existing_title = f"# {state}"

        # Merge new M3U data into existing channels
        for ch in channels:
            name = ch['name']
            new_logo_col = f'<img height="20" src="{ch["logo"]}"/>' if ch["logo"] else name
            
            if name in existing_channels:
                # Update URL and Type because stream sources change frequently
                existing_channels[name]['url'] = ch['url']
                existing_channels[name]['type'] = ch['type']
                
                # Only overwrite the Logo if the current one is just text (or missing) and M3U provided a real logo
                if ch['logo'] and (existing_channels[name]['logo_col'] == name or existing_channels[name]['logo_col'] == ""):
                    existing_channels[name]['logo_col'] = new_logo_col
                    
                # Only overwrite EPG ID if the current one is missing/placeholder
                if ch['epg_id'] != "&nbsp;" and (existing_channels[name]['epg_id'] == "&nbsp;" or existing_channels[name]['epg_id'] == ""):
                    existing_channels[name]['epg_id'] = ch['epg_id']
            else:
                # Append completely new channel from the M3U playlist
                existing_channels[name] = {
                    'url': ch['url'],
                    'logo_col': new_logo_col,
                    'epg_id': ch['epg_id'],
                    'type': ch['type']
                }

        # Write the merged content back to the Markdown file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{existing_title}\n\n")
            f.write("| # | Channel | Link | Logo | EPG id | Type |\n")
            f.write("|:-:|:-------:|:----:|:----:|:------:|:----:|\n")

            # Iterate over the merged dictionary and number them sequentially
            for i, (name, data) in enumerate(existing_channels.items(), start=1):
                f.write(f"| {i} | {name} | [>]({data['url']}) | {data['logo_col']} | {data['epg_id']} | {data['type']} |\n")
                
        print(f"Updated file: {file_path} ({len(existing_channels)} channels)")

if __name__ == "__main__":
    stable_file = "aria.m3u"
    unstable_file = "aria+.m3u"

    print("Starting extraction and merging from playlists...")
    stable_data = parse_m3u(stable_file, "stable")
    unstable_data = parse_m3u(unstable_file, "unstable")

    total_channels = len(stable_data) + len(unstable_data)
    
    if total_channels > 0:
        print(f"Total channels loaded: {total_channels}. Splitting by state and merging...")
        generate_markdown_by_state(stable_data, unstable_data)
        print("All MD files have been successfully updated in the 'channels/' directory.")
    else:
        print("No channels found. Please check the .m3u files.")
