"""
This module contains utility functions for parsing JAM/ADF files.
"""

import struct
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from util.constants import EARLY_NULL_TYPE_OFFSETS, MINIMAL_VALID_KEYWORDS, SDF_PROP_NAMES
from util.db import extract_jam_objects, convert_db_datetime
from util.structure_utils import inject_jam_into_folder

def parse_props_00(adf_content, sp_start_offset, adf_start_offset, verbose=False) -> dict:
    """
    Parse null delimited ADF file and return a dictionary of its contents.
    
    :param adf_content: Null delimited ADF file content
    :param sp_start_offset: Start offset of SP sizes:
    :param adf_start_offset: Start offset of JAM section
    
    :return: A dictionary of ADF contents
    """
    adf_dict = {}
    # Determine phone type by checking the offsets
    is_early = (sp_start_offset, adf_start_offset) in EARLY_NULL_TYPE_OFFSETS
    
    adf_items = filter(None, adf_content[adf_start_offset:].split(b"\00"))
    adf_items = list(map(lambda b: b.decode("cp932", errors="replace"), adf_items))

    adf_dict["AppName"] = adf_items[0]

    if not adf_items[1].startswith("http"):
        adf_dict["AppVer"] = adf_items[1]
    else:
        adf_items.insert(1, None)

    adf_dict["PackageURL"] = adf_items[2]
    
    if adf_items[3].startswith("CLDC"):
        adf_dict["ConfigurationVer"] = adf_items[3]
    else:
        adf_items.insert(3, None)

    adf_dict["AppClass"] = adf_items[4]

    if not adf_items[5].startswith(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        adf_dict["AppParam"] = adf_items[5]
    else:
        adf_items.insert(5, None)

    adf_dict["LastModified"] = adf_items[6]
    
    try:
        # Try parsing the full string
        dt_obj = datetime.strptime(adf_dict["LastModified"], "%a, %d %b %Y %H:%M:%S")
    except ValueError as e:
        if "unconverted data remains:" in str(e):
            # Trim off the unconverted portion
            valid_len = len(adf_dict["LastModified"]) - len(str(e).split("unconverted data remains:")[1].strip())
            trimmed_str = adf_dict["LastModified"][:valid_len].strip()
            dt_obj = datetime.strptime(trimmed_str, "%a, %d %b %Y %H:%M:%S")
        else:
            raise  # Re-raise any other parsing errors

    # Format the datetime object
    formatted_date = dt_obj.strftime("%a, %d %b %Y %H:%M:%S")
    
    adf_dict["LastModified"] = formatted_date

    other_items = []
    if len(adf_items) > 6:
        for adf_item in adf_items[7:]:
            if adf_item.startswith(("DoJa-", "Star-")):
                adf_dict["ProfileVer"] = adf_item
            elif adf_item.startswith(("P", "N", "D", "F", "SO", "SH", "V", "M", "L", "CA", "E")):
                adf_dict["TargetDevice"] = adf_item
            elif adf_item.startswith("http"):
                if adf_dict["PackageURL"] == None:
                    adf_dict["PackageURL"] = adf_item
            elif adf_item.endswith(".gif"):
                adf_dict["AppIcon"] = adf_item
            else:
                other_items.append(adf_item)
            
    adf_dict["UseNetwork"] = 'http'
    adf_dict["UseBrowser"] = 'launch'
    adf_dict["LaunchApp"] = 'yes'
    adf_dict["GetUtn"] = 'terminalid,userid'
            
    # Read SP sizes    
    if is_early:
        sp_sizes = read_spsize_00_early(adf_content, sp_start_offset, verbose)
    else:
        sp_sizes = read_spsize_00(adf_content, sp_start_offset, verbose=verbose)
    
    # Format it into JAM string
    adf_dict["SPsize"] = ",".join(map(str, sp_sizes))

    if verbose:
        print("ADF contents found:")
        for k, v in adf_dict.items():
            print(f"{k}: {v}")
        print(f"Other items found: {other_items}\n")
        
    return adf_dict

def read_spsize_00(adf_content, start_offset, verbose=False) -> list:
    """
    Read SP sizes from null delimited ADF file.
    
    :param adf_content: Null delimited ADF file content
    :param start_offset: Start offset of SP sizes
    
    :return: A list of SP sizes
    """
    integers = []
    offset = start_offset
    
    # Extract 64 bytes from the starting offset
    extracted_bytes = adf_content[offset:offset + 64]
    
    # Iterate over the extracted bytes in chunks of 4 bytes
    for i in range(0, len(extracted_bytes), 4):
        integer = struct.unpack('<I', extracted_bytes[i:i + 4])[0]
        if integer != 0xFFFFFFFF:
            integers.append(integer)
    
    # Check if any SP size is 0
    if 0 in integers:
        if verbose:
            raise ValueError(f"SP sizes are invalid: {integers}")
        
    if verbose:
        print(f"Scratchpad sizes found: {integers}\n")
    
    return integers

def read_spsize_00_early(adf_content, start_offset, verbose=False):
    """
    Read SP size from null delimited early FOMA phone ADF file. It only contains one SP size and can't be split.
    
    :param adf_content: Null delimited ADF file content
    :param start_offset: Start offset of SP sizes
    
    :return: A list of SP size
    """
    integers = []
    integers.append(struct.unpack('<I', adf_content[start_offset:start_offset + 4])[0])
    
    if verbose:
        print(f"Scratchpad sizes found: {integers}\n")
    
    return integers

def parse_props_plaintext(adf_content, verbose=False) -> dict:
    """
    Parse plaintext ADF file and return a dictionary of its contents.
    
    :param adf_content: Plaintext ADF file content
    
    :return: A dictionary of plaintext ADF contents
    """
    keys = {}

    for line in adf_content.splitlines():
        if '=' in line:
            name, value = line.split('=', 1)
            if name.lower().find("spsize") != -1:
                name = "SPsize"
            name = name.strip()
            if name.rfind("\x00") != -1:
                name = name[name.rfind("\x00")+1:]
            keys[name] = value.strip()

    if verbose:
        print("JAM properties found.")
        for key, value in keys.items():
            print(f"{key}: {value}")
        print()
    return keys

def parse_valid_name(package_url, verbose=False) -> str:
    """
    Parse valid app name from PackageURL.
    
    :param package_url: PackageURL of the app
    
    :return: Valid app name
    """
    parsed_url = urlparse(package_url)
    result = ''
    result = os.path.basename(parsed_url.path).strip()
    if result == '' or not (result.lower().endswith('.jar') or result.lower().endswith('.jam')):
        result = ''
        query_params = parse_qs(parsed_url.query)
        for values in query_params.values():
            for value in values:
                if value.endswith('.jar') or value.endswith(".jam") and len(value) > 4:
                    result = value.strip()
                    break
            if result:
                break
        if not result:
            raise ValueError(f"No valid app name found in {package_url}")
    # discriminate if it's just .{format}"
    if (result[0] == '.' and len(result) == 4) or result == '':
        raise ValueError(f"No valid app name found in {package_url}")
    if verbose:
        print(f"Valid app name found: {result}\n")
    # Return a sanitized version of the app name (it could be a URL, so take the last part of the path)
    return os.path.basename(result).split('.')[0]

def fmt_plaintext_jam(adf_dict) -> str:
    """
    Format ADF dictionary into plaintext JAM format.
    
    :param adf_dict: ADF dictionary
    
    :return: Plaintext JAM format
    """
    jam = ""
    for key, value in adf_dict.items():
        jam += f"{key} = {value}\n"
    return jam

def fmt_spsize_header(sp_size_list) -> bytes:
    """
    Format SP sizes into header format.
    Format: SP sizes in 4 bytes each, if not 64 bytes overall, append 0xFFFFFFFF
    
    :param sp_size_list: List of SP sizes
    
    :return: Header format of SP sizes
    """
    sp_size_header = b""
    for sp_size in sp_size_list:
        sp_size_header += struct.pack('<I', sp_size)
    while len(sp_size_header) < 64:
        sp_size_header += b"\xFF\xFF\xFF\xFF"
    return sp_size_header

def find_plausible_keywords_for_validity(adf_file) -> bool:
    """
    Find plausible keywords for validity of the ADF file.
    
    :return: True if the ADF file has some keywords which may make it valid, False otherwise
    """
    return all(keyword in str(adf_file) for keyword in MINIMAL_VALID_KEYWORDS)

def is_valid_sh_header(header, offset):
    """
    Check if the header at the given offset is valid for SH type JAMs.

    :param header: The header bytes to validate.
    :param offset: The offset to validate against.
    :return: True if valid, False otherwise.
    """
    
    # a terrible heuristic pls don't beat me i know i just can't think of anything else
    if any(byte == 0 for byte in header[offset:offset + 32]): 
        return False
    if header[offset:offset + 32] == b'':
        return False
    return True

def filter_sdf_fields(jam_props: dict) -> tuple[dict, dict]:
    """
    Removes specific SDF fields from the jam_props dictionary and returns a tuple:
    (modified jam_props, sdf_props containing the removed fields).

    :param jam_props: The original dictionary containing various keys.
    :return: A tuple containing the modified jam_props (with SDF fields removed)
             and the sdf_props (which only has the removed fields).
    """
    sdf_props = {}
    
    # Safely remove 'PackageURL' if it exists.
    if 'PackageURL' in jam_props:
        sdf_props['PackageURL'] = jam_props['PackageURL']
    
    # Remove any additional SDF keys as defined in SDF_PROP_NAMES.
    for key in SDF_PROP_NAMES:
        if key in jam_props:
            sdf_props[key] = jam_props.pop(key)
    
    return jam_props, sdf_props

def assemble_jam(jam_obj) -> dict:
    jam_dict = dict()
    jam_dict["AppName"] = jam_obj.get("appName", None)
    jam_dict["AppVer"] = jam_obj.get("appVersion", None)
    package_url = jam_obj.get("packageUrl", None)
    jam_dict["PackageURL"] = package_url.data if package_url is not None else None
    jam_dict["AppSize"] = jam_obj.get("jar_Size", None)
    
    jam_dict["SPsize"] = []

    for i in range(15):
        sp_size = jam_obj.get(f"spSize{i}", -1)
        if sp_size == -1:
            break
        jam_dict["SPsize"].append(str(sp_size))

    if not jam_dict["SPsize"]:
        jam_dict.pop("SPsize", None)
    else:
        jam_dict["SPsize"] = ",".join(jam_dict["SPsize"])
    
    app_class = jam_obj.get("appClass", None)
    jam_dict["AppClass"] = app_class.data if app_class is not None else None

    last_modified = jam_obj.get("lastModifiedTime", None)
    jam_dict["LastModified"] = convert_db_datetime(last_modified).strftime("%a, %d %b %Y %H:%M:%S") if last_modified else None

    jam_dict["UseNetwork"] = 'http'
    jam_dict["UseBrowser"] = 'launch'
    jam_dict["LaunchApp"] = 'yes'
    jam_dict["GetUtn"] = 'userid,terminalid'  # Overwritten duplicate
    jam_dict["AppParam"] = jam_obj.get("appParam", None).data if jam_obj.get("appParam", None) else None
    jam_dict["AccessUserInfo"] = 'yes'
    jam_dict["GetSysInfo"] = 'yes'
    jam_dict["ProfileVer"] = jam_obj.get("profileVersion", None)
    jam_dict["TrustedAPID"] = jam_obj.get("trustedApid", None)
    jam_dict["UseTelephone"] = 'call'
    jam_dict["UseStorage"] = 'ext'

    jam_dict = {key: value for key, value in jam_dict.items() if value is not None}
    
    return jam_dict

def parse_jam_objects(java_folder_path: str, verbose=False):
    jam_objects = extract_jam_objects(os.path.join(java_folder_path, "FJJAM.DB"), verbose)
    for obj in jam_objects:
        jam_dict = assemble_jam(obj)
        id = obj["app_No"]
        inject_jam_into_folder(java_folder_path, id, fmt_plaintext_jam(jam_dict), verbose)
    if verbose:
        print("JAM reconstruction from database complete without errors.", end="\n\n")

def remove_garbage_so(content, interval=0x4000, header=0x20, footer=0x13, oob=0x2):
    content_ = content[header: len(content) - footer]
    content_len = len(content_)

    new_content = bytearray()
    for i in range(0, content_len, interval + oob):
        end = min(i + interval, content_len)
        new_content += content_[i : end]

    return new_content