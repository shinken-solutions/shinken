import select, time
from check import Check
from notification import Notification

class Scheduler:
    def __init__(self, daemon):
        self.daemon = daemon

    #Load conf for future use
    def load_conf(self, conf):
        self.conf = conf
        self.hostgroups = conf.hostgroups
        self.services = conf.services
        self.hosts = conf.hosts
        self.contacts = conf.contacts
        self.contactgroups = conf.contactgroups
        self.servicegroups = conf.servicegroups
        self.timeperiods = conf.timeperiods
        self.commands = conf.commands
        self.checks = {}
        self.actions = {}


    #Called by poller to get checks
    #Can get checks and actiosn (notifications and co)
    def get_to_run_checks(self, do_checks=False, do_actions=False):
        res = []
        now = time.time()
        #If poller want to do checks
        if do_checks:
            for c in self.checks.values():
                if c.status == 'scheduled' and c.is_launchable(now):
                    c.status = 'inpoller'
                    res.append(c)
        #If poller want to notify too
        if do_actions:
            for a in self.actions.values():
                contact = self.contacts.items[a.ref['contact']]
                if a.ref_type == 'service':
                    service = self.services.items[a.ref['service']]
                    if a.status == 'scheduled' and service.is_notification_launchable(a, contact):
                        print "***********************Giving a notification to run"
                        service.update_notification(a, contact)
                        a.status = 'inpoller'
                        res.append(a)
                if a.ref_type == 'host':
                    host = self.hosts.items[a.ref['host']]
                    if a.status == 'scheduled' and host.is_notification_launchable(a, contact):
                        print "***********************Giving a notification to run"
                        host.update_notification(a, contact)
                        a.status = 'inpoller'
                        res.append(a)
        return res


    #Caled by poller to send result
    def put_results(self, c):
        if c.type == 'notification':
            print "Get notification from poller", c.id
            if c.ref_type == 'service':
                service = self.services.items[c.ref['service']]
                a = service.get_new_notification_from(c)
                if a is not None:
                    print "==========>Getting a new service notification <========="
                    self.actions[a.id] = a
                del self.actions[c.id]
            if c.ref_type == 'host':
                host = self.hosts.items[c.ref['host']]
                a = host.get_new_notification_from(c)
                if a is not None:
                    print "==========>Getting a new host notification <========="
                    self.actions[a.id] = a
                del self.actions[c.id]


        elif c.type == 'check':
            print "Get check"
            c.status = 'waitconsume'
            self.checks[c.id] = c
        else:
            print "Type unknown"


    #Called every 1sec to consume every result in services or hosts
    #with theses results, they are OK, CRITCAL, UP/DOWN, etc...
    def consume_results(self):
        for c in self.checks.values():
            print c
            if c.status == 'waitconsume':
                if c.ref_type == 'service':
                    actions = self.services.items[c.ref].consume_result(c)
                if c.ref_type == 'host':
                    actions = self.hosts.items[c.ref].consume_result(c)
                for a in actions:
                    print "*******Adding a notification"
                    self.actions[a.id] = a


    #Called every 1sec to delete all checks in a zombie state
    #zombie = not usefull anymore
    def delete_zombie_checks(self):
        id_to_del = []
        for c in self.checks.values():
            if c.status == 'zombie':
                id_to_del.append(c.id)
        #une petite tape dans le doc et tu t'en vas, merci...
        for id in id_to_del:
            del self.checks[id]


    #Notifications are re-scheduling, this function check if unwanted notif
    #are still here (problem notif when it is not)
    def delete_unwanted_notifications(self):
        id_to_del = []
        for a in self.actions.values():
            if a.ref_type == 'service':
                service = self.services.items[a.ref['service']]
                if not service.still_need(a):
                    id_to_del.append(a.id)
            if a.ref_type == 'host':
                host = self.hosts.items[a.ref['host']]
                if not host.still_need(a):
                    id_to_del.append(a.id)

        print "**********Deleting Notifications", id_to_del
        for id in id_to_del:
            del self.actions[id]


    #Main schedule function to make the regular scheduling
    def schedule(self):
        #ask for service their next check
        for s in self.services.items.values():
            c = s.schedule()
            if c is not None:
                self.checks[c.id] = c
        for h in self.hosts.items.values():
            c = h.schedule()
            if c is not None:
                self.checks[c.id] = c


    #Main function
    def run(self):
        print "First scheduling"
        self.schedule()
        timeout = 1.0
        while True :
            socks=self.daemon.getServerSockets()
            avant=time.time()
            
            ins,outs,exs=select.select(socks,[],[],timeout)   # 'foreign' event loop
            if ins != []:
		for s in socks:
                        if s in ins:
				self.daemon.handleRequests()
                                apres=time.time()
				diff = apres-avant
				timeout = timeout - diff
                                break    # no need to continue with the for loop
            else:
                #print "Got timeout"
		timeout = 1.0
                self.schedule()
                self.consume_results()
                self.delete_zombie_checks()
                self.delete_unwanted_notifications()
                
                #stats
                nb_scheduled = len([c for c in self.checks.values() if c.status=='scheduled'])
                nb_inpoller = len([c for c in self.checks.values() if c.status=='inpoller'])
                nb_zombies = len([c for c in self.checks.values() if c.status=='zombie'])
                nb_notifications = len(self.actions)
                print "Notifications:", nb_notifications
                for n in  self.actions.values():
                    if n.ref_type == 'service':
                        print 'Service notification', n
                    if n.ref_type == 'host':
                        print 'Host notification', n
                #print "Got total(",len(self.checks) ,") scheduled(", nb_scheduled, ") inpoller(", nb_inpoller, ") zombies (", nb_zombies, ")"
                print "."

            if timeout < 0:
		timeout = 1.0
