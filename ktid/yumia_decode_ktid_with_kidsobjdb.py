# This script will read a ktid file (file with texture references), and then open
# a .kidsobjdb.json file with file references.  It will output a decoded file in CSV format.
# The .kidsobjdb.json file needs to contain the references, use yumia_find_kidsobjdb_using_ktid.py
# to find a compatible .kidsobjdb file and yumia_decode_kidsobjdb.py to generate the .kidsobjdb.json
# file to use with this script.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import json, struct, csv, os, sys, glob
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise

def read_ktid_using_kidsobjdb_json (ktid_filename, kidsobjdb_json_filename):
    db = json.loads(open(kidsobjdb_json_filename, 'rb').read())
    db_hashes = [x['name_hash'] for x in db]
    with open(ktid_filename, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0,0)
        ktid_values = {}
        while f.tell() < eof:
            index, ktid_hash = struct.unpack("<2I", f.read(8))
            entry = {}
            if ktid_hash in db_hashes:
                db_index = db_hashes.index(ktid_hash)
                if len(db[db_index]['values']) > 0 and isinstance(db[db_index]['values'][0]['value'][0]['value'], int):
                    entry['file_hash'] = "0x{}".format(str(hex(db[db_index]['values'][0]['value'][0]['value']))[2:].zfill(8))
                if 'name' in db[db_index]:
                    entry['resource_name'] = db[db_index]['name']
                else:
                    entry['resource_name'] = ''
            ktid_values[index] = entry
    return(ktid_values)

def process_ktid (ktid_filename, kidsobjdb_json_filename, overwrite = False):
    print("Processing {}...".format(ktid_filename))
    decoded_ktid_data = read_ktid_using_kidsobjdb_json (ktid_filename, kidsobjdb_json_filename)
    csv_filename = ktid_filename + '.csv'
    if os.path.exists(csv_filename) and (overwrite == False):
        if str(input(csv_filename + " exists! Overwrite? (y/N) ")).lower()[0:1] == 'y':
            overwrite = True
    if (overwrite == True) or not os.path.exists(csv_filename):
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_f:
            csv_writer = csv.writer(csv_f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['File Index', 'File Hash', 'File Name'])
            for row in decoded_ktid_data:
                csv_writer.writerow([row, decoded_ktid_data[row]['file_hash'], decoded_ktid_data[row]['resource_name']])
    return

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # If argument given, attempt to decode file in argument
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--overwrite', help="Overwrite existing files", action="store_true")
        parser.add_argument('json_filename', help="Name of .kidsobjdb.json file to reference (required).")
        parser.add_argument('ktid_filename', help="Name of ktid file to read from (required).")
        args = parser.parse_args()
        if os.path.exists(args.json_filename) and os.path.exists(args.ktid_filename):
            process_ktid(args.ktid_filename, args.json_filename, overwrite = args.overwrite)
    else:
        if os.path.exists('CharacterEditor.kidssingletondb.kidsobjdb.json'):
            db_name = 'CharacterEditor.kidssingletondb.kidsobjdb.json'
        else:
            db_name = ''
            while db_name == '':
                raw_db_name = input("Input name of db json file to use for hashing: ")
                if os.path.exists(raw_db_name):
                    db_name = raw_db_name

        ktid_files = glob.glob('*.ktid')
        for i in range(len(ktid_files)):
            process_ktid(ktid_files[i], db_name)