# The main library of shared functions for the Atelier Yumia fdata/rdb modding scripts.
# Place in the same folder as the modding scripts.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import json, base64, struct, shutil, zlib, os, sys
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

def read_decode_mod_json (mod_json_filename):
    mod_data = json.loads(open(mod_json_filename, 'rb').read())
    for i in range(len(mod_data['files'])):
        mod_data['files'][i]['f_extradata'] = base64.b64decode(mod_data['files'][i]['f_extradata'])
        mod_data['files'][i]['r_extradata'] = base64.b64decode(mod_data['files'][i]['r_extradata'])
    return(mod_data)

def create_fdata_idrk (filedata, file_metadata):
    filesize = len(filedata)
    extrasize = len(file_metadata['f_extradata'])
    idrk = bytearray()
    idrk.extend(b'IDRK0000')
    idrk.extend(struct.pack("<3Q", 0x30 + extrasize + filesize, filesize, filesize))
    idrk.extend(struct.pack("<4I", 0, file_metadata['name_hash'], file_metadata['tkid_hash'], 0))
    idrk.extend(file_metadata['f_extradata'])
    idrk.extend(filedata)
    return(idrk)

def create_rdb_idrk (filesize, file_metadata, fdata_index = 0, fdata_offset = 0x10):
    extrasize = len(file_metadata['r_extradata'])
    idrk = bytearray()
    idrk.extend(b'IDRK0000')
    idrk.extend(struct.pack("<3Q", 0x3D + extrasize, file_metadata['string_size'], filesize))
    idrk.extend(struct.pack("<4I", 0, file_metadata['name_hash'], file_metadata['tkid_hash'], 0x20000))
    idrk.extend(file_metadata['r_extradata'])
    idrk.extend(struct.pack("<H2IHI", 0x401, fdata_offset, 0x30 + extrasize + filesize, fdata_index, 0))
    return(idrk)

def read_fdata_for_rbd_insertion (mod_data, fdata_index):
    with open('0x{}.fdata'.format(str(hex(mod_data['fdata_hash']))[2:].zfill(8)), 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0x10,0) # Skip header
        idrk_struct = {}
        while f.tell() < eof:
            fdata_offset = f.tell()
            magic = f.read(8)
            if not magic == b'IDRK0000':
                while f.tell() < eof and not magic == b'IDRK0000':
                    if f.tell() >= eof:
                        break
                    f.seek(-4,1)
                    fdata_offset = f.tell()
                    magic = f.read(8)
            entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
            entry_type, name_hash, tkid_hash, flags = struct.unpack("<4I", f.read(16))
            if name_hash in [x['name_hash'] for x in mod_data['files']]:
                metadata = [x for x in mod_data['files'] if x['name_hash'] == name_hash][0]
                idrk_struct[name_hash] = create_rdb_idrk(unc_size, metadata,\
                    fdata_index = fdata_index, fdata_offset = fdata_offset)
            f.seek(fdata_offset + entry_size)
        return(idrk_struct)

def read_fdata_file (fdata_filename, offset):
    with open(fdata_filename, 'rb') as f:
        f.seek(offset)
        magic = f.read(8)
        assert magic == b'IDRK0000'
        entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
        entry_type, filehash, filetkid, flags = struct.unpack("<4I", f.read(16))
        f_metadata = f.read(entry_size - cmp_size - 0x30)
        if cmp_size == unc_size:
            unc_data = f.read(unc_size)
        else:
            unc_data = bytearray(unc_size)
            unc_offset = 0
            while unc_offset < unc_size:
                zsize, unk0 = struct.unpack("<HQ", f.read(10))
                data_chunk = zlib.decompress(f.read(zsize))
                unc_data[unc_offset:unc_offset+len(data_chunk)] = data_chunk
                unc_offset += len(data_chunk)
        return(unc_data, f_metadata, filehash, filetkid)

def create_empty_fdata ():
    fdata = b'PDRK0000' + struct.pack("<2I", 0x10, 0x10)
    return (fdata)

def append_to_fdata (fdata, filedata, file_metadata):
    idrk = create_fdata_idrk (filedata, file_metadata)
    offset = len(fdata)
    if len(fdata) > 0x10:
        prior_data = bytearray(fdata)[0x10:]
    else:
        prior_data = bytearray()
    fdata = b'PDRK0000' + struct.pack("<2I", 0x10, len(prior_data) + len(idrk) + 0x10) + prior_data + idrk
    return (fdata)

def write_fdata (fdata, fdata_hash):
    open('0x{}.fdata'.format(str(hex(fdata_hash))[2:].zfill(8)), 'wb').write(fdata)

def append_rdx(new_fdata_list, rdx_file = 'root.rdx'):
    if not os.path.exists(rdx_file + '.original'):
        shutil.copy2(rdx_file, rdx_file + '.original')
    with open(rdx_file + '.original', 'rb') as f:
        new_rdx = f.read()
        eof = f.tell()
        f.seek(0)
        while f.tell() < eof:
            marker, ff, fdata = struct.unpack("<2hI", f.read(8))
        markers = []
        for new_fdata in new_fdata_list:
            marker += 1
            new_rdx += struct.pack("<2hI", marker, -1, new_fdata)
            markers.append(marker)
        with open(rdx_file, 'wb') as f2:
            f2.write(new_rdx)
        return(markers)

def replace_files_in_rdb(rdb_file, idrk_struct):
    if not os.path.exists(rdb_file + '.original'):
        shutil.copy2(rdb_file, rdb_file + '.original')
    with open(rdb_file + '.original', 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0,0)
        new_rdb = bytearray()
        new_rdb.extend(f.read(32)) # Header, seems safe to just copy because we are not *adding* files
        while f.tell() < eof:
            start = f.tell()
            magic = f.read(4)
            assert magic == b'IDRK'
            version, entry_size, string_size, file_size = struct.unpack("<I3Q", f.read(28))
            entry_type, file_hash, ktid, flags = struct.unpack("<4I", f.read(16))
            if not (entry_size % 4 == 0):
                aligned_size = entry_size + 4 - (entry_size % 4)
            else:
                aligned_size = entry_size
            if not file_hash in idrk_struct.keys():
                f.seek(start)
                new_rdb.extend(f.read(aligned_size))
            else:
                new_rdb.extend(idrk_struct[file_hash])
                f.seek(start + aligned_size)
        open(rdb_file, 'wb').write(new_rdb)

if __name__ == "__main__":
    pass