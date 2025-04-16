# This script will read a kidsobjdb file (and its corresponding .name file if available)
# and write the data into a JSON file.  Thank you to AlexXsWx, whose tool was invaluable
# for understanding these files.
#
# GitHub eArmada8/yumia_fdata_tools

try:
    import json, struct, os, sys, glob
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise   

def read_kidsobjdb_name (kidsobjdb_namefile):
    with open(kidsobjdb_namefile, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0x0)
        magic = f.read(8)
        if magic == b'_RNK0000':
            entry_size, platform, num_entries, file_size = struct.unpack("<4I", f.read(16))
            all_name_entries = {}
            problems = []
            while f.tell() < eof:
                start = f.tell()
                magic = f.read(8)
                assert magic == b'IRNK0000'
                entry_size, name_hash, num_strings = struct.unpack("<3I", f.read(12))
                string_data_offsets = struct.unpack("<{}I".format(num_strings), f.read(num_strings * 4))
                string_data_temp = list(string_data_offsets) + [entry_size]
                string_length = []
                for i in range(len(string_data_offsets)):
                    string_length.append(string_data_temp[i+1] - string_data_temp[i])
                if entry_size % 4 == 0:
                    block_end = start + entry_size
                else:
                    block_end = start + entry_size + 4 - (entry_size % 4)
                strings = []
                for i in range(num_strings):
                    f.seek(start + string_data_offsets[i])
                    bstring = f.read(string_length[i]).rstrip(b'\x00').replace(b'\xef\xbc\x8d',b'-').replace(b'\xef\xbc\xbb',b'[').replace(b'\xef\xbc\xbd',b']')
                    strings.append(bstring.decode())
                all_name_entries[name_hash] = strings
                f.seek(block_end)
            return(all_name_entries)
        else:
            return({})

def read_kidsobjdb (kidsobjdb_file, kidsobjdb_namefile = '', ask_for_namefile = True):
    with open(kidsobjdb_file, 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0x0)
        problems = []
        magic = f.read(8)
        assert magic == b'_DOK0000'
        entry_size, platform, num_entries = struct.unpack("<3I", f.read(12))
        kidsobjdb_namefile_hash, file_size = struct.unpack("<2I", f.read(8))
        strings = {}
        if not kidsobjdb_namefile == '':
            pass # Filename already provided
        elif os.path.exists(kidsobjdb_file + '.name'):
            kidsobjdb_namefile = kidsobjdb_file + '.name'
        elif os.path.exists(kidsobjdb_file.split('.kidsobjdb')[0] + '.name'):
            kidsobjdb_namefile = kidsobjdb_file.split('.kidsobjdb')[0] + '.name'
        elif os.path.exists("0x{}.name".format(str(hex(kidsobjdb_namefile_hash))[2:].zfill(8))):
            kidsobjdb_namefile = "0x{}.name".format(str(hex(kidsobjdb_namefile_hash))[2:].zfill(8))
        else:
            if ask_for_namefile == True:
                print("The expected filename for the name file is 0x{}.name (.bf6b52c7).".format(str(hex(kidsobjdb_namefile_hash))[2:].zfill(8)))
                raw_kidsobjdb_namefile = input("Input name file location: (or press Enter to skip) ")
                if os.path.exists(raw_kidsobjdb_namefile):
                    kidsobjdb_namefile = raw_kidsobjdb_namefile
                else:
                    print("File not found, skipping name integration.")
                    kidsobjdb_namefile = ''
        if not kidsobjdb_namefile == '' and os.path.exists(kidsobjdb_namefile) and os.path.getsize(kidsobjdb_namefile) > 0:
            strings = read_kidsobjdb_name(kidsobjdb_namefile)
        all_values = []
        while f.tell() < eof:
            start = f.tell()
            magic = f.read(8)
            assert magic in [b'IDOK0000', b'RDOK0000']
            if magic == b'IDOK0000':
                entry_size, prop_name, prop_typename, prop_count = struct.unpack("<4I", f.read(16))
                entry = {'name_hash': prop_name, 'type_hash': prop_typename}
                strings_avail = False
                if prop_name in strings:
                    strings_avail = True
                    entry['name'] = strings[prop_name][0]
                    string_counter = 1
                if strings_avail == True and string_counter < len(strings[prop_name]):
                    entry['type'] = strings[prop_name][string_counter]
                    string_counter += 1
                pheaders = []
                for i in range(prop_count):
                    pheader = {}
                    pheader['type'], pheader['num_values'], pheader['name_hash'] = struct.unpack("<3I", f.read(12))
                    pheaders.append(pheader)
                pvalues = []
                for pheader in pheaders:
                    pvalue = {'name_hash': pheader['name_hash'], 'type': pheader['type']}
                    if pheader['type'] in [0,1,2,3,4,5,8,10,12,13]:
                        bin_type = {0:'b', 1:'B', 2:'h', 3:'H', 4:'i', 5:'I', 8:'f', 10:'4f', 12:'2f', 13:'3f'}[pheader['type']]
                        bin_size = {0:1, 1:1, 2:2, 3:2, 4:4, 5:4, 8:4, 10:16, 12:8, 13: 12}[pheader['type']]
                        values = []
                        for _ in range(pheader['num_values']):
                            value = {}
                            val = struct.unpack("<{}".format(bin_type), f.read(bin_size))
                            if pheader['type'] < 10:
                                val = val[0]
                            else:
                                val = list(val)
                            value['value'] = val
                            if strings_avail == True and string_counter < len(strings[prop_name]):
                                value['name'] = strings[prop_name][string_counter]
                                string_counter += 1
                            values.append(value)
                        pvalue['value'] = values
                    else:
                        problems.append(start)
                        pass
                    pvalues.append(pvalue)
                entry['values'] = pvalues
                all_values.append(entry)
            else: #RDOK
                entry_size, = struct.unpack("<I", f.read(4))
                f.seek(start + entry_size) # Pass over RDOK, implementation of RDOK at some future date maybe
            while not (f.tell() % 4 == 0):
                f.seek(1,1)
        return(all_values)

def process_kidsobjdb (kidsobjdb_file, kidsobjdb_namefile = '', overwrite = False):
    print("Processing {}...".format(kidsobjdb_file))
    kidsobjdb_data = read_kidsobjdb (kidsobjdb_file, kidsobjdb_namefile = kidsobjdb_namefile)
    json_filename = kidsobjdb_file + '.json'
    if os.path.exists(json_filename) and (overwrite == False):
        if str(input(json_filename + " exists! Overwrite? (y/N) ")).lower()[0:1] == 'y':
            overwrite = True
    if (overwrite == True) or not os.path.exists(json_filename):
        open(json_filename, 'wb').write(json.dumps(kidsobjdb_data, indent=4).encode('utf-8'))
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
        parser.add_argument('-n', '--namefile', help="Name of corresponding name file", action="store", type=ascii, default="")
        parser.add_argument('kidsobjdb_filename', help="Name of kidsobjdb file to export from (required).")
        args = parser.parse_args()
        if os.path.exists(args.kidsobjdb_filename) and args.kidsobjdb_filename[-9:] == '.kidsobjdb':
            process_kidsobjdb(args.kidsobjdb_filename, args.namefile, overwrite = args.overwrite)
    else:
        kidsobjdb_files = glob.glob('*.kidsobjdb')
        for i in range(len(kidsobjdb_files)):
            process_kidsobjdb(kidsobjdb_files[i])