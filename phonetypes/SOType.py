from phonetypes.PhoneType import PhoneType
from util.jam_utils import find_plausible_keywords_for_validity, parse_props_plaintext, parse_valid_name, remove_garbage_so, fmt_spsize_header
from util.structure_utils import create_target_folder
from util.verify import verify_jar, verify_sp
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
            is_valid_jam = False
            if not find_plausible_keywords_for_validity(dat_content):
                if verbose:
                    print(f"Warning: {name}.dat does not contain all required JAM keywords. Skipping.\n")
                return
            else:
                is_valid_jam = True
            
            ok = False
            is_so906i = False
            for offset in self.so_type_offsets:
                jam_size = 0
                indent = offset
                
                # Sometimes unrelated elements such as "any" are inserted, causing the starting position to shift.
                for _ in range(5):
                    jam_size = int.from_bytes(dat_content[indent - 2 : indent], "little") - 0x4000
                    jam_content = dat_content[indent : indent + jam_size] # plaintext
                    
                    try:
                        jam_content.decode("cp932")
                    except:
                        indent += jam_size + 2
                        continue
                    
                    if not find_plausible_keywords_for_validity(jam_content):
                        indent += jam_size + 2
                        continue
                    
                    ok = True
                    if offset == 0xF84:
                        is_so906i = True
                    break
                
                if ok:
                    if verbose:
                        print(f"The JAM offset is 0x{offset:X}")
                    break
            else:
                if verbose:
                    print(f"Tried all of the following offsets without success: {[hex(off) for off in self.so_type_offsets]}")
                    if is_valid_jam:
                        print(f'!!! Warning: minimal JAM keywords found in {name}.dat. please report to KeitaiWiki. !!!\n')
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
                    print(f"Warning: Could not read JAM file for {name}.dat. Skipping.\n")
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
            
            
            # Extract JAR and SP
            jar_data = None
            if os.path.exists(jar_path):
                if is_so906i:
                    jar_data = open(jar_path, 'rb').read() 
                else:
                    jar_data = remove_garbage_so(open(jar_path, 'rb').read())
                
                if not verify_jar(jar_data):
                    if verbose:
                        print("!!! Aborted: The JAR is corrupted. !!!")
                    return
            
            sp_data = None
            if os.path.exists(scr_path):
                sp_size_list = jam_props['SPsize'].split(',')
                sp_size_list = [int(sp_size) for sp_size in sp_size_list]
                
                with open(scr_path, "rb")as f:
                    scr_data = f.read() 
                
                header_type = scr_data[0x1E]
                if header_type in [0]:
                    sp_data = remove_garbage_so(open(scr_path, 'rb').read())
                elif header_type in [1, 2]:
                    sp_data = remove_garbage_so(open(scr_path, 'rb').read(), header=0x20+0x17)
                else:
                    sp_data = remove_garbage_so(open(scr_path, 'rb').read())
                
                if not verify_sp(len(sp_data), jam_props['SPsize']):
                    if verbose:
                        print(f"!!! Warning: The size of the SP is different from the description in JAM. ({len(sp_data)} bytes, JAM={sum(sp_size_list)} bytes, {header_type=}) !!!\n")
            
            # Write files
            # Check there is no duplicate app name existing in the target directory
            duplicate_count = 0
            temp_app_name = app_name
            while True:
                if not os.path.exists(os.path.join(target_directory, f"{temp_app_name}.jam")):
                    break
                temp_app_name = f"{app_name}_({duplicate_count+1})"
                duplicate_count += 1
            
            if duplicate_count > 0 and verbose:
                print(f'INFO: The file name "{app_name}.jam" already exists in the output folder, so it will be changed.')
            
            app_name = temp_app_name
            
            new_jam_path = os.path.join(target_directory, app_name+".jam")
            with open(new_jam_path, 'w', encoding=used_encoding) as f:
                f.write(jam_file)
                
            if jar_data:
                new_jar_path = os.path.join(target_directory, app_name+".jar")
                with open(new_jar_path, 'wb') as f:
                    f.write(jar_data)
            else:
                if verbose:
                    print(f"Warning: {name} doesn't have a JAR file. Skipping.")
                    return
            
            if sp_data:
                sp_path = os.path.join(target_directory, app_name+".sp")
                with open(sp_path, 'wb') as f:
                    sp_header = fmt_spsize_header(sp_size_list)
                    f.write(sp_header)
                    f.write(sp_data)
            if verbose:
                print(f'Filename: "{name}" -> "{app_name}"\n')
        
        # Main loop
        
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        for file in os.listdir(top_folder_directory):
            if file.endswith('.dat'):
                if verbose:
                    print('-' * 80)
                    print(f"[{file}]")
                process_triplet(os.path.splitext(file)[0], top_folder_directory)
            
        for folder in ['new', 'old']:
            subdir = os.path.join(top_folder_directory, folder)
            if os.path.exists(subdir):
                for file in os.listdir(subdir):
                    if file.endswith('.dat'):
                        if verbose:
                            print('-' * 80)
                            print(f"[{folder}/{file}]")
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
