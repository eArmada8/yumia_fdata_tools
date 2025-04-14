# This script will read a ktid file (file with texture references), and then open
# a .kidsobjdb.json file with file references.  It will ask for the location of the Atelier Yumia
# Motor folder (with root.rdb, root.rdx and fdata files), and export out all referenced
# textures and metadata.  This script will make a backup of root.rdb/root.rdx if nonexistent,
# and will always use the backup files to ensure extraction original textures.
#
# The .kidsobjdb.json file needs to contain the references, use yumia_find_kidsobjdb_using_ktid.py
# to find a compatible .kidsobjdb file and yumia_decode_kidsobjdb.py to generate the .kidsobjdb.json
# file to use with this script.
#
# This script is dependent on yumia_mod_lib.py, yumia_mod_find_metadata.py and
# yumia_decode_ktid_with_kidsobjdb.py - place them in the same folder as the script.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import struct, base64, json, zlib, os, sys
    from yumia_mod_find_metadata import *
    from yumia_decode_ktid_with_kidsobjdb import *
    from yumia_mod_lib import read_fdata_file
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise

def get_yumia_root_folder ():
    if os.path.exists('yumia_folder.json'):
        yumia_folder = json.loads(open('yumia_folder.json','rb').read())[0]
    else:
        yumia_folder = ''
    while not (os.path.exists(os.path.join(yumia_folder, 'root.rdb.original')) or os.path.exists(os.path.join(yumia_folder, 'root.rdb'))):
        raw_path = input("Please input path to root.rdb / root.rdb.original: ").strip('\'').strip("\"")
        if os.path.exists(raw_path):
            if not os.path.isdir(raw_path):
                raw_path = os.path.dirname(raw_path)
            if os.path.exists(os.path.join(raw_path, 'root.rdb.original')):
                yumia_folder = raw_path
            elif os.path.exists(os.path.join(yumia_folder, 'root.rdb')):
                yumia_folder = raw_path
                shutil.copy2(os.path.join(yumia_folder, 'root.rdb'), os.path.join(yumia_folder, 'root.rdb.original'))
            else:
                print("Invalid path!")
        else:
            print("Invalid entry!")
    if not os.path.exists(os.path.join(yumia_folder, 'root.rdx.original')) and os.path.exists(os.path.join(yumia_folder, 'root.rdx')):
        shutil.copy2(os.path.join(yumia_folder, 'root.rdx'), os.path.join(yumia_folder, 'root.rdx.original'))
    open('yumia_folder.json','wb').write(json.dumps([yumia_folder], indent=4).encode())
    return (yumia_folder)

def grab_ktid_referenced_files (ktid_filename, kidsobjdb_json_filename, overwrite = False):
    print("Processing {}...".format(ktid_filename))
    yumia_folder = get_yumia_root_folder()
    decoded_ktid_data = read_ktid_using_kidsobjdb_json (ktid_filename, kidsobjdb_json_filename)
    for ktid_val in decoded_ktid_data:
        target_filehash = int(decoded_ktid_data[ktid_val]['file_hash'], 16)
        tkid, string_size, footer, r_metadata = find_file_metadata_in_rdb(target_filehash,\
            os.path.join(yumia_folder, 'root.rdb.original'))
        if footer[0] == 1025:
            fdata_file = os.path.join(yumia_folder, find_fdata_file(footer[3], rdx_file = os.path.join(yumia_folder, 'root.rdx.original')))
            f_metadata = find_file_metadata_in_fdata(fdata_file, footer[1])
            metadata = {'name_hash': target_filehash, 'tkid_hash': tkid, 'string_size': string_size,\
                'f_extradata': base64.b64encode(f_metadata).decode(),\
                'r_extradata': base64.b64encode(r_metadata).decode()}
            meta_filename = '{0}_0x{1}.file_metadata.json'.format(str(ktid_val).zfill(3), str(hex(target_filehash))[2:].zfill(8))
            if os.path.exists(meta_filename) and (overwrite == False):
                if str(input("Targeted files already exist! Overwrite? (y/N) ")).lower()[0:1] == 'y':
                    overwrite = True
            if (overwrite == True) or not os.path.exists(meta_filename):
                with open(meta_filename, 'wb') as f:
                    f.write(json.dumps(metadata, indent = 4).encode())
                fdata_filedata, _, filename = read_fdata_file(fdata_file, footer[1])
                open('{0}_{1}'.format(str(ktid_val).zfill(3), filename), 'wb').write(fdata_filedata)
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
            grab_ktid_referenced_files(ktid_files[i], db_name)