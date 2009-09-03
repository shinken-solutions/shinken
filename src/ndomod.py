#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


#This class is use to export information into ndo

import socket
import sys

from plugin import Plugin
from macroresolver import MacroResolver

class Ndomod(Plugin):

    macros = {
        'NDO_API_HELLO' : 'NDO_API_HELLO',
        'NDO_API_PROTOCOL' : 'NDO_API_PROTOCOL',
        'NDO_API_PROTOVERSION' : 'NDO_API_PROTOVERSION',
        'NDO_API_AGENT' : 'NDO_API_AGENT',
        'NDOMOD_NAME' : 'NDOMOD_NAME',
        'NDO_API_AGENTVERSION' : 'NDO_API_AGENTVERSION',
        'NDOMOD_VERSION' : 'NDOMOD_VERSION',
        'NDO_API_STARTTIME' : 'NDO_API_STARTTIME',
        'NDO_API_DISPOSITION' : 'NDO_API_DISPOSITION',
        'NDO_API_DISPOSITION_REALTIME' : 'NDO_API_DISPOSITION_REALTIME',
        'NDO_API_CONNECTION' : 'NDO_API_CONNECTION',
        'NDO_API_CONNECTTYPE' : 'NDO_API_CONNECTTYPE',
        'NDO_API_INSTANCENAME' : 'NDO_API_INSTANCENAME',
        'NDO_API_STARTDATADUMP' : 'NDO_API_STARTDATADUMP'
        'NDO_API_PROCESSDATA' : 'NDO_API_PROCESSDATA',
        'NDO_DATA_TYPE' : 'NDO_DATA_TYPE',
        
        }

    def __init__(self):
        self.name = 'ndomod'
        self.NDO_API_HELLO = 'HELLO'
        self.NDO_API_PROTOCOL = 'PROTOCOL'
        self.NDO_API_PROTOVERSION =  '2'
        self.NDO_API_AGENT = 'AGENT'
        self.NDOMOD_NAME = 'NDOMOD'
        self.NDO_API_AGENTVERSION = 'AGENTVERSION'
        self.NDOMOD_VERSION = '1.4b7'
        self.NDO_API_STARTTIME = 'STARTTIME'
        self.NDO_API_DISPOSITION = 'DISPOSITION'
        self.NDO_API_DISPOSITION_REALTIME = 'REALTIME'
        self.NDO_API_CONNECTION = 'CONNECTION'
        self.NDO_API_CONNECTTYPE = 'CONNECTTYPE'
        self.NDO_API_INSTANCENAME = 'INSTANCENAME'
        self.NDO_API_STARTDATADUMP = 'STARTDATADUMP'
        self.NDO_API_PROCESSDATA = '200'
        self.NDO_DATA_TYPE = '1'

    def init(self, args):
        self.m = MacroResolver()
        self.host = 'localhost'    # The remote host
        self.port = 5668           # The same port as used by the server
        self.s = None

        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            self.af, self.socktype, self.proto, self.canonname, self.sa = res
            try:
                self.s = socket.socket(self.af, self.socktype, self.proto)
            except socket.error, msg:
                self.s = None
                continue
            try:
                self.s.connect(self.sa)
            except socket.error, msg:
                self.s.close()
                #self.s = None
                continue
            break

        if self.s is None:
            print 'could not open socket'
            #sys.exit(1)
        
        self.go_for('HELLO_WORLD', [self])
        self.go_for('NEBCALLBACK_PROCESS_DATA', [self])


    def deinit(self):
        pass
    
    '''HELLO
    PROTOCOL: 2
    AGENT: NDOMOD
    AGENTVERSION: 1.4b7
    STARTTIME: 1246891255
    DISPOSITION: REALTIME
    CONNECTION: UNIXSOCKET
    CONNECTTYPE: INITIAL
    INSTANCENAME: Central
    STARTDATADUMP'''
    HELLO_WORLD = "\n\n$NDO_API_HELLO$\n$NDO_API_PROTOCOL$: $NDO_API_PROTOVERSION$\n$NDO_API_AGENT$: $NDOMOD_NAME$\n$NDO_API_AGENTVERSION$: $NDOMOD_VERSION$\n$NDO_API_STARTTIME$: 1246891255\n$NDO_API_DISPOSITION$: $NDO_API_DISPOSITION_REALTIME$\n$NDO_API_CONNECTION$: UNIXSOCKET\n$NDO_API_CONNECTTYPE$: INITIAL\n$NDO_API_INSTANCENAME$: Central\n$NDO_API_STARTDATADUMP$\n\n"


    '''200:
    1=104
    2=0
    3=0
    4=1246891255.997530
    105=Nagios
    107=3.0.5
    104=11-04-2008
    102=11306
    999'''
    NEBCALLBACK_PROCESS_DATA = "\n$NDO_API_PROCESSDATA$:\n$NDO_DATA_TYPE$=104\n$NDO_DATA_FLAGS$=0\n$NDO_DATA_ATTRIBUTES$=0\n$NDO_DATA_TIMESTAMP$=1246891255.997530\n$NDO_DATA_PROGRAMNAME$=Nagios\n$NDO_DATA_PROGRAMVERSION$=3.0.5\n$NDO_DATA_PROGRAMDATE$=11-04-2008\n$NDO_DATA_PROCESSID$=11306\n$NDO_API_ENDDATA$\n\n"


    '''202:
    1=300
    2=0
    3=0
    4=1246891255.997197
    73=1246891255
    74=262144
    72=Event broker module '/usr/local/nagios/bin/ndomod.o' initialized successfully.
    999'''
    NEBCALLBACK_LOG_DATA = "\n$NDO_API_LOGDATA$:\n$NDO_DATA_TYPE$=%d\n$NDO_DATA_FLAGS$=%d\n$NDO_DATA_ATTRIBUTES=%d\n$NDO_DATA_TIMESTAMP$=%ld.%ld\n$NDO_DATA_LOGENTRYTIME$=%lu\n$NDO_DATA_LOGENTRYTYPE=%d\n$NDO_DATA_LOGENTRY$=%s\n$NDO_API_ENDDATA$\n\n"


    '''203:
    1=400
    2=0
    3=0
    4=1246891332.759113
    117=1246891332.759108
    33=0.0
    123=30
    14=/usr/local/nagios/bin/rss-multiuser
    32=0
    42=0.00000
    110=0
    95=
    999'''
    NEBCALLBACK_SYSTEM_COMMAND_DATA = "\n$NDO_API_SYSTEMCOMMANDDATA$:\n$NDO_DATA_TYPE$=%d\n$NDO_DATA_FLAGS$=%d\n$NDO_DATA_ATTRIBUTES$=%d\n$NDO_DATA_TIMESTAMP$=%ld.%ld\n$NDO_DATA_STARTTIME$=%ld.%ld\n$NDO_DATA_ENDTIME$=%ld.%ld\n$NDO_DATA_TIMEOUT$=%d\n$NDO_DATA_COMMANDLINE$=%s\n$NDO_DATA_EARLYTIMEOUT$=%d\n$NDO_DATA_EXECUTIONTIME$=%.5lf\n$NDO_DATA_RETURNCODE$=%d\n$NDO_DATA_OUTPUT$=%s\n$NDO_API_ENDDATA$\n\n"

    
    '''212:
    1=1201
    2=0
    3=0
    4=1246891332.525263
    53=TWN-TAI
    95=(Return code of 127 is out of bounds - plugin may be missing)
    99=
    27=1
    51=1
    115=1
    25=1
    76=10
    58=1246891302
    81=1246891631
    12=0
    63=1224531935
    57=1224531935
    56=1
    69=0
    65=1246891331
    68=0
    121=1
    59=1246891331
    82=1246898531
    85=0
    88=1
    101=0
    7=0
    26=289
    96=1
    38=1
    8=1
    47=1
    54=0
    98=0.00000
    71=1.01200
    42=0.02177
    113=0
    45=1
    103=1
    91=1
    78=0
    37=
    11=check-fake
    86=5.000000
    109=0.000000
    162=
    999'''
    
    NEBCALLBACK_HOST_STATUS_DATA = "\n$NDO_API_HOSTSTATUSDATA$:\n$NDO_DATA_TYPE$=%d\n$NDO_DATA_FLAGS$=%d\n$NDO_DATA_ATTRIBUTES$=%d\n$NDO_DATA_TIMESTAMP$=%ld.%ld\n$NDO_DATA_HOST$=%s\n$NDO_DATA_OUTPUT$=%s\n$NDO_DATA_PERFDATA$=%s\n$NDO_DATA_CURRENTSTATE$=%d\n$NDO_DATA_HASBEENCHECKED$=%d\n$NDO_DATA_SHOULDBESCHEDULED$=%d\n$NDO_DATA_CURRENTCHECKATTEMPT$=%d\n$NDO_DATA_MAXCHECKATTEMPTS$=%d\n$NDO_DATA_LASTHOSTCHECK$=%lu\n$NDO_DATA_NEXTHOSTCHECK$=%lu\n$NDO_DATA_CHECKTYPE$=%d\n$NDO_DATA_LASTSTATECHANGE$=%lu\n$NDO_DATA_LASTHARDSTATECHANGE$=%lu\n$NDO_DATA_LASTHARDSTATE$=%d\n$NDO_DATA_LASTTIMEUP$=%lu\n$NDO_DATA_LASTTIMEDOWN$=%lu\n$NDO_DATA_LASTTIMEUNREACHABLE$=%lu\n$NDO_DATA_STATETYPE$=%d\n$NDO_DATA_LASTHOSTNOTIFICATION$=%lu\n$NDO_DATA_NEXTHOSTNOTIFICATION$=%lu\n$NDO_DATA_NOMORENOTIFICATIONS$=%d\n$NDO_DATA_NOTIFICATIONSENABLED$=%d\n$NDO_DATA_PROBLEMHASBEENACKNOWLEDGED$=%d\n$NDO_DATA_ACKNOWLEDGEMENTTYPE$=%d\n$NDO_DATA_CURRENTNOTIFICATIONNUMBER$=%d\n$NDO_DATA_PASSIVEHOSTCHECKSENABLED$=%d\n$NDO_DATA_EVENTHANDLERENABLED$=%d\n$NDO_DATA_ACTIVEHOSTCHECKSENABLED$=%d\n$NDO_DATA_FLAPDETECTIONENABLED$=%d\n$NDO_DATA_ISFLAPPING$=%d\n$NDO_DATA_PERCENTSTATECHANGE$=%.5lf\n$NDO_DATA_LATENCY$=%.5lf\n$NDO_DATA_EXECUTIONTIME$=%.5lf\n$NDO_DATA_SCHEDULEDDOWNTIMEDEPTH$=%d\n$NDO_DATA_FAILUREPREDICTIONENABLED$=%d\n$NDO_DATA_PROCESSPERFORMANCEDATA$=%d\n$NDO_DATA_OBSESSOVERHOST$=%d\n$NDO_DATA_MODIFIEDHOSTATTRIBUTES$=%lu\n$NDO_DATA_EVENTHANDLER$=%s\n$NDO_DATA_CHECKCOMMAND$=%s\n$NDO_DATA_NORMALCHECKINTERVAL$=%lf\n$NDO_DATA_RETRYCHECKINTERVAL$=%lf\n$NDO_DATA_HOSTCHECKPERIOD$=%s\n"


    '''213:
    1=1202
    2=0
    3=0
    4=1246891263.352029
    53=sbeutrds
    114=NetQueue
    95=OK
    99=VMwareAccelerateOutQueue=0
    27=0
    51=1
    115=1
    25=1
    76=2
    61=1233761671
    83=0
    12=0
    63=1224530367
    57=1224530367
    56=0
    66=1233761671
    70=0
    67=0
    64=0
    121=1
    62=0
    84=0
    85=0
    88=0
    101=0
    7=0
    26=0
    97=1
    38=1
    9=1
    47=1
    54=0
    98=0.00000
    71=380.48100
    42=1.61800
    113=0
    45=1
    103=1
    93=1
    80=0
    37=
    11=check_win_nrpe_qualif_net_queue!2!3
    86=15.000000
    109=15.000000
    209=24x7
    999'''
    NEBCALLBACK_SERVICE_STATUS_DATA = "\n$NDO_API_SERVICESTATUSDATA$:\n$NDO_DATA_TYPE$=%d\n$NDO_DATA_FLAGS$=%d\n$NDO_DATA_ATTRIBUTES$=%d\n$NDO_DATA_TIMESTAMP$=%ld.%ld\n$NDO_DATA_HOST$=%s\n$NDO_DATA_SERVICE$=%s\n$NDO_DATA_OUTPUT$=%s\n$NDO_DATA_PERFDATA$=%s\n$NDO_DATA_CURRENTSTATE$=%d\n$NDO_DATA_HASBEENCHECKED$=%d\n$NDO_DATA_SHOULDBESCHEDULED$=%d\n$NDO_DATA_CURRENTCHECKATTEMPT$=%d\n$NDO_DATA_MAXCHECKATTEMPTS$=%d\n$NDO_DATA_LASTSERVICECHECK$=%lu\n$NDO_DATA_NEXTSERVICECHECK$=%lu\n$NDO_DATA_CHECKTYPE$=%d\n$NDO_DATA_LASTSTATECHANGE$=%lu\n$NDO_DATA_LASTHARDSTATECHANGE$=%lu\n$NDO_DATA_LASTHARDSTATE$=%d\n$NDO_DATA_LASTTIMEOK$=%lu\n$NDO_DATA_LASTTIMEWARNING$=%lu\n$NDO_DATA_LASTTIMEUNKNOWN$=%lu\n$NDO_DATA_LASTTIMECRITICAL$=%lu\n$NDO_DATA_STATETYPE$=%d\n$NDO_DATA_LASTSERVICENOTIFICATION$=%lu\n$NDO_DATA_NEXTSERVICENOTIFICATION$=%lu\n$NDO_DATA_NOMORENOTIFICATIONS$=%d\n$NDO_DATA_NOTIFICATIONSENABLED$=%d\n$NDO_DATA_PROBLEMHASBEENACKNOWLEDGED$=%d\n$NDO_DATA_ACKNOWLEDGEMENTTYPE$=%d\n$NDO_DATA_CURRENTNOTIFICATIONNUMBER$=%d\n$NDO_DATA_PASSIVESERVICECHECKSENABLED$=%d\n$NDO_DATA_EVENTHANDLERENABLED$=%d\n$NDO_DATA_ACTIVESERVICECHECKSENABLED$=%d\n$NDO_DATA_FLAPDETECTIONENABLED$=%d\n$NDO_DATA_ISFLAPPING$=%d\n$NDO_DATA_PERCENTSTATECHANGE$=%.5lf\n$NDO_DATA_LATENCY$=%.5lf\n$NDO_DATA_EXECUTIONTIME$=%.5lf\n$NDO_DATA_SCHEDULEDDOWNTIMEDEPTH$=%d\n$NDO_DATA_FAILUREPREDICTIONENABLED$=%d\n$NDO_DATA_PROCESSPERFORMANCEDATA$=%d\n$NDO_DATA_OBSESSOVERSERVICE$=%d\n$NDO_DATA_MODIFIEDSERVICEATTRIBUTES$=%lu\n$NDO_DATA_EVENTHANDLER$=%s\n$NDO_DATA_CHECKCOMMAND$=%s\n$NDO_DATA_NORMALCHECKINTERVAL$=%lf\n$NDO_DATA_RETRYCHECKINTERVAL$=%lf\n$NDO_DATA_SERVICECHECKPERIOD$=%s\n"
    

    def go_for(self, callback, data):
        line = getattr(self.__class__, callback)
        tmp = self.m.resolve_macro(line, data)
        print 'TMP:', tmp
        try : 
            self.s.send(tmp)
        except socket.error as exp:
            print 'Socket error:', exp




#lets test
if __name__ == '__main__':
	ndomod = Ndomod()
	ndomod.init('')
