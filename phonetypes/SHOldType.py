from phonetypes.PhoneType import PhoneType
import os
import shutil
from util.jam_utils import parse_props_plaintext, parse_valid_name, fmt_spsize_header, find_plausible_keywords_for_validity, is_valid_sh_header, filter_sdf_fields, fmt_plaintext_jam
from util.structure_utils import create_target_folder

class SHOldType(PhoneType):
    """
    A class to represent old SH phone type of structure with its extraction method.

    Description:
    - Top folders containing apps have folders ending names with .JAV
    - In the folders, there is a .UNQ file, with .ADF, .JAR, .SCP.
    """

    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a SH phone file structure.

        :param top_folder_directory: Top folder directory to extract games from.
        """
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)

        def process_folder(directory):
            if verbose:
                print('-' * 80)
            
            # Get the ADF file and get info
            adf_name = None
            adf_ext = None
            jar_ext = None
            scp_ext = None
            for file in os.listdir(directory):
                if str(file).lower().endswith(".adf"):
                    adf_name = str(file).split(".")[0]
                    adf_ext = str(file).split(".")[1]
                    adf_file = open(os.path.join(directory, file), 'rb').read()
                    # Decode and validate JAM file
                    for encoding in self.encodings:
                        try:
                            jam_file = adf_file.decode(encoding)
                            used_encoding = encoding
                            break
                        except UnicodeDecodeError:
                            if verbose:
                                print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
                    else:
                        if verbose:
                            print(f"Warning: Could not read JAM file {file}. Skipping.")
                        return
                    # Check for validity
                    if not find_plausible_keywords_for_validity(adf_file):
                        if verbose:
                            print(f"Warning: Skipping file {adf_name}: No minimal required keywords found for the .apl to have a valid JAM file")
                        return
                    jam_props = parse_props_plaintext(jam_file, verbose)
                # Prepare path formats due to unsureness of cases
                elif str(file).lower().endswith(".jar"):
                    jar_ext = str(file).split('.')[1]
                elif str(file).lower().endswith(".scp"):
                    scp_ext = str(file).split(".")[1]
            
            if adf_ext is None:
                if verbose:
                    print("Warning: ADF file not found. Skipping.")
                return
            
            # Determine app name
            package_url = jam_props.get('PackageURL')
            app_name = None
            if package_url:
                try:
                    app_name = parse_valid_name(package_url, verbose=verbose)
                except ValueError as e:
                    if verbose:
                        print(f"Warning: {e.args[0]}")

            if not app_name:
                package_url_candidates = [value for value in jam_props.values() if 'http' in value and ' ' not in value]
                for package_url in package_url_candidates:
                    try:
                        app_name = parse_valid_name(package_url, verbose=verbose)
                    except ValueError as e:
                        if verbose:
                            print(f"Warning: {e.args[0]}")
                if app_name is None:
                    if verbose:
                        print(f"Warning: No valid app name found in {file}. Using folder base name.")
                    app_name = adf_name
            
            # Handle duplicate app names
            if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count + 1}"
                self.duplicate_count += 1
            
            try:
                shutil.copyfile(os.path.join(directory, f"{adf_name}.{jar_ext}"), os.path.join(target_directory, f"{app_name}.jar"))
            except Exception:
                if verbose:
                    print("Warning: JAR file not found. Skipping.")
                return
            
            # Check if there is an SCP file with the same name
            if scp_ext is not None:
                scp_file_path = os.path.join(directory, f"{adf_name}.{scp_ext}")
                if os.path.exists(scp_file_path):
                    sp_sizes = jam_props.get('SPsize', '').split(',')
                    sp_sizes = [int(sp_size) for sp_size in sp_sizes if sp_size.isdigit()]
                    header = fmt_spsize_header(sp_sizes)
                    with open(scp_file_path, 'rb') as scp_file:
                        with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                            f.write(header)
                            f.write(scp_file.read())
                            
            # Write the JAM
            try:
                shutil.copyfile(os.path.join(directory, f"{adf_name}.{adf_ext}"), os.path.join(target_directory, f"{app_name}.jam"))
            except Exception:
                if verbose:
                    print("Warning: JAM can't be written. Skipping.")
                return
            
            if verbose:
                print(f"Processed: {adf_name} -> {app_name}\n")
            
        # List all files
        files = os.listdir(top_folder_directory)
        
        # Process each folder
        for dir in files:
            directory = os.path.join(top_folder_directory, dir)
            if os.path.isdir(directory):
                process_folder(directory)
        
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of Old SH type.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        files = os.listdir(top_folder_directory)
        if not any(str(dir).lower().endswith(".jav") for dir in files):
            return None

        return "SHOld"
