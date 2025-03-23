# This script reads all the *.yumiamod.json files (with corresponding *.fdata mods)
# and inserts them into root.rdb and root.rdx.
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
    fdata_indices = append_rdx([x['fdata_hash'] for x in mod_data_list], 'root.rdx')
    idrk_struct = {}
    for i in range(len(mod_data_list)):
        idrk_struct.update(read_fdata_for_rbd_insertion(mod_data_list[i], fdata_indices[i]))
    replace_files_in_rdb('root.rdb', idrk_struct)