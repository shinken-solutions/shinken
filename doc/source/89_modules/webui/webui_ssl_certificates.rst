.. _ssl_certificates:



=======================
WebUI SSL Certification
=======================


Lets start: the goal to to have the server.pem and client.pem file in etc/certs.

Go to the etc/certs directory.
  
::

  
   openssl req -new -nodes -out server.req -keyout server.key -config ./shinken_openssl_cnf
   openssl ca -out server.pem -config ./shinken_openssl_cnf -infiles server.req
   cp server.pem server.pem.bkp
   cp server.key server.pem
   cat server.pem.bkp >> server.pem
   cp server.pem client.pem
  
  
You can try to get the validity with for the arbiter with:
   
::

  openssl s_client -connect localhost:7770</code>
