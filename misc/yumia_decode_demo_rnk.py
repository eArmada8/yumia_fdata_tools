# GitHub eArmada8/yumia_fdata_tools

try:
    import json, struct, os, sys
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

    with open('root.rdb.name', 'rb') as f:
        f.seek(0,2)
        eof = f.tell()
        f.seek(0x18)
        names = {}
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
            # Just getting first string
            f.seek(start + string_data_offsets[0])
            name = f.read(string_length[0]).rstrip(b'\xef\xbc\xbd\x00').replace(b'\xef\xbc\x8d',b' - ').replace(b'\xef\xbc\xbb',b' - ')
            names['0x{}'.format(str(hex(name_hash))[2:].zfill(8))] = name.decode()
            f.seek(block_end)
        sorted_dict_items = sorted(names.items(), key=lambda item: item[1])
        sorted_dict = dict(sorted_dict_items)
        open('names.json','wb').write(json.dumps(sorted_dict,indent=4).encode())
