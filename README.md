# Atelier Yumia fdata mod toolset

This is a small collection of scripts to write custom fdata files for Atelier Yumia and inject them into root.rdb / root.rdx in order to replace existing files in the game.  Other platforms / KT games using the fdata/rdb system are not tested, so YMMV.

## Credits

This tool was written referencing fdata_dump by github.com/DeathChaos25 and the code from github.com/eterniti/eternity_common, and has thus benefited from the extensive research that went into creating those tools that was given away for free.  I am eternally grateful, thank you.  I also want to thank jmedia7 for information about modding KT games and fdata/rdb files and github.com/mlleemiles who answered some questions I had about modding fdata files.

## Requirements:
1. Python 3.9 or newer is required for use of this script.  It is free from the Microsoft Store, for Windows users.  For Linux users, please consult your distro.

## How to use

*All scripts require yumia_mod_lib.py to be in the same folder to run.*

### yumia_mod_find_metadata.py
In order to replace files in the game, the file's fdata and rdb metadata are needed.  Run this script in the `/Atelier Yumia/Motor/` folder and input the 8-digit hexadecimal code of the file you want to replace.  For example, if you want to modify Yumia's outfit `0xA34C62FC.g1m`, then type in `A34C62FC` without the `0x` and it will output `a34c62fc.file_metadata.json`.

### yumia_mod_write_yumiamod_json.py
Once you have all your mod files and file_metadata.json files, put them in the folder and run this script.  It will first ask you for an 8-digit hexadecimal code for a new .fdata file - for example type `88888888` to create a `0x88888888.fdata` file.  Be sure to choose a filename that isn't already in use!

It will then ask for the filename of each file corresponding to the 8-digit hexadecimal code for your file_metadata.json file.  For example, following the above example, it will ask you for the filename of `0xA34C62FC`, which would be `0xA34C62FC.g1m`.  You could also just drag 0xA34C62FC.g1m directly into the window and press enter.  The script will remove the path and leave only the filename.

Once complete, it will output your .yumiamod.json file, which in the example would be `0x88888888.yumiamod.json`.

### yumia_mod_write_fdata_files.py
This script will take the mod files and the .yumiamod.json file, and write an .fdata file containing the files listed in the .yumiamod.json file.  Following the example above, place `0x88888888.yumiamod.json` and `0xA34C62FC.g1m` in the folder with the script and run it.  It will write out your `0x88888888.fdata` file.

*Note:* Please consider including your .yumiamod.json file with your mod when sharing it.  This will allow end users to combine multiple mods together using yumia_mod_insert_into_rdb.py.

### yumia_mod_insert_into_rdb.py
This script will take all the .yumiamod.json files and their corresponding .fdata files, and insert them into root.rdb and root.rdx.  This is intended to be run inside `/Atelier Yumia/Motor/`.  Place all your .yumiamod.json and .fdata files with this script in `/Atelier Yumia/Motor/` and run.  If no backup exists, it will write a backup (`root.rdb.original` and `root.rdx.original`).  It will always start from the original backups, so that duplicate mods will not be inserted when run repeatedly.  After running this script, root.rdb and root.rdx will be updated and the mods will have been inserted into the game. 
