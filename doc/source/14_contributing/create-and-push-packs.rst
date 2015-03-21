.. _contributing/create-and-push-packs:

==============
Shinken packs
==============


What are Packs? 
================

Packs are a small subset of configuration files, templates or pictures about a subject, like Linux or Windows. It's designed to be a "pack" about how to monitor a specific subject. Everyone can contribute by creating and sending their how packs to the `Shinken community website`_.

Technically, it's a zip file with configuration files and some pictures or templates in it.

Let take a simple example with a linux pack, with CPU/Memory/Disk checks via SNMP. Files between [] are optional.

  * pack/templates.cfg -> Define the host template for the "linux-snmp" tag
  * pack/commands.cfg -> Define commands for getting service states
  * [pack/discovery.cfg] -> If you got a discovery rule for a "linux-snmp" (like a nmap based one), you can add it
  * [etc/resource.d/snmp.cfg] -> Resource file, in this example it can be provide default (global) macros $SNMPCOMMUNITY$
  * package.json -> json file that describe your pack
  * services/cpu.cfg -> Your CPU services. They must apply to the "linux-snmp" host tag!
  * services/memory.cfg -> Your Memory services, the same.
  * [libexec/check_snmp_mem.pl] -> Script for execute checks. If script not stable or need to be compiled, you may be don't wanted include this to pack. Best way - place link for download it into file commands.cfg
  * [images/sets/tag.png] -> If you want to put a linux logo for all linux host tagged host, it's here. (size = 40x40px, in png format)
  * [templates/pnp/check_cpu.php] -> If your check_cpu command got a PNP4 template
  * [templates/graphite/check_cpu.graph] -> Same, but for graphite


What does a package.json looks like? 
====================================

It's a json file that describe your "pack". It will give it its name, where it should be installed, and if need give some macros provided by the host tags so it will be easier to configure in the SkonfUI.

Let use our linux-smnp sample:
  
::

  
{
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
        },
        {
            "name": "David Moreau Simard",
            "email": "moi@dmsimard.com"
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


  * name -> The name of your pack. Directory with this name will be created on your /etc/shinken/packs
  * types -> Can be pack or module
  * version -> Pretty simple, the version of pack
  * homepage -> Homepage of pack, is usual a github repo
  * author -> Maintainer of package
  * contributors -> People, who makes changes in this package
  * repository -> Sources
  * keywords -> Help for search via shinken CLI or shinken.io website
  * dependencies -> Describe versions of software need to all works okay. Can provide any strings, besides shinken version

  
How to share the zip pack to the community website? 
====================================================

The community website is available at `shinken.io`_. You will need an account to share your zip packs or retrive some new from others community members. After register put your API key from `shinken.io/~`_ to ~/shinken.ini file.

Now you can push packages:
  
::

  cd my-package
  shinken publish


After 5 minutes you can see your new or updated package on `shinken.io`_ main page.

.. _shinken.io: http://shinken.io
.. _shinken.io/~: http://shinken.io/~
.. _Shinken community website: http://shinken.io
