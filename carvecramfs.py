import sys
import os

def main():
    input_file = sys.argv[1]
    input_dir = os.path.dirname(input_file)

    with open(input_file, "rb") as inf:
        data = inf.read()

    off = -1
    while True:
        off = data.find(b"Compressed ROMFS", off+1)
        if off == -1:
            break
        start = off - 16
        hdr = data[start:start+4]
        assert hdr == b"\x45\x3D\xCD\x28"

        sz = int.from_bytes(data[start+4:start+8], byteorder="little")

        name = "cramfs_{:08X}.bin".format(start)
        output_path = os.path.join(input_dir, name)
        
        with open(output_path, "wb") as outf:
            outf.write(data[start:start+sz])
        print(f"Extracted: {name}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file>")
        sys.exit(1)
    main()
    
    # thanks to xyz and claude <3