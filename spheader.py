# import re
# import sys
# import os
# import codecs

# def create_header_sp(sp_sizes):
#     header = bytearray()
#     for size in sp_sizes:
#         header += size.to_bytes(4, byteorder='little')
#     while len(header) < 64:
#         header += bytes([255])
#     return header

# def main():
#     if len(sys.argv) != 3:
#         print("Usage: python " + sys.argv[0] + " input.jam input.sp")
#         return

#     jam_filename = sys.argv[1]
#     sp_filename = sys.argv[2]

#     if not os.path.isfile(jam_filename):
#         print(f"{jam_filename} not found.")
#         return

#     with codecs.open(jam_filename, "r", encoding="shift-jis") as jam_file:
#         jam_contents = jam_file.read()

#         sp_size_match = re.search(r'SPsize\s*=\s*([\d,]+)', jam_contents)
#         if sp_size_match:
#             sp_size_str = sp_size_match.group(1)
#             sp_sizes = [int(size) for size in sp_size_str.split(',')]
#             header = create_header_sp(sp_sizes)
#             print(f"SPsize: {sp_sizes}")
#         else:
#             print("Not a valid .jam file. SPsize not found.")
#             return

#     with open(sp_filename, "rb") as sp_file:
#         sp_contents = sp_file.read()

#     with open(sp_filename, "wb") as output_file:
#         output_file.write(header + sp_contents)

#     print(f"Header created and saved to {sp_filename}")

# if __name__ == "__main__":
#     main()

import re
import sys
import os
import codecs

def create_header_sp(sp_sizes):
    header = bytearray()
    for size in sp_sizes:
        header += size.to_bytes(4, byteorder='little')
    while len(header) < 64:
        header += bytes([255])
    return header

def process_jam(jam_filename):
    sp_filename = os.path.splitext(jam_filename)[0] + ".sp"

    if not os.path.isfile(jam_filename):
        print(f"{jam_filename} not found.")
        return

    with codecs.open(jam_filename, "r", encoding="shift-jis") as jam_file:
        jam_contents = jam_file.read()

        sp_size_match = re.search(r'SPsize\s*=\s*([\d,]+)', jam_contents)
        if sp_size_match:
            sp_size_str = sp_size_match.group(1)
            sp_sizes = [int(size) for size in sp_size_str.split(',')]
            header = create_header_sp(sp_sizes)
            print(f"SPsize: {sp_sizes}")
        else:
            print(f"Not a valid .jam file: {jam_filename}. SPsize not found.")
            return

    with open(sp_filename, "rb") as sp_file:
        sp_contents = sp_file.read()

    with open(sp_filename, "wb") as output_file:
        output_file.write(header + sp_contents)

    print(f"Header created and saved to {sp_filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python " + sys.argv[0] + " input.jam [input2.jam ...]")
        return

    for jam_filename in sys.argv[1:]:
        process_jam(jam_filename)

if __name__ == "__main__":
    main()
