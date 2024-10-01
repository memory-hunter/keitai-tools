"""
This module contains utility functions for parsing JAM/ADF files.
"""

import struct
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def parse_props_00(adf_content, sp_start_offset, adf_start_offset, verbose=False) -> dict:
    """
    Parse null delimited ADF file and return a dictionary of its contents.
    
    :param adf_content: Null delimited ADF file content
    :param adf_start_offset: Start offset of JAM section
    
    :return: A dictionary of ADF contents
    """
    adf_dict = {}
    
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
    
    # Parse the date string into a datetime object
    dt_obj = datetime.strptime(adf_dict["LastModified"], "%a, %d %b %Y %H:%M:%S")

    # Format the datetime object back to the desired string format with leading zeroes on single digits
    formatted_date = dt_obj.strftime("%a, %d %b %Y %H:%M:%S")
    
    adf_dict["LastModified"] = formatted_date

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
            
    adf_dict["UseNetwork"] = 'http'
    adf_dict["UseBrowser"] = 'launch'
    adf_dict["LaunchApp"] = 'yes'
    adf_dict["GetUtn"] = 'terminalid,userid'
            
    # Read SP sizes    
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
    
    # Check if any SP size is too large
    if sum(integers) > 1024000:
        if verbose:
            raise ValueError(f"SP sizes are too large: {integers}")
        
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
    if verbose:
        print(f"Valid app name found: {result}\n")
    if result == '':
        raise ValueError(f"No valid app name found in {package_url}")
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