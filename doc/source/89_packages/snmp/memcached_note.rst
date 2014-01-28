.. _memcached_note:

Memcached Notes
===============

On Ubuntu 12.04 the default instalation is on port 21201 instead of 11211. This causes the error "[SnmpBooster] Memcache server (127.0.0.1:11211) is not reachable" when shinken starts. 

To change it, you must edit the file /etc/memcachedb.conf 
