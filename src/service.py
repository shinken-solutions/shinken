from command import CommandCall
from copy import deepcopy
from item import Item, Items
from util import to_int, to_char, to_split, to_bool
import random
import time
from check import Check
from notification import Notification
#from timeperiod import Timeperiod
from macroresolver import MacroResolver




class Service(Item):
    id = 0 # Every service have a unique ID

    #properties defined by configuration
    properties={'host_name' : {'required':True},
            'hostgroup_name' : {'required':True},
            'service_description' : {'required':True},
            'display_name' : {'required':False , 'default':None},
            'servicegroups' : {'required':False, 'default':''},
            'is_volatile' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'check_command' : {'required':True},
            'initial_state' : {'required':False, 'default':'o', 'pythonize': to_char},
            'max_check_attempts' : {'required':True, 'pythonize': to_int},
            'check_interval' : {'required':True, 'pythonize': to_int},
            'retry_interval' : {'required':True, 'pythonize': to_int},
            'active_checks_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'passive_checks_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'check_period' : {'required':True},
            'obsess_over_service' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'check_freshness' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'freshness_threshold' : {'required':False, 'default':'0', 'pythonize': to_int},
            'event_handler' : {'required':False, 'default':''},
            'event_handler_enabled' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'low_flap_threshold' : {'required':False, 'default':'-1', 'pythonize': to_int},
            'high_flap_threshold' : {'required':False, 'default':'-1', 'pythonize': to_int},
            'flap_detection_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'flap_detection_options' : {'required':False, 'default':'o,w,c,u', 'pythonize': to_split},
            'process_perf_data' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'retain_status_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'retain_nonstatus_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'notification_interval' : {'required':True, 'pythonize': to_int},
            'first_notification_delay' : {'required':False, 'default':'0', 'pythonize': to_int},
            'notification_period' : {'required':True},
            'notification_options' : {'required':False, 'default':'w,u,c,r,f,s', 'pythonize': to_split},
            'notifications_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'contacts' : {'required':True},
            'contact_groups' : {'required':True},
            'stalking_options' : {'required':False, 'default':'o,w,u,c', 'pythonize': to_split},
            'notes' : {'required':False, 'default':''},
            'notes_url' : {'required':False, 'default':''},
            'action_url' : {'required':False, 'default':''},
            'icon_image' : {'required':False, 'default':''},
            'icon_image_alt' : {'required':False, 'default':''},
            'failure_prediction_enabled' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'parallelize_check' : {'required':False, 'default':'1', 'pythonize': to_bool}
            }
    
    #properties used in the running state
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
        'checks_in_progress' : [],
        'downtimes' : [],
        'flapping_changes' : [],
        'percent_state_change' : 0.0
        }

    #Mapping between Macros and properties (can be prop or a function)
    macros = {
        'SERVICEDESC' : 'service_description',
        'SERVICEDISPLAYNAME' : 'display_name',
        'SERVICESTATE' : 'state',
        'SERVICESTATEID' : 'get_state_id',
        'LASTSERVICESTATE' : 'last_state',
        'LASTSERVICESTATEID' : 'get_last_state_id',
        'SERVICESTATETYPE' : 'state_type',
        'SERVICEATTEMPT' : 'attempt',
        'MAXSERVICEATTEMPTS' : 'max_check_attempts',
        'SERVICEISVOLATILE' : 'is_volatile',
        'SERVICEEVENTID' : None,
        'LASTSERVICEEVENTID' : None,
        'SERVICEPROBLEMID' : None,
        'LASTSERVICEPROBLEMID' : None,
        'SERVICELATENCY' : 'latency',
        'SERVICEEXECUTIONTIME' : 'exec_time',
        'SERVICEDURATION' : 'get_duration',
        'SERVICEDURATIONSEC' : 'get_duration_sec',
        'SERVICEDOWNTIME' : 'get_downtime',
        'SERVICEPERCENTCHANGE' : 'get_percent_change',
        'SERVICEGROUPNAME' : 'get_groupname',
        'SERVICEGROUPNAMES' : 'get_groupnames',
        'LASTSERVICECHECK' : 'last_chk',
        'LASTSERVICESTATECHANGE' : 'last_state_change',
        'LASTSERVICEOK' : 'last_service_ok',
        'LASTSERVICEWARNING' : 'last_service_warning',
        'LASTSERVICEUNKNOWN' : 'last_service_unknown',
        'LASTSERVICECRITICAL' : 'last_service_critical',
        'SERVICEOUTPUT' : 'output',
        'LONGSERVICEOUTPUT' : 'long_output',
        'SERVICEPERFDATA' : 'perf_data',
        'SERVICECHECKCOMMAND' : 'get_check_command',
        'SERVICEACKAUTHOR' : 'ack_author',
        'SERVICEACKAUTHORNAME' : 'get_ack_author_name',
        'SERVICEACKAUTHORALIAS' : 'get_ack_author_alias',
        'SERVICEACKCOMMENT' : 'ack_comment',
        'SERVICEACTIONURL' : 'action_url',
        'SERVICENOTESURL' : 'notes_url',
        'SERVICENOTES' : 'notes'
        }

    def get_name(self):
        return self.host_name+'/'+self.service_description


    #The service is dependent of his father dep
    #Must be AFTER linkify
    def fill_daddy_dependancy(self):
        #Depend of host, all status, is a networkdep and do not have timeperiod
        if self.host is not None:
            self.act_depend_of.append( (self.host, ['d', 'u', 's', 'f'], 'network_dep', None) )

            
    def add_service_act_dependancy(self, srv, status, timeperiod):
        self.act_depend_of.append( (srv, status, 'logic_dep', timeperiod) )


    def add_service_chk_dependancy(self, srv, status, timeperiod):
        self.chk_depend_of.append( (srv, status, 'logic_dep', timeperiod) )


    #Set state with status return by the check
    #and update flapping state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now

        self.last_state = self.state
        if status == 0:
            self.state = 'OK'
        elif status == 1:
            self.state = 'WARNING'
        elif status == 2:
            self.state = 'CRITICAL'
        elif status == 3:
            self.state = 'UNKNOWN'
        else:
            self.state = 'UNDETERMINED'
        if status in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)

    def add_flapping_change(self, b):
        self.flapping_states.append(b)
        #Just 20 changes
        if len(self.flapping_changes) > 20:
            self.flapping_changes.pop(0)
        #Now we add a value, we update the is_flapping prop
        self.update_flapping()

    #We update the is_flapping prop with value in self.flapping_states
    def update_flapping(self):
        #We compute the flapping change in %
        r = 0.0
        i = 0
        for b in self.flapping_changes:
           i += 1
           if b:
               r += i*(1.2-0.8)/20 + 0.8
        r = r / 20

        #Now we get the low_flap_threshold and high_flap_threshold values
        #They can be from self, or class
        (low_flap_threshold, high_flap_threshold) = (self.low_flap_threshold, self.high_flap_threshold)
        if low_flap_threshold == -1:
            cls = self.__class__
            low_flap_threshold = cls.low_flap_threshold
        if high_flap_threshold  == -1:
            cls = self.__class__
            high_flap_threshold = cls.high_flap_threshold

        #Now we check is flapping change
        if self.is_flapping and r < low_flap_threshold:
            self.is_flapping = False
        if not self.is_flapping and r >= high_flap_threshold:
            self.is_flapping = True
        self.percent_state_change = r


    #Return True if status is the state (like OK) or small form like 'o'
    def is_state(self, status):
        if status == self.state:
            return True
        #Now low status
        elif status == 'o' and self.state == 'OK':
            return True
        elif status == 'c' and self.state == 'CRITICAL':
            return True
        elif status == 'w' and self.state == 'WARNING':
            return True
        elif status == 'u' and self.state == 'UNKNOWN':
            return True
        return False


    #Add a attempt but cannot be more than max_check_attempts
    def add_attempt(self):
        self.attempt += 1
        self.attempt = min(self.attempt, self.max_check_attempts)


    #Return True if attempt is at max
    def is_max_attempts(self):
        return self.attempt >= self.max_check_attempts


    #Call by scheduler to see if last state is older than
    #freshness_threshold if check_freshness, then raise a check
    #even if active check is disabled
    def do_check_freshness(self):
        now = time.time()

        #Before, check if class (host or service) have check_freshness OK
        #Then check if item whant fressness, then check fressness
        cls = self.__class__
        if not self.in_checking:
            if cls.check_freshness:
                if self.check_freshness:
                    if self.last_state_update < now - self.freshness_threshold:
                    #print self.last_state_update , now - self.freshness_threshold
                    #print "Ohoh! State is not so fress!", self.service_description, "Last state:", time.asctime(time.localtime(self.last_state_update)), "Threshold", self.freshness_threshold, time.asctime(time.localtime(now - self.freshness_threshold))
                        return self.launch_check(now)
        return None

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


#    #If one of the chk_dep is raise, do not check
#    def is_no_check_dependant(self):
#        for (dep, status, type, tp) in self.chk_depend_of:
#            if tp is None and tp.is_time_valid(now):
#                for s in status:
#                    if dep.is_state(s):
#                        return True
#        return False

    def do_i_raise_dependency(self, status):
        for s in status:
            if self.is_state(s):
                return True
        now = time.time()
        for (dep, status, type, tp) in self.chk_depend_of:
            if dep.do_i_raise_dependency(status):
                if tp is None and tp.is_time_valid(now):
                    return True
        return False


    def is_no_check_dependant(self):
        for (dep, status, type, tp) in self.chk_depend_of:
            if tp is None and tp.is_time_valid(now):
                if dep.do_i_raise_dependency(status):
                        return True
        return False


    #call by a bad consume check where item see that he have dep
    #and maybe he is not in real fault.
    def raise_dependancies_check(self, ref_check_id):
        now = time.time()
        cls = self.__class__
        checks = []
        for (dep, status, type, tp) in self.act_depend_of:
            #If the dep timeperiod is not valid, do notraise the dep, None=everytime
            if tp is None or tp.is_time_valid(now):
                #if the update is 'fresh', do not raise dep, cached_check_horizon = cached_service_check_horizon for service
                if dep.last_state_update < now - cls.cached_check_horizon:
                    checks.append(dep.launch_check(now, ref_check_id))
                else:
                    print "********************************************* The state is FRESH", dep.host_name, time.asctime(time.localtime(dep.last_state_update))
        return checks


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
        else:
            print "Not removing cehck", c.id, "for service", self.get_name()
        self.update_in_checking()

        self.latency = now - c.t_to_go
        self.output = c.output
        self.long_output = c.long_output
        self.set_state_from_exit_status(c.exit_status)
        self.add_attempt()

        #print "SRV Context:", c.id, 'status', c.status, 'depend_on_me', c.depend_on_me, 'exit_status', c.exit_status,'depend_of ', self.act_depend_of

        #If we got a bad result on a normal check, and we have dep, we raise dep checks
        #put the actual check in waitdep and we return all new checks
        if c.exit_status != 0 and c.status == 'waitconsume' and len(self.act_depend_of) != 0:
            print "SRV I depend of someone, and I need a result"
            c.status = 'waitdep'
            #Make sure the check know about his dep
            checks = self.raise_dependancies_check(c.id)
            for check in checks:
                print c.id, "SRV: i depend on check", check.id
                c.depend_on.append(check.id)
            return checks

        #C is a check and someone wait for it
        if c.status == 'waitconsume' and c.depend_on_me is not None:
            print c.id, "SRV OK, someone wait for me", c.depend_on_me
            c.status = 'havetoresolvedep'

        #if finish, check need to be set to a zombie state to be removed
        #it can be change if necessery before return, like for dependancies
        if c.status == 'waitconsume' and c.depend_on_me == None:
            #print "SRV OK, nobody depend on me!!"
            c.status = 'zombie'
        
        #Use to know if notif is raise or not
        no_action = False
        #C was waitdep, but now all dep are resolved, so check for deps
        if c.status == 'waitdep':
            if c.depend_on_me is not None:
                print "Service: OK, someone wait for me", c.depend_on_me
                c.status = 'havetoresolvedep'
            else:
                print "Service great, noboby wait for me!"
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
        if c.exit_status == 0 and (self.last_state == 'OK' or self.last_state == 'PENDING'):
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
        elif c.exit_status == 0 and (self.last_state != 'OK' and self.last_state != 'PENDING'):
            if self.state_type == 'SOFT':
                self.state_type = 'SOFT-RECOVERY'
            elif self.state_type == 'HARD':
                if not no_action:
                    return self.create_notifications('RECOVERY')
                else:
                    return []
            return []
        
        #Volatile part
        elif c.exit_status != 0 and self.is_volatile:
            self.state_type = 'HARD'
            if not no_action:
                return self.create_notifications('PROBLEM')
            else:
                return []
        
        #If no OK in a OK -> going to SOFT
        elif c.exit_status != 0 and self.last_state == 'OK':
            self.state_type = 'SOFT'
            self.attempt = 1
            return []
        
        #If no OK in a no OK : if hard, still hard, if soft, check at self.max_check_attempts
        #when we go in hard, we send notification
        elif c.exit_status != 0 and self.last_state != 'OK':
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
        #next_chk il already set, do not change
        if self.next_chk >= now or self.in_checking and not force:
            return None

        cls = self.__class__
        #if no active check and no force, no check
        #print "Service check?", cls.execute_checks
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
        #print "Next check", time.asctime(time.localtime(self.next_chk))
        
        #Get the command to launch
        return self.launch_check(self.next_chk)


    #Create notifications but without commands. It will be update juste before being send
    def create_notifications(self, type):
        #if notif is disabled, not need to go thurser
        cls = self.__class__
        if not self.notifications_enabled or self.is_in_downtime or not cls.enable_notifications:
            return []
        
        notifications = []
        now = time.time()
        t = self.notification_period.get_next_valid_time_from_t(now)
        
        for contact in self.contacts:
            for cmd in contact.service_notification_commands:
                print "SRV: Raise notification"
                #create without real command, it will be update just before being send
                notifications.append(Notification(type, 'scheduled', 'VOID', {'service' : self.id, 'contact' : contact.id, 'command': cmd}, 'service', t))
        return notifications


    #We are just going to launch the notif to the poller
    #so we must actualise the command (Macros)
    def update_notification(self, n,  contact):
        m = MacroResolver()
        command = n.ref['command']
        n._command = m.resolve_command(command, self.host_name, self, contact, n)


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        if n.type == 'PROBLEM':
            return now > n.t_to_go and self.state != 'OK' and  contact.want_service_notification(now, self.state)
        else:
            return now > n.t_to_go and self.state == 'OK' and  contact.want_service_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    def get_new_notification_from(self, n):
        now = time.time()
        #a recovery notif is send ony one time
        if n.type == 'RECOVERY':
            return None
        return Notification(n.type, 'scheduled','', {'service' : n.ref['service'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'service', now + self.notification_interval * 60)


    #Check if the notificaton is still necessery
    def still_need(self, n):
        now = time.time()
        #if state != OK, te service still got a pb, so notification still necessery
        if self.state != 'OK':
            return True
        #state is OK but notif is in poller, so do not remove, will be done after
        if n.status == 'inpoller':
            return True
        #we do not see why to save this notification, so...
        return False


    #Is in checking if and ony if there are still checks no consumed
    def update_in_checking(self):
        self.in_checking = (len(self.checks_in_progress) != 0)


    #return a check to check the service
    def launch_check(self, t, ref_check_id = None):
        c = None
        if not self.is_no_check_dependant():
            #Get the command to launch
            m = MacroResolver()
            command_line = m.resolve_command(self.check_command, self.host_name, self, None, None)
            
            #Make the Check object and put the service in checking
            #print "Asking for a check with command:", command_line
            c = Check('scheduled',command_line, self.id, 'service', self.next_chk, ref_check_id)
            #We keep a trace of all checks in progress
            #to know if we are in checking_or not
            self.checks_in_progress.append(c.id)
            print self.get_name()+" we ask me for a check" + str(c.id)
        self.update_in_checking()
        #We need to return the check for scheduling adding
        return c


class Services(Items):
    def find_srv_id_by_name_and_hostname(self, host_name, name):
        for s in self:#.items:
            #s = self.items[id]
            #Runtinme first, available only after linkify
            if s.has('service_description') and s.has('host'):
                if s.service_description == name and s.host == host_name:
                        return s.id
            #At config part, available before linkify
            if s.has('service_description') and s.has('host_name'):
                if s.service_description == name and s.host_name == host_name:
                    return s.id
        return None


    def find_srv_by_name_and_hostname(self, host_name, name):
        id = self.find_srv_id_by_name_and_hostname(host_name, name)
        if id is not None:
            return self.items[id]
        else:
            return None


    def linkify(self, hosts, commands, timeperiods, contacts):
        self.linkify_s_by_hst(hosts)
        self.linkify_s_by_cmd(commands)
        self.linkify_s_by_tp(timeperiods)
        self.linkify_s_by_c(contacts)

    #We just search for each host the id of the host
    #and replace the name by the id
    #+ inform the host we are a service of him
    def linkify_s_by_hst(self, hosts):
        for s in self:#.items:
            try:
                hst_name = s.host_name
                
                #The new member list, in id
                hst = hosts.find_by_name(hst_name)
                #self.items[id].host_name = hst
                s.host = hst
                #Let the host know we are his service
                hst.add_service_link(s)
            except AttributeError as exp:
                print exp


    def linkify_s_by_cmd(self, commands):
        for s in self:#.items:
            s.check_command = CommandCall(commands, s.check_command)


    def linkify_s_by_tp(self, timeperiods):
        for s in self:#.items:
            try:
                #notif period
                ntp_name = s.notification_period
                ntp = timeperiods.find_by_name(ntp_name)
                s.notification_period = ntp
            except:
                pass
            try:
                #Check period
                ctp_name = s.check_period
                ctp = timeperiods.find_by_name(ctp_name)
                s.check_period = ctp
            except:
                pass #problem will be check at is_correct fucntion


    def linkify_s_by_c(self, contacts):
        for s in self:#.items:
            #s = self.items[id]
            contacts_tab = s.contacts.split(',')
            new_contacts = []
            for c_name in contacts_tab:
                c_name = c_name.strip()
                c = contacts.find_by_name(c_name)
                new_contacts.append(c)
            s.contacts = new_contacts

    
    def delete_services_by_id(self, ids):
        for id in ids:
            del self.items[id]


    def apply_implicit_inheritance(self, hosts):
        for prop in ['contact_groups', 'notification_interval' , 'notification_period']:
            for s in self:#.items:
                #s = self.items[id]
                if not s.is_tpl():
                    if not s.has(prop) and s.has('host_name'):
                        h = hosts.find_by_name(s.host_name)
                        if h is not None and h.has(prop):
                            setattr(s, prop, getattr(h, prop))


    def apply_inheritance(self, hosts):
        #We check for all Host properties if the host has it
        #if not, it check all host templates for a value
        for prop in Service.properties:
            self.apply_partial_inheritance(prop)

        #Then implicit inheritance
        self.apply_implicit_inheritance(hosts)
        for s in self:#.items:
            #s = self.items[id]
            s.get_customs_properties_by_inheritance(self)


    def apply_dependancies(self):
        for s in self:#.items.values():
            s.fill_daddy_dependancy()


    #We create new service if necessery (host groups and co)
    def explode(self, hostgroups, contactgroups, servicegroups):
        #Hostgroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('contact_groups')
        self.apply_partial_inheritance('hostgroup_name')
        self.apply_partial_inheritance('host_name')

        #The "old" services will be removed. All services with 
        #more than one host or a host group will be in it
        srv_to_remove = []
        
        #We adding all hosts of the hostgroups into the host_name property
        #because we add the hostgroup one AFTER the host, they are before and 
        #hostgroup one will NOT be created
        for s in self:#.items:
            #s = self.items[id]
            if s.has('hostgroup_name'):
                hgnames = s.hostgroup_name.split(',')
                for hgname in hgnames:
                    print "Doing a hgname", hgname
                    hgname = hgname.strip()
                    hnames = hostgroups.get_members_by_name(hgname)
                    #We add hosts in the service host_name
                    print s.host_name, hgname
                    if s.has('host_name') and hnames != []:
                        s.host_name += ',' + str(hnames)
                    else:
                        s.host_name = str(hnames)

        #We adding all hosts of the hostgroups into the host_name property
        #because we add the hostgroup one AFTER the host, they are before and 
        #hostgroup one will NOT be created
        for s in self:#.items:
            #s = self.items[id]
            if s.has('contact_groups'):
                cgnames = s.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if s.has('contacts'):
                            s.contacts += ','+cnames
                        else:
                            s.contacts = cnames
        
        #Then for every host create a copy of the service with just the host
        service_to_check = self.items.keys() #because we are adding services, we can't just loop in it
        for id in service_to_check:
            s = self.items[id]
            if not s.is_tpl(): #Exploding template is useless
                hnames = s.host_name.split(',')
                if len(hnames) >= 2:
                    for hname in hnames:
                        hname = hname.strip()
                        new_s = s.copy()
                        new_s.host_name = hname
                        self.items[new_s.id] = new_s
                    srv_to_remove.append(id)
        
        self.delete_services_by_id(srv_to_remove)

        #Servicegroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('servicegroups')
        for s in self:#.items:
            #s = self.items[id]
            if not s.is_tpl():
                sname = s.service_description
                shname = s.host_name
                if s.has('servicegroups'):
                    sgs = s.servicegroups.split(',')
                    for sg in sgs:
                        servicegroups.add_member(shname+','+sname, sg)
        
