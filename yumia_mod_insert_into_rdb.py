# This script reads all the *.yumiamod.json files (with corresponding *.fdata mods)
# and inserts them into root.rdb and root.rdx.  Backups of the originals will be made,
# and the script will attempt to detect when the game is updated so that it can replace the backups.
#
# Requires yumia_mod_lib.py, place in the same folder as this scripts.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import hashlib, shutil, glob, os, sys
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

    # Check for system updates by comparing the presumed modded files
    if all([os.path.exists(x) for x in ['root.rdb', 'root.rdx', 'root.rdb.sha256', 'root.rdx.sha256',
            'root.rdb.original', 'root.rdx.original']]):
        files_updated_by_game = False
        for filename in ['root.rdb', 'root.rdx']:
            filehash = open(filename+'.sha256','r').read()
            if not filehash == hashlib.file_digest(open(filename,'rb'), 'sha256').hexdigest():
                files_updated_by_game = True
        # If game update has occured, replace the .original files before proceeding
        if files_updated_by_game == True:
            replace = input("Warning!  root.rdb and root.rdx have been changed, has the game been updated? [Y/n] ")
            if len(replace) < 1 or replace[0].upper() == 'Y':
                for filename in ['root.rdb', 'root.rdx']:
                    shutil.copy2(filename, filename + '.original')
    # Load all mods and insert into root.rdb / root.rdx
    mods = glob.glob('*.yumiamod.json')
    mod_data_list = [read_decode_mod_json(x) for x in mods]
    fdata_indices = append_rdx([x['fdata_hash'] for x in mod_data_list], 'root.rdx')
    idrk_struct = {}
    for i in range(len(mod_data_list)):
        idrk_struct.update(read_fdata_for_rbd_insertion(mod_data_list[i], fdata_indices[i]))
    replace_files_in_rdb('root.rdb', idrk_struct)
    # Create file hash signatures (to detect game updates)
    for filename in ['root.rdb', 'root.rdx']:
        filehash = hashlib.file_digest(open(filename,'rb'), 'sha256').hexdigest()
        open(filename+'.sha256','w').write(filehash)