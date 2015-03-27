.. _contributing/modules:

==================================
Shinken modules
==================================


Packages layout 
================

For a MODULE named ABC (ex: `github.com/shinken-monitoring/mod-ip-tag`_ )
  * etc/modules/abc.cfg
  * module/module.py
  * /__init__.py
  * package.json

That"s ALL!


The package.json file 
======================

The package.json is like this:
  
::
  
  {
    "name": "ip-tag",
    "types": ["module"],
    "version": "1.4.1",
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
==================

Before publishing, you must register an account on `shinken.io`_. Then on your account page on `shinken.io/~`_ you will got your **api_key**. Put it on your ~/.shinken.ini.

Then you can :
  
::

  cd  my-package
  shinken publish


That's all :)

.. _shinken.io/~: http://shinken.io/~
.. _github.com/shinken-monitoring/mod-ip-tag: https://github.com/shinken-monitoring/mod-ip-tag
.. _shinken.io: http://shinken.io
