from phonetypes.PhoneType import PhoneType
import os
import struct
import shutil
from util.jam_utils import parse_valid_name, parse_props_00, fmt_plaintext_jam
from util.structure_utils import create_target_folder

class Null3FolderType(PhoneType):
    """
    A class to represent a phone with null delimited adf, using 3 folder, and its extraction method.
    
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
        
        # Process all ADF files, with corresponding JAR and SP files
        # Get the ADF file and its index
        for adf_file in os.listdir(os.path.join(top_folder_directory, "adf")):
            if not adf_file.startswith("adf"):
                continue
            
            if verbose:
                print('-'*80)
            
            adf_index = adf_file[3:]
            
            # Get the corresponding JAR and SP files
            jar_file = os.path.join(top_folder_directory, "jar", f"jar{adf_index}")
            sp_file = os.path.join(top_folder_directory, "sp", f"sp{adf_index}")
            
            # Get the properties from the JAM file
            jam_props = None
            
            for offset in self.null_type_offsets:
                try:
                    adf_file_path = os.path.join(top_folder_directory, "adf", adf_file)
                    adf_content = open(adf_file_path, 'rb').read()
                    jam_props = parse_props_00(adf_content, offset[0], offset[1], verbose=verbose)
                    # Check if any dictionary entry is empty (meaning '' or None)
                    if not all(jam_props.values()):
                        raise ValueError("Empty value found in JAM properties.")
                    # Check if the AppName is valid in encodings
                    for encoding in self.encodings:
                        try:
                            jam_props['AppName'] = jam_props['AppName'].encode(encoding).decode('utf-8')
                            break
                        except UnicodeDecodeError:
                            if verbose:
                                print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
                            if encoding == self.encodings[-1]:
                                raise ValueError("Could not decode AppName.")
                    break
                except Exception:
                    if verbose:
                        print(f"Warning: Not good with offset {offset}. Trying next offset.")
                    if offset == self.null_type_offsets[-1]:
                        if verbose:
                            print(f"Warning: Could not read ADF file {adf_file}. Skipping.\n")
                        return
            
            # Get JAR size in bytes into jam props
            jar_size = os.path.getsize(jar_file)
            jam_props['AppSize'] = jar_size
            
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
                
            # Check there is no duplicate app name existing in the target directory
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
                shutil.copy(sp_file, os.path.join(target_directory, f"{app_name}.sp"))
            
            if verbose:
                print(f"Processed: {adf_file} -> {app_name}\n")
            
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of this type.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        # Check if the top folder directory contains 3 folders: adf, jar, sp
        # Check if the adf folder contains adfX files
        # Check if the jar folder contains jarX files
        # Check if the sp folder contains spX files
        
        # Expected folder names
        required_folders = ["adf", "jar", "sp"]
        
        # Check if the top folder contains the required folders
        for folder in required_folders:
            folder_path = os.path.join(top_folder_directory, folder)
            if not os.path.isdir(folder_path):
                return None
            
            # Check for files with the pattern folderX where X is a number
            folder_files = os.listdir(folder_path)

            # In the adf folder, check for any file starting with 'adffile'
            if folder == "adf":
                for file in folder_files:
                    if file.startswith("adffile"):
                        return None
                    # Check if a file contains at least one 00 byte
                    if open(os.path.join(folder_path, file), 'rb').read().count(b'\x00') == 0:
                        return None
            
            # Ensure there is at least one valid 'folderX' file (e.g., adf1, jar2, sp3)
            valid_file_found = False
            for file in folder_files:
                if file.startswith(folder):
                    suffix = file[len(folder):]
                    if suffix.isdigit():
                        valid_file_found = True
                        break
            
            if not valid_file_found:
                return None

        return "Null3Folder"