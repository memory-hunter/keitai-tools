from phonetypes.DFType import DFType
from phonetypes.SHType import SHType
from phonetypes.Null3FolderType import Null3FolderType
from phonetypes.ModernNType import ModernNType
from phonetypes.NullPlain3FolderType import NullPlain3FolderType
from phonetypes.ModernPType import ModernPType
from util.postprocess import *
import os
import argparse

def main():
    # Parse command line arguments to get the top folder directory, verbose flag or help
    parser = argparse.ArgumentParser(description='Process a directory containing a raw top level folder with keitai apps. Outputs files in emulator import ready format.')
    parser.add_argument('top_folder_directory', help='The top folder directory containing the keitai apps.')
    parser.add_argument('--verbose', action='store_true', help='Print more information.')
    args = parser.parse_args()
    
    print(f"Verbose mode is {'on' if args.verbose else 'off'}")
    
    # Testing the structure of the top folder directory to see which phone type it is
    phone_types = [DFType(), SHType(), Null3FolderType(), ModernNType(), NullPlain3FolderType(), ModernPType()]
    
    test_result = False
    
    for phone_type in phone_types:
        test_result = phone_type.test_structure(args.top_folder_directory)
        if test_result:
            print(f"Top folder directory {args.top_folder_directory} seems to be of {test_result} phone type.")
            break
        
    if not test_result:
        print(f"Top folder directory {args.top_folder_directory} does not seem to be of any type phone. Quitting.")
        return
    
    print(f"Extracting from {args.top_folder_directory}\n")
    
    # Extract the games from the top folder directory
    phone_type = None
    if test_result == "D/F":
        phone_type = DFType()
    elif test_result == "SH":
        phone_type = SHType()
    elif test_result == "Null3Folder":
        phone_type = Null3FolderType()
    elif test_result == "ModernN":
        phone_type = ModernNType()
    elif test_result == "NullPlain3Folder":
        phone_type = NullPlain3FolderType()
    elif test_result == "ModernP":
        phone_type = ModernPType()
    phone_type.extract(os.path.abspath(args.top_folder_directory), verbose=args.verbose)

    # Give options for postprocessing
    print("""Postprocessing options:
    1. Rename SIMPLE games (use if you see lots of 'dljar' containing files)
""")
    output_folder = os.path.abspath(os.path.join(args.top_folder_directory, os.pardir, 'output'))
    postprocess_choice = input("Enter the number of the postprocessing option you want to use or 'q' to quit: ")
    if postprocess_choice == '1':
        post_process_SIMPLE_games(output_folder, verbose=args.verbose)
    elif postprocess_choice == 'q':
        print("Quitting.")
        return
    else:
        print("Invalid choice. Quitting.")
        return
if __name__ == '__main__':
    main()