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
    idrk_header_size = 0x30
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
                if not (entry_size % 4 == 0):
                    f.seek(start + entry_size + 4 - (entry_size % 4))
                else:
                    f.seek(start + entry_size)
            else:
                r_metadata = f.read(entry_size - (string_size + idrk_header_size))
                footer = [struct.unpack("<H", f.read(2))[0]]
                if string_size == 0x11:
                    extra, = struct.unpack("<I", f.read(4))
                footer.extend(list(struct.unpack("<2IH", f.read(10))))
                if string_size == 0x11:
                    footer[1] += (extra & 0xFF) << 2**5
                break
    return(entry_type, tkid, string_size, footer, r_metadata)

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

def find_file_metadata(target_filehash, rdb_file = 'root.rdb', rdx_file = 'root.rdx', file_folder = 'data'):
    entry_type, tkid, string_size, footer, r_metadata = find_file_metadata_in_rdb(target_filehash, rdb_file = rdb_file)
    if footer[0] == 1025:
        fdata_file = find_fdata_file (footer[3], rdx_file = rdx_file)
        f_metadata = find_file_metadata_in_fdata(fdata_file, footer[1])
        return({'name_hash': target_filehash, 'tkid_hash': tkid,\
            'entry_type': entry_type, 'string_size': string_size,\
            'f_extradata': base64.b64encode(f_metadata).decode(),\
            'r_extradata': base64.b64encode(r_metadata).decode()})
    elif footer[0] == 3073:
        fdata_file = os.path.join(file_folder, '0x{}.file'.format(str(hex(target_filehash))[2:].zfill(8)))
        f_metadata = find_file_metadata_in_fdata(fdata_file, 0)
        return({'name_hash': target_filehash, 'tkid_hash': tkid,\
            'entry_type': entry_type, 'string_size': string_size,\
            'f_extradata': base64.b64encode(f_metadata).decode(),\
            'r_extradata': base64.b64encode(r_metadata).decode()})
    else:
        return({})

def retrieve_file_metadata(target_filehash, rdb_file = 'root.rdb', rdx_file = 'root.rdx', file_folder = 'data'):
    metadata = find_file_metadata(target_filehash, rdb_file = rdb_file, rdx_file = rdx_file, file_folder = file_folder)
    with open('{}.file_metadata.json'.format(str(hex(target_filehash))[2:].zfill(8)), 'wb') as f:
        f.write(json.dumps(metadata, indent = 4).encode())

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    if os.path.exists('root.rdb.original') and os.path.exists('root.rdx.original'):
        print("Mods detected, will attempt to use original files.")
        rdb_file = 'root.rdb.original'
        rdx_file = 'root.rdx.original'
    else:
        rdb_file = 'root.rdb'
        rdx_file = 'root.rdx'
    target_filehash = -1
    while target_filehash == -1:
        raw_hash = input("What hash are you looking for? [e.g. 0x1234ABCD] ").lstrip("0x")
        try:
            target_filehash = int(raw_hash, 16)
        except:
            print("Invalid entry!")
    retrieve_file_metadata(target_filehash, rdb_file = rdb_file, rdx_file = rdx_file)