# This script will read a ktid file (file with texture references), and then open
# every kidsobjdb file in the folder and attempt to find a kidsobjdb file that contains
# all the references in that ktid file.  It will skip over files that cannot be properly
# read by my tool.
#
# Requires yumia_decode_kidsobjdb.py, place in the same folder as this script.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import json, struct, os, sys, glob
    from yumia_decode_kidsobjdb import *
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

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
            db_hashes = [x['name_hash'] for x in read_kidsobjdb(kidsobjdb_files[i], kidsobjdb_namefile = '', ask_for_namefile = False)]
            if all([x in db_hashes for x in ktid_hashes]):
                matches.append(kidsobjdb_files[i])
        except AssertionError:
            pass #Not all kidsobjdb files can be decoded by my tool
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