"""
This module contains utility functions for parsing JAM/ADF files.
"""

import struct

def parse_adf(adf_content, start_jam):
    """
    Parse ADF file and return a dictionary of its contents.
    
    :param adf_content: ADF file content
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
                jam_download_url = adf_item
            elif adf_item.endswith(".gif"):
                adf_dict["AppIcon"] = adf_item
            else:
                other_items.append(adf_item)

    print(f"{adf_dict=}, {jam_download_url=}, {other_items=}")
    return adf_dict

def read_spsizes_from_adf(adf_content, start_offset):
    """
    Read SP sizes from ADF file.
    
    :param adf_content: ADF file content
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

    return integers