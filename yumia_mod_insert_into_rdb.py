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

# Currently combines all the lang files, so duplicates will not be detected
def parse_lang_files_for_hashes ():
    lang_files = glob.glob('*.lang')
    name_hashes = []
    for lang_file in lang_files:
        with open(lang_file, 'rb') as f:
            f.seek(0,2)
            eof = f.tell()
            f.seek(0)
            while f.tell() < eof:
                name_hash, offset, size = struct.unpack("<3I", f.read(12))
                name_hashes.append(name_hash)
    return list(set(name_hashes))

# Currently combines all the lang files, so duplicates will not be detected
def remove_hashes_from_lang_files (hash_list):
    lang_files = glob.glob('*.lang')
    for lang_file in lang_files:
        if not os.path.exists(lang_file + '.original'):
            shutil.copy2(lang_file, lang_file + '.original')
    for lang_file in lang_files:
        new_lang_file_data = bytearray()
        with open(lang_file + '.original', 'rb') as f: # Always start with original
            f.seek(0,2)
            eof = f.tell()
            f.seek(0)
            while f.tell() < eof:
                name_hash, offset, size = struct.unpack("<3I", f.read(12))
                if not name_hash in hash_list:
                    new_lang_file_data.extend(struct.pack("<3I", name_hash, offset, size))
        with open(lang_file, 'wb') as f:
            f.write(new_lang_file_data)
        filehash = hashlib.file_digest(open(lang_file,'rb'), 'sha256').hexdigest()
        open(lang_file+'.sha256','w').write(filehash)
    return

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    lang_orig_files = [x[:-9] for x in glob.glob('*.lang.original')]
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
                    if os.path.exists(filename+'.sha256'):
                        filehash = open(filename+'.sha256','r').read() # Check each file individually just in case
                        if not filehash == hashlib.file_digest(open(filename,'rb'), 'sha256').hexdigest():
                            shutil.copy2(filename, filename + '.original')
                # Check for .lang.original files, and replace those
                for filename in lang_orig_files:
                    if os.path.exists(filename+'.sha256'):
                        filehash = open(filename+'.sha256','r').read()
                        if not filehash == hashlib.file_digest(open(filename,'rb'), 'sha256').hexdigest():
                            shutil.copy2(filename, filename + '.original')
    all_localized_name_hashes = parse_lang_files_for_hashes ()
    # Load all mods and insert into root.rdb / root.rdx
    mods = glob.glob('*.yumiamod.json')
    mod_data_list = [read_decode_mod_json(x) for x in mods]
    # Detect duplicates between .yumiamod.json files
    seen = {}
    for i in range(len(mod_data_list)):
        name_hash = [x['name_hash'] for x in mod_data_list[i]['files']]
        for hash_ in name_hash:
            if hash_ in seen:
                print("Warning! {0} in {1} will overwrite the same file in {2}.".format(hex(hash_),
                    os.path.basename(mods[i]), os.path.basename(seen[hash_])))
            seen[hash_] = mods[i]
    fdata_indices = append_rdx([x['fdata_hash'] for x in mod_data_list], 'root.rdx')
    idrk_struct = {}
    for i in range(len(mod_data_list)):
        idrk_struct.update(read_fdata_for_rbd_insertion(mod_data_list[i], fdata_indices[i]))
    files_replaced = replace_files_in_rdb('root.rdb', idrk_struct)
    # Report any files that do not exist in root.rdb so were not replaced
    missing_files = [x for x in seen if not x in files_replaced]
    if len(missing_files) > 0:
        print("Warning! These files do not exist in root.rdb, and cannot be replaced via insertion: {}".format(
            [hex(x) for x in missing_files]))
    # Strip localization indices for any inserted files
    if any([x in idrk_struct for x in all_localized_name_hashes]) or len(lang_orig_files) > 0:
        remove_hashes_from_lang_files(list(idrk_struct.keys()))
    # Create file hash signatures (to detect game updates)
    for filename in ['root.rdb', 'root.rdx']:
        filehash = hashlib.file_digest(open(filename,'rb'), 'sha256').hexdigest()
        open(filename+'.sha256','w').write(filehash)