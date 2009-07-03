from command import CommandCall
from pygraph import digraph
from item import Item, Items
from util import to_int, to_char, to_split, to_bool
import time, random
from macroresolver import MacroResolver
from check import Check
from notification import Notification

class Host(Item):
    id = 1 #0 is reserved for host (primary node for parents)
    properties={'host_name': {'required': True},
                'alias': {'required':  True},
                'display_name': {'required': False, 'default':'none'},
                'address': {'required': True},
                'parents': {'required': False, 'default': '' , 'pythonize': to_split},
                'hostgroups': {'required': False, 'default' : ''},
                'check_command': {'required': False, 'default':''},
                'initial_state': {'required': False, 'default':'u', 'pythonize': to_char},
                'max_check_attempts': {'required': True , 'pythonize': to_int},
                'check_interval': {'required': False, 'default':'0', 'pythonize': to_int},
                'retry_interval': {'required': False, 'default':'0', 'pythonize': to_int},
                'active_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'passive_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'check_period': {'required': True},
                'obsess_over_host': {'required': False, 'default':'0' , 'pythonize': to_bool},
                'check_freshness': {'required': False, 'default':'0', 'pythonize': to_bool},
                'freshness_threshold': {'required': False, 'default':'0', 'pythonize': to_int},
                'event_handler': {'required': False, 'default':''},
                'event_handler_enabled': {'required': False, 'default':'0', 'pythonize': to_bool},
                'low_flap_threshold': {'required':False, 'default':'25', 'pythonize': to_int},
                'high_flap_threshold': {'required': False, 'default':'50', 'pythonize': to_int},
                'flap_detection_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'flap_detection_options': {'required': False, 'default':'o,d,u', 'pythonize': to_split},
                'process_perf_data': {'required': False, 'default':'1', 'pythonize': to_bool},
                'retain_status_information': {'required': False, 'default':'1', 'pythonize': to_bool},
                'retain_nonstatus_information': {'required': False, 'default':'1', 'pythonize': to_bool},
                'contacts': {'required': True},
                'contact_groups': {'required': True},
                'notification_interval': {'required': True, 'pythonize': to_int},
                'first_notification_delay': {'required': False, 'default':'0', 'pythonize': to_int},
                'notification_period': {'required': True},
                'notification_options': {'required': False, 'default':'d,u,r,f', 'pythonize': to_split},
                'notifications_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'stalking_options': {'required': False, 'default':'o,d,u', 'pythonize': to_split},
                'notes': {'required': False, 'default':''},
                'notes_url': {'required': False, 'default':''},
                'action_url': {'required': False, 'default':''},
                'icon_image': {'required': False, 'default':''},
                'icon_image_alt': {'required': False, 'default':''},
                'vrml_image': {'required': False, 'default':''},
                'statusmap_image': {'required': False, 'default':''},
                '2d_coords': {'required': False, 'default':''},
                '3d_coords': {'required': False, 'default':''},
                'failure_prediction_enabled': {'required' : False, 'default' : '0', 'pythonize': to_bool}
                }

    running_properties = {
        'last_chk' : 0,
        'next_chk' : 0,
        'in_checking' : False,
        'latency' : 0,
        'attempt' : 0,
        'state' : 'PENDING',
        'state_type' : 'SOFT',
        'output' : '',
        'long_output' : '',
        'is_flapping' : False,
        'is_in_downtime' : False,
        'act_depend_of' : [], #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : [], #dependencies for checks raise, so BEFORE checks
        'last_state_update' : time.time(),
        'services' : [],
        'checks_in_progress' : [],
        'downtimes' : [],
        'flapping_changes' : [],
        'percent_state_change' : 0.0
        }


    macros = {'HOSTNAME' : 'host_name',
              'HOSTDISPLAYNAME' : 'display_name',
              'HOSTALIAS' :  'alias',
              'HOSTADDRESS' : 'address',
              'HOSTSTATE' : 'state',
              'HOSTSTATEID' : 'get_stateid',
              'LASTHOSTSTATE' : 'last_state',
              'LASTHOSTSTATEID' : 'get_last_stateid',
              'HOSTSTATETYPE' : 'state_type',
              'HOSTATTEMPT' : 'attempt',
              'MAXHOSTATTEMPTS' : 'max_check_attempts',
              'HOSTEVENTID' : None,
              'LASTHOSTEVENTID' : None,
              'HOSTPROBLEMID' : None,
              'LASTHOSTPROBLEMID' : None,
              'HOSTLATENCY' : 'latency',
              'HOSTEXECUTIONTIME' : 'exec_time',
              'HOSTDURATION' : 'get_duration',
              'HOSTDURATIONSEC' : 'get_duration_sec',
              'HOSTDOWNTIME' : 'get_downtime',
              'HOSTPERCENTCHANGE' : 'get_percent_change',
              'HOSTGROUPNAME' : 'get_groupname',
              'HOSTGROUPNAMES' : 'get_groupnames',
              'LASTHOSTCHECK' : 'last_chk',
              'LASTHOSTSTATECHANGE' : 'last_state_change',
              'LASTHOSTUP' : 'last_host_up',
              'LASTHOSTDOWN' : 'last_host_down',
              'LASTHOSTUNREACHABLE' : 'last_host_unreachable',
              'HOSTOUTPUT' : 'output',
              'LONGHOSTOUTPUT' : 'long_output',
              'HOSTPERFDATA' : 'perf_data',
              'HOSTCHECKCOMMAND' : 'get_check_command',
              'HOSTACKAUTHOR' : 'ack_author',
              'HOSTACKAUTHORNAME' : 'get_ack_author_name',
              'HOSTACKAUTHORALIAS' : 'get_ack_author_alias',
              'HOSTACKCOMMENT' : 'ack_comment',
              'HOSTACTIONURL' : 'action_url',
              'HOSTNOTESURL' : 'notes_url',
              'HOSTNOTES' : 'notes',
              'TOTALHOSTSERVICES' : 'get_total_services',
              'TOTALHOSTSERVICESOK' : 'get_total_services_ok',
              'TOTALHOSTSERVICESWARNING' : 'get_total_services_warning',
              'TOTALHOSTSERVICESUNKNOWN' : 'get_total_services_unknown',
              'TOTALHOSTSERVICESCRITICAL' : 'get_total_services_critical'
        }



    def clean(self):
        pass




    #Check is required prop are set:
    #template are always correct
    #contacts OR contactgroups is need
    def is_correct(self):
        if self.is_tpl:
            return True
        for prop in Host.properties:
            if not self.has(prop) and Host.properties[prop]['required']:
                if prop == 'contacts' or prop == 'contacgroups':
                    pass
                else:
                    print "I do not have", prop
                    return False
        if self.has('contacts') or self.has('contacgroups'):
            return True
        else:
            print "I do not have contacts nor contacgroups"
            return False

    #Macro part
    def get_total_services(self):
        return str(len(self.services))


    def get_name(self):
        return self.host_name


    def add_host_act_dependancy(self, h, status, timeperiod):
        self.act_depend_of.append( (h, status, 'logic_dep', timeperiod) )


    def add_host_chk_dependancy(self, h, status, timeperiod):
        self.chk_depend_of.append( (h, status, 'logic_dep', timeperiod) )


    def add_service_link(self, service):
        self.services.append(service)


    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now
        self.last_state = self.state
        
        if status == 0:
            self.state = 'UP'
        elif status == 1 or status == 2 or status == 3:
            self.state = 'DOWN'
        else:
            self.state = 'UNDETERMINED'


    def is_state(self, status):
        if status == self.state:
            return True
        #Now low status
        elif status == 'o' and self.state == 'UP':
            return True
        elif status == 'd' and self.state == 'DOWN':
            return True
        elif status == 'u' and self.state == 'UNREACHABLE':
            return True
        return False


    #Add a attempt but cannot be more than max_check_attempts
    def add_attempt(self):
        self.attempt += 1
        self.attempt = min(self.attempt, self.max_check_attempts)


    def is_max_attempts(self):
        return self.attempt >= self.max_check_attempts

    #Call by scheduler to see if last state is older than
    #freshness_threshold if check_freshness, then raise a check
    #even if active check is disabled
    def do_check_freshness(self):
        now = time.time()
        #print self.check_freshness
        if self.check_freshness:
            if self.last_state_update < now - self.freshness_threshold:
                print "Ohoh! State is not so fress!", self.host_name, "Last state:", time.asctime(time.localtime(self.last_state_update\
)), "Threshold", self.freshness_threshold, time.asctime(time.localtime(now - self.freshness_threshold))
                self.launch_check(now)



    def raise_dependancies_check(self, ref_check_id):
        now = time.time()
        checks = []
        cls = self.__class__
        for (dep, status, type, tp) in self.act_depend_of:
            #If the dep timeperiod is not valid, do notraise the dep, None=everytime
            if tp is None or tp.is_time_valid(now):
                #if the update is 'fresh', do not raise dep, cached_check_horizon = cached_service_check_horizon for service
                if dep.last_state_update < now - cls.cached_check_horizon:
                    checks.append(dep.launch_check(now, ref_check_id))
                else:
                    print "********************************************* The state is FRESH", dep.host_name, time.asctime(time.localtime(dep.last_state_update))
        return checks


    #If one of the chk_dep is raise, do not check
    def is_no_check_dependant(self):
        for (dep, status, type, tp) in self.chk_depend_of:
            if tp is None and tp.is_time_valid(now):
                for s in status:
                    if dep.is_state(s):
                        return True
        return False


    def fill_parents_dependancie(self):
        print "Me", self.host_name, "is getting my parents"
        print "I-ve got my parents", self.parents
        print "Before", self.act_depend_of
        #self.act_depend_of = []
        for parent in self.parents:
            print "I add a daddy!", parent.host_name
            self.act_depend_of.append( (parent, ['d', 'u', 's', 'f'], 'network_dep', None) )
        print "finnaly : ", self.act_depend_of


    #When all dep are resolved, this function say if
    #action can be raise or not by viewing dep status
    #network_dep have to be all raise to be no action
    #logic_dep : just one is enouth
    def is_no_action_dependant(self):
        #Use to know if notif is raise or not
        #no_action = False
        parent_is_down = []
        #So if one logic is Raise, is dep
        #is one network is no ok, is not dep
        #at teh end, raise no dep
        for (dep, status, type, tp) in self.act_depend_of:
            #For logic_dep, only one state raise put no action
            if type == 'logic_dep':
                for s in status:
                    if dep.is_state(s):
                        return True
            #more complicated: if none of the states are match, the host is down
            else:
                p_is_down = False
                dep_match = [dep.is_state(s) for s in status] 
                if True in dep_match:#the parent match a case, so he is down
                    p_is_down = True
                parent_is_down.append(p_is_down)
        #if a parent is not down, no dep can explain the pb
        if False in parent_is_down:
            return False
        else:# every parents are dead, so... It's not my fault :)
            return True


    #consume a check return and send action in return
    #main function of reaction of checks like raise notifications
    #Special case:
    #is_flapping : immediate notif when problem
    #is_in_downtime : no notification
    #is_volatile : notif immediatly
    def consume_result(self, c):
        now = time.time()

        #The check is consume, uptade the in_checking propertie
        if c.id in self.checks_in_progress:
            self.checks_in_progress.remove(c.id)
        self.update_in_checking()

        self.latency = now - c.t_to_go
        self.output = c.output
        self.long_output = c.long_output
        self.set_state_from_exit_status(c.exit_status)
        self.add_attempt()

        print "host: Context:", c.id, "status", c.status, "depend_on_me", c.depend_on_me, "exist_status", c.exit_status, "depend_of", self.act_depend_of
        for (p, flags, type, tp) in self.act_depend_of:
            print "Me", self.host_name, "I depend on", p.host_name
        
        #If we got a bad result on a normal check, and we have dep, we raise dep checks
        #put the actual check in waitdep and we return all new checks
        if c.exit_status != 0 and c.status == 'waitconsume' and len(self.act_depend_of) != 0:
            print "Host: I depend of someone, and I need a result"
            c.status = 'waitdep'
            #Make sure the check know about his dep
            checks = self.raise_dependancies_check(c.id)
            print "Me", self.host_name, "lookp for my parent", self.act_depend_of[0][0].host_name, "FIN"
            for check in checks:
                print "HOST: I depend on,", check.id
                c.depend_on.append(check.id)
            return checks
        
        #C is a check and someone wait for it
        if c.status == 'waitconsume' and c.depend_on_me is not None:
            print "Host: OK, someone wait for me", c.depend_on_me
            c.status = 'havetoresolvedep'


        #if finish, check need to be set to a zombie state to be removed
        #it can be change if necessery before return, like for dependancies
        if c.status == 'waitconsume' and c.depend_on_me == None:
            print "Host: OK, nobody depend on me!!"
            c.status = 'zombie'
        
        #Use to know if notif is raise or not
        no_action = False
        #C was waitdep, but now all dep are resolved, so check for deps
        if c.status == 'waitdep':
            if c.depend_on_me is not None:
                print "Host: OK, someone wait for me", c.depend_on_me
                c.status = 'havetoresolvedep'
            else:
                print "Host great, noboby wait for me!"
                c.status = 'zombie'
            #Check deps
            no_action = self.is_no_action_dependant()
            print "No action:", no_action

        #If no_action is False, maybe we are in downtime, so no_action become true
        if no_action == False:
            for dt in self.downtimes:
                if dt.is_in_downtime():
                    no_action = True

        #If ok in ok : it can be hard of soft recovery
        if c.exit_status == 0 and (self.last_state == 'UP' or self.last_state == 'PENDING'):
            #action in return can be notification or other checks (dependancies)
            if (self.state_type == 'SOFT' or self.state_type == 'SOFT-RECOVERY') and self.last_state != 'PENDING':
                if self.is_max_attempts() and (self.state_type == 'SOFT' or self.state_type == 'SOFT-RECOVERY'):
                    self.state_type = 'HARD'
                else:
                    self.state_type = 'SOFT-RECOVERY'
            else:
                self.attempt = 1
                self.state_type = 'HARD'
            return []
        
        #If OK on a no OK : if SOFT-> SOFT recovery, if hard, still hard
        elif c.exit_status == 0 and (self.last_state != 'UP' and self.last_state != 'PENDING'):
            if self.state_type == 'SOFT':
                self.state_type = 'SOFT-RECOVERY'
            elif self.state_type == 'HARD':
                if not no_action:
                    return self.create_notifications('RECOVERY')
                else:
                    return []
            return []
        
        #Volatile part
        elif c.exit_status != 0 and self.has('is_volatile') and self.is_volatile:
            self.state_type = 'HARD'
            if not no_action:
                return self.create_notifications('PROBLEM')
            else:
                return []
        
        #If no OK in a OK -> going to SOFT
        elif c.exit_status != 0 and self.last_state == 'UP':
            self.state_type = 'SOFT'
            self.attempt = 1
            return []
        
        #If no OK in a no OK : if hard, still hard, if soft, check at self.max_check_attempts
        #when we go in hard, we send notification
        elif c.exit_status != 0 and self.last_state != 'UP':
            if self.is_max_attempts() and self.state_type == 'SOFT':
                self.state_type = 'HARD'
                #raise notification only if self.notifications_enabled is True
                if self.notifications_enabled:
                    if not no_action:
                        return self.create_notifications('PROBLEM')
                    else:
                        return []
        return []


    def schedule(self, force=False, force_time=None):
        #if last_chk == 0 put in a random way so all checks are not in the same time
        
        now = time.time()
        print "ME", self.host_name, self.next_chk, self.in_checking, self.checks_in_progress, id(self.checks_in_progress)
        #next_chk il already set, do not change
        if self.next_chk >= now or self.in_checking:
            return None

        cls = self.__class__
        #if no active check and no force, no check
        if (not self.active_checks_enabled or not cls.execute_checks) and not force:
            return None

        
        #Interval change is in a HARD state or not
        if self.state == 'HARD':
            interval = self.check_interval
        else:
            interval = self.retry_interval

        #The next_chk is pass so we need a new one
        #so we got a check_interval
        if self.next_chk == 0:
            r = interval * (random.random() - 0.5)
            time_add = interval*10/2 + r*10
        else:
            time_add = interval*10
        
        if force_time is None:
            self.next_chk = self.check_period.get_next_valid_time_from_t(now + time_add)
        else:
            self.next_chk = force_time
        
        print "Next check", time.asctime(time.localtime(self.next_chk))
        
        #Get the command to launch
        return self.launch_check(self.next_chk)    



    #Create notifications but without commands. It will be update juste before being send
    def create_notifications(self, type):
        notifications = []
        now = time.time()
        t = self.notification_period.get_next_valid_time_from_t(now)
        print "HOST: We are creating a notification for", time.asctime(time.localtime(t))
        #print self
        for contact in self.contacts:
            for cmd in contact.host_notification_commands:
                #create without real command, it will be update just before being send
                notifications.append(Notification(type, 'scheduled', 'VOID', {'host' : self.id, 'contact' : contact.id, 'command': cmd}, 'host', t))
        return notifications


    #We are just going to launch the notif to the poller
    #so we must actualise the command (Macros)
    def update_notification(self, n,  contact):
        m = MacroResolver()
        command = n.ref['command']
        n._command = m.resolve_command(command, self, None, contact, n)


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        return now > n.t_to_go and self.state != 'UP' and  contact.want_host_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    def get_new_notification_from(self, n):
        now = time.time()
        return Notification(n.type, 'scheduled','', {'host' : n.ref['host'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'host', now + self.notification_interval * 60)


    #Check if the notificaton is still necessery
    def still_need(self, n):
        now = time.time()
        #if state != UP, the host still got a pb, so notification still necessery
        if self.state != 'UP':
            return True
        #state is UP but notif is in poller, so do not remove, will be done after
        if n.status == 'inpoller':
            return True
        #we do not see why to save this notification, so...
        return False


    #Is in checking if and ony if there are still checks no consumed    
    def update_in_checking(self):
        self.in_checking = (len(self.checks_in_progress) != 0)
    

    #return a check to check the host
    def launch_check(self, t , ref_check_id = None):
        c = None
        if not self.is_no_check_dependant():
            #Get the command to launch
            m = MacroResolver()
            command_line = m.resolve_command(self.check_command, self, None, None, None)
            
            #Make the Check object and put the service in checking
            print "Asking for a check with command:", command_line
            c = Check('scheduled',command_line, self.id, 'host', self.next_chk, ref_check_id)
            
            #We keep a trace of all checks in progress
            #to know if we are in checking_or not
            self.checks_in_progress.append(c.id)
        self.update_in_checking()
        #We need to return the check for scheduling adding
        return c




class Hosts(Items):
    name_property = "host_name" #use for the search by name
    inner_class = Host #use for know what is in items


    def linkify(self, timeperiods=None, commands=None, contacts=None):
        self.linkify_h_by_tp(timeperiods)
        self.linkify_h_by_h()
        self.linkify_h_by_cmd(commands)
        self.linkify_h_by_c(contacts)

    #Simplify notif_period and check period by timeperiod id
    def linkify_h_by_tp(self, timeperiods):
        for h in self:#.items.values():
            print "Linify ", h
            try:
                #notif period
                ntp_name = h.notification_period
                ntp = timeperiods.find_by_name(ntp_name)
                h.notification_period = ntp
                #check period
                ctp_name = h.check_period
                ctp = timeperiods.find_by_name(ctp_name)
                h.check_period = ctp
            except AttributeError (exp):
                print exp
    

    #Simplify parents names by host id
    def linkify_h_by_h(self):
        for h in self:#.items.values():
            parents = h.parents
            #The new member list, in id
            new_parents = []
            for parent in parents:
                new_parents.append(self.find_by_name(parent))
            print "Me,", h.host_name, "define my parents", new_parents
            #We find the id, we remplace the names
            h.parents = new_parents

    
    #Simplify hosts commands by commands id
    def linkify_h_by_cmd(self, commands):
        for h in self:#.items.values():
            h.check_command = CommandCall(commands, h.check_command)


    def linkify_h_by_c(self, contacts):
        for h in self:#.items:
            #h = self.items[id]
            contacts_tab = h.contacts.split(',')
            new_contacts = []
            for c_name in contacts_tab:
                c_name = c_name.strip()
                c = contacts.find_by_name(c_name)
                new_contacts.append(c)
                
            h.contacts = new_contacts


    #We look for hostgroups property in hosts and
    def explode(self, hostgroups, contactgroups):
        #Hostgroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('hostgroups')
        self.apply_partial_inheritance('contact_groups')
        
        #Explode host in the hostgroups
        for h in self:#.items.values():
            if not h.is_tpl():
                hname = h.host_name
                if h.has('hostgroups'):
                    hgs = h.hostgroups.split(',')
                    for hg in hgs:
                        hostgroups.add_member(hname, hg.strip())
        
        #We add contacts of contact groups into the contacts prop
        for h in self:#.items:
            #h = self.items[id]
            if h.has('contact_groups'):
                cgnames = h.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if h.has('contacts'):
                            h.contacts += ','+cnames
                        else:
                            h.contacts = cnames

        
    #Create depenancies:
    #Parent graph: use to find quickly relations between all host, and loop
    #Depencies at the host level: host parent
    def apply_dependancies(self):
        #Create parent graph
        self.parents = digraph()
        #0 is pynag node
        self.parents.add_node(0)
        for h in self:#.items.values():
            id = h.id
            if id not in self.parents:
                self.parents.add_node(id)
                        
            if len(h.parents) >= 1:
                for parent in h.parents:
                    parent_id = parent.id
                    if parent_id not in self.parents:
                        self.parents.add_node(parent_id)
                    self.parents.add_edge(parent_id, id)
                    print "Add relation between", parent_id, id
            else:#host without parent are pynag childs
                print "Add relation between", 0, id
                self.parents.add_edge(0, id)
        print "Loop: ", self.parents.find_cycle()
        #print "Fin loop check"
        
        for h in self:#.items.values():
            h.fill_parents_dependancie()
                

        #Debug
        #dot = self.parents.write(fmt='dot')
        #f = open('graph.dot', 'w')
        #f.write(dot)
        #f.close()
        #import os
        # Draw as a png (note: this requires the graphiz 'dot' program to be installed)
        #os.system('dot graph.dot -Tpng > hosts.png')
