I just build some of the new nagios-plugins-1.3.1 using cygwin. 
They don't need a full cygwin install, all stuff needed (cygwin1.dll plus the ssl-dlls for some) is included. 

Note that I didn't do a lot of testing with them, but they seem to work for me... 

Included are: 
- check_dummy 
- check_http 
- check_tcp 
- check_udp 
- check_smtp 
- check_time 
- check_ssh 
- negate 
- urlize 