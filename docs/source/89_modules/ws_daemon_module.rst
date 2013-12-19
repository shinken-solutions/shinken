.. _ws_daemon_module:



===================
Web Service Module 
===================


The Ws_arbiter module is a Receiver or Arbiter module to receive passive check results from remote hosts via HTTP(s). This module is considered a work in progress but can be used for testing and improvement.




Configuring the Web Service Module 
===================================


If data is POSTed to this page, it will validate the data to determine if it is a service or host check result and submit the data to the Shinken external command queue.

The web service listens by default to TCP port 7760.
The web service supports anonymous or authenticated access.
Web service parameters are set in the Shinken-specific.cfg file, in the Ws_arbiter module.
To enable the web service, simply add the module to your Arbiter or Receiver daemon configuration in Shinken-specific.cfg




Using the Web Service Module 
=============================


The web service listens for POSTs to: /push_check_result

Use curl or embed the HTTP calls in your software to submit check results.


curl -u user:password -d "time_stamp=$(date +%s)&host_name=host-checked&service_description=service-checked&return_code=0&output=Everything OK" http://shinken-srv:7760/push_check_result

Example with more readability:
	
  
::

  curl 

-u user:password 
  -d "time_stamp=$(date +%s)
  
::

  &host_name=host-checked
  &service_description=service-checked
  &return_code=0
  &output=Everything OK
  http://shinken-srv:7760/push_check_result