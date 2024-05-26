import sys
import os
import datetime
import struct
import shutil
import fnmatch

def read_integers_from_adf(adf_content, offset):
    integers = []

    while True:
        integer = struct.unpack('<I', adf_content[offset:offset + 4])[0]

        if integer == 0xFFFFFFFF:
            break

        integers.append(integer)
        offset += 4

    return integers

def parse_adf(adf_file_path, jar_folder, sp_folder, output_folder, offset):
    with open(adf_file_path, 'rb') as adf_file:
        adf_content = adf_file.read()

    http_index = adf_content.lower().find(b'http://')
    if http_index == -1:
        print("No 'http://' found in the ADF file.")
        return

    adf_parts = adf_content[http_index:].split(b'\x00')

    if len(adf_parts) < 4:
        print("Invalid ADF file format")
        return

    package_url = adf_parts[0].decode('shift-jis')
    app_class = adf_parts[1].decode('shift-jis')

    adf_base_name = os.path.basename(adf_file_path).lower().replace('adf', '')
    jar_file_path = os.path.join(jar_folder, f'jar{adf_base_name}')
    sp_file_path = os.path.join(sp_folder, f'sp{adf_base_name}')

    if not os.path.exists(jar_file_path):
        print(f"No JAR file found for {adf_file_path}")
        return
    
    if not os.path.exists(sp_file_path):
        print(f"No SP file found for {adf_file_path}, continuing anyway...")

    app_size = os.path.getsize(jar_file_path)

    sp_sizes = read_integers_from_adf(adf_content, offset)

    sp_size_line = "SPsize = " + ",".join(map(str, sp_sizes))

    current_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S')

    arr = [part.decode('shift-jis') for part in adf_parts[2:]]

    arr = list(filter(None, arr))
    app_params = ' '.join(arr[:-2])

    app_name = jar_file_path.split("\\")[-1]

    adf_template = f'''PackageURL = {package_url}
AppSize = {app_size}
AppName = {app_name}
AppVer = v1.00
AppClass = {app_class}
{sp_size_line}
UseNetwork = http
UseBrowser = launch
LastModified = {current_date}
AppParam = {app_params}
'''
    # append .jam to filename
    jam_file_path = os.path.join(output_folder, f'{adf_base_name}.jam'.replace('adf', ''))
    with open(jam_file_path, 'w') as jam_file:
        jam_file.write(adf_template)

    shutil.copy(jar_file_path, os.path.join(output_folder, f'jar{adf_base_name}.jar').replace('jar', ''))
    
    if os.path.exists(sp_file_path):
        shutil.copy(sp_file_path, os.path.join(output_folder, f'sp{adf_base_name}.sp').replace('sp', ''))

    print(f"Successfully processed {adf_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Usage: python {sys.argv[0]} adf_directory jar_directory sp_directory offset")
    else:
        curr_dir = os.getcwd()
         # hex to decimal
        offset = int(sys.argv[4], 16)
        adf_directory = sys.argv[1]
        jar_directory = sys.argv[2]
        sp_directory = sys.argv[3]
        output_directory = curr_dir + "\\output\\"
        os.makedirs(output_directory, exist_ok=True)
        adf_files = [file for file in os.listdir(adf_directory) if fnmatch.fnmatch(file.lower(), 'adf*')]
        for adf_file in adf_files:
            parse_adf(os.path.join(adf_directory, adf_file), jar_directory, sp_directory, output_directory, offset)