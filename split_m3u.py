import os

def split_m3u(input_file, channels_per_file=500):
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    header = []
    entries = []
    i = 0

    # Save #EXTM3U header
    if lines and lines[0].startswith("#EXTM3U"):
        header.append(lines[0])
        i = 1

    # Each channel consists of an #EXTINF line and its URL
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            if i + 1 < len(lines):
                entries.append([lines[i], lines[i + 1]])
                i += 2
            else:
                break
        else:
            i += 1

    total_files = (len(entries) + channels_per_file - 1) // channels_per_file

    for n in range(total_files):
        output = f"playlist_part_{n + 1}.m3u"
        with open(output, "w", encoding="utf-8") as out:
            out.writelines(header)
            start = n * channels_per_file
            end = start + channels_per_file
            for entry in entries[start:end]:
                out.writelines(entry)

        print(f"Created {output}")

if __name__ == "__main__":
    split_m3u("playlist.m3u", channels_per_file=500)
