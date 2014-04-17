.. _integration/specific-cgi-parameters:

The parameters below are deprecated and are **only** useful if you use the old Nagios CGI UI. 

=============
Nagios CGI UI
=============


.. _integration/specific-cgi-parameters#object_cache_file:

Object Cache File 
==================

Format:
  
::

  object_cache_file=<file_name>
  
Example:
  
::

  object_cache_file=/var/lib/shinken/objects.cache
  
This directive is used to specify a file in which a cached copy of :ref:`Object Configuration Overview <configuration/configobject>` should be stored. The cache file is (re)created every time Shinken is (re)started.


.. _integration/specific-cgi-parameters#temp_file:

Temp File 
==========

======== ==========================================
Format:  temp_file=<file_name>                     
Example: temp_file=/var/lib/shinken/nagios.tmp
======== ==========================================

This is a temporary file that Nagios periodically creates to use when updating comment data, status data, etc. The file is deleted when it is no longer needed.


.. _integration/specific-cgi-parameters#temp_path:

Temp Path 
==========

======== ====================
Format:  temp_path=<dir_name>
Example: temp_path=/tmp      
======== ====================

This is a directory that Nagios can use as scratch space for creating temporary files used during the monitoring process. You should run **tmpwatch**, or a similiar utility, on this directory occassionally to delete files older than 24 hours.


.. _integration/specific-cgi-parameters#status_file:

Status File 
============

======== ============================================
Format:  status_file=<file_name>                     
Example: status_file=/var/lib/shinken/status.dat
======== ============================================

This is the file that Nagios uses to store the current status, comment, and downtime information. This file is used by the CGIs so that current monitoring status can be reported via a web interface. The CGIs must have read access to this file in order to function properly. This file is deleted every time Nagios stops and recreated when it starts.


Status File Update Interval 
============================

======== ================================
Format:  status_update_interval=<seconds>
Example: status_update_interval=15       
======== ================================

This setting determines how often (in seconds) that Nagios will update status data in the :ref:`Status File <integration/specific-cgi-parameters#status_file>`. The minimum update interval is 1 second.
