.. _spm:


Shinken Package Manager
=======================

.. important::  I don't now how you get here :)  it's a poc of the design of a shinken pack manager. A pack can be a module, a configuration pack or what ever you want.

A pack can be about :
  * configuration
  * module

Each pack should have a pack.json file that describe it.

  
::

  
  {
  
::

  "name": "linux",
  "version": "1.2",
  "description": "Standard linux checks, like CPU, RAM and disk space. Checks are done by SNMP.",
  "type": "configuration",
  "dependencies": {
     "shinken" : ">1.2"
  },
  "repository": {
    "type": "git",
    "url": "git://github.com/naparuba/pack-cfg-linux.git"
  },
  "keywords": [
    "linux", "snmp"
  ],
  "author": "Jean Gabès <naparuba@gmail.com>",
  "license": "Affero GPLv3",
  "configuration":{
    "path":"os/",
    "macros":{
         "_SNMPCOMMUNITY": {"type":"string",
                             "description":"The read snmp community allowed on the linux server"
                             },
              }
  }
  }


And for a module one :


  
::

  
  {
  
::

  "name": "logstore_mongodb",
  "version": "1.2",
  "description": "Log store module for LiveStatus. Will save the logs into Mongodb.",
  "type": "module",
  "dependencies": {
     "shinken" : ">1.2",
     "livestatus" : ">1.2"
  },
  "repository": {
    "type": "git",
    "url": "git://github.com/naparuba/pack-module-logstore_mongodb.git"
  },
  "keywords": [
    "mongodb", "log", "livestatus"
  ],
  "author": "Gerhard Lausser <>",
  "license": "Affero GPLv3"
  }


The spm command should be really simple to use.

  
::

   spm install linux
This will download the linux pack and put the good files into the rigth place.

  
::

  spm search linux
This will output all the pack with linux in the name or the description.

  
::

  spm create
This will create a .tar.gz file with all inside.

  
::

  spm publish
This will push the .tar.gz file to the registry.shinken-montioring.org website. Will use the ~/.spm/api.key for credentials.

  
::

  spm adduser
This will try to register you to the registry website. If the username you propose is already defined, propose you to login and get your API key.
