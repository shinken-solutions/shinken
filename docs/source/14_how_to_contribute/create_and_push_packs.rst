.. _create_and_push_packs:


Shinken packs
=============


What are Packs? 
~~~~~~~~~~~~~~~~


Packs are a small subset of configuration files, templates or pictures about a subject, like Linux or windows. It's designed to be a "pack" about how to monitor a specific subject. Everyone can contribute by creating and sending their how packs to the `Shinken community website`_.

Technically, it's a zip file with configuration files and some pictures or templates in it. 

Let take a simple example with a linux pack, with only a CPU and a memory services checks. Files between [] are optional.

  * templates.cfg -> define the host template for the "linux" tag
  * commands.cfg -> define commands for getting CPU and Memory information, like by snmp for example.
  * linux.pack -> json file that describe your pack
  * [discovery.cfg] -> if you got a discovery rule for a "linux" (like a nmap based one), you can add it
  * services/
  * services/cpu.cfg -> Your two services. They must apply to the "linux" host tag!
  * services/memory.cfg
  * [images/sets/tag.png] -> if you want to put a linux logo for all linux host tagged host, it's here. (size = 40x40px, in png format)
  * [templates/pnp/check_cpu.php] -> if your check_cpu command got a PNP4 template
  * [templates/graphite/check_cpu.graph] -> same, but for graphite



What does a .pack file looks like ? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's a json file that describe your "pack". It will give it its name, where it should be installed, and if need give some macros provided by the host tags so it will be easier to configure in the SkonfUI.

Let use our previous Linux sample:
  
::

  
  {
  "name":"linux",
  "description":"Standard linux checks, like CPU, RAM and disk space. Checks are done by SNMP.",
  "path":"os/",
  "macros":{
  
::

         "_SNMPCOMMUNITY": {"type":"string",
                             "description":"The read snmp community allowed on the linux server"
                             },
  
         "_LOAD_WARN": {"type":"string",
                             "description": "Value for starting warning state for the load average at 1m,5m,15m"
                             },
         "_LOAD_CRIT": {"type":"string",
                             "description": "Value for starting critical state for the load average at 1m,5m,15m"
                             },
  
         "_MEM_WARN": {"type":"percent",
                                "description": "Warning level for used disk space"
                             },
         "_MEM_CRIT": {"type":"percent",
                                "description": "Critical level for used disk space"
                             },
  
         "_CPU_WARN": {"type":"percent",
                                "description": "Warning level for the CPU usage"
                             }
        }
  }


Name and description are quite easy to understand. Path is where this pack will be installed on the etc/packs directory for the user (and where it will be push in the community website). It can be a full path, like os/unix/ if you want.

Macros is a hash map of macro names with two values: type and description. Type can be in "string" or "percent" from now. It will give a simple input in SkonfUI for the SNMPCOMMUNITY macro for example, but a "slider" for warning/critical values (so a value between 0 and 100, integer).




How to create a zip pack from a configuration directory? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


If you push a valid .pack in the configuration directory in etc/packs, you will be able to create a zip pack with the shinken-packs command. Let use again our linux sample. For example, the configuration directory with templates.cfg, commands.cfg, discovery.cfg, the linux.pack file and the services directory is in etc/packs/os/linux.

  
::

  shinken-packs -c -s /var/lib/shinken/share -p etc/packs/os/linux/linux.pack
  
It will generate the file /tmp/linux.zip for you. All you need to give to the shinken-packs command is the .pack path, and in option the share path where you have your images and templates directory. The command will automatically parse this directory and take the good image set by looking a the pack name (like configured in the .pack file) and took each template that is available for your commands in the commands.cfg file.

You are done. Your zip pack is done and available in /tmp/linux.zip Congrats! :)




How to share the zip pack to the community website? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The community website is available at `community.shinken-monitoring.org`_. You will need an account to share your zip packs or retrive some new from others community members.



Register on the community website and retrieve your API key 
************************************************************

You can register online at `community.shinken-monitoring.org/register`_ or you can also do it in a CLI way with your shinken-packs command.

.. tip::  You only need to register once. All your packs will be pushed with the same account.

.. note::  You will also need the python-pycurl library, but it should be ok on most distribution already.
You need a valid email for registering (so you can validate your account).

  
::

  bin/shinken-packs -r -l mylogin -P mypassword -e email@google.com
  
.. tip::  If you are behind a proxy, you will need to add a --proxy http://user:password@proxy-server:3128 argument in your shinken-packs command. It will be need for all community calls like registering or pushing zip packs.

You will have an email with a link to validate your email (so we will only spam users that want it :) )

In order to push or retrieve packs you will need an api_key that will be generated when you will validate your account. You can connect to the community website and go in your account panel to get it, or you can get it from the shinken-packs command. 

  
::

  bin/shinken-packs -g --login mylogin -P mypassword
  
It will give you your api_key, something that looks like d9be716aad1d41988ad87b1a454274a50.




Push your zip pack 
*******************


Now you got your can push your /tmp/linux.zip pack and make it available for the community!

  
::

  bin/shinken-packs -u -k d9be716aad1d41988ad87b1a454274a50 -z /tmp/linux.zip
  
Then it's done! You can go to the community website and look at your new shared zip pack. Thanks a lot for sharing :)

.. _community.shinken-monitoring.org: http://community.shinken-monitoring.org
.. _community.shinken-monitoring.org/register: http://community.shinken-monitoring.org/register
.. _Shinken community website: http://community.shinken-monitoring.org
