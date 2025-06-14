from util.constants import *
from abc import ABC, abstractmethod

class PhoneType(ABC):
    """
    An abstract class to represent a phone type with its extraction method.
    """
    
    def __init__(self):
        """
        Initialize the phone type.
        """
        self.duplicate_count = 0
        self.encodings = ENCODINGS
        self.null_type_offsets = NULL_TYPE_OFFSETS
        self.plaintext_cutoff_offsets = PLAINTEXT_CUTOFF_OFFSETS
        self.sh_type_offsets = SH_TYPE_OFFSETS
        self.so_type_offsets = SO_TYPE_OFFSETS
        self.so_no_garb_offsets = SO_NO_GARB

    @abstractmethod
    def extract(self, top_folder_directory, verbose=False):
        """
        Abstract method to extract phone type from the top folder directory.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        ...
    
    @staticmethod
    @abstractmethod
    def test_structure(self, top_folder_directory):
        """
        Abstract method to test the structure of the top folder directory to see if it is of corresponding phone type.
        
        :param top_folder_directory: Top folder directory to test the structure of.
        """
        ...