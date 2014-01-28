.. _advancedtopics-stalking:




================
 State Stalking 
================




Introduction 
=============


State "stalking" is a feature which is probably not going to used by most users. When enabled, it allows you to log changes in the output service and host checks even if the state of the host or service does not change. When stalking is enabled for a particular host or service, Shinken will watch that host or service very carefully and log any changes it sees in the output of check results. As you'll see, it can be very helpful to you in later analysis of the log files.



How Does It Work? 
==================


Under normal circumstances, the result of a host or service check is only logged if the host or service has changed state since it was last checked. There are a few exceptions to this, but for the most part, that's the rule.

If you enable stalking for one or more states of a particular host or service, Shinken will log the results of the host or service check if the output from the check differs from the output from the previous check. Take the following example of eight consecutive checks of a service:



================ ============== =============================================================================== ============================================================================= ==========================================================================
Service Check #: Service State: Service Check Output:                                                           Logged Normally                                                               Logged With Stalking                                                      
x                OK             RAID array optimal                                                              -                                                                             -                                                                         
x+1              OK             RAID array optimal                                                              -                                                                             -                                                                         
x+2              WARNING        RAID array degraded (1 drive bad, 1 hot spare rebuilding)                       .. image:: /_static/images///official/images/checkmark.png}} 
   :scale: 90 % .. image:: /_static/images///official/images/checkmark.png
   :scale: 90 %
x+3              CRITICAL       RAID array degraded (2 drives bad, 1 host spare online, 1 hot spare rebuilding) .. image:: /_static/images///official/images/checkmark.png}} 
   :scale: 90 % .. image:: /_static/images///official/images/checkmark.png
   :scale: 90 %
x+4              CRITICAL       RAID array degraded (3 drives bad, 2 hot spares online)                         -                                                                             .. image:: /_static/images///official/images/checkmark.png
   :scale: 90 %
x+5              CRITICAL       RAID array failed                                                               -                                                                             .. image:: /_static/images///official/images/checkmark.png
   :scale: 90 %
x+6              CRITICAL       RAID array failed                                                               -                                                                             -                                                                         
x+7              CRITICAL       RAID array failed                                                               -                                                                             -                                                                         
================ ============== =============================================================================== ============================================================================= ==========================================================================

Given this sequence of checks, you would normally only see two log entries for this catastrophe. The first one would occur at service check x+2 when the service changed from an OK state to a WARNING state. The second log entry would occur at service check x+3 when the service changed from a WARNING state to a CRITICAL state.

For whatever reason, you may like to have the complete history of this catastrophe in your log files. Perhaps to help explain to your manager how quickly the situation got out of control, perhaps just to laugh at it over a couple of drinks at the local pub...

Well, if you had enabled stalking of this service for CRITICAL states, you would have events at x+4 and x+5 logged in addition to the events at x+2 and x+3. Why is this? With state stalking enabled, Shinken would have examined the output from each service check to see if it differed from the output of the previous check. If the output differed and the state of the service didn't change between the two checks, the result of the newer service check would get logged.

A similar example of stalking might be on a service that checks your web server. If the **check_http** plugin first returns a WARNING state because of a 404 error and on subsequent checks returns a WARNING state because of a particular pattern not being found, you might want to know that. If you didn't enable state stalking for WARNING states of the service, only the first WARNING state event (the 404 error) would be logged and you wouldn't have any idea (looking back in the archived logs) that future WARNING states were not due to a 404, but rather some text pattern that could not be found in the returned web page.



Should I Enable Stalking? 
==========================


First, you must decide if you have a real need to analyze archived log data to find the exact cause of a problem. You may decide you need this feature for some hosts or services, but not for all. You may also find that you only have a need to enable stalking for some host or service states, rather than all of them. For example, you may decide to enable stalking for WARNING and CRITICAL states of a service, but not for OK and UNKNOWN states.

The decision to to enable state stalking for a particular host or service will also depend on the plugin that you use to check that host or service. If the plugin always returns the same text output for a particular state, there is no reason to enable stalking for that state.



How Do I Enable Stalking? 
==========================


You can enable state stalking for hosts and services by using the stalking_options directive in :ref:`host and service definitions <configuringshinken-configobject>`.



How Does Stalking Differ From Volatile Services? 
=================================================


:ref:`Volatile services <advancedtopics-volatileservices>` are similar, but will cause notifications and event handlers to run. Stalking is purely for logging purposes.



Caveats 
========


You should be aware that there are some potential pitfalls with enabling stalking. These all relate to the reporting functions found in various :ref:`CGIs <thebasics-cgis>` (histogram, alert summary, etc.). Because state stalking will cause additional alert entries to be logged, the data produced by the reports will show evidence of inflated numbers of alerts.

As a general rule, I would suggest that you *not* enable stalking for hosts and services without thinking things through. Still, it's there if you need and want it.

