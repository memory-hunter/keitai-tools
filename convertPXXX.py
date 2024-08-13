import os
import shutil
import sys
import re

def extract_app_name(adf_path):
    with open(adf_path, 'rb') as adf:
        content = adf.read()
    # Find PackageURL to determine the output name
    package_url_match = re.search(rb'PackageURL.+?([^\r\n\/:*?"<>|]+)\.jar', content)
    if package_url_match:
        # Extract the filename without extension
        base_name = os.path.splitext(package_url_match.group(1).decode('utf-8', errors='ignore'))[0]
    else:
        base_name = os.path.splitext(os.path.basename(adf_path))[0]

    if base_name.find('=') != -1:
        base_name = base_name.split('=')[1].strip()
    
    return base_name

def process_subdirectory(subfolder, target_directory):
    print(f"\nProcessing directory: {subfolder}")
    folder_name = os.path.basename(subfolder)
    base_name = folder_name
    app_name = None

    # Process ADF
    adf_file = next((f for f in os.listdir(subfolder) if f.lower() == 'adf'), None)
    if adf_file:
        adf_path = os.path.join(subfolder, adf_file)
        app_name = extract_app_name(adf_path)
        if app_name:
            new_adf_path = os.path.join(target_directory, f"{app_name}.jam")
        else:
            new_adf_path = os.path.join(target_directory, f"{base_name}.jam")
    
        with open(adf_path, 'rb') as adf:
            adf.seek(0x5EBC)
            content = adf.read()
    
        with open(new_adf_path, 'wb') as new_adf:
            new_adf.write(content)
    
        print(f"ADF: {adf_path} => {new_adf_path}")

    # Process JAR
    jar_file = next((f for f in os.listdir(subfolder) if f.lower() in ['jar', 'mini']), None)
    if jar_file:
        jar_path = os.path.join(subfolder, jar_file)
        if app_name:
            new_jar_name = f"{app_name}.jar"
        else:
            new_jar_name = f"{base_name}.jar"
        new_jar_path = os.path.join(target_directory, new_jar_name)
        shutil.copy2(jar_path, new_jar_path)
        print(f"JAR: {jar_path} => {new_jar_path}")

    # Process SP (no concatenation, just copy if exists)
    sp_file = next((f for f in os.listdir(subfolder) if f.lower() == 'sp'), None)
    if sp_file:
        sp_path = os.path.join(subfolder, sp_file)
        if app_name:
            new_sp_name = f"{app_name}.sp"
        else:
            new_sp_name = f"{base_name}.sp"
        new_sp_path = os.path.join(target_directory, new_sp_name)
        shutil.copy2(sp_path, new_sp_path)
        print(f"SP: {sp_path} => {new_sp_path}")

    # Remove the processed subdirectory
    shutil.rmtree(subfolder)

def process_main_directory(main_directory):
    for item in os.listdir(main_directory):
        item_path = os.path.join(main_directory, item)
        if os.path.isdir(item_path) and item.isdigit():
            process_subdirectory(item_path, main_directory)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} input_folder")
        sys.exit(1)

    main_directory = sys.argv[1]
    process_main_directory(main_directory)
    print(f"\nAll done! => {main_directory}")