.. _runningshinken-verifyconfig:



Verifying Your Configuration 
=============================


Every time you modify your :ref:`Configuration Overview <configuringshinken-config>`, you should run a sanity check on them. It is important to do this before you (re)start Shinken, as Shinken will shut down if your configuration contains errors.



How to verify the configuration 
--------------------------------


In order to verify your configuration, run Shinken-arbiter with the "-v" command line option like so:

::

  linux:~ # /usr/local/shinken/bin/shinken-arbiter -v -c /usr/local/shinken/etc/nagios.cfg -c /usr/local/shinken/etc/shinken-specific.cfg
  
If you've forgotten to enter some critical data or misconfigured things, Shinken will spit out a warning or error message that should point you to the location of the problem. Error messages generally print out the line in the configuration file that seems to be the source of the problem. On errors, Shinken will exit the pre-flight check. If you get any error messages you'll need to go and edit your configuration files to remedy the problem. Warning messages can generally be safely ignored, since they are only recommendations and not requirements.



Important caveats 
------------------



1. Shinken will not check the syntax of module variables
2. Shinken will not check the validity of data passed to modules
3. Shinken will NOT notify you if you mistyped an expected variable, it will treat it as a custom variable.
4. Shinken sometimes uses variables that expect lists, the order of items in lists is important, check the relevant documentation



How to apply your changes 
--------------------------


Once you've verified your configuration files and fixed any errors you can go ahead and :ref:`(re)start Shinken <runningshinken-startstop>`.

