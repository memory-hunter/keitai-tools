import os
import sys
import shutil

def process_subdirectories(main_dir):
    # Check if the provided path is a directory
    if not os.path.isdir(main_dir):
        print(f"Error: {main_dir} is not a directory")
        return

    # Loop through each subdirectory in the main directory
    for sub_dir in os.listdir(main_dir):
        sub_dir_path = os.path.join(main_dir, sub_dir)
        
        if os.path.isdir(sub_dir_path):
            # List all files starting with "sp" in the subdirectory
            sp_files = [f for f in os.listdir(sub_dir_path) if f.startswith("sp")]

            if sp_files:
                # Create the path for the "out" file
                out_file_path = os.path.join(sub_dir_path, "out")

                # Concatenate the contents of all "sp" files into "out"
                with open(out_file_path, 'wb') as out_file:
                    for sp_file in sp_files:
                        sp_file_path = os.path.join(sub_dir_path, sp_file)
                        with open(sp_file_path, 'rb') as file:
                            shutil.copyfileobj(file, out_file)

                # Remove the original "sp" files
                for sp_file in sp_files:
                    os.remove(os.path.join(sub_dir_path, sp_file))

                # Rename "out" to "sp"
                sp_file_path = os.path.join(sub_dir_path, "sp")
                os.rename(out_file_path, sp_file_path)

if __name__ == "__main__":
    # Check if a directory is provided as an argument
    if len(sys.argv) != 2:
        print("Usage: python", sys.argv[0], "<directory>", )
        sys.exit(1)

    main_directory = sys.argv[1]
    process_subdirectories(main_directory)
