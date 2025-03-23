# This script will read root.rdb, root.rdx and the corresponding .fdata file to
# creates a .file_metadata.json file.  Run in the /Atelier Yumia/Motor/ folder.
# It will ask for the filenames of the files (usually the hash plus an extension).
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import struct, base64, json, os, sys
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

def find_file_metadata_in_rdb (target_filehash, rdb_file = 'root.rdb'):
    r_metadata = b''
    with open(rdb_file, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0x20,0)
        while f.tell() < eof:
            start = f.tell()
            magic = f.read(4)
            assert magic == b'IDRK'
            version, entry_size, string_size, file_size = struct.unpack("<I3Q", f.read(28))
            entry_type, file_hash, tkid, flags = struct.unpack("<4I", f.read(16))
            if not file_hash == target_filehash:
                f.seek(start + entry_size + 4 - (entry_size % 4))
            else:
                r_metadata = f.read(entry_size - 0x3D)
                footer = struct.unpack("<H2IHI", f.read(16))
                break
    return(tkid, string_size, footer, r_metadata)

def find_fdata_file (fdata_index, rdx_file = 'root.rdx'):
    with open(rdx_file, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0)
        success = False
        while f.tell() < eof:
            marker, ff, fdata_hash = struct.unpack("<2hI", f.read(8))
            if marker == fdata_index:
                success = True
                break
    if not success:
        return("")
    else:
        return('0x{}.fdata'.format(str(hex(fdata_hash))[2:].zfill(8)))

def find_file_metadata_in_fdata(fdata_file, offset):
    with open(fdata_file, 'rb') as f:
        f.seek(offset)
        magic = f.read(8)
        assert magic == b'IDRK0000'
        entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
        entry_type, filehash, filetkid, flags = struct.unpack("<4I", f.read(16))
        f_metadata = f.read(entry_size - cmp_size - 0x30)
        return(f_metadata)

def retrieve_file_metadata(target_filehash, rdb_file = 'root.rdb', rdx_file = 'root.rdx'):
    tkid, string_size, footer, r_metadata = find_file_metadata_in_rdb(target_filehash, rdb_file = rdb_file)
    if footer[0] == 1025:
        fdata_file = find_fdata_file (footer[3], rdx_file = rdx_file)
        f_metadata = find_file_metadata_in_fdata(fdata_file, footer[1])
        metadata = {'name_hash': target_filehash, 'tkid_hash': tkid, 'string_size': string_size,\
            'f_extradata': base64.b64encode(f_metadata).decode(),\
            'r_extradata': base64.b64encode(r_metadata).decode()}
        with open('{}.file_metadata.json'.format(str(hex(target_filehash))[2:].zfill(8)), 'wb') as f:
            f.write(json.dumps(metadata, indent = 4).encode())

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    target_filehash = -1
    while target_filehash == -1:
        raw_hash = input("What hash are you looking for? [Omit the '0x', type only the 8 hex digits] ")
        try:
            target_filehash = int(raw_hash, 16)
        except:
            print("Invalid entry!")
    retrieve_file_metadata(target_filehash)