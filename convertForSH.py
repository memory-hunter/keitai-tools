import os
import sys
import re
import shutil

def process_apl_file(apl_path, output_dir):
    # Read the APL file
    with open(apl_path, 'rb') as f:
        content = f.read()
    if content[39] == 0:
        cut_index = 39
    elif content[23] == 0:
        cut_index = 23
    else:
        # Skip this file if no null byte is found at either position
        print(f"Skipping file {apl_path}: No null byte found at 0x40 or 0x24")
        return

    # Cut the content at the found position
    content = content[cut_index + 1:]

    # Find the ZIP header (50 4B 03 04)
    zip_header_index = content.find(b'\x50\x4B\x03\x04')
    
    if zip_header_index == -1:
        print(f"Failed: No ZIP header found in {apl_path}")
        return

     # Find the first byte less than 0x0A before the ZIP header
    match = re.search(rb'[\x00-\x09]', content[:zip_header_index])
    
    if match:
        last_crlf_index = match.start()
        # Process the content up to this index
        jam_content = content[:last_crlf_index]
    else:
        print(f"No byte less than 0x0A found before ZIP header in {apl_path}")
        return

    # Extract JAR content
    jar_content = content[zip_header_index:]

    # Find PackageURL to determine the output name
    package_url_match = re.search(rb'PackageURL.+?([^\r\n\/:*?"<>|]+)\.jar', jam_content)
    if package_url_match:
        # Extract the filename without extension
        base_name = os.path.splitext(package_url_match.group(1).decode('utf-8', errors='ignore'))[0]
    else:
        base_name = os.path.splitext(os.path.basename(apl_path))[0]

    if base_name.find('=') != -1:
        base_name = base_name.split('=')[1].strip()

    # Write JAM file
    jam_path = os.path.join(output_dir, f"{base_name}.jam")
    with open(jam_path, 'wb') as f:
        f.write(jam_content)

    # Write JAR file
    jar_path = os.path.join(output_dir, f"{base_name}.jar")
    with open(jar_path, 'wb') as f:
        f.write(jar_content)

    # Look for and rename SCP file
    apl_dir = os.path.dirname(apl_path)
    scp_name = os.path.splitext(os.path.basename(apl_path))[0] + '.scp'
    scp_path = os.path.join(apl_dir, scp_name)
    if os.path.exists(scp_path):
        new_sp_path = os.path.join(output_dir, f"{base_name}.sp")
        shutil.copy(scp_path, new_sp_path)
        print(f"JAM => {jam_path}")
        print(f"JAR => {jar_path}")
        print(f"SP  => {new_sp_path}")
    else:
        print(f"JAM => {jam_path}")
        print(f"JAR => {jar_path}")

def main(input_folder):
    # Create output folder
    output_dir = os.path.join(input_folder, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Process all APL files in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.apl'):
            print(f"\n[{filename}]")
            try:
                apl_path = os.path.join(input_folder, filename)
                process_apl_file(apl_path, output_dir)
            except Exception as e:
                print(f"Failed: {str(e)}")

    print(f"\nAll done! => {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} input_folder")
    else:
        main(sys.argv[1])