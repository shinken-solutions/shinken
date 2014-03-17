.. _advanced/oncallrotation:

===================
 On-Call Rotations 
===================


Introduction 
=============

.. image:: /_static/images///official/images/objects-contacts.png
   :scale: 90 %

 

.. image:: /_static/images///official/images/objects-timeperiods.png
   :scale: 90 %

Admins often have to shoulder the burden of answering pagers, cell phone calls, etc. when they least desire them. No one likes to be woken up at 4 am to fix a problem. But its often better to fix the problem in the middle of the night, rather than face the wrath of an unhappy boss when you stroll in at 9 am the next morning.

For those lucky admins who have a team of gurus who can help share the responsibility of answering alerts, on-call rotations are often setup. Multiple admins will often alternate taking notifications on weekends, weeknights, holidays, etc.

I'll show you how you can create :ref:`timeperiod <thebasics/timeperiods>` definitions in a way that can facilitate most on-call notification rotations. These definitions won't handle human issues that will inevitably crop up (admins calling in sick, swapping shifts, or throwing their pagers into the river), but they will allow you to setup a basic structure that should work the majority of the time.


Scenario 1: Holidays and Weekends 
==================================

Two admins - John and Bob - are responsible for responding to Shinken alerts. John receives all notifications for weekdays (and weeknights) - except for holidays - and Bob gets handles notifications during the weekends and holidays. Lucky Bob. Here's how you can define this type of rotation using timeperiods...

First, define a timeperiod that contains time ranges for holidays:

  
::

  define timeperiod{
    name    holidays
    timeperiod_name holidays
    january 1    00:00-24:00    ; New Year's Day
    2008-03-23    00:00-24:00    ; Easter (2008)
    2009-04-12    00:00-24:00    ; Easter (2009)
    monday -1 may    00:00-24:00    ; Memorial Day (Last Monday in May)
    july 4    00:00-24:00    ; Independence Day
    monday 1 september    00:00-24:00    ; Labor Day (1st Monday in September)
    thursday 4 november    00:00-24:00    ; Thanksgiving (4th Thursday in November)
    december 25    00:00-24:00    ; Christmas
    december 31    17:00-24:00    ; New Year's Eve (5pm onwards)
   }
  
Next, define a timeperiod for John's on-call times that include weekdays and weeknights, but excludes the dates/times defined in the holidays timeperiod above:

  
::

  define timeperiod{
    timeperiod_name    john-oncall
    monday    00:00-24:00
    tuesday    00:00-24:00
    wednesday    00:00-24:00
    thursday    00:00-24:00
    friday    00:00-24:00
    exclude     holidays    ; Exclude holiday dates/times defined elsewhere
  }
  
You can now reference this timeperiod in John's contact definition:

  
::

  define contact{
    contact_name    john
    ...
    host_notification_period    john-oncall
    service_notification_period    john-oncall
  }
  
Define a new timeperiod for Bob's on-call times that include weekends and the dates/times defined in the holidays timeperiod above:

  
::

  define timeperiod{
    timeperiod_name    bob-oncall
    friday    00:00-24:00
    saturday    00:00-24:00
    use    holidays    ; Also include holiday date/times defined elsewhere
  }
  
You can now reference this timeperiod in Bob's contact definition:

  
::

  define contact{
    contact_name    bob
    ...
    host_notification_period    bob-oncall
    service_notification_period    bob-oncall
  }


Scenario 2: Alternating Days 
=============================

In this scenario John and Bob alternate handling alerts every other day - regardless of whether its a weekend, weekday, or holiday.

Define a timeperiod for when John should receive notifications. Assuming today's date is August 1st, 2007 and John is handling notifications starting today, the definition would look like this:

  
::

  define timeperiod{
    timeperiod_name    john-oncall
    2007-08-01 / 2 00:00-24:00    ; Every two days, starting August 1st, 2007
  }
  
Now define a timeperiod for when Bob should receive notifications. Bob gets notifications on the days that John doesn't, so his first on-call day starts tomorrow (August 2nd, 2007).

  
::

  define timeperiod{
    timeperiod_name    bob-oncall
    2007-08-02 / 2 00:00-24:00    ; Every two days, starting August 2nd, 2007
  }
  
Now you need to reference these timeperiod definitions in the contact definitions for John and Bob:

  
::

  define contact{
    contact_name    john
    ...
    host_notification_period    john-oncall
    service_notification_period    john-oncall
  }
  define contact{
    contact_name    bob
    ...
    host_notification_period    bob-oncall
    service_notification_period    bob-oncall
  }


Scenario 3: Alternating Weeks 
==============================

In this scenario John and Bob alternate handling alerts every other week. John handles alerts Sunday through Saturday one week, and Bob handles alerts for the following seven days. This continues in perpetuity.

Define a timeperiod for when John should receive notifications. Assuming today's date is Sunday, July 29th, 2007 and John is handling notifications this week (starting today), the definition would look like this:

  
::

  define timeperiod{
     timeperiod_name    john-oncall
    2007-07-29 / 14 00:00-24:00    ; Every 14 days (two weeks), starting Sunday, July 29th, 2007
    2007-07-30 / 14 00:00-24:00    ; Every other Monday starting July 30th, 2007
    2007-07-31 / 14 00:00-24:00    ; Every other Tuesday starting July 31st, 2007
    2007-08-01 / 14 00:00-24:00    ; Every other Wednesday starting August 1st, 2007
    2007-08-02 / 14 00:00-24:00    ; Every other Thursday starting August 2nd, 2007
    2007-08-03 / 14 00:00-24:00    ; Every other Friday starting August 3rd, 2007
    2007-08-04 / 14 00:00-24:00    ; Every other Saturday starting August 4th, 2007
  }
  
Now define a timeperiod for when Bob should receive notifications. Bob gets notifications on the weeks that John doesn't, so his first on-call day starts next Sunday (August 5th, 2007).

  
::

  define timeperiod{
    timeperiod_name    bob-oncall
    2007-08-05 / 14 00:00-24:00    ; Every 14 days (two weeks), starting Sunday, August 5th, 2007
    2007-08-06 / 14 00:00-24:00    ; Every other Monday starting August 6th, 2007
    2007-08-07 / 14 00:00-24:00    ; Every other Tuesday starting August 7th, 2007
    2007-08-08 / 14 00:00-24:00    ; Every other Wednesday starting August 8th, 2007
    2007-08-09 / 14 00:00-24:00    ; Every other Thursday starting August 9th, 2007
    2007-08-10 / 14 00:00-24:00    ; Every other Friday starting August 10th, 2007
    2007-08-11 / 14 00:00-24:00    ; Every other Saturday starting August 11th, 2007
  }
  
Now you need to reference these timeperiod definitions in the contact definitions for John and Bob:

  
::

  define contact{
    contact_name    mjohn
    ...
    host_notification_period    john-oncall
    service_notification_period    john-oncall
  }
  define contact{
    contact_name    bob
    ...
    host_notification_period    bob-oncall
    service_notification_period    bob-oncall
  }


Scenario 4: Vacation Days 
==========================

In this scenarios, John handles notifications for all days except those he has off. He has several standing days off each month, as well as some planned vacations. Bob handles notifications when John is on vacation or out of the office.

First, define a timeperiod that contains time ranges for John's vacation days and days off:

  
::

  define timeperiod{
    name    john-out-of-office
    timeperiod_name    john-out-of-office
    day 15    00:00-24:00    ; 15th day of each month
    day -1    00:00-24:00    ; Last day of each month (28th, 29th, 30th, or 31st)
    day -2    00:00-24:00    ; 2nd to last day of each month (27th, 28th, 29th, or 30th)
    january 2    00:00-24:00    ; January 2nd each year
    june 1 - july 5    00:00-24:00    ; Yearly camping trip (June 1st - July 5th)
    2007-11-01 - 2007-11-10 00:00-24:00    ; Vacation to the US Virgin Islands (November 1st-10th, 2007)
  }
  
Next, define a timeperiod for John's on-call times that excludes the dates/times defined in the timeperiod above:

  
::

  define timeperiod{
    timeperiod_name    john-oncall
    monday    00:00-24:00
    tuesday    00:00-24:00
    wednesday    00:00-24:00
    thursday    00:00-24:00
    friday    00:00-24:00
    exclude    john-out-of-office    ; Exclude dates/times John is out
  }
  
You can now reference this timeperiod in John's contact definition:

  
::

  define contact{
    contact_name    john
    ...
    host_notification_period    john-oncall
    service_notification_period    john-oncall
  }
  
Define a new timeperiod for Bob's on-call times that include the dates/times that John is out of the office:

  
::

  define timeperiod{
    timeperod_name    bob-oncall
    use    john-out-of-office    ; Include holiday date/times that John is out
  }
  
You can now reference this timeperiod in Bob's contact definition:

  
::

  define contact{
    contact_name    bob
    ...
    host_notification_period    bob-oncall
    service_notification_period    bob-oncall
  }


Other Scenarios 
================

There are a lot of other on-call notification rotation scenarios that you might have. The date exception directive in :ref:`timeperiod definitions <thebasics/timeperiods>` is capable of handling most dates and date ranges that you might need to use, so check out the different formats that you can use. If you make a mistake when creating timeperiod definitions, always err on the side of giving someone else more on-call duty time. :-)

