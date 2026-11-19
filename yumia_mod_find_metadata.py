# This script will read root.rdb, root.rdx and the corresponding .fdata file to
# creates a .file_metadata.json file.  Run in the /Atelier Yumia/Motor/ folder.
# It will ask for the filenames of the files (usually the hash plus an extension).
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import struct, base64, json, glob, os, sys
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

# Currently combines all the lang files, so duplicates will not be detected
def parse_lang_files (lang_code):
    lang_files = glob.glob('*{}.lang'.format(lang_code))
    locators = {}
    for lang_file in lang_files:
        with open(lang_file, 'rb') as f:
            f.seek(0,2)
            eof = f.tell()
            f.seek(0)
            while f.tell() < eof:
                name_hash, offset, size = struct.unpack("<3I", f.read(12))
                locators[name_hash] = {'offset': offset, 'size': size}
    return locators

def find_file_metadata_in_rdb (target_filehash, rdb_file = 'root.rdb'):
    def read_variable_size_int(f):
        dword1, = struct.unpack("<I", f.read(4))
        if dword1 & 0x80000000:
            dword2, = struct.unpack("<I", f.read(4))
            return ((dword1 & 0x7FFFFFFF) << 32) + dword2
        else:
            return dword1
    idrk_header_size = 0x30
    r_metadata = b''
    location_record = {'skip': True}
    with open(rdb_file, 'rb') as f:
        magic = f.read(8)
        assert magic == b'_DRK0000'
        header_size, version, num_files, namefile_hash = struct.unpack("<4I", f.read(16))
        file_folder = f.read(header_size - f.tell()).rstrip(b'\x00').decode()
        for _ in range(num_files):
            start = f.tell()
            magic = f.read(8)
            assert magic == b'IDRK0000'
            entry_size, payload_size, file_size = struct.unpack("<3Q", f.read(24))
            param_data_size, file_hash, tkid, flags = struct.unpack("<4I", f.read(16))
            if not file_hash == target_filehash:
                if not (entry_size % 4 == 0):
                    f.seek(start + entry_size + 4 - (entry_size % 4))
                else:
                    f.seek(start + entry_size)
            else:
                r_metadata = f.read(entry_size - (payload_size + idrk_header_size))
                if ((flags >> 16) & 0xF == 2) and (payload_size >= 13):
                    location_record['kind'], location_record['flags'] = struct.unpack("<2B", f.read(2))
                    bits_set = [location_record['flags'] & 1, location_record['flags'] & 2,
                        location_record['flags'] & 4, location_record['flags'] & 8]
                    location_record['offset'] = read_variable_size_int(f)
                    location_record['size'] = read_variable_size_int(f)
                    if bits_set[0]:
                        location_record['container'], = struct.unpack("<H", f.read(2))
                    if bits_set[1]:
                        location_record['subcontainer'], = struct.unpack("<B", f.read(1))
                    if bits_set[2]:
                        location_record['rdx_index'], = struct.unpack("<H", f.read(2))
                    location_record['loose_file'] = True if bits_set[3] else False
                    location_record['skip'] = False
                break
    return(param_data_size, tkid, payload_size, location_record, r_metadata, file_folder)

def find_fdata_file (fdata_index, rdx_file = 'root.rdx'):
    with open(rdx_file, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0)
        success = False
        while f.tell() < eof:
            marker, root_folder, sub_folder, fdata_hash = struct.unpack("<H2BI", f.read(8))
            if marker == fdata_index:
                success = True
                break
    if not success:
        return("")
    else:
        return('0x{}.fdata'.format(str(hex(fdata_hash))[2:].zfill(8)))

def find_file_metadata_in_fdata(fdata_filename, target_filehash, location_record, file_folder):
    offset = location_record['offset'] if location_record['loose_file'] == False else 0
    fdata_files = glob.glob('{}**/{}'.format(file_folder if location_record['loose_file'] == True
        else '', fdata_filename), recursive = True)
    if len(fdata_filename) > 0 and len(fdata_files) > 0:
        if len(fdata_files) > 1:
            print("More than one copy of container {} found!  Please select an option:".format(fdata_filename))
            for i in range(len(fdata_files)):
                print("{}. {}".format(i+1, fdata_files[i]))
            input_ = -1
            while input_ == -1:
                raw_input = input("Type in the number of the file you would like to use: ")
                if raw_input.isnumeric() and int(raw_input) in range(1, len(fdata_files)+1):
                    input_ = int(raw_input) - 1
            fdata_file = fdata_files[input_]
            try:
                lang_code = os.path.dirname(fdata_file).replace('\\','/').split('/')[-1]
                if lang_code != '':
                    lang_updates = parse_lang_files(lang_code)
                    offset = lang_updates[target_filehash]['offset']
            except KeyError:
                pass # Try the original offset
        else:
            fdata_file = fdata_files[0]
    else:
        print("Warning, container {} not found!  Metadata will be empty.".format(fdata_filename))
        return(b'')
    with open(fdata_file, 'rb') as f:
        f.seek(offset)
        magic = f.read(8)
        assert magic == b'IDRK0000'
        entry_size, cmp_size, unc_size = struct.unpack("<3Q", f.read(24))
        param_data_size, filehash, filetkid, flags = struct.unpack("<4I", f.read(16))
        f_metadata = f.read(entry_size - cmp_size - 0x30)
        return(f_metadata)

def find_file_metadata(target_filehash, rdb_file = 'root.rdb', rdx_file = 'root.rdx'):
    param_data_size, tkid, payload_size, location_record, r_metadata, file_folder = find_file_metadata_in_rdb(
        target_filehash, rdb_file = rdb_file)
    if location_record['skip'] == False and location_record['kind'] == 1:
        if location_record['loose_file'] == True:
            fdata_file = '0x{}.file'.format(str(hex(target_filehash))[2:].zfill(8))
        elif 'rdx_index' in location_record:
            fdata_file = find_fdata_file (location_record['rdx_index'], rdx_file = rdx_file)
        else:
            print("Warning! Skipping file, unknown locator format: {}".format(location_record))
            return({})
        f_metadata = find_file_metadata_in_fdata(fdata_file, target_filehash, location_record, file_folder)
        if len(f_metadata) == 0:
            print("Metadata not found for target hash {}!".format(hex(target_filehash)))
            return({})
        return({'name_hash': target_filehash, 'tkid_hash': tkid,\
            'param_data_size': param_data_size, 'payload_size': payload_size,\
            'f_extradata': base64.b64encode(f_metadata).decode(),\
            'r_extradata': base64.b64encode(r_metadata).decode()})
    else:
        print("Metadata not found for target hash {} due to missing / incompatible root.rdb entry!".format(hex(target_filehash)))
        return({})

def retrieve_file_metadata (target_filehash, rdb_file = 'root.rdb', rdx_file = 'root.rdx'):
    metadata = find_file_metadata(target_filehash, rdb_file = rdb_file, rdx_file = rdx_file)
    if len(metadata) > 0:
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
        raw_hash = input("What hash are you looking for? [e.g. 0x1234ABCD] ").strip()
        try:
            target_filehash = int(raw_hash, 16)
        except:
            print("Invalid entry!")
    retrieve_file_metadata(target_filehash, rdb_file = rdb_file, rdx_file = rdx_file)