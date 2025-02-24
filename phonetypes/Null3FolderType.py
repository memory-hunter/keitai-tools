from phonetypes.PhoneType import PhoneType
import os
import shutil
from util.jam_utils import parse_valid_name, parse_props_00, fmt_plaintext_jam, fmt_spsize_header
from util.structure_utils import create_target_folder

class Null3FolderType(PhoneType):
    """
    A class to represent a phone with null delimited adf, using 3 folders, and its extraction method.
    
    Description:
    - Top folder contains 3 folders: adf, jar, sp
    - in adf folder, there are adfX files, where X is the index
    - in jar folder, there are jarX files, where X is the index
    - in sp folder, there are spX files, where X is the index
    
    For further proof of type assurance, the top folder may contain files "$____DIR._ID", "$_____00._BK" or "APPINFO"
    """
    
    def extract(self, top_folder_directory, verbose=False):
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        # Get actual folder names while preserving case
        folder_map = {folder.lower(): folder for folder in os.listdir(top_folder_directory)}

        # Ensure required folders exist (case-insensitive check)
        required_folders = ["adf", "jar", "sp"]
        if not all(folder in folder_map for folder in required_folders):
            if verbose:
                print("Error: Missing required folders (adf, jar, sp) in top folder.")
            return

        # Paths to required folders (preserving original case)
        folder_paths = {folder: os.path.join(top_folder_directory, folder_map[folder]) for folder in required_folders}

        # Process all ADF files, with corresponding JAR and SP files
        for adf_file in os.listdir(folder_paths["adf"]):
            if not adf_file.lower().startswith("adf"):
                continue

            if verbose:
                print('-' * 80)

            adf_index = adf_file[3:]

            # Get the corresponding JAR and SP files
            jar_file = os.path.join(folder_paths["jar"], f"{folder_paths["jar"][-3:]}{adf_index}")
            sp_file = os.path.join(folder_paths["sp"], f"{folder_paths["sp"][-2:]}{adf_index}")

            # Get the properties from the JAM file
            jam_props = None

            for offset in self.null_type_offsets:
                try:
                    adf_file_path = os.path.join(folder_paths["adf"], adf_file)
                    adf_content = open(adf_file_path, 'rb').read()
                    jam_props = parse_props_00(adf_content, offset[0], offset[1], verbose=verbose)

                    # Ensure JAM properties are valid
                    if not all(jam_props.values()) or any(len(value) == 0 for value in jam_props.values()):
                        raise ValueError("Empty value found in JAM properties.")
                    if " " in jam_props['PackageURL']:
                        raise ValueError("Space found in PackageURL.")

                    break
                except Exception as e:
                    if verbose:
                        print(f"Warning: Not good with offset {offset}. Trying next offset.")
                        print(f"    - {e.args[0]}")
            else:
                if verbose:
                    print(f"Warning: Could not read ADF file {adf_file}. Skipping.\n")
                continue

            if jam_props is None:
                if verbose:
                    print(f"Warning: Could not read ADF file {adf_file}'s props. Skipping.\n")
                continue

            # Get JAR size in bytes into jam props
            try:
                jar_size = os.path.getsize(jar_file)
                jam_props['AppSize'] = jar_size
            except FileNotFoundError:
                if verbose:
                    print(f"Warning: JAR file {jar_file} not found. Skipping {adf_file}.")
                continue

            # Get app name
            app_name = None
            try:
                app_name = parse_valid_name(jam_props['PackageURL'], verbose=verbose)
            except ValueError as e:
                if verbose:
                    print(f"Warning: {e.args[0]}")

            if not app_name:
                if verbose:
                    print(f"Warning: No valid app name found in {adf_file}. Using base name.")
                app_name = f'{os.path.splitext(adf_file)[0]}'

            # Check for duplicate app names
            if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count+1}"
                self.duplicate_count += 1

            # Build JAM file content
            jam_file = fmt_plaintext_jam(jam_props)

            # Write JAM file
            for encoding in self.encodings:
                try:
                    with open(os.path.join(target_directory, f"{app_name}.jam"), 'w', encoding=encoding) as f:
                        f.write(jam_file)
                    break
                except UnicodeEncodeError:
                    if verbose:
                        print(f"Warning: UnicodeEncodeError with {encoding}. Trying next encoding.")
                    if encoding == self.encodings[-1]:
                        if verbose:
                            print(f"Warning: Could not write JAM file {app_name}. Skipping.")
                        return

            # Copy JAR and SP files
            shutil.copy(jar_file, os.path.join(target_directory, f"{app_name}.jar"))

            if os.path.exists(sp_file):
                try:
                    sp_size_list = jam_props['SPsize'].split(',')
                    sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                    sp_header = fmt_spsize_header(sp_size_list)
                    with open(sp_file, 'rb') as sp, open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                        f.write(sp_header)
                        f.write(sp.read())
                except Exception as e:
                    if verbose:
                        print(f"Warning: Failed to process SP file {sp_file}. Error: {e}")

            if verbose:
                print(f"Processed: {adf_file} -> {app_name}")
            
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of this type.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        # Expected folder names (case-insensitive detection)
        required_folders = ["adf", "jar", "sp"]

        # Get the actual folder names while preserving case
        folder_map = {folder.lower(): folder for folder in os.listdir(top_folder_directory)}

        # Ensure all required folders exist (case-insensitively)
        if not all(folder in folder_map for folder in required_folders):
            return None

        # Paths to required folders (preserving original case)
        folder_paths = {folder: os.path.join(top_folder_directory, folder_map[folder]) for folder in required_folders}

        # Check if the "sp" folder contains any subfolders
        sp_folder_path = folder_paths["sp"]
        sp_contents = os.listdir(sp_folder_path)

        for item in sp_contents:
            if os.path.isdir(os.path.join(sp_folder_path, item)):
                return None  

        for folder in required_folders:
            folder_path = folder_paths[folder]
            folder_files = os.listdir(folder_path)

            # In the adf folder, check for any file starting with 'adffile'
            if folder == "adf":
                for file in folder_files:
                    if file.lower().startswith("adffile"):
                        return None
                    # Check if a file contains at least one 00 byte
                    with open(os.path.join(folder_path, file), 'rb') as f:
                        if f.read().count(b'\x00') == 0:
                            return None
            
            # Ensure there is at least one valid 'folderX' file (e.g., adf1, jar2, sp3)
            valid_file_found = False
            for file in folder_files:
                if file.lower().startswith(folder):
                    suffix = file[len(folder):]
                    if suffix.isdigit():
                        valid_file_found = True
                        break
            
            if not valid_file_found:
                return None

        return "Null3Folder"
