from phonetypes.PhoneType import PhoneType
import os
import struct
import shutil
from util.jam_utils import parse_props_plaintext, parse_valid_name, fmt_spsize_header
from util.structure_utils import create_target_folder

class SHType(PhoneType):
    """
    A class to represent a SH phone type of structure with its extraction method.
    
    Description:
    - Top folder contains .apl and .scp files with same names.
    - .scp files are direct .sp files.
    - .apl file contains headers and contents of (not limited to these, since other files need to be discovered):
        - jam file
        - sdf file
        - icon160 file
        - icon48 file
        - jar file
    """
    
    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a SH phone file structure.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        def process_file(apl_file_path):
            if verbose:
                print('-'*80)
            
            apl_name = os.path.basename(apl_file_path).split('.')[0]
            
            with open(apl_file_path, 'rb') as apl_file:
                # Get the header which contains sizes and determine offset
                size_header = apl_file.read(41)

                # Determine start of file contents
                if chr(size_header[24]).isalpha():
                    # Alphabetical symbol at 24th byte
                    jam_size, sdf_size, unknown_size1, icon160_size, icon48_size, jar_size = struct.unpack(
                        '<IIIIII',
                        size_header[:24]
                    )
                    offset = 24
                elif chr(size_header[40]).isalpha():
                    # Alphabetical symbol at 40th byte
                    jam_size, sdf_size, unknown_size1, icon160_size, icon48_size, unknown_size2, unknown_size3, unknown_size4, unknown_size5, jar_size = struct.unpack(
                        '<IIIIIIIIII',
                        size_header[:40]
                    )
                    offset = 40
                else:
                    # Handle the case where neither byte is an alphabetical symbol
                    if verbose:
                        print(f"WARNING: Skipping file {apl_name}: No alphabetical symbol found at 0x24 or 0x40")
                    return
                
                # Reset offsets
                if offset == 40:
                    apl_file.seek(-1, os.SEEK_CUR)
                elif offset == 24:
                    apl_file.seek(-17, os.SEEK_CUR)
                
                # Fetch data
                jam_file = apl_file.read(jam_size)
                sdf_file = apl_file.read(sdf_size)
                unknown1_file = apl_file.read(unknown_size1)
                if offset == 40:
                    unknown2_file = apl_file.read(unknown_size2)
                    unknown3_file = apl_file.read(unknown_size3)
                    unknown4_file = apl_file.read(unknown_size4)
                    unknown5_file = apl_file.read(unknown_size5)
                icon160_file = apl_file.read(icon160_size)
                icon48_file = apl_file.read(icon48_size)
                jar_file = apl_file.read(jar_size)
                
                # Read JAM file with different encodings
                for encoding in self.encodings:
                    try:
                        jam_file = jam_file.decode(encoding)
                        used_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        if verbose:
                            print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
                else:
                    if verbose:
                        print(f"Warning: Could not read JAM file {apl_name}. Skipping.")
                    return
                
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
                            print(f"Warning: No valid app name found in {apl_file_path}. Using base name.")
                        app_name = f'{apl_name}'
                
                # Check there is no duplicate app name existing in the target directory
                if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                    if verbose:
                        print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                    app_name = f"{app_name}_{self.duplicate_count+1}"
                    self.duplicate_count += 1
                    
                # Check if there exists .scp file with the same name, if exists, copy to target directory with .sp extension
                scp_file_path = os.path.join(os.path.dirname(apl_file_path), f"{apl_name}.scp")
                if os.path.exists(scp_file_path):
                    # Get the SPsize string from props and make , delimited integer list
                    sp_sizes = jam_props['SPsize'].split(',')
                    sp_sizes = [int(sp_size) for sp_size in sp_sizes]
                    header = fmt_spsize_header(sp_sizes)
                    with open(scp_file_path, 'rb') as scp_file:
                        with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                            f.write(header)
                            f.write(scp_file.read())
                    
                # Write the JAM file with app name
                if jam_size > 0:
                    with open(os.path.join(target_directory, f"{app_name}.jam"), 'w', encoding=used_encoding) as f:
                        f.write(jam_file)
                    
                # Write the SDF file with app name
                if sdf_size > 0:
                    with open(os.path.join(target_directory, f"{app_name}.sdf"), 'wb') as f:
                        f.write(sdf_file)
                    
                # Write the JAR file with app name
                if jar_size > 0:
                    with open(os.path.join(target_directory, f"{app_name}.jar"), 'wb') as f:
                        f.write(jar_file)
                
                if verbose:
                    print(f"Processed: {apl_name} -> {app_name}\n")
            
        # List all files
        files = os.listdir(top_folder_directory)
        
        # Process APL and SCP files with the same name
        apl_files = [f for f in files if f.lower().endswith('.apl')]
        
        for apl_file in apl_files:
            apl_file_path = os.path.join(top_folder_directory, apl_file)
            process_file(apl_file_path)
        
    def test_structure(self, top_folder_directory):  
        """
        Test if the top folder directory is of a SH phone file structure.
        
        :param top_folder_directory: Top folder directory to test.
        :return: True if the top folder directory is of a SH phone file structure, False otherwise.
        """
        
        # Check that there are no subdirectories and only .apl and .scp files are present.
        
        files = os.listdir(top_folder_directory)       
        subdirectories = [f for f in files if os.path.isdir(os.path.join(top_folder_directory, f))]
        if subdirectories:
            return None
        
        apl_scp_files = [f for f in files if f.lower().endswith('.apl') or f.lower().endswith('.scp')]
        if not apl_scp_files:
            return None
        
        return "SH"
        
        