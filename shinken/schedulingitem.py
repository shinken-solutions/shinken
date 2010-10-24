#!/usr/bin/env python
#Copyright (C) 2009-2010 Gabes Jean, naparuba@gmail.com
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


#from command import CommandCall
#from copy import deepcopy
from item import Item
#from util import to_int, to_char, to_split, to_bool
import random
import time

from check import Check
from notification import Notification
from timeperiod import Timeperiod
from macroresolver import MacroResolver
from eventhandler import EventHandler
from log import Log


class SchedulingItem(Item):

    # global counters used for [current|last]_[host|service]_[event|problem]_id
    current_event_id = 0
    current_problem_id = 0

    #Add a flapping change, but no more than 20 states
    #Then update the self.is_flapping bool by calling update_flapping
    def add_flapping_change(self, b):
        self.flapping_changes.append(b)

        #Keep just 20 changes (global flap_history value)
        flap_history = self.__class__.flap_history

        if len(self.flapping_changes) > flap_history:
            self.flapping_changes.pop(0)
        #Now we add a value, we update the is_flapping prop
        self.update_flapping()


    #We update the is_flapping prop with value in self.flapping_states
    #Old values have less weight than new ones
    def update_flapping(self):
        flap_history = self.__class__.flap_history
        #We compute the flapping change in %
        r = 0.0
        i = 0
        for b in self.flapping_changes:
            i += 1
            if b:
                r += i*(1.2-0.8)/flap_history + 0.8
        r = r / flap_history

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
            #We also raise a log entry
            self.raise_flapping_stop_log_entry(r, low_flap_threshold)
        if not self.is_flapping and r >= high_flap_threshold:
            self.is_flapping = True
            #We also raise a log entry
            self.raise_flapping_start_log_entry(r, high_flap_threshold)
        self.percent_state_change = r


    #Add an attempt but cannot be more than max_check_attempts
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
                if self.check_freshness and self.freshness_threshold != 0:
                    if self.last_state_update < now - (self.freshness_threshold + cls.additional_freshness_latency):
                        #Raise a log
                        self.raise_freshness_log_entry(int(now-self.last_state_update), int(now-self.freshness_threshold))
                        #And a new check
                        return self.launch_check(now)
        return None


    #Raise all impact from my error. I'm setting myself
    #as a problem, and I register myself as this in all
    #hosts/services that depend_on_me. So they are now my
    #impacts
    def set_myself_as_problem(self):
        now = time.time()
        #print "ME %s is now a PROBLEM" % self.get_dbg_name()
        self.is_problem = True
        #we should warn potentials impact of our problem
        #and they should be cool to register them so I've got
        #my impacts list
        for (impact, status, dep_type, tp, inh_par) in self.act_depend_of_me:
            #Check if the status is ok for impact
            for s in status:
                if self.is_state(s):
                    #now check if we should bailout because of a
                    #not good timeperiod for dep
                    if tp is None or tp.is_time_valid(now):
                        #print "I can call %s for registering me as a problem" % impact.get_dbg_name()
                        new_impacts = impact.register_a_problem(self)
                        self.impacts.extend(new_impacts)
                        #Make element unique in this list
                        self.impacts = list(set(self.impacts))

        #And we register a new broks for update status
        b = self.get_update_status_brok()
        self.broks.append(b)



    #Look for my impacts, and remove me from theirs problems list
    def no_more_a_problem(self):
        if self.is_problem:
            #print "Me %s is no more a problem! Cool" % self.get_dbg_name()
            self.is_problem = False

            #we warn impacts that we are no more a problem
            for impact in self.impacts:
                #print "I'm deregistring from impact %s" % impact.get_dbg_name()
                impact.deregister_a_problem(self)

            #we can just drop our impacts list
            self.impacts = []

            #And we register a new broks for update status
            b = self.get_update_status_brok()
            self.broks.append(b)


    #call recursively by potentials impacts so they
    #update their source_problems list. But do not
    #go below if the problem is not a real one for me
    #like If I've got multiple parents for examples
    def register_a_problem(self, pb):
        now = time.time()
        was_an_impact = self.is_impact
        #Our father already look of he impacts us. So if we are here,
        #it's that we really are impacted
        self.is_impact = True
        #print "Is me %s an impact? %s" % (self.get_dbg_name(), self.is_impact)

        impacts = []
        #Ok, if we are impacted, we can add it in our
        #problem list
        #TODO : remove this unused check
        if self.is_impact:
            #Maybe I was a problem myself, now I can say : not my fault!
            if self.is_problem:
                #print "I was a problem, but now me %s is a simple impact! Cool" % self.get_dbg_name()
                self.no_more_a_problem()

            #Ok, we are now an impact, we should take the good state
            #but only when we just go in impact state
            if not was_an_impact:
                self.set_impact_state()

            #And we register a new broks for update status
            b = self.get_update_status_brok()
            self.broks.append(b)

            #Ok now we can be a simple impact
            impacts.append(self)
            if pb not in self.source_problems:
                self.source_problems.append(pb)
            #we should send this problem to all potential impact that
            #depend on us
            #print "Guys depending on me:"
            for (impact, status, dep_type, tp, inh_par) in self.act_depend_of_me:
                #print "Potential impact :", impact.get_dbg_name(), status, dep_type, tp
                #Check if the status is ok for impact
                for s in status:
                    if self.is_state(s):
                        #now check if we should bailout because of a
                        #not good timeperiod for dep
                        if tp is None or tp.is_time_valid(now):
                            #print "I can call %s for registering a root problem (%s)" % (impact.get_dbg_name(), pb.get_dbg_name())
                            new_impacts = impact.register_a_problem(pb)
                            impacts.extend(new_impacts)

        #now we return all impacts (can be void of course)
        #DBG
        #print "At my level, I raised impacts :"
        #for i in impacts:
        #    print i.get_dbg_name()
        #DBG
        return impacts


    #Just remove the problem from our problems list
    #and check if we are still 'impacted'. It's not recursif because problem
    #got the lsit of all its impacts
    def deregister_a_problem(self, pb):
        #print "We are asking ME %s to remove a pb %s from %s" % (self.get_dbg_name(), pb.get_dbg_name(), self.source_problems)
        self.source_problems.remove(pb)

        #For know if we are still an impact, maybe our dependancies
        #are not aware of teh remove of the impact state because it's not ordered
        #so we can just look at if we still have some problem in our list
        if len(self.source_problems) == 0:
            self.is_impact = False
            #No more an impact, we can unset the impact state
            self.unset_impact_state()

        #And we register a new broks for update status
        b = self.get_update_status_brok()
        self.broks.append(b)


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
        for (dep, status, type, tp, inh_par) in self.act_depend_of:
            #For logic_dep, only one state raise put no action
            if type == 'logic_dep':
                for s in status:
                    if dep.is_state(s):
                        return True
            #more complicated: if none of the states are match, the host is down
            else: #network_dep
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


    #We check if we are no action just because of ours parents (or host for
    #service)
    #TODO : factorize with previous check?
    def check_and_set_unreachability(self):
        parent_is_down = []
        #We must have all parents raised to be unreachable
        for (dep, status, type, tp, inh_par) in self.act_depend_of:
            #For logic_dep, only one state raise put no action
            if type == 'network_dep':
                p_is_down = False
                dep_match = [dep.is_state(s) for s in status]
                if True in dep_match:#the parent match a case, so he is down
                    p_is_down = True
                parent_is_down.append(p_is_down)

        #if a parent is not down, no dep can explain the pb
        if False in parent_is_down:
            return
        else:# every parents are dead, so... It's not my fault :)
            self.set_unreachable()
            return


    #Use to know if I raise dependency for soneone else (with status)
    #If I do not raise dep, maybe my dep raise me. If so, I raise dep.
    #So it's a recursive function
    def do_i_raise_dependency(self, status, inherit_parents):
        #Do I raise dep?
        for s in status:
            if self.is_state(s):
                return True

        #If we do not inherit parent, we have no reason to be blocking
        if not inherit_parents:
            return False

        #Ok, I do not raise dep, but my dep maybe raise me
        now = time.time()
        for (dep, status, type, tp, inh_parent) in self.chk_depend_of:
            if dep.do_i_raise_dependency(status, inh_parent):
                if tp is None or tp.is_time_valid(now):
                    return True

        #No, I relly do not raise...
        return False


    #Use to know if my dep force me not to be checked
    #So check the chk_depend_of if they raise me
    def is_no_check_dependant(self):
        now = time.time()
        for (dep, status, type, tp, inh_parent) in self.chk_depend_of:
            if tp is None or tp.is_time_valid(now):
                if dep.do_i_raise_dependency(status, inh_parent):
                    return True
        return False


    #call by a bad consume check where item see that he have dep
    #and maybe he is not in real fault.
    def raise_dependancies_check(self, ref_check):
        now = time.time()
        cls = self.__class__
        checks = []
        for (dep, status, type, tp, inh_par) in self.act_depend_of:
            #If the dep timeperiod is not valid, do notraise the dep,
            #None=everytime
            if tp is None or tp.is_time_valid(now):
                #if the update is 'fresh', do not raise dep,
                #cached_check_horizon = cached_service_check_horizon for service
                if dep.last_state_update < now - cls.cached_check_horizon:
                    i = dep.launch_check(now, ref_check)
                    if i != None:
                        checks.append(i)
                else:
                    print "DBG: **************** The state is FRESH", dep.host_name, time.asctime(time.localtime(dep.last_state_update))
        return checks


    #Main scheduling function
    #If a check is in progress, or active cehck are disabled, do
    #not schedule a check.
    #The check interval change with HARD state or not:
    #SOFT: retry_interval
    #HARD: check_interval
    #The first scheduling is a little random, so all checks
    #are not launch in the same time...
    def schedule(self, force=False, force_time=None):
        #print "Scheduling:", self.get_name()
        #if last_chk == 0 put in a random way so all checks
        #are not in the same time

        now = time.time()
        #next_chk il already set, do not change
        #if self.next_chk >= now or self.in_checking and not force:
        if self.in_checking and not force:
            return None

        cls = self.__class__
        #if no active check and no force, no check
        #print "Service check?", cls.execute_checks
        if (not self.active_checks_enabled or not cls.execute_checks) and not force:
            return None

        #If I do not have an check_timeperiod and no force time, i do nothing
        if (not hasattr(self, 'check_period') or self.check_period == None and force_time==None):
            return None

        #Interval change is in a HARD state or not
        if self.state_type == 'HARD':
            interval = self.check_interval * 60
        else: #TODO : if no retry_interval?
            interval = self.retry_interval * 60

        #The next_chk is pass so we need a new one
        #so we got a check_interval
        if self.next_chk == 0:
            #At the start, we cannot have a interval more than cls.max_check_spread
            #is service_max_check_spread or host_max_check_spread in config
            interval = min(interval, cls.max_check_spread * 60)
            r = interval * (random.random() - 0.5)
            time_add = interval/2 + r
        else:
            time_add = interval

        if force_time is None:
            self.next_chk = self.check_period.get_next_valid_time_from_t(now + time_add)
        else:
            self.next_chk = force_time

        #If next time is None, do not go
        if self.next_chk == None:
            self.raise_no_next_check_log_entry()
            return None

        #Get the command to launch, and put it in queue
        self.launch_check(self.next_chk)


    #If we've got a system time change, we need to compensate it
    #If modify all past value. For active one like next_chk, it's the current
    #checks that will give us the new value
    def compensate_system_time_change(self, difference):
        #We only need to change some value
        need_change = ['last_notification', 'last_state_change', 'last_hard_state_change']
        for p in need_change:
            val = getattr(self, p) # current value
            #Do not go below 1970 :)
            val = max(0, val + difference) #diff can be -
            setattr(self, p, val)


    def remove_in_progress_check(self, c):
        #The check is consume, uptade the in_checking propertie
        if c in self.checks_in_progress:
            self.checks_in_progress.remove(c)
        else:
            print "Not removing check", c, "for ", self.get_name()
        self.update_in_checking()


    #Is in checking if and ony if there are still checks no consumed
    def update_in_checking(self):
        self.in_checking = (len(self.checks_in_progress) != 0)


    #Del just a notification that is retured
    def remove_in_progress_notification(self, n):
        if n.id in self.notifications_in_progress:
            n.status = 'zombie'
            del self.notifications_in_progress[n.id]


    #We do not need ours currents pending notifications,
    #so we zombify them and clean our list
    def remove_in_progress_notifications(self):
        for n in self.notifications_in_progress.values():
            self.remove_in_progress_notification(n)


    #Get a event handler if item got an event handler
    #command. It must be enabled locally and globally
    def get_event_handlers(self):
        cls = self.__class__
        if self.event_handler == None or not self.event_handler_enabled or not cls.enable_event_handlers:
            return

        print self.event_handler.__dict__
        m = MacroResolver()
        data = self.get_data_for_event_handler()
        cmd = m.resolve_command(self.event_handler, data)
        e = EventHandler(cmd, timeout=cls.event_handler_timeout)
        print "DBG: Event handler call created"
        print "DBG: ",e.__dict__
        self.raise_event_handler_log_entry(self.event_handler)

        #ok we can put it in our temp action queue
        self.actions.append(e)


    #Whenever a non-ok hard state is reached, we must check whether this
    #host/service has a flexible downtime waiting to be activated
    def check_for_flexible_downtime(self):
        status_updated = False
        for dt in self.downtimes:
            #activate flexible downtimes (do not activate triggered downtimes)
            if dt.fixed == False and dt.is_in_effect == False and dt.start_time <= self.last_chk and self.state_id != 0 and dt.trigger_id == 0:
                n = dt.enter() # returns downtimestart notifications
                if n is not None:
                    self.actions.append(n)
                status_updated = True
        if status_updated == True:
            self.broks.append(self.get_update_status_brok())


    #consume a check return and send action in return
    #main function of reaction of checks like raise notifications
    #Special case:
    #is_flapping : immediate notif when problem
    #is_in_scheduled_downtime : no notification
    #is_volatile : notif immediatly (service only)
    def consume_result(self, c):
        OK_UP = self.__class__.ok_up #OK for service, UP for host

        #We check for stalking if necessery
        #so if check is here
        self.manage_stalking(c)

        #Latency can be <0 is we get a check from the retention file
        #so if <0, set 0
        try:
            self.latency = max(0, c.check_time - c.t_to_go)
        except TypeError:
            #DBG
            print "DBG ERROR about time: ", c.check_time, c.t_to_go, c.ref.get_name()

        #Ok, the first check is done
        self.has_been_checked = 1

        #Now get data from check
        self.execution_time = c.execution_time
        self.last_chk = c.check_time
        self.output = c.output
        self.long_output = c.long_output

        #Get the perf_data only if we want it in the configuration
        if self.__class__.process_performance_data and self.process_perf_data:
            self.last_perf_data = self.perf_data
            self.perf_data = c.perf_data

        #Before set state, module thems
        for rm in self.resultmodulations:
            if rm != None:
                c.exit_status = rm.module_return(c.exit_status)

        #If we got a bad result on a normal check, and we have dep,
        #we raise dep checks
        #put the actual check in waitdep and we return all new checks
        if c.exit_status != 0 and c.status == 'waitconsume' and len(self.act_depend_of) != 0:
            #print self.get_name(), "I depend of someone, and I need a result"
            c.status = 'waitdep'
            #Make sure the check know about his dep
            #C is my check, and he wants dependancies
            checks_id = self.raise_dependancies_check(c)
            for check_id in checks_id:
                #Get checks_id of dep
                c.depend_on.append(check_id)
            #Ok, no more need because checks are not
            #take by host/service, and not returned

        self.set_state_from_exit_status(c.exit_status)

        #we change the state, do whatever we are or not in
        #an impact mode, we can put it
        self.state_changed_since_impact = True

        #The check is consume, uptade the in_checking propertie
        self.remove_in_progress_check(c)

        #C is a check and someone wait for it
        if c.status == 'waitconsume' and c.depend_on_me != []:
            #print c.id, self.get_name(), "OK, someone wait for me", len(c.depend_on_me)
            c.status = 'havetoresolvedep'

        #if finish, check need to be set to a zombie state to be removed
        #it can be change if necessery before return, like for dependancies
        if c.status == 'waitconsume' and c.depend_on_me == []:
            #print "SRV OK, nobody depend on me!!"
            c.status = 'zombie'

        #Use to know if notif is raise or not
        no_action = False

        #C was waitdep, but now all dep are resolved, so check for deps
        if c.status == 'waitdep':
            if c.depend_on_me != []:
                #print self.get_name(), "OK, someone wait for me", len(c.depend_on_me)
                c.status = 'havetoresolvedep'
            else:
                #print self.get_name(), "Great, noboby wait for me!"
                c.status = 'zombie'
            #Check deps
            no_action = self.is_no_action_dependant()
            #We recheck just for network_dep. Maybe we are just unreachable
            #and we need to overide the state_id
            self.check_and_set_unreachability()

        #no more return of actions or broks
        #but put them in a queue
        #res = []

        #OK following a previous OK. perfect if we were not in SOFT
        if c.exit_status == 0 and (self.last_state == OK_UP or self.last_state == 'PENDING'):
            #print "Case 1 (OK following a previous OK) : code:%s last_state:%s" % (c.exit_status, self.last_state)
            self.unacknowledge_problem()
            #action in return can be notification or other checks (dependancies)
            if (self.state_type == 'SOFT') and self.last_state != 'PENDING':
                if self.is_max_attempts() and self.state_type == 'SOFT':
                    self.state_type = 'HARD'
                else:
                    self.state_type = 'SOFT'
            else:
                self.attempt = 1
                self.state_type = 'HARD'

        #OK following a NON-OK.
        elif c.exit_status == 0 and (self.last_state != OK_UP and self.last_state != 'PENDING'):
            self.unacknowledge_problem()
            #print "Case 2 (OK following a NON-OK) : code:%s last_state:%s" % (c.exit_status, self.last_state)
            if self.state_type == 'SOFT':
                #OK following a NON-OK still in SOFT state
                self.add_attempt()
                self.raise_alert_log_entry()
                #Eventhandler gets OK;SOFT;++attempt, no notification needed
                self.get_event_handlers()
                #Internally it is a hard OK
                self.state_type = 'HARD'
                self.attempt = 1
            elif self.state_type == 'HARD':
                #OK following a HARD NON-OK
                self.raise_alert_log_entry()
                #Eventhandler and notifications get OK;HARD;maxattempts
                #Ok, so current notifications are not need, we 'zombie' thems
                self.remove_in_progress_notifications()
                if not no_action:
                    self.create_notifications('RECOVERY')
                self.get_event_handlers()
                #Internally it is a hard OK
                self.state_type = 'HARD'
                self.attempt = 1

                #DBG: PROBLEM/IMPACT management
                #I'm no more a problem if I was one
                self.no_more_a_problem()

        #Volatile part
        #Only for service
        elif c.exit_status != 0 and hasattr(self, 'is_volatile') and self.is_volatile:
            #print "Case 3 (volatile only)"
            #There are no repeated attempts, so the first non-ok results
            #in a hard state
            self.attempt = 1
            self.state_type = 'HARD'
            #status != 0 so add a log entry (before actions that can also raise log
            #it is smarter to log error before notification)
            self.raise_alert_log_entry()
            self.check_for_flexible_downtime()
            self.remove_in_progress_notifications()
            if not no_action:
                self.create_notifications('PROBLEM')
            #Ok, event handlers here too
            self.get_event_handlers()

            #DBG : can raise a problem...
            #PROBLEM/IMPACT
            #I'm a problem only if I'm the root problem,
            #so not no_action:
            if not no_action:
                self.set_myself_as_problem()

        #NON-OK follows OK. Everything was fine, but now trouble is ahead
        elif c.exit_status != 0 and (self.last_state == OK_UP or self.last_state == 'PENDING'):
            #print "Case 4 : NON-OK follows OK : code:%s last_state:%s" % (c.exit_status, self.last_state)
            if self.is_max_attempts():
                # if max_attempts == 1 we're already in deep trouble
                self.state_type = 'HARD'
                self.raise_alert_log_entry()
                self.remove_in_progress_notifications()
                self.check_for_flexible_downtime()
                if not no_action:
                    self.create_notifications('PROBLEM')
                #Oh? This is the typical go for a event handler :)
                self.get_event_handlers()

                #DBG : can raise a problem...
                #PROBLEM/IMPACT
                #I'm a problem only if I'm the root problem,
                #so not no_action:
                if not no_action:
                    self.set_myself_as_problem()

            else:
                #This is the first NON-OK result. Initiate the SOFT-sequence
                #Also launch the event handler, he might fix it.
                self.attempt = 1
                self.state_type = 'SOFT'
                self.raise_alert_log_entry()
                self.get_event_handlers()

        #If no OK in a no OK : if hard, still hard, if soft,
        #check at self.max_check_attempts
        #when we go in hard, we send notification
        elif c.exit_status != 0 and self.last_state != OK_UP:
            #print "Case 5 (no OK in a no OK) : code:%s last_state:%s state_type:%s" % (c.exit_status, self.last_state,self.state_type)
            if self.state_type == 'SOFT':
                self.add_attempt()
                if self.is_max_attempts():
                    #Ok here is when we just go to the hard state
                    self.state_type = 'HARD'
                    self.raise_alert_log_entry()
                    self.remove_in_progress_notifications()
                    #There is a request in the Nagios trac to enter downtimes
                    #on soft states which does make sense. If this becomes
                    #the default behavior, just move the following line
                    #into the else-branch below.
                    self.check_for_flexible_downtime()
                    if not no_action:
                        self.create_notifications('PROBLEM')
                    #So event handlers here too
                    self.get_event_handlers()

                    #DBG : can raise a problem...
                    #PROBLEM/IMPACT
                    #I'm a problem only if I'm the root problem,
                    #so not no_action:
                    if not no_action:
                        self.set_myself_as_problem()

                else:
                    self.raise_alert_log_entry()
                    #eventhandler is launched each time during the soft state
                    self.get_event_handlers()
            else:
                #Send notifications whenever the state has changed. (W -> C)
                if self.state != self.last_state:
                    self.unacknowledge_problem_if_not_sticky()
                    self.raise_alert_log_entry()
                    self.remove_in_progress_notifications()
                    if not no_action:
                        self.create_notifications('PROBLEM')

                    #DBG : can raise a problem...
                    #PROBLEM/IMPACT
                    #Maybe our new state can raise the problem
                    #when the last one was not
                    #I'm a problem only if I'm the root problem,
                    #so not no_action:
                    if not no_action:
                        self.set_myself_as_problem()

                elif self.in_scheduled_downtime_during_last_check == True:
                    #during the last check i was in a downtime. but now
                    #the status is still critical and notifications
                    #are possible again. send an alert immediately
                    self.remove_in_progress_notifications()
                    if not no_action:
                        self.create_notifications('PROBLEM')

        #Reset this flag. If it was true, actions were already taken
        self.in_scheduled_downtime_during_last_check == False

        #now is the time to update state_type_id
        if self.state_type == 'HARD':
            self.state_type_id = 1
        else:
            self.state_type_id = 0

        # update event/problem-counters
        self.update_event_and_problem_id()
        self.broks.append(self.get_check_result_brok())
        self.get_obsessive_compulsive_processor_command()
        self.get_perfdata_command()


    def update_event_and_problem_id(self):
        OK_UP = self.__class__.ok_up #OK for service, UP for host
        if self.state != self.last_state and self.last_state != 'PENDING' or self.state != OK_UP and self.last_state == 'PENDING':
            SchedulingItem.current_event_id += 1
            self.last_event_id = self.current_event_id
            self.current_event_id = SchedulingItem.current_event_id
            # now the problem_id
            if self.state != OK_UP and self.last_state == 'PENDING':
                # broken ever since i can remember
                SchedulingItem.current_problem_id += 1
                self.last_problem_id = self.current_problem_id
                self.current_problem_id = SchedulingItem.current_problem_id
            elif self.state != OK_UP and self.last_state != OK_UP:
                # State transitions between non-OK states (e.g. WARNING to CRITICAL) do not cause this problem id to increase.
                pass
            elif self.state == OK_UP:
                # If the service is currently in an OK state, this macro will be set to zero (0).
                self.last_problem_id = self.current_problem_id
                self.current_problem_id = 0
            else:
                # Every time a service (or host) transitions from an OK or UP state to a problem state, a global problem ID number is incremented by one (1).
                SchedulingItem.current_problem_id += 1
                self.last_problem_id = self.current_problem_id
                self.current_problem_id = SchedulingItem.current_problem_id


    #Called by scheduler when a notification is ok to be send
    #(so fuilly prepared to be send to reactionner). Here we update the command with
    #status of now, and we add the contact to set of contact we notified. And we raise the log
    #entry
    def prepare_notification_for_sending(self, n):
        if n.status == 'inpoller':
            self.update_notification_command(n)
            self.notified_contacts.add(n.contact)
            self.raise_notification_log_entry(n)


    #Just update the notification command by resolving Macros
    #And because we are just launching the notification, we can say
    #taht this contact have been notified
    def update_notification_command(self, n):
        m = MacroResolver()
        data = self.get_data_for_notifications(n.contact, n)
        n.command = m.resolve_command(n.command_call, data)



    #See if an escalation is eligible
    def is_escalable(self, t):
        #Check is an escalation match the current_notification_number
        for es in self.escalations:
            if es.is_eligible(t, self.state, self.current_notification_number):
                return True
        return False


    #Get all contacts (uniq) from eligible escalations
    def get_escalable_contacts(self, t):
        contacts = set()
        for es in self.escalations:
            if es.is_eligible(t, self.state, self.current_notification_number):
                contacts.update(es.contacts)
        return list(contacts)


    # Create a "master" notification here, which will later
    # (immediately before the reactionner gets it) be split up
    # in many "child" notifications, one for each contact.
    def create_notifications(self, type, t_wished = None):
        cls = self.__class__
        #t_wished==None for the first notification launch after consume
        #here we must look at the self.notification_period
        if t_wished == None:
            now = time.time()
            t_wished = now
            #if first notification, we must add first_notification_delay
            if self.current_notification_number == 0 and type == 'PROBLEM':
                last_time_non_ok_or_up = self.last_time_non_ok_or_up()
                if last_time_non_ok_or_up == 0:
                    # this happens at initial
                    t_wished = now + self.first_notification_delay * cls.interval_length
                else:
                    t_wished = last_time_non_ok_or_up + self.first_notification_delay * cls.interval_length
            t = self.notification_period.get_next_valid_time_from_t(t_wished)
        else:
            #We follow our order
            t = t_wished

        if self.notification_is_blocked_by_item(type, t_wished) and self.first_notification_delay == 0 and self.notification_interval == 0:
            # If notifications are blocked on the host/service level somehow
            # and repeated notifications are not configured,
            # we can silently drop this one
            return

        if type == 'PROBLEM':
            # Create the notification with an incremented notification_number.
            # The current_notification_number  of the item itself will only
            # be incremented when this notification (or its children)
            # have actually be sent.
            next_notif_nb = self.current_notification_number + 1
        elif type == 'RECOVERY':
            # Recovery resets the notification counter to zero
            self.current_notification_number = 0
            next_notif_nb = self.current_notification_number
        else:
            # downtime/flap/etc do not change the notification number
            next_notif_nb = self.current_notification_number
        n = Notification(type, 'scheduled', 'VOID', None, self, None, t, \
            timeout=cls.notification_timeout, \
            notif_nb=next_notif_nb)

        #Keep a trace in our notifications queue
        self.notifications_in_progress[n.id] = n
        #and put it in the temp queue for scheduler
        self.actions.append(n)


    # In create_notifications we created a notification "template". When it's
    # time to hand it over to the reactionner, this master notification needs
    # to be split in several child notifications, one for each contact
    # To be more exact, one for each contact who is willing to accept
    # notifications of this type and at this time
    def scatter_notification(self, n):
        cls = self.__class__
        childnotifications = []

        if n.contact:
            # only master notifications can be split up
            return []
        if n.type == 'RECOVERY':
            if self.first_notification_delay != 0 and len(self.notified_contacts) == 0:
                # Recovered during first_notification_delay. No notifications
                # have been sent yet, so we keep quiet
                contacts = []
            else:
                # The old way. Only send recover notifications to those contacts
                # who also got problem notifications
                #contacts = list(self.notified_contacts)
                # The new way. Allow recover-only contacts
                contacts = self.contacts
            self.notified_contacts.clear()
        else:
            #Check is an escalation match. If yes, get all contacts from escalations
            if self.is_escalable(n.t_to_go):
                contacts = self.get_escalable_contacts(n.t_to_go)
            #else take normal contacts
            else:
                contacts = self.contacts

        for contact in contacts:
            #Get the property name for notif commands, like
            #service_notification_commands for service
            notif_commands = contact.get_notification_commands(cls.my_type)

            for cmd in notif_commands:
                child_n = Notification(n.type, 'scheduled', 'VOID', cmd, self,
                    contact, n.t_to_go, timeout=cls.notification_timeout,
                    notif_nb=n.notif_nb )
                if not self.notification_is_blocked_by_contact(child_n, contact):
                    # Update the notification with fresh status information
                    # of the item. Example: during the notification_delay
                    # the status of a service may have changed from WARNING to CRITICAL
                    self.update_notification_command(child_n)
                    self.raise_notification_log_entry(child_n)
                    self.notifications_in_progress[child_n.id] = child_n
                    childnotifications.append(child_n)

            if n.type == 'PROBLEM':
                # Remember the contacts. We might need them later in the
                # recovery code some lines above
                self.notified_contacts.add(contact)

        return childnotifications


    #return a check to check the host/service
    #and return id of the check
    def launch_check(self, t, ref_check = None, force=False):
        c = None
        cls = self.__class__

        #if I'm already in checking, Why launch a new check?
        #If ref_check_id is not None , this is a dependancy_ check
        #If none, it might be a forced check, so OK, I do a new
        if not force and (self.in_checking and ref_check != None):
            #print "FUCK, I do not want to launch a new check, I alreay have one"
            c_in_progress = self.checks_in_progress[0] #0 is OK because in_checking is True
            if c_in_progress.t_to_go > time.time(): #Very far?
                c_in_progress.t_to_go = time.time() #No, I want a check right NOW
            c_in_progress.depend_on_me.append(ref_check)
            return c_in_progress.id

        if force or (not self.is_no_check_dependant()):
            #Get the command to launch
            m = MacroResolver()
            data = self.get_data_for_checks()
            command_line = m.resolve_command(self.check_command, data)

            #And get all environnement varialbe if need
            if cls.enable_environment_macros or cls.use_large_installation_tweaks:
                env = m.get_env_macros(data)
            else:
                env = {}

            #Make the Check object and put the service in checking
            #print "Asking for a check with command:", command_line
            #Make the check inherit poller_tag from the command
            c = Check('scheduled', command_line, self, t, ref_check, timeout=cls.check_timeout, poller_tag=self.check_command.poller_tag)
            #We keep a trace of all checks in progress
            #to know if we are in checking_or not
            self.checks_in_progress.append(c)
            #print self.get_name()+" we ask me for a check" + str(c.id)
        self.update_in_checking()

        #We need to put this new check in our actions queue
        #so scheduler can take it
        if c != None:
            self.actions.append(c)
            return c.id
        #None mean I already take it into account
        return None


    #Get the perfdata command with macro resolved for this
    def get_perfdata_command(self):
        cls = self.__class__
        if not cls.process_performance_data or not self.process_perf_data:
            return

        if cls.perfdata_command != None:
            m = MacroResolver()
            data = self.get_data_for_event_handler()
            cmd = m.resolve_command(cls.perfdata_command, data)
            e = EventHandler(cmd, timeout=cls.perfdata_timeout)

            #ok we can put it in our temp action queue
            self.actions.append(e)
