# This script ask for a g1m hash (e.g. g1m file name), and then open
# every kidsobjdb file in the folder and attempt to find a kidsobjdb file that contains
# a linked file reference.  Only searches IDOK0000 references, not RDOK0000.
# It will skip over files that cannot be properly read by my tool.
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

def hunt_for_kidsobjdb_using_g1m_hash (g1m_hash):
    kidsobjdb_files = glob.glob('*.kidsobjdb')
    matches = []
    for i in range(len(kidsobjdb_files)):
        try:
            db_data = read_kidsobjdb(kidsobjdb_files[i], kidsobjdb_namefile = '', ask_for_namefile = False)
            db_values = [x['values'] for x in db_data]
            hash_matches = [i for i in range(len(db_values)) if len(db_values[i]) > 0\
                and len(db_values[i][0]['value']) > 0
                and isinstance(db_values[i][0]['value'][0]['value'], int)\
                and db_values[i][0]['value'][0]['value'] == g1m_hash]
            if len(hash_matches) > 0:
                matches.append(kidsobjdb_files[i])
        except AssertionError:
            print("Skipping {} due to unknown formatting.".format(kidsobjdb_files[i]))
    return (matches)
    
if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    g1m_hash = -1
    while g1m_hash == -1:
        raw_hash = input("Input g1m hash to search for ktid file: [e.g. 0x1234ABCD] ").lstrip("0x")
        try:
            g1m_hash = int(raw_hash, 16)
        except:
            print("Invalid entry!")
    matches = hunt_for_kidsobjdb_using_g1m_hash(g1m_hash)
    print("Kidsobjdb files with {0}: {1}".format('0x{}'.format(str(hex(g1m_hash))[2:].zfill(8)), matches))
    input("Press Enter to quit.")