.. _advanced/result-modulations:

==================
Result modulations
==================


How result modulations works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depending on your configuration you may want to consider a critical state returned by plugin to be only a warning.
For example if you don't want a critical state to be emitted during the night (because it will wake someone up) then you can consider the critical state as a warning.


How to define a result_modulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  define resultmodulation{
    resultmodulation_name     critical_is_warning
    exit_codes_match          2       ; list of code to change
    exit_code_modulation      1       ; code that will be put if the code match
    modulation_period         night    ; period when to apply the modulation
  }

  define host{
    check_command                  check_ping
    check_period                   24x7
    host_name                      localhost
    use                            generic-host
    resultmodulations              critical_is_warning
  }

Here critical from check_ping will be modulated into a warning for the host localhost.