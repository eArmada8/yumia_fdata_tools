# This script reads all the *.yumiamod.json files and creates responding fdata files.
# It expects the referenced game files to be present in the same directly as
# the .yumiamod.json file.
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

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    mods = glob.glob('*.yumiamod.json')
    mod_data_list = [read_decode_mod_json(x) for x in mods]
    for mod_data in mod_data_list:
        fdata = create_empty_fdata()
        for i in range(len(mod_data['files'])):
            filedata = open(mod_data['files'][i]['filename'],'rb').read()
            fdata = append_to_fdata(fdata, filedata, mod_data['files'][i])
        write_fdata(fdata, mod_data['fdata_hash'])