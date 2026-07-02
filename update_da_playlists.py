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
    
    # Regular expressions for individual attributes
    group_pattern = re.compile(r'group-title="([^"]+)"')
    logo_pattern = re.compile(r'tvg-logo="([^"]+)"')
    id_pattern = re.compile(r'tvg-id="([^"]+)"')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTINF:"):
            # Get the channel name (everything after the last comma)
            parts = line.split(",")
            name = parts[-1].strip() if len(parts) > 1 else "Unknown Channel"
            
            # Get attributes using regex
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

def generate_markdown_by_state(stable_channels, unstable_channels, output_dir="channels"):
    """
    Groups channels by state and generates a separate MD file for each
    according to the specified structure.
    """
    all_channels = stable_channels + unstable_channels
    grouped_channels = {}

    # Group by state
    for ch in all_channels:
        state = ch['state']
        if state not in grouped_channels:
            grouped_channels[state] = []
        grouped_channels[state].append(ch)

    # Create the target directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate files
    for state, channels in grouped_channels.items():
        # Safely format the filename (e.g., "CZ - Czechia" -> "cz___czechia")
        safe_filename = "".join([c if c.isalnum() else "_" for c in state]).lower()
        safe_filename = re.sub(r'_+', '_', safe_filename).strip('_')
        
        file_path = os.path.join(output_dir, f"{safe_filename}.md")

        with open(file_path, 'w', encoding='utf-8') as f:
            # Markdown heading
            f.write(f"# {state}\n\n")
            
            # Table header exactly matching your template
            f.write("| # | Channel | Link | Logo | EPG id | Type |\n")
            f.write("|:-:|:-------:|:----:|:----:|:------:|:----:|\n")

            # Print channels with numbering
            for i, ch in enumerate(channels, start=1):
                # Handle missing logo - replace with the channel name
                logo_col = f'<img height="20" src="{ch["logo"]}"/>' if ch["logo"] else ch["name"]
                
                # Write the row
                f.write(f"| {i} | {ch['name']} | [>]({ch['url']}) | {logo_col} | {ch['epg_id']} | {ch['type']} |\n")
                
        print(f"Generated file: {file_path} ({len(channels)} channels)")

if __name__ == "__main__":
    stable_file = "aria.m3u"
    unstable_file = "aria+.m3u"

    print("Starting extraction from playlists...")
    stable_data = parse_m3u(stable_file, "stable")
    unstable_data = parse_m3u(unstable_file, "unstable")

    total_channels = len(stable_data) + len(unstable_data)
    
    if total_channels > 0:
        print(f"Total channels loaded: {total_channels}. Splitting by state...")
        generate_markdown_by_state(stable_data, unstable_data)
        print("All MD files have been successfully generated in the 'channels/' directory.")
    else:
        print("No channels found. Please check the .m3u files.")
