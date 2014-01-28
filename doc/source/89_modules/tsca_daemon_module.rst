.. _tsca_daemon_module:





=====================================
TSCA (Thrift Service Check Acceptor) 
=====================================


TSCA is a receiver/arbiter module to receive hosts and services check results. It provides the same functions as NSCA with additional features. High performance binary transmission, multi line output and auto generated clients for a variety of languages. 



What is thrift ? 
=================


Let's cut and paste the wikipedia definition from`en.wikipedia.org/wiki/Apache_Thrift`_ :

"Thrift is an interface definition language that is used to define and create services for numerous languages.[1] It is used as a remote procedure call (RPC) framework [..]. It combines a software stack with a code generation engine to build services that work efficiently to a varying degree and seamlessly between ActionScript, C#, C++ (on POSIX-compliant systems), Cappuccino, Cocoa, Erlang, Haskell, Java, OCaml, Perl, PHP, Python, Ruby, and Smalltalk."



Installation 
=============


In any case, you have to install thrift with support for python (on the server side) and languages you want to use for clients.

Get it from `thrift.apache.org`_ or in your favorite distribution repository.



Server side 
------------


Go to the tsca module directory and generate the python stub for the server side installation

  
::

  cd shinken/modules/tsca
  $ thrift --gen py tsca.thrift
  
Declare the module is shinken-specific.org
  
::

  define module{
        module_name     TSCA
        module_type     tsca_server
        host            0.0.0.0
        port            9090
  }
  
  


Samples clients 
----------------


There are three(3) client samples written in python, ruby and java in contrib/clients/TSCA of the Shinken distribution. You can use and extend them to send data directly in your code directly to Shinken's TSCA receiver/arbiter module.

The samples clients read a CSV file from stdin and send them the the TSCA running on localhost:9090. The CSV has the following format :
  
::

  hostname,service description,output,rc
  
Any use of TCP in an application should take care not to block the program and to have very short timeouts. For applications that need non blocking functions, prefer a UDP based transport or a local buffer file with a separate application(send_nsca, thrift, etc) to forward your data to Shinken.



Ruby 
~~~~~


Generate the stub 
  
::

  $ thrift --gen rb ../../../shinken/modules/tsca/tsca.thrift
  
Run the client
  
::

  $ cat file_state | ruby RubyClient.rb
  


Python 
~~~~~~~


Generate the stub 
  
::

  $ thrift --gen py ../../../shinken/modules/tsca/tsca.thrift
  
Run the client
  
::

  $ cat file_state | python PythonClient.py
  


java 
~~~~~


Generate the stub 
  
::

  $ thrift --gen java ../../../shinken/modules/tsca/tsca.thrift
  
Compile the client
  
::

  $ ant
  
Run the client
  
::

  $ cat file_state | java JavaClientThrift

.. _thrift.apache.org: http://thrift.apache.org
.. _en.wikipedia.org/wiki/Apache_Thrift: http://en.wikipedia.org/wiki/Apache_Thrift