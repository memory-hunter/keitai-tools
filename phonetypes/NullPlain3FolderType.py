from phonetypes.PhoneType import PhoneType
import os
import shutil
from util.jam_utils import parse_valid_name, parse_props_00, parse_props_plaintext, fmt_plaintext_jam, fmt_spsize_header
from util.structure_utils import create_target_folder

class NullPlain3FolderType(PhoneType):
    """
    A class to represent a phone with null delimited adf OR plaintext adf, using 3 folder, and its extraction method.
    
    Description:
    - Top folder contains 3 folders: adf, jar, sp
    - in adf folder, there are adfX or adffileX files, where X is the index
    - in jar folder, there are jarX files, where X is the index
    - in sp folder, there are spX files, where X is the index
    """
    
    def extract(self, top_folder_directory, verbose=False):
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        # First, get all jar files and get file index from the name
        for jar_file in os.listdir(os.path.join(top_folder_directory, "jar")):
            if not jar_file.lower().startswith("jar"):
                continue
            jar_index = jar_file[3:]
            
            # Get the corresponding adf or adffile and sp files
            adf_file_path = os.path.join(top_folder_directory, "adf", f"adf{jar_index}")
            adffile_file_path = os.path.join(top_folder_directory, "adf", f"adffile{jar_index}")
            sp_file_path = os.path.join(top_folder_directory, "sp", f"sp{jar_index}")
            
            using_adf = False
            
            # Check if adf or adffile file exists and prioritize adffile file
            if os.path.exists(adffile_file_path):
                adf_file_path = adffile_file_path
            elif not os.path.exists(adf_file_path):
                continue
            else:
                using_adf = True
            
            if verbose:
                print('-'*80)
                
            # Get the properties from the JAM file
            jam_props = None
            used_encoding = None
            
            if using_adf:
                # Get the properties from the JAM file
                for offset in self.null_type_offsets:
                    try:
                        adf_content = open(adf_file_path, 'rb').read()
                        jam_props = parse_props_00(adf_content, offset[0], offset[1], verbose=verbose)
                        # Check if any dictionary entry is empty (meaning '' or None)
                        if not all(jam_props.values()):
                            raise ValueError("Empty value found in JAM properties.")
                        # Check if the AppName is valid in encodings
                        for encoding in self.encodings:
                            try:
                                jam_props['AppName'] = jam_props['AppName'].encode(encoding).decode('utf-8')
                                used_encoding = encoding
                                break
                            except UnicodeDecodeError:
                                if verbose:
                                    print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
                        else:
                            raise ValueError("Could not decode AppName.")
                        break
                    except Exception:
                        if verbose:
                            print(f"Warning: Not good with offset {offset}. Trying next offset.")
                        if offset == self.null_type_offsets[-1]:
                            if verbose:
                                print(f"Warning: Could not read ADF file {os.path.basename(adf_file_path)}.")
                            break
                       
                if jam_props is None:
                    if verbose:
                        print(f"Warning: Could not read ADF file {os.path.basename(adf_file_path)}'s props. Skipping.\n")
                    continue
                
                # Get the app name
                app_name = None
                try:
                    app_name = parse_valid_name(jam_props['PackageURL'], verbose=verbose)
                except ValueError as e:
                    if verbose:
                        print(f"Warning: {e.args[0]}")

                if not app_name:
                    if verbose:
                        print(f"Warning: No valid app name found in {os.path.basename(adf_file_path)}. Using base name.")
                    app_name = f'{os.path.splitext(os.path.basename(adf_file_path))[0]}'
                    
                # Check there is no duplicate app name existing in the target directory
                if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                    if verbose:
                        print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                    app_name = f"{app_name}_{self.duplicate_count+1}"
                    self.duplicate_count += 1
                    
                # Get JAR size in bytes into jam props
                jar_size = os.path.getsize(os.path.join(top_folder_directory, "jar", jar_file))
                jam_props['AppSize'] = jar_size
                
                # Format the JAM properties into plaintext jam
                new_jam_content = fmt_plaintext_jam(jam_props, verbose=verbose)
                
                # Write the new JAM file
                with open(os.path.join(target_directory, f"{app_name}.jam"), 'w', encoding=used_encoding) as f:
                    f.write(new_jam_content)
                
                # Copy the JAR file
                shutil.copyfile(os.path.join(top_folder_directory, "jar", jar_file), os.path.join(target_directory, f"{app_name}.jar"))
                
                # Write the SP file with header if it exists
                if os.path.exists(sp_file_path):
                    sp_size_list = jam_props['SPsize'].split(',')
                    sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                    sp_header = fmt_spsize_header(sp_size_list)
                    with open(sp_file_path, 'rb') as sp:
                        with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                            f.write(sp_header)
                            f.write(sp.read())
            else:
                # Get the properties from the plaintext JAM file
                for encoding in self.encodings:
                    try:
                        adf_content = open(adf_file_path, 'r', encoding=encoding).read()
                        jam_props = parse_props_plaintext(adf_content, verbose=verbose)
                        used_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        if verbose:
                            print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
                    if encoding == self.encodings[-1]:
                        if verbose:
                            print(f"Warning: Could not read ADF file {os.path.basename(adf_file_path)}.")
                        break
                
                if jam_props is None:
                    if verbose:
                        print(f"Warning: Could not read ADF file {os.path.basename(adf_file_path)}'s props. Skipping.\n")
                    continue
                
                # Get the app name
                app_name = None
                try:
                    app_name = parse_valid_name(jam_props['PackageURL'], verbose=verbose)
                except ValueError as e:
                    if verbose:
                        print(f"Warning: {e.args[0]}")
                        
                if not app_name:
                    if verbose:
                        print(f"Warning: No valid app name found in {os.path.basename(adf_file_path)}. Using base name.")
                    app_name = f'{os.path.splitext(os.path.basename(adf_file_path))[0]}'
                    
                # Check there is no duplicate app name existing in the target directory
                if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                    if verbose:
                        print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                    app_name = f"{app_name}_{self.duplicate_count+1}"
                    self.duplicate_count += 1
                    
                # Copy the ADF file, JAR file, and write SP header with size header
                shutil.copyfile(adf_file_path, os.path.join(target_directory, f"{app_name}.jam"))
                shutil.copyfile(os.path.join(top_folder_directory, "jar", jar_file), os.path.join(target_directory, f"{app_name}.jar"))
                if os.path.exists(sp_file_path):
                    sp_size_list = jam_props['SPsize'].split(',')
                    sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                    sp_header = fmt_spsize_header(sp_size_list)
                    with open(sp_file_path, 'rb') as sp:
                        with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                            f.write(sp_header)
                            f.write(sp.read())
            
            if verbose:
                print(f"Processed: {os.path.basename(adf_file_path)} -> {app_name}\n")
                
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of this type.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        # Check if the top folder directory contains 3 folders: adf, jar, sp
        # Check if the adf folder contains adfX files or adffileX files
        # Check if the jar folder contains jarX files
        # Check if the sp folder contains spX files
        
        # Expected folder names
        required_folders = ["adf", "jar", "sp"]
        
        folders_list = os.listdir(top_folder_directory)
        # Lower all folder names
        folders_list = [folder.lower() for folder in folders_list]
        
        # Check if the top folder contains the required folders
        for folder in required_folders:
            if folder.lower() not in folders_list:
                return None
            folder_path = os.path.join(top_folder_directory, folder)
            # Check for files with the pattern folderX where X is a number
            folder_files = os.listdir(folder_path)
            
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

        return "NullPlain3Folder"