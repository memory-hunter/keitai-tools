import os
import shutil
from util.jam_utils import find_plausible_keywords_for_validity, parse_props_plaintext, parse_valid_name, swap_spsize_header_endian
from util.structure_utils import create_target_folder
from phonetypes.PhoneType import PhoneType

class MType(PhoneType):
    """
    A class to represent Motorola phone.
    
    Description:
    - Contains trjava.log, J2MEST.SYS and USR files
    - .adf file for JAM, .jar for JAR, .rms for SP files. SP files have headers already. ADF is in plaintext
    """
    
    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a M phone.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        def process_adf(adf_file_name, target_directory):
            if verbose:
                print('-' * 80)
                
            # Get the corresponding JAR and SP files
            jar_file = os.path.join(top_folder_directory, adf_file_name + ".jar")
            sp_file = os.path.join(top_folder_directory, adf_file_name + ".rms")
            
            # Read JAM file with different encodings
            jam_file = None
            for encoding in self.encodings:
                try:
                    jam_file = open(os.path.join(top_folder_directory, adf_file_name + '.adf'), 'r', encoding=encoding).read()
                    break
                except UnicodeDecodeError:
                    if verbose:
                        print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
            else:
                if verbose:
                    print(f"Warning: Could not read JAM file {adf_file_name}. Skipping.\n")
                return
            
            # Validate the JAM file
            if (not find_plausible_keywords_for_validity(jam_file)):
                if verbose:
                    print(f"Warning: {adf_file_name} does not contain all required keywords. Skipping.\n")
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
                        print(f"Warning: No valid app name found in {adf_file_name}. Using base folder name.")
                    app_name = f'{os.path.basename(adf_file_name)}'
                
            # Check there is no duplicate app name existing in the target directory
            if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count+1}"
                self.duplicate_count += 1
                
            # Copy over JAM file with app name
            src = os.path.join(top_folder_directory, adf_file_name + ".adf")
            dst = os.path.join(target_directory, f"{app_name}.jam")
            shutil.copy2(src, dst)
            
            # Copy over JAR file with app name
            dst = os.path.join(target_directory, f"{app_name}.jar")
            shutil.copy2(jar_file, dst)
            
            # Copy over SP after removing last 64 bytes and endian-swapping the header
            # (???? no idea what actually is the extra 64 bytes but since the header is there for the sp im just taking the end away)
            if (os.path.exists(sp_file)):
                with open(os.path.join(top_folder_directory, adf_file_name + ".rms"), 'rb') as rms:
                    rms_file = bytearray(rms.read())
                    rms_file[0:64] = swap_spsize_header_endian(rms_file[0:64])
                    rms_file = rms_file[:-64]
                    with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as sp:
                        sp.write(rms_file)
            
            if verbose:
                print(f"Processed: {adf_file_name} -> {app_name}\n")
            
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        all_adf_names = [str(adf).split(".adf")[0] for adf in os.listdir(top_folder_directory) if str(adf).endswith(".adf")]
        
        for adf in all_adf_names:
            process_adf(adf, target_directory)
        
    
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of M type phone file structure type.
        
        :param top_folder_directory: Top folder directory to test the structure of.
        """
        # Expected files
        required_files = ["J2MEPCK", "J2MEST.SYS", "J2MEST.USR", "trjava.log"]
        files = os.listdir(top_folder_directory)
        
        if any(file in required_files for file in required_files):
            return "M"
        
        return None
        