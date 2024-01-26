import re
import sys
import os
import codecs

def create_header_sp(sp_sizes):
    header = bytearray()
    for size in sp_sizes:
        header += size.to_bytes(4, byteorder='little')
    while len(header) < 64:
        header += bytes([255])
    return header

def process_jam(jam_filename):
    sp_filename = os.path.splitext(jam_filename)[0] + ".sp"

    if not os.path.isfile(jam_filename):
        print(f"{jam_filename} not found.")
        return

    with codecs.open(jam_filename, "r", encoding="shift-jis") as jam_file:
        try:
            jam_contents = jam_file.read()

            sp_size_match = re.search(r'SPsize\s*=\s*([\d,]+)', jam_contents)
            if sp_size_match:
                sp_size_str = sp_size_match.group(1)
                sp_sizes = [int(size) for size in sp_size_str.split(',')]
                header = create_header_sp(sp_sizes)
                print(f"SPsize: {sp_sizes}")
            else:
                print(f"Not a valid .jam file: {jam_filename}. SPsize not found.")
                return
        except Exception:
            print(f"Failed to read {jam_filename}. Skipping.")
            return

    with open(sp_filename, "rb") as sp_file:
        sp_contents = sp_file.read()

    with open(sp_filename, "wb") as output_file:
        output_file.write(header + sp_contents)

    print(f"Header created and saved to {sp_filename}")

def process_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"{folder_path} is not a valid folder.")
        return

    jam_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jam")]

    if not jam_files:
        print(f"No .jam files found in {folder_path}.")
        return

    for jam_file in jam_files:
        jam_filepath = os.path.join(folder_path, jam_file)
        process_jam(jam_filepath)

def main():
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " folder_path")
        return

    folder_path = sys.argv[1]
    process_folder(folder_path)

if __name__ == "__main__":
    main()
