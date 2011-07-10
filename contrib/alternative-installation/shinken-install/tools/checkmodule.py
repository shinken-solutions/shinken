#!/usr/bin/env python
import sys
import getopt
def main(argv):                         
	try:                                
		opts, args = getopt.getopt(argv, "m:")
		ret=0
		for o, a in opts:
			if o == "-m":
				try:
					exec("import "+a)
					print "OK"
				except:
					print "KO"
					ret=2
	except:           
		ret=1
	sys.exit(ret) 

if __name__ == "__main__":
	main(sys.argv[1:])
