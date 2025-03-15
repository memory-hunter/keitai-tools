import os
from util.jam_utils import parse_props_plaintext
from util.constants import ENCODINGS
from urllib.parse import urlparse, parse_qs

def post_process_SIMPLE_games(output_folder_path, verbose=False):
    """
    This function is a postprocessing script for the SIMPLE games. Sometimes, their links have 'dljar.jar' in them
    which is valid, but then one of the link arguments have the real name. This script will fix that by renaming
    the 'dljar.jar' to the real name.
    """
    if verbose:
        print("Postprocessing SIMPLE games name pattern.")
    for root, _, files in os.walk(output_folder_path):
        for file in files:
            if 'dljar' in file and file.endswith('.jam'):
                for encoding in ENCODINGS:
                    try:
                        file_content = open(os.path.join(root, file), 'r', encoding=encoding).read()
                        jam_props = parse_props_plaintext(file_content, verbose)
                        package_url = jam_props.get('PackageURL', None) if jam_props else None
                        if package_url:
                            url_parsed = parse_qs(urlparse(package_url).query)
                            # Get 'f' argument from the URL
                            real_name = url_parsed.get('f', None)[0] if url_parsed else None
                            if real_name:
                                os.rename(os.path.join(root, file), os.path.join(root, real_name + '.jam'))
                                # Find the corresponding .jar and .sp files with the same name as the current .jam
                                # Rename them to the real name and append the extension
                                for ext in ['.jar', '.sp', '.sdf']:
                                    os.rename(os.path.join(root, file.replace('.jam', ext)), os.path.join(root, real_name + ext))
                            if verbose:
                                print(f"Renamed: {file} -> {real_name}")
                                break
                    except UnicodeDecodeError:
                        if verbose:
                            print(f"Could not decode {file} with encoding {encoding}, trying next encoding.")
                        continue
                else:
                    if verbose:
                        print(f"Could not decode {file} with any encoding. Skipping.")
                    continue
    if verbose:
        print("Postprocessing SIMPLE games done.")

def post_process_konami_name_in_qs(output_folder_path, verbose=False):
    if verbose:
        print("Postprocessing Konami games name pattern.")
    for root, _, files in os.walk(output_folder_path):
        for file in files:
            if file.endswith('.jam'):
                for encoding in ENCODINGS:
                    try:
                        file_content = open(os.path.join(root, file), 'r', encoding=encoding).read()
                        jam_props = parse_props_plaintext(file_content, False)
                        package_url = jam_props.get('PackageURL', None) if jam_props else None
                        if package_url:
                            url_parsed = parse_qs(urlparse(package_url).query)
                            # Get 'appliname' argument from the URL
                            mid = url_parsed.get('appliname', None)
                            if mid is not None:    
                                real_name = url_parsed.get('appliname', None)[0] if url_parsed else None
                                if real_name:
                                    real_name = real_name.split('.')[0]
                                    os.rename(os.path.join(root, file), os.path.join(root, real_name + '.jam'))
                                    # Find the corresponding .jar and .sp files with the same name as the current .jam
                                    # Rename them to the real name and append the extension
                                    for ext in ['.jar', '.sp', '.sdf']:
                                        os.rename(os.path.join(root, file.replace('.jam', ext)), os.path.join(root, real_name + ext))
                                    if verbose:
                                        print(f"Renamed: {file} -> {real_name}")
                                    break
                        break
                    except UnicodeDecodeError:
                        if verbose:
                            print(f"Could not decode {file} with encoding {encoding}, trying next encoding.")
                        continue
                else:
                    if verbose:
                        print(f"Could not decode {file} with any encoding. Skipping.")
                    continue
    if verbose:
        print("Postprocessing Konami games done.")