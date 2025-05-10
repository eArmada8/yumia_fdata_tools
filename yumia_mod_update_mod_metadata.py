# This script will replace all the metadata in mods using the metadata in the game folder.
# Run in the /Atelier Yumia/Motor/ folder.  It will find all the .yumiamod.json files and
# replace all their metadata.  If there are corresponding .fdata files, the metadata within
# will also be replaced.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import glob, json, os, sys
    from yumia_mod_find_metadata import *
    from yumia_mod_lib import *
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise

def update_mod_json (mod_json_filename, rdb_file = 'root.rdb', rdx_file = 'root.rdx', file_folder = 'data'):
    mod_data = json.loads(open(mod_json_filename, 'rb').read())
    for i in range(len(mod_data['files'])):
        mod_data['files'][i].update(find_file_metadata(mod_data['files'][i]['name_hash'],\
            rdb_file = rdb_file, rdx_file = rdx_file, file_folder = file_folder))
    with open(mod_json_filename, 'wb') as f:
        f.write(json.dumps(mod_data, indent = 4).encode())
    return

def update_mod_fdata (fdata_filename):
    mod_data = read_decode_mod_json(fdata_filename.split('.fdata')[0] + '.yumiamod.json')
    mod_filenames = {(x['name_hash'],x['tkid_hash']):x['filename'] for x in mod_data['files']}
    fdata_files = read_fdata_for_idrk_information(fdata_filename)
    fdata_offsets = {x['name_tkid']: x['offset'] for x in fdata_files}
    fdata = create_empty_fdata()
    for i in range(len(mod_data['files'])):
        name_tkid = (mod_data['files'][i]['name_hash'], mod_data['files'][i]['tkid_hash'])
        if name_tkid in fdata_offsets:
            filedata, _, filename = read_fdata_file(fdata_filename, fdata_offsets[name_tkid])
            fdata = append_to_fdata(fdata, filedata, mod_data['files'][i])
        else:
            input("Warning! {} missing from fdata file! Press Enter to continue".format(mod_data['files'][i]['filename']))
    write_fdata(fdata, mod_data['fdata_hash'])
    return

def update_mod (mod_json_filename, rdb_file = 'root.rdb', rdx_file = 'root.rdx', file_folder = 'data'):
    if os.path.exists(mod_json_filename):
        update_mod_json(mod_json_filename, rdb_file = rdb_file, rdx_file = rdx_file, file_folder = file_folder)
        fdata_filename = mod_json_filename.split('.yumiamod.json')[0] + '.fdata'
        if os.path.exists(fdata_filename):
            update_mod_fdata(fdata_filename)
    return

if __name__ == "__main__":
    # Set current directory
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    if os.path.exists('root.rdb.original') and os.path.exists('root.rdx.original'):
        print("Mods detected, will attempt to use original files.")
        rdb_file = 'root.rdb.original'
        rdx_file = 'root.rdx.original'
    else:
        rdb_file = 'root.rdb'
        rdx_file = 'root.rdx'

    mods = glob.glob('*.yumiamod.json')
    for i in range(len(mods)):
        update_mod(mods[i], rdb_file = rdb_file, rdx_file = rdx_file)