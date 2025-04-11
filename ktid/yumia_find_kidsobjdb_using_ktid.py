# This script will read a ktid file (file with texture references), and then open
# every kidsobjdb file in the folder and attempt to find a kidsobjdb file that contains
# all the references in that ktid file.  It will skip over files that cannot be properly
# read by my tool.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import json, struct, os, sys, glob
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

def read_kidsobjdb_for_hashes (kidsobjdb_file):
    with open(kidsobjdb_file, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0x0)
        problems = []
        magic = f.read(8)
        assert magic == b'_DOK0000'
        entry_size, platform, num_entries = struct.unpack("<3I", f.read(12))
        kidsobjdb_namefile_hash, file_size = struct.unpack("<2I", f.read(8))
        all_hashes = []
        while f.tell() < eof:
            start = f.tell()
            magic = f.read(8)
            assert magic in [b'IDOK0000', b'RDOK0000']
            entry_size, prop_name, prop_typename, prop_count = struct.unpack("<4I", f.read(16))
            all_hashes.append(prop_name)
            f.seek(start + entry_size)
            while not (f.tell() % 4 == 0):
                f.seek(1,1)
        return(all_hashes)

def hunt_for_kidsobjdb_using_ktid (ktid_filename):
    ktid_hashes = []
    with open(ktid_filename, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0,0)
        while f.tell() < eof:
            index, ktid_hash = struct.unpack("<2I", f.read(8))
            ktid_hashes.append(ktid_hash)
    kidsobjdb_files = glob.glob('*.kidsobjdb')
    matches = []
    for i in range(len(kidsobjdb_files)):
        try:
            db_hashes = read_kidsobjdb_for_hashes(kidsobjdb_files[i])
        except AssertionError:
            print("Skipping {} due to unknown formatting.".format(kidsobjdb_files[i]))
        if all([x in db_hashes for x in ktid_hashes]):
            matches.append(kidsobjdb_files[i])
    return (matches)
    
if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # If argument given, attempt to search using file in argument
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('ktid_filename', help="Name of ktid file to read from (required).")
        args = parser.parse_args()
        if os.path.exists(args.ktid_filename) and args.ktid_filename[-5:] == '.ktid':
            matches = hunt_for_kidsobjdb_using_ktid(args.ktid_filename)
    else:
        matches = []
        ktid_files = glob.glob('*.ktid')
        for i in range(len(ktid_files)):
            matches.append(hunt_for_kidsobjdb_using_ktid(ktid_files[i]))
    print("Matches: {}".format(matches))
    open('kidsobjdb_matches.json','wb').write(json.dumps(matches, indent=4).encode())
    input("Results saved in kidsobjdb_matches.json.  Press Enter to quit.")