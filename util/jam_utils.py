"""
This module contains utility functions for parsing JAM/ADF files.
"""

import struct
import os
from urllib.parse import urlparse, parse_qs

def parse_props_00(adf_content, start_jam, verbose=False) -> dict:
    """
    Parse null delimited ADF file and return a dictionary of its contents.
    
    :param adf_content: Null delimited ADF file content
    :param start_jam: Start offset of JAM section
    
    :return: A dictionary of ADF contents
    """
    adf_dict = {}
    
    adf_items = filter(None, adf_content[start_jam:].split(b"\00"))
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

    other_items = []
    if len(adf_items) > 6:
        for adf_item in adf_items[7:]:
            if adf_item.startswith(("P", "N", "D", "F", "SO", "SH", "V", "M", "L", "CA", "E")):
                adf_dict["TargetDevice"] = adf_item
            elif adf_item.startswith(("DoJa-", "Star-")):
                adf_dict["ProfileVer"] = adf_item
            elif adf_item.startswith("http"):
                if adf_dict["PackageURL"] == None:
                    adf_dict["PackageURL"] = adf_item
            elif adf_item.endswith(".gif"):
                adf_dict["AppIcon"] = adf_item
            else:
                other_items.append(adf_item)

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

    while True:
        integer = struct.unpack('<I', adf_content[offset:offset + 4])[0]

        if integer == 0xFFFFFFFF:
            break

        integers.append(integer)
        offset += 4
    
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
    if verbose:
        print(f"Valid app name found: {result}\n")
    if result == '':
        raise ValueError(f"No valid app name found in {package_url}")
    return os.path.splitext(result)[0]