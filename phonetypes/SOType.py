from phonetypes.PhoneType import PhoneType
import os

class SOType(PhoneType):
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
        raise Exception("TODO HEHEHEH!")

    def test_structure(self, top_folder_directory):
        """
        Test if the top folder directory is of a SO phone file structure.

        :param top_folder_directory: Top folder directory to test.
        :return: True if the top folder directory is of a SH phone file structure, False otherwise.
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
