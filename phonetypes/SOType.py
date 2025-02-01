from phonetypes.PhoneType import PhoneType
from util.jam_utils import find_plausible_keywords_for_validity
from util.structure_utils import create_target_folder
import os

class SOType(PhoneType):
    """
    A class to represent a SH phone type of structure with its extraction method.

    Description:
    - Top folder contains folders new and old, with files of .dat, .jar and .scr with the same name in the root directory.
    - .jar, and .sp file has custom stuff intermingled (header + footer + oob in between, needs removal).
    
    """

    def extract(self, top_folder_directory, verbose=False):
        """
        Extract games from the top folder directory in a SO phone file structure.

        :param top_folder_directory: Top folder directory to extract games from.
        """
         # first parse dat, get sizes and content of it, i think it has jam
        # then check garb removal on sp, if size match, ok
        # remove garbage from jar
        # rename all as usual
        
        # do the same for new and old folder contents, in output, it should be also in new and old folders
        
        # can get sp size from sp to match header + footer removal sizes
        
        # need to add the garbage remover in utils (header + footer + oob)
        
        # need to add SO offsets to the utils
        # Create the target directory at the same level as the top folder directory
        target_directory = create_target_folder(top_folder_directory)
        
        def process_triplet(name, target_folder):
            if verbose:
                print('-' * 80)
            dat_path = os.path.join(top_folder_directory, f"{name}.dat")
            jar_path = os.path.join(top_folder_directory, f"{name}.jar")
            if not os.path.isfile(jar_path):
                if verbose:
                        print(f"Warning: {name} does not have .jar file. Skipping.\n")
                return
            scr_path = os.path.join(top_folder_directory, f"{name}.scr")
            
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
                jam_size = 0
                for _ in range(5):
                    indent = offset + jam_size
                    print(f"{jam_size:X}")
                    # "any" etc may occasionally be inserted, causing the indent to shift
                    # check if next 3 bytes are "any"
                    if dat_content[indent:indent + 3] == b"any":
                        indent += 3
                    indent += 2
                    print(f"Trying offset 0x{indent:X}")
                    jam_size = int.from_bytes(dat_content[indent - 2 : indent], "little") - 0x4000
                    print(f"{jam_size:X}")
                    jam_content = dat_content[indent : indent + jam_size] # plaintext
                    print(jam_content[:30])
                    if jam_size > 0x30 and find_plausible_keywords_for_validity(jam_content):
                        ok = True
                        break
                else:
                    if verbose:
                        print(f"Warning: 0x{offset:X} is not a valid offset for {name}. Trying next offset.")
                if ok:
                    break
            else:
                if verbose:
                    print(f"Warning: {name} does not contain a valid JAM file. Skipping.")
                return
            return
            #raise Exception("Continue doing this")
            
        for file in os.listdir(top_folder_directory):
            if file.endswith('.dat'):
                process_triplet(os.path.splitext(file)[0], target_directory)
            
        for folder in ['new', 'old']:
            for file in os.listdir(os.path.join(top_folder_directory, folder)):
                if file.endswith('.dat'):
                    process_triplet(os.path.splitext(file)[0], os.path.join(target_directory, folder))
       
        """
        For the Sony phone's JAR and SP, @Irdkwia discovered that they have a 0x20 byte header, a 0x13 byte footer, and 0x2 bytes of garbage every 0x4000 bytes!!
He and I then worked up a conversion script! If the JAR is corrupted, a warning message will be displayed, so check the log.
(Note that for SO903iTV, the JAM start offset is different and -s 0xD44 is required.)
        
        """
        
        raise Exception("TODO HEHEHEH!")

    def test_structure(self, top_folder_directory):
        """
        Test if the top folder directory is of a SO phone file structure.

        :param top_folder_directory: Top folder directory to test.
        :return: True if the top folder directory is of a SO phone file structure, False otherwise.
        """
        # check if folders new and old exist
        if not os.path.exists(os.path.join(top_folder_directory, 'new')) or not os.path.exists(os.path.join(top_folder_directory, 'old')):
            return None
        
        # check at least one .dat, .jar, .scr files with same name exist in the root dir (000.dat, 000.jar, 000.scr)
        for file in os.listdir(top_folder_directory):
            if file.endswith('.dat'):
                if os.path.exists(os.path.join(top_folder_directory, file.replace('.dat', '.jar'))) or os.path.exists(os.path.join(top_folder_directory, file.replace('.dat', '.scr'))):
                    return "SO"
        
        return None
