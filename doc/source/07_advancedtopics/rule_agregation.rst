.. _rule_agregation:

================
Aggregation rule
================


Goal 
*****

Got a way to define sort of agregation service for host services.





Sample 1 
*********

::
  
  define host{
   _disks   /,/var,/backup
  }
 
  define service {
   register 0
   description  Disk $KEY$
   check_command   check_disk!$KEY$
  }

  
  define service {
   description All Disks
   check_command   bp_rule!., Disk $_HOSTDISKS$
  }


ok this version sucks, we cannot parse this:
  
::

  bp_rule!., Disk /,/var/backup</code>
  


version 2 (tag based agregation) 
*********************************

::
  
  define host{
   name template
   register 0
  }

  
  define host{
   host_name host1
   use template
   _disks    /,/var,/backup
  }

  
  define service {
   register 0
   description  Disk $KEY$
   check_command   check_disk!$KEY$
   duplicate_foreach _disks
   business_rule_aggregate disks
  }

  
  define service {
   description All Disks
   host_name anyhost
   check_command   bp_rule!host1,a:disks
  }

  
  define service {
   description All Disks template based
   host_name template
   check_command   bp_rule!,a:disks
   register 0
  }

