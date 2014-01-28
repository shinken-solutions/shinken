.. _serviceextinfo:
.. _configuringshinken/configobjects/serviceextinfo:




========================================
Extended Service Information Definition 
========================================




Description 
============


Extended service information entries are basically used to make the output from the status and extinfo CGIs look pretty. They have no effect on monitoring and are completely optional.

.. note::   Tip: As of Nagios 3.x, all directives contained in extended service information definitions are also available in service definitions. Thus, you can choose to define the directives below in your service definitions if it makes your configuration simpler. Separate extended service information definitions will continue to be supported for backward compatability.



Definition Format 
==================


Bold directives are required, while the others are optional.



======================= =========================
define serviceextinfo{                           
**host_name**           ***host_name***          
**service_description** ***service_description***
notes                   *notes*                  
notes_url               *notes_url*              
action_url              *action_url*             
icon_image              *image_file*             
icon_image_alt          *alt_string*             
}                                                
======================= =========================




Example Definition 
===================


	define serviceextinfo{
	host_name		linux2
	service_description	Log Anomalies
	notes			Security-related log anomalies on secondary Linux server
	notes_url		http://webserver.localhost.localdomain/serviceinfo.pl?host=linux2&service=Log+Anomalies
	icon_image		security.png 
	icon_image_alt		Security-Related Alerts
	}



Directive Descriptions 
=======================


   host_name
  
This directive is used to identify the short name of the host that the service is associated with.

   service_description
  
This directive is description of the service which the data is associated with.

   notes
  
This directive is used to define an optional string of notes pertaining to the service. If you specify a note here, you will see the it in the :ref:`extended information <thebasics-cgis#thebasics-cgis-extinfo_cgi>` CGI (when you are viewing information about the specified service).

   notes_url
  
This directive is used to define an optional URL that can be used to provide more information about the service. If you specify an URL, you will see a link that says "Extra Service Notes" in the extended information CGI (when you are viewing information about the specified service). Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. /cgi-bin/nagios/). This can be very useful if you want to make detailed information on the service, emergency contact methods, etc. available to other support staff.

   action_url
  
This directive is used to define an optional URL that can be used to provide more actions to be performed on the service. If you specify an URL, you will see a link that says "Extra Service Actions" in the extended information CGI (when you are viewing information about the specified service). Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. /cgi-bin/nagios/).

   icon_image
  
This variable is used to define the name of a GIF, PNG, or JPG image that should be associated with this host. This image will be displayed in the :ref:`status <thebasics-cgis#thebasics-cgis-status_cgi>` and :ref:`extended information <thebasics-cgis#thebasics-cgis-extinfo_cgi>` CGIs. The image will look best if it is 40x40 pixels in size. Images for hosts are assumed to be in the logos/ subdirectory in your HTML images directory (i.e. /usr/local/nagios/share/images/logos).

   icon_image_alt
  
This variable is used to define an optional string that is used in the ALT tag of the image specified by the *<icon_image>* argument. The ALT tag is used in the :ref:`status <thebasics-cgis#thebasics-cgis-status_cgi>`, :ref:`extended information <thebasics-cgis#thebasics-cgis-extinfo_cgi>` and :ref:`statusmap <thebasics-cgis#thebasics-cgis-statusmap_cgi>` CGIs.
