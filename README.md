# Atelier Yumia fdata mod toolset and ktid decoder

This is a small collection of scripts to write custom fdata files for Atelier Yumia and inject them into root.rdb / root.rdx in order to replace existing files in the game.  There are also tools to assist in finding the textures (g1t files) that are used by models (g1m files) in Atelier Yumia.  Other platforms / KT games using the fdata/rdb system are not tested, so YMMV.

## Credits

This tool was written referencing fdata_dump by github.com/DeathChaos25 and the code from github.com/eterniti/eternity_common, and has thus benefited from the extensive research that went into creating those tools that was given away for free.  I am eternally grateful, thank you.  I also want to thank jmedia7 for information about modding KT games and fdata/rdb files and github.com/mlleemiles who answered some questions I had about modding fdata files.  I also want to thank AlexXsWx and eterniti, whose tools provided me with insight into the kidsobjdb format, and I want to thank woofhat for information about using CharacterEditor.kidssingletondb.kidsobjdb to find character model textures.

## Requirements:
1. Python 3.9 or newer is required for use of this script.  It is free from the Microsoft Store, for Windows users.  For Linux users, please consult your distro.

## FData Tools - How to use

*All scripts require yumia_mod_lib.py to be in the same folder to run.*

### yumia_mod_find_metadata.py
In order to replace files in the game, the file's fdata and rdb metadata are needed.  Run this script in the `/Atelier Yumia/Motor/` folder and input the 8-digit hexadecimal code of the file you want to replace.  For example, if you want to modify Yumia's outfit `0xA34C62FC.g1m`, then type in `A34C62FC` without the `0x` and it will output `a34c62fc.file_metadata.json`.  (If you type the 0x, the script will also accept the value.)

### yumia_mod_write_yumiamod_json.py
Once you have all your mod files and file_metadata.json files, put them in the folder and run this script.  It will first ask you for an 8-digit hexadecimal code for a new .fdata file - for example type `88888888` to create a `0x88888888.fdata` file.  (If you type the 0x, the script will also accept the value.)  Be sure to choose a filename that isn't already in use!

It will then ask for the filename of each file corresponding to the 8-digit hexadecimal code for your file_metadata.json file.  For example, following the above example, it will ask you for the filename of `0xA34C62FC`, which would be `0xA34C62FC.g1m`.  You could also just drag `0xA34C62FC.g1m` directly into the window and press enter.  The script will remove the path and leave only the filename.

Once complete, it will output your .yumiamod.json file, which in the example would be `0x88888888.yumiamod.json`.

### yumia_mod_write_fdata_files.py
This script will take the mod files and the .yumiamod.json file, and write an .fdata file containing the files listed in the .yumiamod.json file.  Following the example above, place `0x88888888.yumiamod.json` and `0xA34C62FC.g1m` in the folder with the script and run it.  It will write out your `0x88888888.fdata` file.

*Note:* Please consider including your .yumiamod.json file with your mod when sharing it.  This will allow end users to combine multiple mods together using `yumia_mod_insert_into_rdb.py`.

### yumia_mod_insert_into_rdb.py
This script will take all the .yumiamod.json files and their corresponding .fdata files, and insert them into `root.rdb` and `root.rdx`.  This is intended to be run inside `/Atelier Yumia/Motor/`.  Place all your .yumiamod.json and .fdata files with this script in `/Atelier Yumia/Motor/` and run.  If no backup exists, it will write a backup (`root.rdb.original` and `root.rdx.original`).  It will always start from the original backups, so that duplicate mods will not be inserted when run repeatedly.  After running this script, `root.rdb` and `root.rdx` will be updated and the mods will have been inserted into the game.

### yumia_mod_extract_files_from_fdata.py
This script will unpack an .fdata file into its component files.  Needed to unpack the files created by yumia_mod_write_fdata_files.py.  This script can also unpack .file files (usually in the /data folder in Atelier Yumia).

### yumia_mod_update_mod_metadata.py
Run in the /Atelier Yumia/Motor folder; this script will find all the .yumiamod.json files (and their corresponding .fdata) files and replace all the included metadata with metadata from the base game.  Meant to be used to fix broken mods, or possibly port mods from one platform to another.  Requires both yumia_mod_lib.py and yumia_mod_find_metadata.py to run.

## KTID Tools - How to use

The KTID tools are meant to be used to find and subsequently mine data from `CharacterEditor.kidssingletondb.kidsobjdb`, a file used by Atelier Yumia and common to other KT games that use .ktid files to point g1m character models to g1t texture packs.  There are two strategies to finding this file.  Both start with identifying a character model (.g1m), by dumping all the .g1m files, filtering by size as character models tend to be larger than other objects, and looking for a character model (my [g1m exporter](https://github.com/eArmada8/gust_stuff) can be used but [Project G1M](https://github.com/Joschuka/Project-G1M) is faster for this application).

In games where the associated KTID and G1M files are kept in the same fdata file (e.g. Atelier Yumia), the KTID file can be directly extracted and used (`yumia_find_kidsobjdb_using_ktid.py`).  If they are not in the same .fdata file, then the slower method of using the .g1m hash is used (`yumia_find_kidsobjdb_using_g1mhash.py`).

To use the searching tools, dump all the .kidsobjdb files into one folder using [qrdbtool](https://github.com/eterniti/qrdbtool) or [fdata_dump](https://github.com/DeathChaos25/fdata_dump).  There are many of these files in a KT game so I recommend only extracting files > 100KB or so, which will dramatically reduce the number of files to search through.  qrdbtool supports sorting the files by size to dramatically reduce extraction time.

### yumia_find_kidsobjdb_using_ktid.py
This script will take a .ktid file, and check its stored hashes against every .kidsobjdb file in a folder and attempt to find a matching file.  If starting with a character model .ktid file, it should find `CharacterEditor.kidssingletondb.kidsobjdb` even if no filenames are available, if that file is present in the folder with the script and .ktid file.  This method is very fast, as the script only reads the indices of the databases and not the contents.  It is also very reliable as it will only flag a match if the entire .ktid hashes properly against the database.

### yumia_find_kidsobjdb_using_g1mhash.py
This script will prompt the use for the 8-digit hexadecimal hash of a .g1m file (e.g. `A34C62FC` for Yumia's default outfit `0xA34C62FC.g1m`), and check that hash against every .kidsobjdb file in a folder and attempt to find a matching file.  If starting with a character model .g1m's hash, it should find `CharacterEditor.kidssingletondb.kidsobjdb` even if no filenames are available, if that file is present in the folder with the script.  This method is slow, as the script must fully parse the database.  It should be reliable in that all matches are real matches, but it may find more than one database that references the model - note that `CharacterEditor.kidssingletondb.kidsobjdb` is fairly large (806 KB in Atelier Yumia for example) so matching files that are small are unlikely to be `CharacterEditor.kidssingletondb.kidsobjdb`.

Once `CharacterEditor.kidssingletondb.kidsobjdb` has been identified with either of the above scripts, either delete all the other .kidsobjdb files or move the correct file to a new folder with yumia_decode_kidsobjdb.py.  I also recommend renaming the file to `CharacterEditor.kidssingletondb.kidsobjdb`; for example if the script identified `0xb290631c.kidsobjdb`, rename `0xb290631c.kidsobjdb` to `CharacterEditor.kidssingletondb.kidsobjdb` and delete all the other .kidsobjdb files (back them up to somewhere else in case you have the wrong file).

### yumia_decode_kidsobjdb.py
This script will decode a .kidsobjdb database into a .json file, for use with the ktid scripts.  Run this script in a folder with `CharacterEditor.kidssingletondb.kidsobjdb`, and it will parse the file.  The first thing it will do is ask for the corresponding `CharacterEditor.kidssingletondb.kidsobjdb.name` file, and it will give the 8-digit hash of the file to ease identification of that file.  (If KT deleted the file from the game install, as in the case of Atelier Yumia, just press Enter to continue, and no names will be incorporated into the JSON.)  The script will output a `CharacterEditor.kidssingletondb.kidsobjdb.json` file which will be used by the following scripts.  *Please note that the kidsobjdb implementation is very incomplete and does not support RDOK blocks at this time.  Its intention is only to decode `CharacterEditor.kidssingletondb.kidsobjdb`.*

Place `CharacterEditor.kidssingletondb.kidsobjdb.json` in a folder with `yumia_find_ktid_with_kidsobjdb.py` and `yumia_decode_ktid_with_kidsobjdb.py`.

### yumia_find_ktid_with_kidsobjdb.py
This script will take a .g1m hash, and search through `CharacterEditor.kidssingletondb.kidsobjdb.json` to find its corresponding .ktid file.  This may not be necessary, if the game packages the .g1m file with its .ktid file in the same .fdata file.  However, this method is likely to be more reliable than .fdata association, since it is using the same database that the game engine is using to find associated files.  It will report all the candidate hashes (usually 3-4), but `CharacterEditor.kidssingletondb.kidsobjdb` does not have enough information to find the true .ktid files.  If it finds either `root.rdb.original` (takes precedence) or `root.rdb` in the same folder, it will use the additional information in the rdb to identify the true .ktid file - be sure to use the original unaltered rdb file!  For example, if you input `4801fc99` for `0x4801FC99.g1m`, it will find `0x05c82502`, meaning `0x05c82502.ktid` is the ktid file associated with `0x4801FC99.g1m`.

### yumia_decode_ktid_with_kidsobjdb.py
This script will take a .ktid file, and search through `CharacterEditor.kidssingletondb.kidsobjdb.json` to decode the contents of the .ktid file.  It will report all the material texture slots, and the filename hashes for all the .g1t texture packs for those slots  (games utilizing this system will only have a single texture in each pack).  The decoded values are written to a .csv file, e.g. `0x05c82502.ktid` will be decoded and all values saved in `0x05c82502.ktid.csv`.  If decoded file names are found (because `CharacterEditor.kidssingletondb.kidsobjdb.name` was available when `yumia_decode_kidsobjdb.py` decoded `CharacterEditor.kidssingletondb.kidsobjdb`), those filenames will also be in the .csv file.

### yumia_grab_textures_using_ktid.py
This script will take a .ktid file, and search through `CharacterEditor.kidssingletondb.kidsobjdb.json` to decode the contents of the .ktid file.  It will then ask for the name of the folder where `root.rdb`, `root.rdx` and all the .fdata files are, e.g. `{Steam}/Atelier Yumia/Motor/`.  It will then extract all the metadata and texture files at once to the current folder, numbered in the order of the .ktid file to match the .g1m material texture slots (e.g. for Yumia, the files will be `000_0x1158305d.g1t` and `000_0x1158305d.file_metadata.json`, so on).  It will always use `root.rdb.original` and `root.rdx.original` to retrieve unmodded files, and if those files do not exist then the script will create them from `root.rdb` and `root.rdx` in a manner identical to `yumia_mod_insert_into_rdb.py`.