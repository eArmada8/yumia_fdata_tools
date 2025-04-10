# This script reads all the *.file_metadata.json files and creates a yumiamod.json file.
# It will ask for the filenames of the files (usually the hash plus an extension).
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import glob, json, os, sys
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    fdata_filehash = -1
    while fdata_filehash == -1:
        raw_hash = input("What fdata hash would you like to use? [Omit the '0x', type only the 8 hex digits] ").lstrip("0x")
        try:
            fdata_filehash = int(raw_hash, 16)
        except:
            print("Invalid entry!")
    yumiamod = {'fdata_hash': fdata_filehash}
    files = glob.glob('*.file_metadata.json')
    metadata_list = [json.loads(open(x, 'rb').read()) for x in files]
    file_data = []
    for metadata in metadata_list:
        name_hash = '0x{}'.format(str(hex(metadata['name_hash']))[2:].zfill(8))
        raw_file = input("What filename for {}? [You can drag the game file into the window] ".format(name_hash)).strip("\"")
        file_struct = {'filename': os.path.basename(raw_file)}
        file_struct.update(metadata)
        file_data.append(file_struct)
    yumiamod['files'] = file_data
    with open('0x{}.yumiamod.json'.format(str(hex(fdata_filehash))[2:].zfill(8)),'wb') as f:
        f.write(json.dumps(yumiamod, indent = 4).encode())