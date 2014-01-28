.. _timeperiod:
.. _configuringshinken/configobjects/timeperiod:




=======================
Time Period Definition 
=======================




Description 
============


A time period is a list of times during various days that are considered to be “valid" times for notifications and service checks. It consists of time ranges for each day of the week that “rotate" once the week has come to an end. Different types of exceptions to the normal weekly time are supported, including: specific weekdays, days of generic months, days of specific months, and calendar dates.



Definition Format 
==================


Bold directives are required, while the others are optional.



=================== ===========================================
define timeperiod{                                             
**timeperiod_name** ***timeperiod_name***                      
**alias**           ***alias***                                
[weekday]           *timeranges*                               
[exception]         *timeranges*                               
exclude             [*timeperiod1,timeperiod2,...,timeperiodn*]
}                                                              
=================== ===========================================



Example Definitions 
====================


  
::

  	  define timeperiod{
  	  timeperiod_name         nonworkhours
  	  alias                   Non-Work Hours
  	  sunday                  00:00-24:00              ; Every Sunday of every week
  	  monday                  00:00-09:00,17:00-24:00  ; Every Monday of every week
  	  tuesday                 00:00-09:00,17:00-24:00  ; Every Tuesday of every week
  	  wednesday               00:00-09:00,17:00-24:00  ; Every Wednesday of every week
  	  thursday                00:00-09:00,17:00-24:00  ; Every Thursday of every week
  	  friday                  00:00-09:00,17:00-24:00  ; Every Friday of every week
  	  saturday                00:00-24:00              ; Every Saturday of every week
  	  }
  
  	  define timeperiod{
  	  timeperiod_name         misc-single-days
  	  alias                   Misc Single Days
  	  1999-01-28              00:00-24:00              ; January 28th, 1999
  	  monday 3                00:00-24:00              ; 3rd Monday of every month
  	  day 2                   00:00-24:00              ; 2nd day of every month
  	  february 10             00:00-24:00              ; February 10th of every year
  	  february -1             00:00-24:00              ; Last day in February of every year
  	  friday -2               00:00-24:00              ; 2nd to last Friday of every month
  	  thursday -1 november    00:00-24:00              ; Last Thursday in November of every year
  	  }
  
  	  define timeperiod{
  	  timeperiod_name                 misc-date-ranges
  	  alias                           Misc Date Ranges
  	  2007-01-01 - 2008-02-01         00:00-24:00      ; January 1st, 2007 to February 1st, 2008
  	  monday 3 - thursday 4           00:00-24:00      ; 3rd Monday to 4th Thursday of every month
  	  day 1 - 15                      00:00-24:00      ; 1st to 15th day of every month
  	  day 20 - -1                     00:00-24:00      ; 20th to the last day of every month
  	  july 10 - 15                    00:00-24:00      ; July 10th to July 15th of every year
  	  april 10 - may 15               00:00-24:00      ; April 10th to May 15th of every year
  	  tuesday 1 april - friday 2 may  00:00-24:00      ; 1st Tuesday in April to 2nd Friday in May of every year
  	  }
  
  	  define timeperiod{
  	  timeperiod_name                      misc-skip-ranges
  	  alias                                Misc Skip Ranges
  	  2007-01-01 - 2008-02-01 / 3          00:00-24:00    ; Every 3 days from January 1st, 2007 to February 1st, 2008
  	  2008-04-01 / 7                       00:00-24:00    ; Every 7 days from April 1st, 2008 (continuing forever)
  	  monday 3 - thursday 4 / 2            00:00-24:00    ; Every other day from 3rd Monday to 4th Thursday of every month
  	  day 1 - 15 / 5                       00:00-24:00    ; Every 5 days from the 1st to the 15th day of every month
  	  july 10 - 15 / 2                     00:00-24:00    ; Every other day from July 10th to July 15th of every year
  	  tuesday 1 april - friday 2 may / 6   00:00-24:00    ; Every 6 days from the 1st Tuesday in April to the 2nd Friday in May of every year
  	  }
  


Directive Descriptions 
=======================


   timeperiod_name
  
This directives is the short name used to identify the time period.

   alias
  
This directive is a longer name or description used to identify the time period.

   [weekday]
  
The weekday directives (“*sunday*" through “*saturday*")are comma-delimited lists of time ranges that are “valid" times for a particular day of the week. Notice that there are seven different days for which you can define time ranges (Sunday through Saturday). Each time range is in the form of **HH:MM-HH:MM**, where hours are Specified on a 24 hour clock. For example, **00:15-24:00** means 12:15am in the morning for this day until 12:00am midnight (a 23 hour, 45 minute total time range). If you wish to exclude an entire day from the timeperiod, simply do not include it in the timeperiod definition.

The daterange format are multiples : 
  * Calendar Daterange : look like a standard date, so like 2005-04-04 - 2008-09-19.
  * Month Week Day: Then there are the month week day daterange same than before, but without the year and with day names That give something like : tuesday 2 january - thursday 4 august / 5
  * Now Month Date Daterange: It looks like : february 1 - march 15 / 3
  * Now Month Day Daterange. It looks like day 13 - 14
  * Now Standard Daterange: Ok this time it's quite easy: monday

   [exception]
  
You can specify several different types of exceptions to the standard rotating weekday schedule. Exceptions can take a number of different forms including single days of a specific or generic month, single weekdays in a month, or single calendar dates. You can also specify a range of days/dates and even specify skip intervals to obtain functionality described by “every 3 days between these dates". Rather than list all the possible formats for exception strings, I'll let you look at the example timeperiod definitions above to see what's possible. :-) Weekdays and different types of exceptions all have different levels of precedence, so its important to understand how they can affect each other. More information on this can be found in the documentation on :ref:`timeperiods <thebasics-timeperiods>`.

   exclude
  
This directive is used to specify the short names of other timeperiod definitions whose time ranges should be excluded from this timeperiod. Multiple timeperiod names should be separated with a comma.


.. note::  The day skip functionality is not managed from now, so it's like all is / 1 
