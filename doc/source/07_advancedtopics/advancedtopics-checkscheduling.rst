.. _advancedtopics-checkscheduling:




===================================
 Service and Host Check Scheduling 
===================================



The scheduling 
===============


The scheduling of Shinken is quite simple. The first scheduling take care of the max_service_check_spread and max_host_check_spread so the time of the first schedule will be in the 

::

 start+max_*_check_spread*interval_length (60s in general) 

if the check_timeperiod agree with it.

.. note::  Shinken do not take care about Nagios \*_inter_check_delay_method : this is always 's' (smart) because other options are just useless for nearly everyone. And it also do not use the \*_interleave_factor too.

Nagios make a average of service by host to make it's dispatch of checks in the first check window. Shinken use a random way of doing it : the check is between t=now and t=min(t from next timeperiod, max_*_check_spread), but in a random way. So you will will have the better distribution of checks in this period, intead of the nagios one where hosts with differents number of services can be agresively checks.

After this first scheduling, the time for the next check is just t_check+check_interval if the timepriod is agree for it (or just the next time available in the timeperiod). In the future, a little random value (like few seconds) will be add for such cases.

