import os
import shutil
import sys
import re
import urllib.parse

def extract_base_name(content, filename):
    folder_name = os.path.basename(os.path.dirname(filename))
    package_url_match = re.search(rb'PackageURL.+?([^\r\n\/:*?"<>|]+)\.jar', content)
    if package_url_match:
        encoded_url = package_url_match.group(0).decode('utf-8', errors='ignore')
        decoded_url = urllib.parse.unquote(encoded_url)
        base_name_match = re.search(r'([^\r\n\/:*?"<>|]+)\.jar', decoded_url)
        if base_name_match:
            base_name = os.path.splitext(base_name_match.group(1))[0]
        else:
            base_name = folder_name
    else:
        base_name = folder_name
    
    print(base_name)
    
    if base_name.find('=') != -1:
        base_name = base_name.split('=')[1].strip()
    
    return base_name if base_name else folder_name

def concatenate_sp_files(subfolder):
    sp_files = sorted([f for f in os.listdir(subfolder) if f.lower().startswith('sp')])
    if not sp_files:
        return None
    
    concatenated_content = b''
    for sp_file in sp_files:
        sp_path = os.path.join(subfolder, sp_file)
        with open(sp_path, 'rb') as f:
            concatenated_content += f.read()
        print(f"  Concatenated: {sp_file}")
    
    return concatenated_content

def process_subdirectory(subfolder, target_directory):
    print(f"\nProcessing directory: {subfolder}")
    folder_name = os.path.basename(subfolder)

    # Process JAM
    jam_file = next((f for f in os.listdir(subfolder) if f.lower().endswith('.jam') or f.lower() == 'jam'), None)
    if jam_file:
        jam_path = os.path.join(subfolder, jam_file)
        with open(jam_path, 'rb') as f:
            content = f.read()
        base_name = extract_base_name(content, jam_path)
        if not base_name or base_name == '.':
            base_name = folder_name
        new_jam_path = os.path.join(target_directory, f"{base_name}.jam")
        shutil.copy2(jam_path, new_jam_path)
        print(f"JAM: {jam_path} => {new_jam_path}")
    else:
        print("No JAM file found. Using directory name as base name.")
        base_name = folder_name

    # Process JAR
    jar_files = [f for f in os.listdir(subfolder) if f.lower().endswith('.jar') or f.lower() in ['jar', 'fulljar', 'minijar']]
    non_minijar_files = [f for f in jar_files if 'minijar' not in f.lower()]
    
    if non_minijar_files:
        jar_file = non_minijar_files[0]
    elif jar_files:
        jar_file = jar_files[0]  # This will be the minijar if no other jars are found
    else:
        jar_file = None

    if jar_file:
        jar_path = os.path.join(subfolder, jar_file)
        new_jar_path = os.path.join(target_directory, f"{base_name}.jar")
        shutil.copy2(jar_path, new_jar_path)
        print(f"JAR: {jar_path} => {new_jar_path}")

    # Process SP
    sp_content = concatenate_sp_files(subfolder)
    if sp_content:
        new_sp_path = os.path.join(target_directory, f"{base_name}.sp")
        with open(new_sp_path, 'wb') as f:
            f.write(sp_content)
        print(f"SP: Concatenated SP files => {new_sp_path}")

    # Remove the processed subdirectory
    shutil.rmtree(subfolder)

def process_main_directory(main_directory):
    for item in os.listdir(main_directory):
        item_path = os.path.join(main_directory, item)
        if os.path.isdir(item_path):
            process_subdirectory(item_path, main_directory)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} input_folder")
        sys.exit(1)

    main_directory = sys.argv[1]
    process_main_directory(main_directory)
    print(f"\nAll done! => {main_directory}")