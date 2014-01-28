.. _setup_nrpe_booster_module:



NRPE Module 
------------




What is it 
~~~~~~~~~~~


The NRPE module allows Shinken Pollers to bypass the launch of the check_nrpe process. It reads the check command and opens the connection by itself. It scales the use of NRPE for active supervision of servers hosting NRPE agents.

The command definitions should be identical to the check_nrpe calls.



How to define it 
~~~~~~~~~~~~~~~~~

The definition is very easy (and you probably just have to uncomment it):

  
::

  define module{
       module_name       NrpeBooster
       module_type       nrpe_poller
  }
  
Then you add it to your poller object:

  
::

  define poller {
      [...]
      modules   NrpeBooster
  }
  
Then just tag all your check_nrpe commands with this module:
  
::

  define command {
     command_name   check_nrpe
     command_line   $USER1$/check_nrpe -H $HOSTADRESS$ -c $ARG1$ -a $ARG2$
     module_type    nrpe_poller
  }
That's it. From now on all checks that use this command will use Shinken's NRPE module and will be launched by it.