from phonetypes.PhoneType import PhoneType
import os
import shutil
from util.jam_utils import parse_props_plaintext, parse_valid_name, fmt_spsize_header, find_plausible_keywords_for_validity, parse_jam_objects
from util.structure_utils import create_target_folder

class DFType(PhoneType):
    """
    A class to represent a D or an F phone type of structure with its extraction method.
    
    Description:
    - One top folder containing game folders numbered starting from 00.
    - Each game folder contains a "jam", "[full/mini]jar" files. If jam doesn't exist, FJJAM.DB is used to reconstruct them.
    - "spX" files are indexed starting from 0, where X is the index.
    """
    
    needs_reconstruction = False
    
    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a D or F phone file structure.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        def process_subdirectory(subfolder, target_directory):
            if verbose:
                print('-'*80)
            
            # List all files
            files = os.listdir(subfolder)
            
            # Process JAM
            jam_file_path = next((f for f in files if f.lower() == 'jam'), None)
            
            if not jam_file_path:
                if verbose:
                    print(f"No JAM file found in {subfolder}. Skipping.\n")
                return
            
            # Read JAM file with different encodings
            jam_file = None
            for encoding in self.encodings:
                try:
                    jam_file = open(os.path.join(subfolder, jam_file_path), 'r', encoding=encoding).read()
                    break
                except UnicodeDecodeError:
                    if verbose:
                        print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
            else:
                if verbose:
                    print(f"Warning: Could not read JAM file {jam_file_path}. Skipping.\n")
                return
            
            if (not find_plausible_keywords_for_validity(jam_file)):
                if verbose:
                    print(f"Warning: {subfolder} does not contain all required keywords. Skipping.\n")
                return
            
            # Get the properties from the JAM file
            jam_props = parse_props_plaintext(jam_file, verbose=verbose)
            
            package_url = None
            try:
                package_url = jam_props['PackageURL']
            except KeyError:
                    if verbose:
                        print(f"Warning: No PackageURL found in JAM file.")
            
            # Determine valid name for the app
            app_name = None
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
                        print(f"Warning: No valid app name found in {jam_file_path}. Using base folder name.")
                    app_name = f'{os.path.basename(subfolder)}'
                
            # Check there is no duplicate app name existing in the target directory
            if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count+1}"
                self.duplicate_count += 1                
            
            # Copy over JAM file with app name
            src = os.path.join(subfolder, jam_file_path)
            dst = os.path.join(target_directory, f"{app_name}.jam")
            shutil.copy2(src, dst)
            
            # Find jar files, could be "jar" or ("fulljar" and/or "minijar")
            jar_files = [f for f in files if any(substring in f.lower() for substring in ['jar', 'fulljar', 'minijar'])]
            
            # Copy over jar files, name jar and fulljar files with app name, for minijar, use app name + "_mini"
            for jar_file in jar_files:
                if 'minijar' in jar_file.lower():
                    shutil.copy2(os.path.join(subfolder, jar_file), os.path.join(target_directory, f"{app_name}_mini.jar"))
                else:
                    shutil.copy2(os.path.join(subfolder, jar_file), os.path.join(target_directory, f"{app_name}.jar"))
                    
            # Concatenate all "spX" files
            sp_files = [f for f in files if f.lower().startswith('sp')]
            concatenated_content = b''
            for sp_file in sp_files:
                with open(os.path.join(subfolder, sp_file), 'rb') as f:
                    concatenated_content += f.read()
            
            # Write concatenated content to a file
            if concatenated_content != b'':
                sp_size_list = jam_props['SPsize'].split(',')
                sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                header = fmt_spsize_header(sp_size_list)
                with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as wf:
                    wf.write(header)
                    wf.write(concatenated_content)
                
            if verbose:
                print(f"Processed: {subfolder} -> {app_name}\n")
                
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        # hack: run test structure again to get the reconstruction flag set if needed
        self.test_structure(top_folder_directory)
        
        # Reconstruct JAMs if needed
        if self.needs_reconstruction:
            if verbose:
                print("No JAM files detected in the game folders. Reconstructing from FJJAM.DB database.")
            parse_jam_objects(top_folder_directory, verbose)
        
        # List all folders in the top folder directory
        for folder in os.listdir(top_folder_directory):
            folder_path = os.path.join(top_folder_directory, folder)
            if os.path.isdir(folder_path):
                # Process the subdirectory and output into folder "output" at the same level as top level directory
                process_subdirectory(folder_path, target_directory)
                
    def test_structure(self, top_folder_directory, verbose=False) -> bool:
        """
        Test the structure of the top folder directory to see if it is a D/F type.
        
        :param top_folder_directory: Top folder directory to test the structure of.
        :param verbose: If True, prints debug information.
        
        :return: True if at least one subfolder satisfies the D/F type structure, False otherwise.
        """
        
        keywords = [
            "ENTRY",
            "JAVAADL",
            "JAVAEXE",
            "JAVASYS",
            "PUSHSMS"
        ]
        
        if any(k.upper() in keywords for k in os.listdir(top_folder_directory)):
            return None # exit early if a modern n type is found
        
        if not os.path.isdir(top_folder_directory):
            return None
        
        subdirs = [f for f in os.listdir(top_folder_directory) if os.path.isdir(os.path.join(top_folder_directory, f))]
        if not subdirs:
            return None
        
        valid_jar_names = {'jar', 'fulljar', 'minijar'}
        found_valid_structure = False
        
        for folder in subdirs:
            # Check if the folder name contains at least one digit or an underscore
            if not any(c.isdigit() or c == '_' for c in folder):
                continue
            
            folder_path = os.path.join(top_folder_directory, folder)
            files = os.listdir(folder_path)
            
            # Check if the folder contains a JAM file
            if not any('jam' in f.lower() for f in files):
                self.needs_reconstruction = True
            
            # Check if the folder contains a JAR file of any type
            if not any(name in f.lower() for f in files for name in valid_jar_names):
                continue
            
            found_valid_structure = True
            break  # No need to check further, we found a valid folder
        
        return "D/F" if found_valid_structure else None