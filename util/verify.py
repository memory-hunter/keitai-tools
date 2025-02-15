import zipfile
import io

def verify_jar(jar_data):
    if jar_data[0:4] != b"PK\x03\x04":
        return False
    
    try:
        with io.BytesIO(jar_data) as jar_stream, zipfile.ZipFile(jar_stream, "r") as f:
            return f.testzip() is None
    except zipfile.BadZipFile:
        return False

def verify_sp(spsize, jam_spsize_str):
    jam_spsize = sum([int(n) for n in jam_spsize_str.split(",")])
    return spsize == jam_spsize