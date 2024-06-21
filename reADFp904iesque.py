import sys
import os

def remove_adf_header(adf_file):
    return adf_file[0x9B4:]

def rename_folders(adf_folder, jar_folder, sp_folder):
    for folder, extension in [(adf_folder, 'jam'), (jar_folder, 'jar'), (sp_folder, 'sp')]:
        for filename in os.listdir(folder):
            os.rename(os.path.join(folder, filename), os.path.join(folder, f"{filename}.{extension}"))
            
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python3 {sys.argv[0]} adf_folder jar_folder sp_folder")
        exit(-1)
    adf_folder = sys.argv[1]
    jar_folder = sys.argv[2]
    sp_folder = sys.argv[3]
    if not os.path.isdir(adf_folder):
        print(f"{adf_folder} is not a directory")
        exit(1)
    if not os.path.isdir(jar_folder):
        print(f"{jar_folder} is not a directory")
        exit(1)
    if not os.path.isdir(sp_folder):
        print(f"{sp_folder} is not a directory")
        exit(1)
    rename_folders(adf_folder, jar_folder, sp_folder)

    for filename in os.listdir(adf_folder):
        with open(os.path.join(adf_folder, filename), "rb") as f:
            data = f.read()
        with open(os.path.join(adf_folder, filename), "wb") as f:
            f.write(remove_adf_header(data))
            