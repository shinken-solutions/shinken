from pexpect import *
child = spawn ('/bin/sh -c "ping -c 1 localhsot"')
try:
	child.expect_exact(EOF, timeout=5)
	print child.__dict__
	child.terminate(force=True)	
	print "Status:", child.exitstatus
	print "Alive!"
	#print child.isalive()
except TIMEOUT:
	print "On le kill"
	child.terminate(force=True)
