from xml.etree.ElementTree import ElementTree

tree = ElementTree()
tree.parse("local.xml")
p = tree.findall('host')
print "Number of host", len(p)


# Say if a host is up or not
def is_up(h):
    status = h.find('status')
    state = status.attrib['state']
    return state == 'up'


class DetectedHost:
    def __init__(self):
        self.ip = ''
        self.mac_vendor = ''
        self.host_name = ''

        self.os_possibilities = []
        self.os = ('', '')
        self.open_ports = []


    # Keep the first name we got
    def set_host_name(self, name):
        if self.host_name == '':
            self.host_name = name

    # Fill the different os possibilities
    def add_os_possibility(self, os, osgen, accuracy):
        self.os_possibilities.append( (os, osgen, accuracy) )

    # Look at ours oses and see which one is the better
    def compute_os(self):
        # bailout if we got no os :(
        if len(self.os_possibilities) == 0:
            return

        max_accuracy = 0
        for (os, osgen, accuracy) in self.os_possibilities:
            if accuracy > max_accuracy:
                max_accuracy = accuracy

        # now get the entry with the max value
        for (os, osgen, accuracy) in self.os_possibilities:
            if accuracy == max_accuracy:
                self.os = (os, osgen)


for h in p:
    # Bypass non up hosts
    if not is_up(h):
        continue
    
    dh = DetectedHost()

    # Now we get the ipaddr and the mac vendor
    # for future VMWare matching
    #print h.__dict__
    addrs = h.findall('address')
    for addr in addrs:
        #print "Address", addr.__dict__
        addrtype = addr.attrib['addrtype']
        if addrtype == 'ipv4':
            dh.ip = addr.attrib['addr']
        if addrtype == "mac":
            dh.mac_vendor = addr.attrib['vendor']


    # Now we got the hostnames
    host_names = h.findall('hostnames')
    for h_name in host_names:
        h_names = h_name.findall('hostname')
        for h_n in h_names:
            #print 'hname', h_n.__dict__
            #print 'Host name', h_n.attrib['name']
            dh.set_host_name(h_n.attrib['name'])


    # Now print the traceroute
    traces = h.findall('trace')
    for trace in traces:
        hops = trace.findall('hop')
        #for hop in hops:
        #    print hop.__dict__


    # Now the OS detection
    os = h.find('os')
    #print os.__dict__
    cls = os.findall('osclass')
    for c in cls:
        #print "Class", c.__dict__
        family = c.attrib['osfamily']
        accuracy = c.attrib['accuracy']
        if 'osgen' in c.attrib:
            osgen = c.attrib['osgen']
        else:
            osgen = None
        #print "Type:", family, osgen, accuracy
        dh.add_os_possibility(family, osgen, accuracy)
    # Ok we can compute our OS now :)
    dh.compute_os()


    # Now the ports :)
    allports = h.findall('ports')
    for ap in allports:
        ports = ap.findall('port')
        for p in ports:
            #print "Port", p.__dict__
            p_id = p.attrib['portid']
            s = p.find('state')
            #print s.__dict__
            state = s.attrib['state']
            if state == 'open':
                dh.open_ports.append(int(p_id))

    print dh.__dict__

    print "\n\n"
    
