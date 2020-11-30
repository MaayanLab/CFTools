# CFTools
Common Fund Tools Signature Commons

This repository contains the schemas and scripts used to build the Common Fund Tools Sigcom instance found in [nih-cfde-tools.org](https://nih-cfde-tools.org)

### In the Sigcom database
1. `Libraries` represent CFDE programs
2. `Signatures` represent tools that their development was supported by a CFDE program (grant)

### To update new tools
Run `/scripts/update_new_tools.py`

The script performs the following operations:

1. Filters tools from BioToolStory website and pushes them into the CFTools website.
2. Backs up the CFTools data (libraries and signatures) by saving a dump csv file for each data type.
3. Refreshes the dynamic figures on the CFTools website.

### To delete a tool/signature
Run function `delete_data` in `/scripts/update_new_tools.py`

### To delete all tools
Run `del_all_tools` in `/scripts/update_new_tools.py`
