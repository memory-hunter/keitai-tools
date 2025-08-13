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
        pass
    
    def test_structure(self, top_folder_directory):
        """
        Test the structure of the top folder directory to see if it is of M type phone file structure type.
        
        :param top_folder_directory: Top folder directory to test the structure of.
        """
        pass