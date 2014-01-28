.. _amazon_ec3_import_module:



Amazon AWS/EC2 import 
======================




Description 
------------


You can import data from Amazon AWS/EC3 `AWS`_ into Shinken to create hosts.

Amazon provide VM hosting with EC3. With this arbiter module, you will be able to load your EC2 hosts into Shinken.



Prerequisites 
--------------


   You will need the `libcloud`_ package installed on your Arbiter server.
  


Configuring the Landscape import module 
----------------------------------------


In your shinken-specific.cfg file, just add (or uncomment):



::

  define module {
   module_name      AWS
   module_type      aws_import
   
   # Configure your REAL key and secret for AWS
   api_key              PAAAB2CILT80I0ZA0999
   secret           GGtWAAAzEItz0utWUeCe9BJKIYWX/hdSbA6YCHHH
   default_template generic-host        ; if the host is not tagged, use this one
   }
  
  

* Put in key and secret your private Landscape access.
  * default_template will be used if your host is not "tagged" in Landscape



Configuring the Arbiter module 
-------------------------------


And add it in your Arbiter object as a module.
  
::

  define arbiter{
       arbiter_name     Arbiter-Master
       
       address          localhost                   ;IP or DNS adress
       port             7770
       spare            0
       modules           AWS
       }
  
Restart your Arbiter and it's done :)



Generated hosts 
----------------

The configuration generated will look as below :

  
::

  define host {
      host_name            i-3fc56e5a
      address              8.8.4.4
      use                  t1.micro,MyTag,EC2,generic-host
      _EC2_AVAILABILITY    us-east-1a
      _EC2_CLIENTTOKEN    
      _EC2_DNS_NAME    
      _EC2_GROUPS          quicklaunch-1
      _EC2_IMAGEID         ami-1b814f72
      _EC2_INSTANCEID      i-3fc56e5a
      _EC2_INSTANCETYPE    t1.micro
      _EC2_KERNELID        aki-825ea7eb
      _EC2_KEYNAME         testaws
      _EC2_LAUNCHDATETIME  2012-09-26T12:19:38.000Z
      _EC2_LAUNCHINDEX     0
      _EC2_PRIVATE_DNS    
      _EC2_PRIVATE_IP    
      _EC2_PRODUCTCODE    
      _EC2_PUBLIC_IP       8.8.4.4
      _EC2_RAMDISKID       None
      _EC2_STATUS          stopped
      _EC2_TAGS            demo:myvalue,use:MyTag
   }
  
Here with a stopped t1.micro instance with no name. You can put your how "use" parameter by adding a EC2 tag "use" on your VM. It will be output on the host configuration so you can setup the monitoring as you want.
.. _libcloud: http://libcloud.apache.org/index.html
.. _AWS: https://console.aws.amazon.com
