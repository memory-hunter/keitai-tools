import os

def strip_first_n_bytes(file_path, n):
    """Strip the first n bytes from the given file."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        if len(content) > n:
            with open(file_path, 'wb') as f:
                f.write(content[n:])
        else:
            # If the file is less than or equal to n bytes, clear the file
            open(file_path, 'wb').close()
        print(f"Processed: {file_path}")
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")

def process_directory(directory, n):
    """Recursively process all files in the given directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            strip_first_n_bytes(file_path, n)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory> bytes")
    else:
        directory = sys.argv[1]
        n = int(sys.argv[2])
        process_directory(directory, n)
# thanks chatgpt!