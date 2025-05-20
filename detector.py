import os
import sys

def find_packageurl_in_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            index = data.find(b'PackageURL')
            if index != -1:
                print(f"Found in {file_path}: 0x{index:X}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

def search_dat_files(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.dat'):
                file_path = os.path.join(dirpath, filename)
                find_packageurl_in_file(file_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detector.py <root_directory>")
        sys.exit(1)
    root_directory = sys.argv[1]

    search_dat_files(root_directory)