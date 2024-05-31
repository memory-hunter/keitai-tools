import re
import sys
import os

PREFERRED_ENCODINGS = ['shift-jis', 'cp932', 'utf-8']

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

    for encoding in PREFERRED_ENCODINGS:
        try:
            with open(jam_filename, "r", encoding=encoding) as jam_file:
                jam_contents = jam_file.read()
                sp_size_match = re.search(r'SPsize\s*=\s*([\d,]+)', jam_contents, re.IGNORECASE)
                if sp_size_match:
                    sp_size_str = sp_size_match.group(1)
                    sp_sizes = [int(size) for size in sp_size_str.split(',')]
                    header = create_header_sp(sp_sizes)
                    print(f"SPsize: {sp_sizes}")
                    break
                else:
                    print(f"Not a valid .jam file: {jam_filename}. SPsize not found.")
                    return
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Failed to read {jam_filename} with encoding {encoding}: {e}")
            return

    else:
        print(f"Failed to read {jam_filename} with any of the preferred encodings.")
        return

    try:
        with open(sp_filename, "rb") as sp_file:
            sp_contents = sp_file.read()

        with open(sp_filename, "wb") as output_file:
            output_file.write(header + sp_contents)

        print(f"Header created and saved to {sp_filename}")
    except Exception as e:
        print(f"Failed to process {sp_filename}: {e}.")

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
