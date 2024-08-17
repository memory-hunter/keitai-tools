import re
import sys
import os
import datetime
import struct
import shutil
import fnmatch
import email.utils
import traceback
import convertForEmulator_p900i
import convertPXXX

PREFERRED_ENCODINGS = ['shift-jis', 'cp932', 'utf-8']

START_SPSIZE = 0x94
START_JAM = 0x160

def main(start_spsize, start_jam):
    adf_directory = sys.argv[1]
    jar_directory = sys.argv[2]
    sp_directory = sys.argv[3]

    curr_dir = os.getcwd()
    output_folder = curr_dir + "\\output\\"
    os.makedirs(output_folder, exist_ok=True)
    adf_filenames = [file for file in os.listdir(adf_directory) if fnmatch.fnmatch(file.lower(), 'adffile*')]

    for adf_filename in adf_filenames:
        print(f"\n[{adf_filename}]")
        try:
            file_number_str = os.path.basename(adf_filename).lower().replace('adffile', '')
            adf_file_path = os.path.join(adf_directory, adf_filename)
            jar_file_path = os.path.join(jar_directory, f'jar{file_number_str}')
            sp_file_path = os.path.join(sp_directory, f'sp{file_number_str}')
            for encoding in PREFERRED_ENCODINGS:
                try:
                    with open(adf_file_path, "r", encoding=encoding) as file:
                        adf_content = file.read()
                    break
                except UnicodeDecodeError:
                    continue
            with open(sp_file_path, "rb") as file:
                sp_content = file.read()
                
            new_sp_file = convertForEmulator_p900i.add_header_to_sp(adf_content, sp_content)

            if not os.path.exists(jar_file_path):
                print(f"Failed: No JAR file found.")
                continue
            
            jar_name = convertPXXX.extract_app_name(adf_file_path)
            if jar_name == "adf":
                jar_name = f"app{file_number_str}"
            
            new_jam_file_path = os.path.join(output_folder, f'{jar_name}.jam')
            new_jar_file_path = os.path.join(output_folder, f'{jar_name}.jar')
            new_sp_file_path = os.path.join(output_folder, f'{jar_name}.sp')
                
            shutil.copy(jar_file_path, new_jar_file_path)
            shutil.copy(adf_file_path, new_jam_file_path)
            # if new sp size < 64 bytes, skip writing the file
            if len(new_sp_file) > 64:
                with open(new_sp_file_path, 'wb') as sp_file:
                    sp_file.write(new_sp_file)

            print(f"Successfully processed!")
        except Exception as e:
            traceback.print_exc()
    print(f"\nAll done! => {output_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} adf_directory jar_directory sp_directory")
    else:
        main(START_SPSIZE, START_JAM)