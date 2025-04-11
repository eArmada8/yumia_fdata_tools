# This script will find a ktid file hash (file with texture references) using a g1m file hash.
#
# The .kidsobjdb.json file needs to contain the references, use yumia_find_kidsobjdb_using_ktid.py
# to find a compatible .kidsobjdb file and yumia_decode_kidsobjdb.py to generate the .kidsobjdb.json
# file to use with this script.
#
# Additionally, place an unmodded root.rdb (or root.rdb.original - root.rdb.original will take
# precedence over root.rdb) in the folder to narrow compatible hashes to the actual ktid file.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import json, struct, csv, os, sys, glob
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise

def read_rdb_filenames (rdb_file = 'root.rdb'):
    files = []
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
            files.append((file_hash, tkid))
            if not (entry_size % 4 == 0):
                f.seek(start + entry_size + 4 - (entry_size % 4))
            else:
                f.seek(start + entry_size)
    return(files)

def find_ktid_using_g1m_hash (g1m_hash, kidsobjdb_json_filename):
    assoc_files = []
    assoc_ktid_files = []
    db = json.loads(open(kidsobjdb_json_filename, 'rb').read())
    db_values = [x['values'] for x in db]
    matches = [i for i in range(len(db_values)) if len(db_values[i]) > 0\
        and len(db_values[i][0]['value']) > 0
        and isinstance(db_values[i][0]['value'][0]['value'], int)\
        and db_values[i][0]['value'][0]['value'] == g1m_hash]
    if len(matches) > 0:
        values = [x['value'][0]['value'] for x in db_values[matches[0]]\
            if len(x['value']) == 1 and isinstance(x['value'][0]['value'], int)]
        assoc_file_entries = [x for x in values if x in [x['name_hash'] for x in db]]
        assoc_db_values = [x['values'] for x in db if x['name_hash'] in assoc_file_entries]
        assoc_matches = [i for i in range(len(assoc_db_values)) if len(assoc_db_values[i]) > 0\
            and len(assoc_db_values[i][0]['value']) > 0
            and isinstance(assoc_db_values[i][0]['value'][0]['value'], int)]
        assoc_file_hashes = [assoc_db_values[i][0]['value'][0]['value'] for i in assoc_matches\
            if assoc_db_values[i][0]['value'][0]['value'] > 10]
        assoc_files = ['0x{}'.format(str(hex(x))[2:].zfill(8)) for x in assoc_file_hashes]
        print("These *referenced* file hashes are associated with {0}: {1}".format('0x{}'.format(str(hex(g1m_hash))[2:].zfill(8)), assoc_files))
        if os.path.exists('root.rdb.original') or os.path.exists('root.rdb'):
            ktid_type_hash = 0x8e39aa37
            if os.path.exists('root.rdb.original'):
                rdb_filenames = read_rdb_filenames('root.rdb.original')
            else:
                rdb_filenames = read_rdb_filenames('root.rdb')
            ktid_files = [x[0] for x in rdb_filenames if x[1] == ktid_type_hash]
            assoc_ktid_files = ['0x{}'.format(str(hex(x))[2:].zfill(8)) for x in assoc_file_hashes if x in ktid_files]
            if len(assoc_ktid_files) > 0:
                print("Of those, the following matches are ktid files: {0}".format(assoc_ktid_files))
            else:
                print("None of those are ktid files in root.rdb...")
        else:
            print("Neither root.rdb.original nor root.rdb available, skipping file type check.")
        input("Press Enter to continue.")
    return(assoc_ktid_files)

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    if os.path.exists('CharacterEditor.kidssingletondb.kidsobjdb.json'):
        kidsobjdb_json_filename = 'CharacterEditor.kidssingletondb.kidsobjdb.json'
    else:
        kidsobjdb_json_filename = ''
        while kidsobjdb_json_filename == '':
            raw_db_name = input("Input name of db json file to use for hashing: ")
            if os.path.exists(raw_db_name):
                kidsobjdb_json_filename = raw_db_name
    g1m_hash = -1
    while g1m_hash == -1:
        raw_hash = input("Input g1m hash to search for ktid file: [e.g. 0x1234ABCD] ").lstrip("0x")
        try:
            g1m_hash = int(raw_hash, 16)
        except:
            print("Invalid entry!")
    find_ktid_using_g1m_hash(g1m_hash, kidsobjdb_json_filename = kidsobjdb_json_filename)