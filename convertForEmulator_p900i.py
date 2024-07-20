import re
import sys
import os
import datetime
import struct
import shutil
import fnmatch
import email.utils
import traceback

START_SPSIZE = 0x8C
START_JAM = 0xD4

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
            sp_file_path = os.path.join(sp_directory, f'sp{file_number_str}')

            if not os.path.exists(jar_file_path):
                print(f"Failed: No JAR file found.")
                continue

            with open(adf_file_path, "rb") as file:
                adf_content = file.read()

            with open(os.path.join(adf_directory, jar_file_path), "rb") as file:
                jar_content = file.read()

            if os.path.exists(sp_file_path):
                with open(sp_file_path, "rb") as file:
                    sp_content = file.read()
            else:
                sp_content = bytes()
                print(f"No SP file found for {adf_file_path}, continuing anyway...")

            new_adf_content, new_sp_content, jar_name = convert(adf_content, jar_content, sp_content, start_spsize, start_jam)

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

def convert(adf_content, jar_content, sp_content, start_spsize, start_jam):
    try:
        sp_sizes = read_spsizes_from_adf(adf_content, start_spsize)
    except struct.error:
        print("Failed: bronken ADF file.")
        return

    adf_dict = perse_adf(adf_content, start_jam)

    # Re-format LastModified
    adf_dict["LastModified"] = email.utils.parsedate_to_datetime(adf_dict["LastModified"])
    adf_dict["LastModified"] = format_last_modified(adf_dict["LastModified"])

    # create a jam
    jam_str = ""
    for key, value in adf_dict.items():
        jam_str += f"{key} = {value}\n"

    jam_str += f"AppSize = {len(jar_content)}\n"
    if len(sp_sizes): jam_str += f"SPsize = {','.join(map(str, sp_sizes))}\n"
    jam_str += f"UseNetwork = http\n"
    jam_str += f"UseBrowser = launch\n"

    new_adf_content = jam_str.encode("cp932", errors="replace")

    new_sp_content = add_header_to_sp(jam_str, sp_content)

    if m := re.match(r'(?:.+?([^\r\n\/:*?"><|=]+)\.jar)+', adf_dict["PackageURL"]):
        jar_name = m[1]
    else:
        jar_name = ""

    return (new_adf_content, new_sp_content, jar_name)

def read_spsizes_from_adf(adf_content, start_offset):
    integers = []
    offset = start_offset

    while True:
        integer = struct.unpack('<I', adf_content[offset:offset + 4])[0]

        if integer == 0xFFFFFFFF:
            break

        integers.append(integer)
        offset += 4

    return integers

def perse_adf(adf_content, start_jam):
    adf_dict = {}

    # Parse adf. order: AppName [AppVer] PackageURL [ConfigurationVer] AppClass [AppParam] LastModified [TargetDevice] [ProfileVer] jar_download_url
    adf_items = filter(None, adf_content[start_jam:].split(b"\00"))
    adf_items = list(map(lambda b: b.decode("cp932", errors="replace"), adf_items))

    adf_dict["AppName"] = adf_items[0]

    if not adf_items[1].startswith("http"):
        adf_dict["AppVer"] = adf_items[1]
    else:
        adf_items.insert(1, None)

    adf_dict["PackageURL"] = adf_items[2]
    
    if adf_items[3] in ["CLDC-1.1", "CLDC-1.0"]:
        adf_dict["ConfigurationVer"] = adf_items[3]
    else:
        adf_items.insert(3, None)

    adf_dict["AppClass"] = adf_items[4]

    if not adf_items[5].startswith(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        adf_dict["AppParam"] = adf_items[5]
    else:
        adf_items.insert(5, None)

    adf_dict["LastModified"] = adf_items[6]

    other_items = []
    if len(adf_items) > 6:
        for adf_item in adf_items[7:]:
            if adf_item.startswith(("P9", "N9", "N7")):
                adf_dict["TargetDevice"] = adf_item
            elif adf_item.startswith(("DoJa-1.0", "DoJa-2.0", "DoJa-2.1", "DoJa-2.2", "DoJa-3.0", "DoJa-3.5", "DoJa-4.0", "DoJa-4.1", "DoJa-5.0", "DoJa-5.1")):
                adf_dict["ProfileVer"] = adf_item
            elif adf_item.startswith("http"):
                jar_download_url = adf_item
            elif adf_item.endswith(".gif"):
                adf_dict["AppIcon"] = adf_item
            else:
                other_items.append(adf_item)

    print(f"{adf_dict=}, {jar_download_url=}, {other_items=}")
    return adf_dict

def add_header_to_sp(jam_str, sp_contents):
    def create_header_sp(sp_sizes):
        header = bytearray()
        for size in sp_sizes:
            header += size.to_bytes(4, byteorder='little')
        while len(header) < 64:
            header += bytes([255])
        return header

    sp_size_match = re.search(r'SPsize\s*=\s*([\d,]+)', jam_str)
    if sp_size_match:
        sp_size_str = sp_size_match.group(1)
        sp_sizes = [int(size) for size in sp_size_str.split(',')]
        header = create_header_sp(sp_sizes)
    else:
        header = create_header_sp([0])

    return header + sp_contents

def format_last_modified(last_modified_dt):
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    weekday_name = weekdays[last_modified_dt.weekday()]
    month_name = months[last_modified_dt.month - 1]

    last_modified_str = last_modified_dt.strftime(f"{weekday_name}, %d {month_name} %Y %H:%M:%S")
    return last_modified_str

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} adf_directory jar_directory sp_directory")
    else:
        main(START_SPSIZE, START_JAM)