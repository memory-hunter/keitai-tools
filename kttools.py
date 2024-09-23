from phonetypes.DFType import DFType
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
    phone_types = [DFType()]
    
    test_result = False
    
    for phone_type in phone_types:
        test_result = phone_type.test_structure(args.top_folder_directory, verbose=args.verbose)
        if test_result:
            break
        
    if not test_result:
        print(f"Top folder directory {args.top_folder_directory} does not seem to be of any type phone. Quitting.")
        return
    
    print(f"Extracting from {args.top_folder_directory}\n")
    
    # Extract the games from the top folder directory
    DFType().extract(os.path.abspath(args.top_folder_directory), verbose=args.verbose)

if __name__ == '__main__':
    main()