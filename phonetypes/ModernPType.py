from phonetypes.PhoneType import PhoneType
import os
import shutil
from util.jam_utils import parse_valid_name, fmt_spsize_header, parse_props_plaintext
from util.structure_utils import create_target_folder

class ModernPType(PhoneType):
    """
    A class to represent a Modern Panasonic file structure type, and its extraction method.
    
    Description:
    - Top folder contains 3 folders: adf, jar, sp
    - in adf, jar and sp folders, there are numbered files and each are associated with each other across folders
    """
    
    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a Modern Panasonic phone file structure.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        # List all files in the "ADF" folder in the top folder directory
        adf_folder = os.path.join(top_folder_directory, "adf")
        adf_files = os.listdir(adf_folder)
        
        # Go through all files in the "ADF" folder and process the same numbered files in the "JAR" and "SP" folders
        for adf_file in adf_files:
            if verbose:
                print('-'*80)
                
            # Get the file number from the adf file
            adf_index = int(adf_file)
            
            # Get the corresponding jar and sp files
            jar_file = os.path.join(top_folder_directory, "jar", str(adf_index))
            sp_file = os.path.join(top_folder_directory, "sp", str(adf_index))
            
            adf_file = open(os.path.join(adf_folder, adf_file), 'rb').read()
            
            # Find the offset for plaintext cutoff
            for offset in self.plaintext_cutoff_offsets:
                if b'\x00' in adf_file[offset:]:
                    if verbose:
                        print(f"Plaintext cutoff not good for offset {offset}. Trying next offset.")
                    continue
                else:
                    if verbose:
                        print(f"Plaintext cutoff found at offset {offset}.")
                    adf_file = adf_file[offset:]
                    # Turn bytes into lines of text
                    for encoding in self.encodings:
                        try:
                            adf_file = adf_file.decode(encoding)
                            used_encoding = encoding
                            break
                        except UnicodeDecodeError:
                            if verbose:
                                print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
                    else:
                        if verbose:
                            print(f"Warning: Could not decode ADF file. Skipping.\n")
                        return
                    break
            else:
                if verbose:
                    print(f"Plaintext cutoff not found. Skipping.\n")
                return
            
            # Get the properties from the ADF file
            jam_props = parse_props_plaintext(adf_file, verbose=verbose)
            
            # Get name of the app
            app_name = None
            package_url = None
            try:
                package_url = jam_props['PackageURL']
            except KeyError:
                    if verbose:
                        print(f"Warning: No PackageURL found in JAM file.")
            
            # Determine valid name for the app
            if package_url:
                try:
                    app_name = parse_valid_name(package_url, verbose=verbose)
                except ValueError as e:
                    if verbose:
                        print(f"Warning: {e.args[0]}")
            
            if not app_name:
                package_url_candidates = [value for value in jam_props.values() if value.find('http') != -1 and value.find(' ') == -1]
                for package_url in package_url_candidates:
                    try:
                        app_name = parse_valid_name(package_url, verbose=verbose)
                    except ValueError as e:
                        if verbose:
                            print(f"Warning: {e.args[0]}")
                if app_name is None:
                    if verbose:
                        print(f"Warning: No valid app name found in {adf_index}. Using base folder name.")
                        app_name = 'adf' + str(adf_index)
            
            # Check there is no duplicate app name existing in the target directory
            if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count+1}"
                self.duplicate_count += 1
            
            # Write the JAM and JAR to the target directory, put header on the SP and write
            with open(os.path.join(target_directory, f"{app_name}.jam"), 'w', encoding=used_encoding) as jam_file:
                jam_file.write(adf_file)
                
            if os.path.exists(jar_file):
                with open(jar_file, 'rb') as jar_file:
                    with open(os.path.join(target_directory, f"{app_name}.jar"), 'wb') as target_jar_file:
                        target_jar_file.write(jar_file.read())
            
            if os.path.exists(sp_file):
                with open(sp_file, 'rb') as sp_file:
                    sp_size_list = jam_props['SPsize'].split(',')
                    sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                    sp_header = fmt_spsize_header(sp_size_list)
                    with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                        f.write(sp_header)
                        f.write(sp_file.read())
            
            if verbose:
                print(f"Processed: {str(adf_index)} -> {app_name}\n")
            
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of Modern Panasonic file structure type.
        
        :param top_folder_directory: Top folder directory to test the structure of.
        """
        # Check if the top folder directory contains adf, jar and sp folders
        # Check if there are at least numbered files in adf, jar and sp folders
        # Expected folder names
        required_folders = ["adf", "jar", "sp"]
        
        folders_list = os.listdir(top_folder_directory)
        # Lower all folder names
        folders_list = [folder.lower() for folder in folders_list]
        
        # Check if the top folder contains the required folders
        for folder in required_folders:
            if folder.lower() not in folders_list:
                return None
        
        # Check if each required folder contains at least one numbered file
        for folder in required_folders:
            folder_path = os.path.join(top_folder_directory, folder)
            folder_contents = os.listdir(folder_path)
            
            # Check if there is at least one file with a numeric name
            if not any(item.isdigit() for item in folder_contents):
                return None
        
        return "ModernP"