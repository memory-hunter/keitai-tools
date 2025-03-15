import os
import argparse
from util.postprocess import post_process_SIMPLE_games, post_process_konami_name_in_qs
from phonetypes import DFType, SHType, Null3FolderType, ModernNType, NullPlain3FolderType, NullPlain3FolderCSPType, ModernPType, SOType

PHONE_TYPES = {
    "D/F": DFType.DFType,
    "SH": SHType.SHType,
    "Null3Folder": Null3FolderType.Null3FolderType,
    "ModernN": ModernNType.ModernNType,
    "NullPlain3Folder": NullPlain3FolderType.NullPlain3FolderType,
    "NullPlain3FolderCSP": NullPlain3FolderCSPType.NullPlain3FolderCSPType,
    "ModernP": ModernPType.ModernPType,
    "SO": SOType.SOType
}

POSTPROCESS_OPTIONS = {
    (post_process_SIMPLE_games, "Rename SIMPLE games (use if you see many 'dljar' files)"),
    (post_process_konami_name_in_qs, "Rename Konami games by using the 'appliname' field in the link"),
}

def get_phone_type(directory):
    for name, cls in PHONE_TYPES.items():
        if cls().test_structure(directory):
            return name, cls()
    return None, None

def main():
    parser = argparse.ArgumentParser(description='Process a directory of keitai apps into emulator-ready format.')
    parser.add_argument('top_folder_directory', help='Top folder directory containing keitai apps.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode.')
    args = parser.parse_args()

    print(f"Verbose mode is {'on' if args.verbose else 'off'}")

    phone_type_name, phone_type_instance = get_phone_type(args.top_folder_directory)
    if not phone_type_instance:
        print(f"Directory {args.top_folder_directory} does not match any known phone type. Quitting")
        return

    print(f"Detected phone type: {phone_type_name}. Extracting...")
    phone_type_instance.extract(os.path.abspath(args.top_folder_directory), verbose=args.verbose)

    output_folder = os.path.abspath(os.path.join(args.top_folder_directory, os.pardir, 'output'))
    options_string = "\n".join([f"{key}. {desc}" for key, (_, desc) in POSTPROCESS_OPTIONS.items()])
    print(f"""Postprocessing options:\n{options_string}\n""")
    postprocess_choice = input("Enter the number of the postprocessing option you want to use or 'q' to quit: ")
    if postprocess_choice in POSTPROCESS_OPTIONS:
        func, _ = POSTPROCESS_OPTIONS[postprocess_choice]
        func(output_folder, verbose=args.verbose)
    elif postprocess_choice == 'q':
        print("Quitting.")
    else:
        print("Invalid choice. Quitting.")

if __name__ == '__main__':
    main()
