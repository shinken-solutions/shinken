#!/usr/bin/env python
#   Autor : David Hannequin <david.hannequin@gmail.com>
#   Date : 29 Nov 2011

#
# Script init
#

import sys
import os
import argparse
import getopt 

# SET Command Generator 
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time

#
# Usage 
#

def usage():
    print 'Usage :'
    print sys.argv[0] + ' -H <hostaddress> -C <community> -w <load1,load5,load15> -c <load1,load5,load15>'
#    print '-p --port : snmp port by default 161' 

#
# Main
#

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hHCwcp:v", ["help", "hostaddress", "community", "warning", "critical", "port" ])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) 
        usage()
        sys.exit(2)
    output = None
    verbose = False

    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-H", "--hostaddress"):
            notification = a
        elif o in ("-C", "--community"):
            notification = a
        elif o in ("-w", "--warning"):
            notification = a
        elif o in ("-c", "--critical"):
            notification = a
        elif o in ("-p", "--port"):
            notification = a
	else :
	    assert False , "unknown options"



if __name__ == "__main__":
    main()
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--hostaddress')
    parser.add_argument('-C', '--community')
    parser.add_argument('-w', '--warning')
    parser.add_argument('-c', '--critical')
    parser.add_argument('-p', '--port')
    args = parser.parse_args()

    hostaddress = args.hostaddress
    community = args.community
    warning = args.warning
    critical = args.critical
	
#    port = int(args.port[1:-1])
    port = 161	

    # Protocol version to use
    pMod = api.protoModules[api.protoVersion1]
    
    # Build PDU
    reqPDU =  pMod.GetRequestPDU()
    pMod.apiPDU.setDefaults(reqPDU)
    pMod.apiPDU.setVarBinds(
        reqPDU, (((1,3,6,1,4,1,2021,10,1,3,1), pMod.Null()),
                 ((1,3,6,1,4,1,2021,10,1,3,2), pMod.Null()),
                 ((1,3,6,1,4,1,2021,10,1,3,3), pMod.Null()))
        )

    # Build message
    reqMsg = pMod.Message()
    pMod.apiMessage.setDefaults(reqMsg)
    pMod.apiMessage.setCommunity(reqMsg, community)
    pMod.apiMessage.setPDU(reqMsg, reqPDU)
    
    def cbTimerFun(timeNow, startedAt=time()):
        if timeNow - startedAt > 5 :
            raise "Request timed out"
        
    def cbRecvFun(transportDispatcher, transportDomain, transportAddress,
                  wholeMsg, reqPDU=reqPDU):
        while wholeMsg:
            rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
            rspPDU = pMod.apiMessage.getPDU(rspMsg)
            # Match response to request
            if pMod.apiPDU.getRequestID(reqPDU)==pMod.apiPDU.getRequestID(rspPDU):
                # Check for SNMP errors reported
                errorStatus = pMod.apiPDU.getErrorStatus(rspPDU)
                if errorStatus:
                    print errorStatus.prettyPrint()
                else:
                    for oid, val in pMod.apiPDU.getVarBinds(rspPDU):
                        print 'Load : %s' % (val.prettyPrint()) 
                transportDispatcher.jobFinished(1)
        return wholeMsg
    
    transportDispatcher = AsynsockDispatcher()
    transportDispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openClientMode()
        )
    transportDispatcher.registerRecvCbFun(cbRecvFun)
    transportDispatcher.registerTimerCbFun(cbTimerFun)
    transportDispatcher.sendMessage(
        encoder.encode(reqMsg), udp.domainName, (hostaddress, port)
        )
    transportDispatcher.jobStarted(1)
    transportDispatcher.runDispatcher()
    transportDispatcher.closeDispatcher()

