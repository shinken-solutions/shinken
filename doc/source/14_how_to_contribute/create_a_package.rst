.. _create_a_package:


Shinken modules and Shinken packs
=================================


Packages layout 
~~~~~~~~~~~~~~~~

For a MODULE named ABC (ex: `github.com/shinken-monitoring/mod-ip-tag`_ )
  * etc/modules/abc.cfg
  * module/module.py
  *       /__init__.py
  * package.json

That"s ALL!

For a PACK named ABC (for an example look at github.com/shinken-monitoring/pack-linux-snmp
  
::

   pack/templates.cfg
        /services/
        /commands.cfg
        […....]
   share/images/sets/ABC/tag.png  (if need)
        /templates/graphite/mycommand.graph
  
  


The package.json file 
~~~~~~~~~~~~~~~~~~~~~~

The package.json is like this for a PACK:
  
::

  
  {
  
::

   "name": "linux-snmp",
   "types": ["pack"],
   "version": "1.4",
   "homepage": "https://github.com/shinken-monitoring/pack-linux-snmp",
   "author": "Jean Gabès",
   "description": "Linux checks based on SNMP",
   "contributors": [
      {
         "name": "Jean Gabès",
         "email": "naparuba@gmail.com"
      }
   ],
   "repository": "https://github.com/shinken-monitoring/pack-linux-snmp",
   "keywords": [
      "pack",
      "linux",
      "snmp"
   ],
   "dependencies": {
      "shinken": ">=1.4"
   },
   "license": "AGPL"
  }


And for a module :
  
::

  
  {
  
::

  "name": "ip-tag",
  "types": ["module"],
  "version": "1.4",
  "homepage": "http://github.com/shinken-monitoring/mod-ip-tag",
  "author": "Jean Gabès",
  "description": "Tag host by their IP ranges",
  "contributors": [
    {
      "name": "Jean Gabès",
      "email": "naparuba@gmail.com"
    }
  ],
  "repository": "https://github.com/shinken-monitoring/mod-ip-tag",
  "keywords": [
    "module",
    "arbiter",
    "ip"
  ],
  "dependencies": {
    "shinken": ">=1.4"
  },
  "license": "AGPL"
  }





How to publish it 
~~~~~~~~~~~~~~~~~~

Before publishing, you must register an account on `shinken.io`_. Then on your account page on `shinken.io/~`_ you will got your **api_key**. Put it on your ~/.shinken.ini.

Then you can :
  
::

  cd  my-package
  shinken publish
That's all :)

.. note::  currently the integration process is a script on the shinken.io website, so you need to ask naparuba@gmail.com to launch it before he take time to put it on a cron :) ).
.. _shinken.io/~: http://shinken.io/~
.. _github.com/shinken-monitoring/mod-ip-tag: https://github.com/shinken-monitoring/mod-ip-tag
.. _shinken.io: http://shinken.io
