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

START_SPSIZE = 0xB0
START_JAM = 0xDC

def main(start_spsize, start_jam):
    adf_directory = sys.argv[1]
    jar_directory = sys.argv[2]
    sp_directory = sys.argv[3]

    curr_dir = os.getcwd()
    output_folder = curr_dir + "\\output\\"
    os.makedirs(output_folder, exist_ok=True)
    adf_filenames = [file for file in os.listdir(adf_directory) if fnmatch.fnmatch(file.lower(), 'adf*')]

    for adf_filename in adf_filenames:
        print(f"\n[{adf_filename}]")
        try:
            file_number_str = os.path.basename(adf_filename).lower().replace('adf', '')
            adf_file_path = os.path.join(adf_directory, adf_filename)
            jar_file_path = os.path.join(jar_directory, f'jar{file_number_str}')
            inner_sp_folder_path = os.path.join(sp_directory, f'sp{file_number_str}')

            if not os.path.exists(jar_file_path):
                print(f"Failed: No JAR file found.")
                continue

            with open(adf_file_path, "rb") as file:
                adf_content = file.read()

            with open(os.path.join(adf_directory, jar_file_path), "rb") as file:
                jar_content = file.read()

            sp_content = bytes()
            for n_str in [str(n) for n in range(20)]:
                sp_path = os.path.join(inner_sp_folder_path, n_str)
                if os.path.exists(sp_path):
                    with open(sp_path, "rb") as file:
                        sp_content = sp_content + file.read()
                else:
                    break
            
            if len(sp_content) == 0:
                print(f"No SP file found for {adf_file_path}, continuing anyway...")

            new_adf_content, new_sp_content, jar_name = convertForEmulator_p900i.convert(adf_content, jar_content, sp_content, start_spsize, start_jam)

            new_jam_file_path = os.path.join(output_folder, f'{file_number_str}_{jar_name}.jam')
            new_jar_file_path = os.path.join(output_folder, f'{file_number_str}_{jar_name}.jar')
            new_sp_file_path = os.path.join(output_folder, f'{file_number_str}_{jar_name}.sp')
                
            with open(new_jam_file_path, 'wb') as adf_file:
                adf_file.write(new_adf_content)

            shutil.copy(jar_file_path, new_jar_file_path)

            with open(new_sp_file_path, 'wb') as sp_file:
                sp_file.write(new_sp_content)

            print(f"Successfully processed!")
        except Exception as e:
            traceback.print_exc()
    print(f"\nAll done! => {output_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} adf_directory jar_directory sp_directory")
    else:
        main(START_SPSIZE, START_JAM)
