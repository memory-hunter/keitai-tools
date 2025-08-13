from phonetypes.PhoneType import PhoneType
import os
import struct
from util.jam_utils import parse_props_plaintext, parse_valid_name, fmt_spsize_header, find_plausible_keywords_for_validity, is_valid_sh_header, filter_sdf_fields, fmt_plaintext_jam
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
        Extract games from the top folder directory in a SO phone file structure.

        :param top_folder_directory: Top folder directory to extract games from.
        """
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)

        def process_file(apl_file_path):
            if verbose:
                print('-' * 80)

            apl_name = os.path.basename(apl_file_path).split('.')[0]

            # Preliminary check for the file to have a valid JAM entry
            apl_contents = open(apl_file_path, 'rb').read()
            if not find_plausible_keywords_for_validity(apl_contents):
                if verbose:
                    print(f"Warning: Skipping file {apl_name}: No minimal required keywords found for the .apl to have a valid JAM file")
                return
            
            valid_offset = -1
            
            with open(apl_file_path, 'rb') as apl_file:
                size_header = apl_file.read(max(self.sh_type_offsets) + 32)  # Read offset + 32
                for offset in self.sh_type_offsets:
                    # Check if header is valid
                    if is_valid_sh_header(size_header, offset):
                        if offset != 0:
                            # Dynamically unpack header based on offset
                            num_integers = offset // 4
                            format_string = f'<{"I" * num_integers}'
                            unpacked_values = struct.unpack(format_string, size_header[:offset])

                            # Assign values to variables
                            jam_size, sdf_size, unknown_size1, icon160_size, icon48_size, *extra_sizes, jar_size = unpacked_values

                        valid_offset = offset
                        # If a valid offset is found, stop checking further offsets
                        if verbose:
                            print(f"Valid header found at offset {offset}")
                        break
                else:
                    # If no valid offset is found
                    if verbose:
                        print(f"Warning: Skipping file {apl_name}. It has no known offsets as a header for sizes.")
                    return
                
                # Process the contents of the file using the unpacked sizes
                # Reset the file pointer based on the offset
                apl_file.seek(offset)
                
                if valid_offset == 0:
                    if verbose:
                        print(f"Assuming linear JAM + SDF + ICON + ... + JAR structure.")
                    whole_content = apl_file.read()
                    # Find if there is an icon between SDF and JAR by using GIF file magic header
                    gif_pos = whole_content.find(b"GIF89a")
                    # Find the first archive header
                    jar_pos = whole_content.find(b"\x50\x4B\x03\04")
                    # The GIF magic header found is not an icon if it is inside the archive
                    if gif_pos > jar_pos:
                        gif_pos = -1
                    if jar_pos == -1:
                        if verbose:
                            print(f"Warning: Skipping file {apl_name}: Unknown format.")
                        return
                    jam_file = whole_content[:jar_pos if gif_pos == -1 else gif_pos]
                    jar_file = whole_content[jar_pos:]
                    jam_size = len(jam_file)
                    jar_size = len(jar_file)
                    sdf_size = 0
                elif valid_offset != 0:
                    # Fetch data
                    jam_file = apl_file.read(jam_size)
                    sdf_file = apl_file.read(sdf_size)
                    unknown1_file = apl_file.read(unknown_size1)
                    for idx, extra_size in enumerate(extra_sizes):
                        extra_file = apl_file.read(extra_size)
                    icon160_file = apl_file.read(icon160_size)
                    icon48_file = apl_file.read(icon48_size)
                    jar_file = apl_file.read(jar_size)
                
                # Decode and validate JAM file
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
                
                # Get props as kv map
                jam_props = parse_props_plaintext(jam_file, verbose=verbose)
                
                if valid_offset == 0:
                    # Filter out SDF fields
                    jam_props, sdf_props = filter_sdf_fields(jam_props)
                    jam_file = fmt_plaintext_jam(jam_props)
                    sdf_file = fmt_plaintext_jam(sdf_props).encode()
                    sdf_size = len(sdf_file)
                
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
                            print(f"Warning: No valid app name found in {apl_file_path}. Using base name.")
                        app_name = apl_name

                # Handle duplicate app names
                if os.path.exists(os.path.join(target_directory, f"{app_name}.jam")):
                    if verbose:
                        print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                    app_name = f"{app_name}_{self.duplicate_count + 1}"
                    self.duplicate_count += 1

                # Check if there is an SCP file with the same name
                scp_file_path = os.path.join(os.path.dirname(apl_file_path), f"{apl_name}.scp")
                if os.path.exists(scp_file_path):
                    sp_sizes = jam_props.get('SPsize', '').split(',')
                    sp_sizes = [int(sp_size) for sp_size in sp_sizes if sp_size.isdigit()]
                    header = fmt_spsize_header(sp_sizes)
                    with open(scp_file_path, 'rb') as scp_file:
                        with open(os.path.join(target_directory, f"{app_name}.sp"), 'wb') as f:
                            f.write(header)
                            f.write(scp_file.read())

                # Write files
                if jam_size > 0:
                    with open(os.path.join(target_directory, f"{app_name}.jam"), 'w', encoding=used_encoding) as f:
                        f.write(jam_file)

                if sdf_size > 0:
                    with open(os.path.join(target_directory, f"{app_name}.sdf"), 'wb') as f:
                        f.write(sdf_file)

                if jar_size > 0:
                    with open(os.path.join(target_directory, f"{app_name}.jar"), 'wb') as f:
                        f.write(jar_file)

                if verbose:
                    print(f"Processed: {apl_name} -> {app_name}\n")

        # List all files
        files = os.listdir(top_folder_directory)

        # Process APL files
        apl_files = [f for f in files if f.lower().endswith('.apl')]

        for apl_file in apl_files:
            apl_file_path = os.path.join(top_folder_directory, apl_file)
            process_file(apl_file_path)

    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of SH type.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        files = os.listdir(top_folder_directory)
        subdirectories = [f for f in files if os.path.isdir(os.path.join(top_folder_directory, f))]
        if subdirectories:
            return None

        apl_scp_files = [f for f in files if f.lower().endswith('.apl') or f.lower().endswith('.scp')]
        if not apl_scp_files:
            return None

        return "SH"
