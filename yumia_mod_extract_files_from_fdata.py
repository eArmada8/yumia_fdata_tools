# This script reads all the *.fdata files in the current folder and extracts their contents.
# If a corresponding .yumiamod.json file exists, it will read that file to use the stored
# filenames; otherwise it will use the hashes in the .fdata file as filenames.
#
# Requires yumia_mod_lib.py, place in the same folder as this scripts.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import glob, os, sys
    from yumia_mod_lib import *
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

def extract_files_from_fdata (fdata_filename, overwrite = False):
    mod_filenames = {} # If a .yumiamod.json file exists, we can read it for the original filenames
    if os.path.exists(fdata_filename.split('.fdata')[0] + '.yumiamod.json'):
        mod_data = read_decode_mod_json(fdata_filename.split('.fdata')[0] + '.yumiamod.json')
        mod_filenames = {(x['name_hash'],x['tkid_hash']):x['filename'] for x in mod_data['files']}
    fdata_files = read_fdata_for_idrk_information(fdata_filename)
    for i in range(len(fdata_files)):
        try:
            filedata, _, filename = read_fdata_file(fdata_filename, fdata_files[i]['offset'])
            if fdata_files[i]['name_tkid'] in mod_filenames:
                filename = mod_filenames[fdata_files[i]['name_tkid']]
            if os.path.exists(filename) and (overwrite == False):
                if str(input("Files to be extracted from {} already exist! Overwrite? (y/N) ".format(fdata_filename))).lower()[0:1] == 'y':
                    overwrite = True
            if (overwrite == True) or not os.path.exists(filename):
                open(filename, 'wb').write(filedata)
        except zlib.error as e:
            print("Extraction of {} in {} failed! Skipping...".format(fdata_files[i]['name_tkid'], fdata_filename))
            print("ZLib error: {}".format(str(e)))
    return

def extract_files_from_file (file_filename, overwrite = False):
    mod_filenames = {} # If a .yumiamod.json file exists, we can read it for the original filenames
    if os.path.exists(file_filename.split('.file')[0] + '.yumiamod.json'):
        mod_data = read_decode_mod_json(file_filename.split('.file')[0] + '.yumiamod.json')
        mod_filenames = {(x['name_hash'],x['tkid_hash']):x['filename'] for x in mod_data['files']}
    file_idrkdata = read_fdata_for_idrk_information(file_filename)
    try:
        filedata, _, filename = read_fdata_file(file_filename, 0)
        if file_idrkdata[0]['name_tkid'] in mod_filenames:
            filename = mod_filenames[file_idrkdata[0]['name_tkid']]
        if os.path.exists(filename) and (overwrite == False):
            if str(input("{} already exists! Overwrite? (y/N) ".format(filename))).lower()[0:1] == 'y':
                overwrite = True
        if (overwrite == True) or not os.path.exists(filename):
            open(filename, 'wb').write(filedata)
    except zlib.error as e:
        print("Extraction of {} failed! Skipping...".format(file_filename))
        print("ZLib error: {}".format(str(e)))
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
        parser.add_argument('fdata_file', help="Name of fdata file to export from (required).")
        args = parser.parse_args()
        if os.path.exists(args.fdata_file) and args.fdata_file[-6:] == '.fdata':
            extract_files_from_fdata(args.fdata_file, overwrite = args.overwrite)
        elif os.path.exists(args.fdata_file) and args.fdata_file[-5:] == '.file':
            extract_files_from_file(args.fdata_file, overwrite = args.overwrite)
    else:
        fdata_files = glob.glob('*.fdata')
        for i in range(len(fdata_files)):
            extract_files_from_fdata(fdata_files[i])
        file_files = glob.glob('*.file')
        for i in range(len(file_files)):
            extract_files_from_file(file_files[i])
