.. _vmware_arbiter_module:


VMWare Arbiter module
=====================


How it works 
~~~~~~~~~~~~~

The arbiter has a module that allows the host->VM automatic host dependency creation. In fact, the module is far more generic than just this. It's a generic "host link dependencies" module.

It reads a mapping file (simple json format) with son->father links. It call an external script at a regular interval : the one I wrote is a VMWare mapping one. It used the check_esx3.pl (that all ESX admin should have) plugin and generate the mapping file. When this file is changed, the module reloads it, creates new links and deletes old ones. So when you VMotion a virtual machine, in the next pass, there will be creation of a new link and deletion of the old one in the scheduler that manages it :)




How to define it 
~~~~~~~~~~~~~~~~~

The definition is very easy :

  
::

  define module{
       module_name       VMWare_auto_linking
       module_type       hot_dependencies
       mapping_file      /tmp/vmware_mapping_file.json
       mapping_command   /usr/local/shinken/libexec/link_vmware_host_vm.py -x '/usr/local/shinken/libexec/check_esx3.pl' -V 'vcenter.mydomain.com' -u 'admin' -p 'secret' -r 'lower|nofqdn'  -o /tmp/vmware_mapping_file.json
       mapping_command_interval 60   ; optionnal
       mapping_command_timeout   300 ; optionnal
  }
  
Then you add it in you arbiter object :

  
::

  define arbiter {
      [...]
      modules   VMWare_auto_linking
  }
  
So here, it will call the script /usr/local/shinken/libexec/link_vmware_host_vm.py with a listing of the vCenter vcenter.mydomain.com and generate the mapping file /tmp/vmware_mapping_file.json.

You can call :
   /usr/local/shinken/libexec/link_vmware_host_vm.py --help
for the full help on this script.

It looks at the file modification time each second. This command can also be launch by an external cron of course.

.. note::  So if you want to write a script that does this for XEN servers, all you need is to generate a json file with all the mapping. I didn't wrote the doc about this, but you can look in the test file for it, the format is very very easy :)

Here is an example of the JSON mapping file syntax:

%%:ref:`["host", "physical_host"], ["host", "virtual_machine"` <["host", "physical_host"], ["host", "virtual_machine">, :ref:`"host", "physical_host"], ["host", "other_virtual_machine"` <"host", "physical_host"], ["host", "other_virtual_machine">]%%

So just a list of couple 'host' string (from now only host are managed) and the host name.

Beware about it : you need the real host_name, including case.
