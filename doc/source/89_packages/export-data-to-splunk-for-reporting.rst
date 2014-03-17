.. _export_data_to_splunk_for_reporting:

=============================
Exporting data for reporting 
=============================


Shinken can export necessary data for reporting in 3rd party systems.


Raw_socket module 
==================


The raw socket module exports reporting data using a syslog format to a raw TCP socket. Theses logs can be captured, parsed and indexed by any log management system like Splunk or Logstash.


Why export reporting data 
==========================


Custom UIs like Thruk, Multisite, WebUI, Adagios, Nagios IX, etc. All have poor or inflexible reporting. Simply because these are not reporting engines.

This also permits to have a generic reporting method that can accept data from any Nagios, Shinken, Icinga or even Riemann.


Reporting module using Splunk 
==============================


Splunk was selected as the reporting platform for creating, managing and presenting reports. Though the raw_socket module does not have any Splunk specific particularities. It is notable that Splunk reports can be embedded in any 3rd party UI using its REST API.


Raw_socket log format 
======================


The logs are plain-text and compliant with RFC3164. They use an intelligent date format, a configurable seperator " "(space by default), and key=value pairs in the message data portion of the log. Should a key or value contain a space they must be double quoted. This is syslog using structured data without going to full out JSON that may not be compatible with all log management systems.

The message fields that are supplied in each status update in addition to the standard syslog header are:

  * Hostname
  * Servicename
  * Business impact
  * Host/Service status
  * Host/Service previous status
  * Acknowedgement status
  * Maintenance status

Any time the maintenance, host, service or acknowledgement status changes, a log is sent by the Shinken raw_socket module.

Having all relevant data in each log makes it very easy to compute reports for given time periods.

The hostgroup or service group memberships, custom variables or any other configuration related data should be queried from the monitoring system using its API (Livestatus in the case of Shinken and Nagios).


Raw_socket module availability 
===============================


The module is available in both Shinken 1.4 and Shinken 2.0. The module will be integrated in master branches once unit tests and end-to-end testing is completed. 3rd quarter 2013.

