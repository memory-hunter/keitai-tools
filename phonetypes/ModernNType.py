from phonetypes.PhoneType import PhoneType
import os
import shutil
from util.jam_utils import parse_valid_name, fmt_spsize_header, parse_props_plaintext
from util.structure_utils import create_target_folder

class ModernNType(PhoneType):
    """
    A class to represent a Modern NEC file structure type, and its extraction method.
    
    Description:
    - Top folder contains numbered folders starting from 0.
    - Each numbered folder contains a adf, jar, sp file, and possibly a mini file.
    """
    
    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a Modern NEC phone file structure.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        def process_subdirectory(subfolder, target_directory):
            if verbose:
                print('-'*80)
            
            # List all files
            files = os.listdir(subfolder)
            
            # Process ADF
            next_adf = next((f for f in files if f.lower().startswith('adf')), None)
            if not next_adf:
                if verbose:
                    print(f"No ADF file found in {subfolder}. Skipping.\n")
                return
            
            adf_file_path = os.path.join(subfolder, next_adf)
            
            # Get the corresponding JAR and SP files
            adf_index = os.path.basename(subfolder)
            
            adf_file = open(os.path.join(subfolder, adf_file_path), 'rb').read()
            
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
                if not app_name:
                    package_url_candidates = jam_props['']
                if app_name is None:
                    if verbose:
                        print(f"Warning: No valid app name found in {adf_file_path}. Using base folder name.")
                        app_name = 'adf' + adf_index
            
            # Check there is no duplicate app name existing in the target directory
            if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count+1}"
                self.duplicate_count += 1
                
            # Get the corresponding files
            jar_file_path = os.path.join(subfolder, f"jar")
            sp_file_path = os.path.join(subfolder, f"sp")
            mini_file_path = os.path.join(subfolder, f"mini")
            
            # Copy over jar, sp and mini and write jam file
            with open(os.path.join(target_directory, f"{app_name}.jam"), 'w', encoding=used_encoding) as f:
                f.write(adf_file)
            if os.path.exists(jar_file_path):
                shutil.copy(jar_file_path, os.path.join(target_directory, f"{app_name}.jar"))
            # Add a header to SP file
            if os.path.exists(sp_file_path):
                sp_size_list = jam_props['SPsize'].split(',')
                sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                sp_header = fmt_spsize_header(sp_size_list)
                with open(sp_file_path, 'rb') as sp:
                    with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                        f.write(sp_header)
                        f.write(sp.read())
            if os.path.exists(mini_file_path):
                shutil.copy(mini_file_path, os.path.join(target_directory, f"{app_name}_mini.jar"))
                
            if verbose:
                print(f"Processed: {subfolder} -> {app_name}\n")
        
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        # List all folders in the top folder directory
        for folder in os.listdir(top_folder_directory):
            folder_path = os.path.join(top_folder_directory, folder)
            if os.path.isdir(folder_path):
                # Process the subdirectory and output into folder "output" at the same level as top level directory
                process_subdirectory(folder_path, target_directory)
            
    
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of Modern NEC file structure type.
        
        :param top_folder_directory: Top folder directory to test the structure of.
        """
        # Check if the top folder directory contains numbered folders use os.walk
        if not(any(folder.isdigit() for folder in os.listdir(top_folder_directory))):
            return None

        # Check if each numbered folder contains an adf file if it has any number of files, skip if empty
        for _, folders, _ in os.walk(top_folder_directory):
            folders = [folder for folder in folders if folder.isdigit()]
            for folder in folders:
                print(folder)
                folder_path = os.path.join(top_folder_directory, folder)
                if not os.listdir(folder_path):
                    continue
                if not any(f.lower().startswith('adf') for f in os.listdir(folder_path)):
                    return None

        return "ModernN"