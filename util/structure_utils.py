import os

def create_target_folder(top_folder_directory):
    # Create the target directory at the same level as the top folder directory
    target_directory = os.path.join(os.path.dirname(top_folder_directory), 'output')
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    return target_directory

def inject_jam_into_folder(java_folder_path, id, jam_file, verbose=False):
    # Find folder with id filled upto two digits and insert as 'jam'
    if not os.path.exists(java_folder_path):
        if verbose:
            print("ERROR: Java folder path not valid. Exiting.")
        raise Exception("Invalid Java folder path.")
    if not os.path.exists(os.path.join(java_folder_path, f"{int(id):02}")):
        if verbose:
            print(f"WARNING: Folder with ID {id} doesn't exist. Skipping.")
        return
    with open(os.path.join(java_folder_path, f"{int(id):02}", "jam"), "w", encoding="cp932") as f:
        f.write(jam_file)
    if verbose:
        print(f"Injected JAM into folder {id}.")