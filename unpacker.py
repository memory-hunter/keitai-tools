import os
import shutil
import sys

def process_subdirectories(target_directory):
    for root, dirs, files in os.walk(target_directory):
        # Process only immediate subdirectories
        if root == target_directory:
            continue

        for filename in files:
            if "adf" in filename or "jam" in filename:
                new_filename = os.path.basename(root) + ".jam"
            elif "sp" in filename:
                new_filename = os.path.basename(root) + ".sp"
            elif "jar" in filename:
                new_filename = os.path.basename(root) + ".jar"
            else:
                continue

            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_filename)

            os.rename(old_path, new_path)

        # Copy all contents to the top directory
        destination_directory = target_directory
        for item in os.listdir(root):
            item_path = os.path.join(root, item)
            destination_path = os.path.join(destination_directory, item)

            if item.endswith((".jam", ".jar", ".sp")) and os.path.isfile(item_path):
                shutil.copy2(item_path, destination_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)

    target_directory = sys.argv[1]
    process_subdirectories(target_directory)

    # Delete all directories except the root
    for root, dirs, files in os.walk(target_directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if dir_path != target_directory:
                shutil.rmtree(dir_path)
