from phonetypes.DFType import DFType
import os
import argparse

def main():
    # Parse command line arguments to get the top folder directory, verbose flag or help
    parser = argparse.ArgumentParser(description='Process a directory containing a raw top level folder with keitai apps. Outputs files in emulator import ready format.')
    parser.add_argument('top_folder_directory', help='The top folder directory containing the keitai apps.')
    parser.add_argument('--verbose', action='store_true', help='Print more information.')
    args = parser.parse_args()
    
    # Create a D or F phone type object
    phone_type = DFType()
    
    print(f"Verbose mode is {'on' if args.verbose else 'off'}")
    print(f"Extracting from {args.top_folder_directory}\n")
    
    # Extract the games from the top folder directory
    phone_type.extract(os.path.abspath(args.top_folder_directory), verbose=args.verbose)

if __name__ == '__main__':
    main()