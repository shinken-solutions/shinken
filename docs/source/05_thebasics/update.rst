.. _update:



Update Shinken 
---------------


  - grab the latest shinken archive and extract its content
  - cd into the resulting folder
  - backup shinken configuration plugins and addons and copy the backup id: 

::

  ./install -b</code>


.. warning::  Be careful with your add-ons...Actually Shinken's install script does NOT backs up all add-on configuration files...Take a look at saved files (usually at /opt/backup/bck-shinken.YYYYMMDDhhmmss.tar.gz, need uncompress before search) and check what is and what is not saved before remove. Install script can be easyly improved by adding few lines for other folders at functions "backup" and "restore", see NAGVIS or PNP examples
  - remove shinken (if you installed addons with the installer say no to the question about removing the addons): <code>./install -u
  - install the new version: 

::

  ./install -i</code>
  - restore the backup: <code>./install -r backupid

.. important::  It's recommended to pull stable version from git. Current master version may be not safe. Please use tagged release. 
   List (not full) of git tags : 1.0rc1, 1.2rc2
   
