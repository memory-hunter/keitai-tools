from abc import ABC, abstractmethod

class PhoneType(ABC):
    """
    An abstract class to represent a phone type with its extraction method.
    """

    @abstractmethod
    def extract(self, top_folder_directory, verbose=False):
        """
        Abstract method to extract phone type from the top folder directory.
        
        :param top_folder_directory: Top folder directory to extract games from.
        """
        ...