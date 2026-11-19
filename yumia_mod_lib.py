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

def create_fdata_idrk (cmp_data, unc_size, file_metadata, cmp_flag = 0):
    cmp_size = len(cmp_data)
    param_block_size = len(file_metadata['f_extradata'])
    payload = file_metadata['f_extradata'][4:] + cmp_data
    param_count, = struct.unpack("<I", file_metadata['f_extradata'][4:8])
    param_data_size = param_block_size - (12 * param_count + 8)
    idrk = bytearray()
    idrk.extend(b'IDRK0000')
    idrk.extend(struct.pack("<3Q", 0x30 + param_block_size + cmp_size, cmp_size, unc_size))
    idrk.extend(struct.pack("<4I", param_data_size, file_metadata['name_hash'], file_metadata['tkid_hash'], cmp_flag << 20))
    idrk.extend(struct.pack("<I", zlib.crc32(cmp_data)))
    idrk.extend(payload)
    return(idrk)

def create_rdb_idrk (unc_size, entry_size, file_metadata, flags, fdata_index = 0, fdata_offset = 0x10):
    def write_variable_size_int (int_):
        assert int_ < (1 << 63)
        if int_ < (1 << 31):
            return struct.pack("<I", int_)
        else:
            return struct.pack("<2I", (int_ >> 32) | 0x80000000, int_ & 0xFFFFFFFF)
    param_block_size = len(file_metadata['r_extradata'])
    param_count, = struct.unpack("<I", file_metadata['r_extradata'][4:8])
    param_data_size = param_block_size - (12 * param_count + 8)
    new_flags = 0x20000 | (flags & 0x03F00000)
    location = bytearray()
    location.extend(struct.pack("<2B", 1, 4))
    location.extend(write_variable_size_int(fdata_offset))
    location.extend(write_variable_size_int(entry_size))
    location.extend(struct.pack("<HB", fdata_index, 0))
    idrk = bytearray()
    idrk.extend(b'IDRK0000')
    idrk.extend(struct.pack("<3Q", 0x30 + param_block_size + len(location), len(location), unc_size))
    idrk.extend(struct.pack("<4I", param_data_size, file_metadata['name_hash'], file_metadata['tkid_hash'], new_flags))
    idrk.extend(file_metadata['r_extradata'])
    idrk.extend(location)
    while len(idrk) % 4 > 0:
        idrk.extend(b'\x00')
    return(idrk)

def read_fdata_for_idrk_information (fdata_filename):
    with open(fdata_filename, 'rb') as f:
        magic = f.read(8)
        f.seek(0,2)
        eof = f.tell()
        if magic == b'PDRK0000':
            f.seek(0x10,0) # Skip header
        else:
            f.seek(0,0) # .file mode
        idrk_entries = []
        while f.tell() < eof:
            fdata_offset = f.tell()
            magic = f.read(8)
            if not magic == b'IDRK0000':
                f.seek(-0x18,1) # Jump backwards in case this is an .fdata file from an older version of this tool
                while f.tell() < eof and not magic == b'IDRK0000':
                    if f.tell() >= eof:
                        break
                    f.seek(-7,1)
                    fdata_offset = f.tell()
                    magic = f.read(8)
            entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
            param_data_size, name_hash, tkid_hash, flags = struct.unpack("<4I", f.read(16))
            idrk_entries.append({'offset': fdata_offset, 'name_tkid': (name_hash, tkid_hash), 'flags': flags})
            entry_end = fdata_offset + entry_size
            if entry_end % 0x10:
                entry_end += (0x10 - entry_end % 0x10)
            f.seek(entry_end)
        return(idrk_entries)

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
                f.seek(-0x18,1) # Jump backwards in case this is an .fdata file from an older version of this tool
                while f.tell() < eof and not magic == b'IDRK0000':
                    if f.tell() >= eof:
                        break
                    f.seek(-7,1)
                    fdata_offset = f.tell()
                    magic = f.read(8)
            entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
            param_data_size, name_hash, tkid_hash, flags = struct.unpack("<4I", f.read(16))
            if name_hash in [x['name_hash'] for x in mod_data['files']]:
                metadata = [x for x in mod_data['files'] if x['name_hash'] == name_hash][0]
                idrk_struct[name_hash] = create_rdb_idrk(unc_size, entry_size, metadata,\
                    flags, fdata_index = fdata_index, fdata_offset = fdata_offset)
            entry_end = fdata_offset + entry_size
            if entry_end % 0x10:
                entry_end += (0x10 - entry_end % 0x10)
            f.seek(entry_end)
        return(idrk_struct)

def read_fdata_file (fdata_filename, offset):
    # decrypt_type3_payload() written by Claude AI
    def decrypt_type3_payload (payload, name_hash, tkid_hash, unc_size):
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except ModuleNotFoundError as e:
            print("Python module missing! {}".format(e.msg))
            print("Cannot decrypt file {}, skipping.".format(hex(name_hash)))
            return(b'')
        if len(payload) < 32 or (len(payload) - 16) % 16:
            return(b'')
        iv = payload[:16]
        iv_dw1, iv_dw2 = struct.unpack_from("<2I", iv, 4)
        key = struct.pack("<4I", iv_dw2 ^ 0x25544EF3, name_hash ^ 0x5FAD6629,
                                 tkid_hash ^ 0xCF99643A, iv_dw1 ^ 0xBA2F39D5)
        dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        data = dec.update(payload[16:]) + dec.finalize()
        pad = data[-1]
        if not (1 <= pad <= 16 and data[-pad:] == bytes([pad]) * pad and len(data) - pad == unc_size):
            return(b'') # Return b'' if the decoding failed - this might be byte flipped zlib chunked format instead ??
        return(data[:-pad])
    #Thank you to github/eterniti for extensions
    tkid_vals = { 0x0bd05b27: "mit" , 0x0d34474d: "srst", 0x17614af5: "g1mx", 0x1fdcaa40: "kidstask", 0x20a6a0bb: "kidsobjdb",\
        0x27bc54b7: "rigbin", 0x4d0102ac: "g1em", 0x4f16d0ef: "kts", 0x5153729b: "mtl", 0x54738c76: "g1co", 0x5599aa51: "kscl",\
        0x563bdef1: "g1m", 0x56d8deda: "sid", 0x5c3e543c: "swg", 0x6fa91671: "g1a", 0x757347e0: "bpo", 0x786dcd84: "g1n",\
        0x79c724c2: "g1p", 0x7bcd279f: "g1s", 0x9cb3a4b6: "oidex", 0xa027e46b: "mov", 0xa8d88566: "g1cox", 0xafbec60c: "g1t",\
        0xb097d41f: "g1e", 0xb0a14534: "sgcbin", 0xb1630f51: "kidsrender", 0xbbd39f2d: "srsa", 0xbbf9b49d: "grp", 0xbe144b78: "ktid",\
        0xbf6b52c7: "name", 0xd7f47fb1: "efpl", 0xdbcb74a9: "oid", 0xf20de437: "texinfo", 0x1ab40ae8: "oid", 0x56efe45c: "grp",\
        0xe6a3c3bb: "oidex", 0x8e39aa37: "ktid", 0xb340861a: "mtl", 0xed410290: "kts", 0x82945a44: "lsqtree", 0xf13845ef: "sclshape",\
        0x5b2970fc: "ktf2", 0x32ac9403: "g1fpose", 0x133d2c3b: "sid", 0x2bcc0c02: "g1frani", 0x6dbd6ea6: "mit", 0x1a6300fd: "g1es",\
        0xad57ebba: "g1t_new"}
    with open(fdata_filename, 'rb') as f:
        f.seek(offset)
        magic = f.read(8)
        assert magic == b'IDRK0000'
        entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
        param_data_size, filehash, filetkid, flags = struct.unpack("<4I", f.read(16))
        f_metadata = f.read(entry_size - cmp_size - 0x30)
        cmp_flag = (flags >> 20) & 0x3F
        filename = "0x{0}.{1}".format(str(hex(filehash))[2:].zfill(8),\
            tkid_vals[filetkid] if filetkid in tkid_vals else hex(filetkid))
        if cmp_flag == 0:
            unc_data = f.read(unc_size)
        elif cmp_flag == 3: # Encryption: 16-byte IV followed by AES-128-CBC ciphertext with PKCS7 padding
            unc_data = decrypt_type3_payload (f.read(cmp_size), filehash, filetkid, unc_size)
        else:
            unc_data = bytearray(unc_size)
            unc_offset = 0
            while unc_offset < unc_size:
                if cmp_flag == 1: # FETH Mode
                    zsize, = struct.unpack("<I", f.read(4))
                elif cmp_flag == 4: # Standard Mode (e.g. Atelier Yumia, etc)
                    zsize, unk0 = struct.unpack("<HQ", f.read(10))
                else:
                    print("Unknown compression type: {}  Please report!".format(cmp_flag))
                    print("Skipping file {} in {}.".format(filename, fdata_filename))
                    return(b'', f_metadata, filename)
                data_chunk = zlib.decompress(f.read(zsize))
                unc_data[unc_offset:unc_offset+len(data_chunk)] = data_chunk
                unc_offset += len(data_chunk)
        return(unc_data, f_metadata, filename)

def create_empty_fdata ():
    fdata = b'PDRK0000' + struct.pack("<2I", 0x10, 0x10)
    return (fdata)

# zchunk_checksum() written by Claude AI
def zchunk_checksum (data):
    seeds = struct.unpack('<32Q', bytes.fromhex(
    "d0976d0204710db3f564b89d4faf15d97786d3ff495737578ee2066fa7a26a5a"
    "40f55496ed8b85ef33571d405a987947faf12fa86af7682d0a96a7ff5666ff73"
    "4321221e77914caaf3c8bb18416f2111aad75d6c1cb92c555c09be2a6057c0bd"
    "a4c6a44026d4afa6850c498e70fa2475243f03ea4ee28750dbdffe2179647ecd"
    "9741fac8fa38997d0ddf42cf383bcba649c292e87ceac0f0a58c0bc297f25fa1"
    "151c5bab14000fa0305490a7d7d98ea68e06903172b6ccf4ec4df696897f8d9a"
    "836926573a207a855ca7ba81dbe1a87eee0fd5be99dbf9e0a7d905e50990cb96"
    "7d870d7e3ed1e7841fb57880caaab3b1acdfc5ebe8e864aae98391f1fa3986e7"))
    u64 = lambda b, o: struct.unpack_from('<Q', b, o)[0]
    n = len(data)
    seed = seeds[n & 31]
    if n < 16:
        length = n & ~7 # 0 or 8
        if n < 8:
            start = n ^ seed # huge → reset below → result is just seed
        else:
            start = (seed ^ u64(data, 0)) % n
    else:
        v = (seed ^ u64(data, 8)) & 31 # only the low 5 bits matter
        length = (v if v < n else n) & ~7 # 0, 8, 16 or 24
        start  = (seed ^ u64(data, 0)) % n
    start &= ~7
    if start + length > n:
        start = 0
    h = seed
    for i in range(start, start + length, 8):
        h = (h + u64(data, i)) % (2**64)
    return h

def compress_data (filedata, cmp_flag = 0):
    if cmp_flag in [1,4]:
        chunks = [filedata[i : i + 0x4000] for i in range(0, len(filedata), 0x4000)]
        cmp_data = bytearray()
        for i in range(len(chunks)):
            cmp_chunk = zlib.compress(chunks[i])
            if cmp_flag == 1:
                cmp_data.extend(struct.pack("<I", len(cmp_chunk)))
            elif cmp_flag == 4:
                cmp_data.extend(struct.pack("<HQ", len(cmp_chunk), zchunk_checksum(cmp_chunk)))
            cmp_data.extend(cmp_chunk)
        cmp_data.extend(struct.pack("<I" if cmp_flag == 1 else "<H", 0)) # Termination chunk
    else: # Default to zero compression if 0 or an unsupported cmp_flag is given
        cmp_data, cmp_flag = filedata, 0
    return cmp_data, cmp_flag

def append_to_fdata (fdata, filedata, file_metadata, cmp_flag = 0):
    cmp_data, cmp_flag = compress_data (filedata, cmp_flag)
    idrk = create_fdata_idrk (cmp_data, len(filedata), file_metadata, cmp_flag)
    offset = len(fdata)
    if len(fdata) > 0x10:
        prior_data = bytearray(fdata)[0x10:]
    else:
        prior_data = bytearray()
    fdata = b'PDRK0000' + struct.pack("<2I", 0x10, len(prior_data) + len(idrk) + 0x10) + prior_data + idrk
    if len(fdata) % 0x10:
        fdata += b'\x00' * (0x10 - len(fdata) % 0x10)
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
        old_markers = []
        old_fdata_files = []
        while f.tell() < eof:
            marker, root_folder, sub_folder, fdata = struct.unpack("<H2BI", f.read(8))
            old_markers.append(marker)
            old_fdata_files.append(fdata)
        marker = max(old_markers)
        new_markers = []
        for new_fdata in new_fdata_list:
            marker += 1
            if new_fdata in old_fdata_files:
                print("Warning! {} already exists in the original root.rdx!".format(hex(new_fdata)))
                print("Unless every file in the original {} exists in the new version, the game will crash.".format(hex(new_fdata)))
            new_rdx += struct.pack("<H2BI", marker, 0xFF, 0xFF, new_fdata)
            new_markers.append(marker)
        if marker >= 0x800 or len(old_markers + new_markers) > 0x800:
            print("Warning!  There are more than 2048 .fdata files indexed in root.rdx!")
            input("Some .fdata files may be skipped.  Press Enter to continue.")
        with open(rdx_file, 'wb') as f2:
            f2.write(new_rdx)
        return(new_markers)

def replace_files_in_rdb(rdb_file, idrk_struct):
    if not os.path.exists(rdb_file + '.original'):
        shutil.copy2(rdb_file, rdb_file + '.original')
    with open(rdb_file + '.original', 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0xC,0)
        new_rdb = bytearray(b'_DRK0000') + struct.pack("<I", 0x20) #Header size
        new_rdb.extend(f.read(0x14)) # Header, seems safe to just copy because we are not *adding* files
        while f.tell() < eof:
            start = f.tell()
            magic = f.read(4)
            assert magic == b'IDRK'
            version, entry_size, string_size, file_size = struct.unpack("<I3Q", f.read(28))
            param_data_size, file_hash, ktid, flags = struct.unpack("<4I", f.read(16))
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