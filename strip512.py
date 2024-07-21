import os

def strip_first_512_bytes(file_path):
    """Strip the first 512 bytes from the given file."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        if len(content) > 512:
            with open(file_path, 'wb') as f:
                f.write(content[512:])
        else:
            # If the file is less than or equal to 512 bytes, clear the file
            open(file_path, 'wb').close()
        print(f"Processed: {file_path}")
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")

def process_directory(directory):
    """Recursively process all files in the given directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            strip_first_512_bytes(file_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
    else:
        directory = sys.argv[1]
        process_directory(directory)
# thanks chatgpt!