.. _setup_macro_modulations:


=================
Macro modulations
=================


How macros modulations works 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


It's a good idea to have macros for critical/warning levels on the host or its templates. But sometime even with this, it can be hard to manage such cases wher you want to have high levels during the night, and a lower one during the day.

macro_modulations is made for this.



How to define a macro_modulation 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  
::

  define  macromodulation{
        macromodulation_name            HighDuringNight
        modulation_period               night
        _CRITICAL                       20
        _WARNING                        10
  }
  
  
  define host{
    check_command                  check_ping
    check_period                   24x7
    host_name                      localhost
    use                            generic-host
    macromodulations               HighDuringNight
    _CRITICAL                      5
    _WARNING                       2
  }
  
With this, the services will get 5 and 2 for the threshold macros during the day, and will automatically get 20 and 10 during the night timeperiod. You can have as many  modulations as you want. **The first modulation enabled will take the lead.**
