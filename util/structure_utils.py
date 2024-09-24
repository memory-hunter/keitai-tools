import os

def create_target_folder(top_folder_directory):
    # Create the target directory at the same level as the top folder directory
    target_directory = os.path.join(os.path.dirname(top_folder_directory), 'output')
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    return target_directory