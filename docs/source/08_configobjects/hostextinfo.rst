.. _hostextinfo:
.. _configuringshinken/configobjects/hostextinfo:




=====================================
Extended Host Information Definition 
=====================================




Description 
============


Extended host information entries are basically used to make the output from the status, statusmap, statuswrl, and extinfo CGIs look pretty. They have no effect on monitoring and are completely optional.

.. note::  Tip: As of Nagios 3.x, all directives contained in extended host information definitions are also available in host definitions. Thus, you can choose to define the directives below in your host definitions if it makes your configuration simpler. Separate extended host information definitions will continue to be supported for backward compatability.



Definition Format 
==================


Bold directives are required, while the others are optional.



=================== =========================
define hostextinfo{                          
**host_name**       ***host_name***          
notes               *notes*                  
notes_url           *notes_url*              
action_url          *action_url*             
icon_image          *image_file*             
icon_image_alt      *alt_string*             
vrml_image          *image_file*             
statusmap_image     *image_file*             
2d_coords           *x_coord,y_coord*        
3d_coords           *x_coord,y_coord,z_coord*
}                                            
=================== =========================




Example Definition 
===================



	define hostextinfo{
	host_name	netware1
	notes		This is the primary Netware file server
	notes_url	http://webserver.localhost.localdomain/hostinfo.pl?host=netware1
	icon_image	novell40.png 
	icon_image_alt	IntranetWare 4.11
	vrml_image	novell40.png
	statusmap_image	novell40.gd2
	2d_coords	100,250
	3d_coords	100.0,50.0,75.0
	}



Directive Descriptions 
=======================


   host_name
  
This variable is used to identify the short name of the host which the data is associated with.

   notes
  
This directive is used to define an optional string of notes pertaining to the host. If you specify a note here, you will see the it in the :ref:`extended information <thebasics-cgis#thebasics-cgis-extinfo_cgi>` CGI (when you are viewing information about the specified host).

   notes_url
  
This variable is used to define an optional URL that can be used to provide more information about the host. If you specify an URL, you will see a link that says "Extra Host Notes" in the extended information CGI (when you are viewing information about the specified host). Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. /cgi-bin/nagios/). This can be very useful if you want to make detailed information on the host, emergency contact methods, etc. available to other support staff.

   action_url
  
This directive is used to define an optional URL that can be used to provide more actions to be performed on the host. If you specify an URL, you will see a link that says "Extra Host Actions" in the extended information CGI (when you are viewing information about the specified host). Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. /cgi-bin/nagios/).

   icon_image
  
This variable is used to define the name of a GIF, PNG, or JPG image that should be associated with this host. This image will be displayed in the status and extended information CGIs. The image will look best if it is 40x40 pixels in size. Images for hosts are assumed to be in the logos/ subdirectory in your HTML images directory (i.e. /usr/local/nagios/share/images/logos).

   icon_image_alt
  
This variable is used to define an optional string that is used in the ALT tag of the image specified by the *<icon_image>* argument. The ALT tag is used in the status, extended information and statusmap CGIs.

   vrml_image
  
This variable is used to define the name of a GIF, PNG, or JPG image that should be associated with this host. This image will be used as the texture map for the specified host in the :ref:`statuswrl <thebasics-cgis#thebasics-cgis-statuswrl_cgi>` CGI. Unlike the image you use for the <icon_image> variable, this one should probably not have any transparency. If it does, the host object will look a bit wierd. Images for hosts are assumed to be in the logos/ subdirectory in your HTML images directory (i.e. /usr/local/nagios/share/images/logos).

   statusmap_image
  
This variable is used to define the name of an image that should be associated with this host in the :ref:`statusmap <thebasics-cgis#thebasics-cgis-statusmap_cgi>` CGI. You can specify a JPEG, PNG, and GIF image if you want, although I would strongly suggest using a GD2 format image, as other image formats will result in a lot of wasted CPU time when the statusmap image is generated. GD2 images can be created from PNG images by using the pngtogd2 utility supplied with Thomas Boutell's gd library. The GD2 images should be created in uncompressed format in order to minimize CPU load when the statusmap CGI is generating the network map image. The image will look best if it is 40x40 pixels in size. You can leave these option blank if you are not using the statusmap CGI. Images for hosts are assumed to be in the logos/ subdirectory in your HTML images directory (i.e. /usr/local/nagios/share/images/logos).

   2d_coords
  
This variable is used to define coordinates to use when drawing the host in the :ref:`statusmap <thebasics-cgis#thebasics-cgis-statusmap_cgi>` CGI. Coordinates should be given in positive integers, as they correspond to physical pixels in the generated image. The origin for drawing (0,0) is in the upper left hand corner of the image and extends in the positive x direction (to the right) along the top of the image and in the positive y direction (down) along the left hand side of the image. For reference, the size of the icons drawn is usually about 40x40 pixels (text takes a little extra space). The coordinates you specify here are for the upper left hand corner of the host icon that is drawn. Note: Don't worry about what the maximum x and y coordinates that you can use are. The CGI will automatically calculate the maximum dimensions of the image it creates based on the largest x and y coordinates you specify.

   3d_coords
  
This variable is used to define coordinates to use when drawing the host in the :ref:`statuswrl <thebasics-cgis#thebasics-cgis-statuswrl_cgi>` CGI. Coordinates can be positive or negative real numbers. The origin for drawing is (0.0,0.0,0.0). For reference, the size of the host cubes drawn is 0.5 units on each side (text takes a little more space). The coordinates you specify here are used as the center of the host cube.
