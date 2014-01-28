.. _multiple_urls:



Multiple action urls 
=====================


Since version <*insert the version number here*>, multiple action urls can be set for a service.

Syntax is : 

  
::

  
  define service {
   service_description name of the service
   [...]
   action_url URL1,ICON1,ALT1|URL2,ICON2,ALT2|URL3,ICON3,ALT3
  }


  * URLx are the url you want to use
  * ICONx are the images you want to display the link as. It can be either a local file, relative to the folder webui/plugins/eltdetail/htdocs/ or an url.
  * ALTx are the alternative texts you want to display when the ICONx file is missing, or not set.