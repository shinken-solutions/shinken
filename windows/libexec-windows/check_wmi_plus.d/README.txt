This directory contains .ini files for check_wmi_plus.pl.
You can see more ini files and upload your own at http://www.edcint.co.nz/checkwmiplus

You can define a specific ini file in the plugin itself or via the command line (--inifile).
That ini file is always read first (if defined).

The location of this directory can be specified in the plugin itself or via the command line (--inidir).
Ini files in this directory are read in the default directory order.
Ini files read later merge with earlier ini files.
For any settings that exist in one or more files, the last one read is set.
