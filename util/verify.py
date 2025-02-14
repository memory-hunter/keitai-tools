import zipfile
import io

def verify_jar(jar_data):
    if jar_data[0:4] != b"PK\x03\x04":
        return False
    
    jar_stream = io.BytesIO(jar_data)
    
    with zipfile.ZipFile(jar_stream, "r") as f:
        return f.testzip() is None

def verify_sp(spsize, jam_spsize_str):
    jam_spsize = sum([int(n) for n in jam_spsize_str.split(",")])
    return spsize == jam_spsize