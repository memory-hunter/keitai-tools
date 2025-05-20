from phonetypes.PhoneType import PhoneType
from util.jam_utils import find_plausible_keywords_for_validity, parse_props_plaintext, parse_valid_name, remove_garbage_so, fmt_spsize_header
from util.structure_utils import create_target_folder
import os

class SOType(PhoneType):
    """
    A class to represent a SH phone type of structure with its extraction method.

    Description:
    - Top folder contains folders new and old (optional), with files of .dat, .jar and .scr with the same name in the root directory.
    - .jar, and .sp file has custom stuff intermingled (header + footer + oob in between, needs removal).
    
    """

    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a SO phone file structure.

        :param top_folder_directory: Top folder directory to extract games from.
        """
        
        def process_triplet(name, target_folder):
            if verbose:
                print('-' * 80)
            dat_path = os.path.join(target_folder, f"{name}.dat")
            jar_path = os.path.join(target_folder, f"{name}.jar")
            if not os.path.isfile(jar_path):
                if verbose:
                        print(f"Warning: {name} does not have .jar file. Skipping.\n")
                return
            scr_path = os.path.join(target_folder, f"{name}.scr")
            
            with open(dat_path, 'rb') as file:
                dat_content = file.read()
                
            # Verify if valid keywords are present
            if not find_plausible_keywords_for_validity(dat_content):
                if verbose:
                    print(f"Warning: {name} does not contain all required keywords. Skipping.\n")
                return
            else:
                if verbose:
                    print(f"Warning: minimal keywords found in {name}. If it still fails to detect any JAM, please report to KeitaiWiki.\n")
            
            ok = False
            for offset in self.so_type_offsets:
                if verbose:
                    print(f"Trying offset 0x{offset:X}")
                jam_size = 0
                indent = offset + jam_size
                for i in range(5):
                    indent = indent + jam_size
                    # "any" etc may occasionally be inserted, causing the indent to shift
                    # check if next 3 bytes are "any"
                    if dat_content[indent:indent + 3] == b"any":
                        indent += 3
                        i-=1
                        continue
                    indent += 2
                    jam_size = int.from_bytes(dat_content[indent - 2 : indent], "little") - 0x4000
                    jam_content = dat_content[indent : indent + jam_size] # plaintext
                    if jam_size > 0x30 and find_plausible_keywords_for_validity(jam_content):
                        ok = True
                        break
                else:
                    if verbose:
                        print(f"Warning: 0x{offset:X} is not a valid offset for {name}. Trying next offset.")
                if ok:
                    if verbose:
                        print(f"Using offset 0x{offset:X} as it seems to be the useful one.\n")
                    break
            else:
                if verbose:
                    print(f"Warning: {name} does not contain a valid JAM file. Skipping.")
                return
            
            jam_file = None
            for encoding in self.encodings:
                try:
                    jam_file = jam_content.decode(encoding)
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    if verbose:
                        print(f"Warning: UnicodeDecodeError with {encoding}. Trying next encoding.")
            else:
                if verbose:
                    print(f"Warning: Could not read JAM file for {name}. Skipping.\n")
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
                        print(f"Warning: No valid app name found in {name}. Using base folder name.")
                        app_name = f'{os.path.basename(name)}'
            
            # Extract JAR and SP and write files
            # Check there is no duplicate app name existing in the target directory
            if os.path.exists(os.path.join(target_folder, app_name+".jam")):
                if verbose:
                    print(f"Warning: {app_name}.jam already exists in {target_directory}.")
                app_name = f"{app_name}_{self.duplicate_count+1}"
                self.duplicate_count += 1 
            new_jam_path = os.path.join(target_directory, app_name+".jam")
            with open(new_jam_path, 'w', encoding=used_encoding) as f:
                f.write(jam_file)
                
            if os.path.exists(jar_path):
                jar_data = remove_garbage_so(open(jar_path, 'rb').read())
                new_jar_path = os.path.join(target_directory, app_name+".jar")
                with open(new_jar_path, 'wb') as f:
                    f.write(jar_data)
            else:
                if verbose:
                    print(f"Warning: {name} doesn't have a JAR file. Skipping.")
                    return
            
            if os.path.exists(scr_path):
                sp_data = remove_garbage_so(open(scr_path, 'rb').read())
                sp_path = os.path.join(target_directory, app_name+".sp")
                with open(sp_path, 'wb') as f:
                    sp_size_list = jam_props['SPsize'].split(',')
                    sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                    header = fmt_spsize_header(sp_size_list)
                    f.write(fmt_spsize_header(header))
                    f.write(sp_data)
                
            if verbose:
                print(f"Processed: {name} -> {app_name}\n")
        
        # Main loop
        
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        for file in os.listdir(top_folder_directory):
            if file.endswith('.dat'):
                process_triplet(os.path.splitext(file)[0], top_folder_directory)
            
        for folder in ['new', 'old']:
            subdir = os.path.join(top_folder_directory, folder)
            if os.path.exists(subdir):
                for file in os.listdir(subdir):
                    if file.endswith('.dat'):
                        print(file)
                        process_triplet(os.path.splitext(file)[0], subdir)

    def test_structure(self, top_folder_directory):
        """
        Test if the top folder directory is of a SO phone file structure.

        :param top_folder_directory: Top folder directory to test.
        :return: True if the top folder directory is of a SO phone file structure, False otherwise.
        """
        # check at least one .dat, .jar, .scr files with same name exist in the root dir (000.dat, 000.jar, 000.scr)
        for file in os.listdir(top_folder_directory):
            if file.endswith('.dat'):
                if os.path.exists(os.path.join(top_folder_directory, file.replace('.dat', '.jar'))) or os.path.exists(os.path.join(top_folder_directory, file.replace('.dat', '.scr'))):
                    return "SO"
        
        return None
