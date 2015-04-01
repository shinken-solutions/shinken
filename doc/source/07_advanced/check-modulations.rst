.. _advanced/check-modulations:

=================
Check modulations
=================


How check modulations works
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depending on your configuration you may want to change the check_command during the night.
For example, you want to send more packets for a ping during the night because there is less network activity so that you can get more accurate data.


How to define a check_modulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  define checkmodulation{
    checkmodulation_name     ping_night
    check_command            check_ping_night
    check_period             night
  }



  define host{
    check_command                  check_ping
    check_period                   24x7
    host_name                      localhost
    use                            generic-host
    checkmodulations               ping_night
  }

Here check_ping will be modulated into check_ping_night for the host localhost.