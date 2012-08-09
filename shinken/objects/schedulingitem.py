#!/usr/bin/env python
# Copyright (C) 2009-2010 :
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

""" This class is a common one for service/host. Here you
will find all scheduling related functions, like the schedule
or the consume_check ones. It's a quite important class!
"""


import random
import time

from item import Item

from shinken.check import Check
from shinken.notification import Notification
from shinken.macroresolver import MacroResolver
from shinken.eventhandler import EventHandler
from shinken.dependencynode import DependencyNodeFactory
from shinken.util import safe_print

# on system time change just reevaluate the following attributes :
on_time_change_update = ( 'last_notification', 'last_state_change', 'last_hard_state_change' )


class SchedulingItem(Item):

    # global counters used for [current|last]_[host|service]_[event|problem]_id
    current_event_id = 0
    current_problem_id = 0


    # Call by picle for data-ify the host
    # we do a dict because list are too dangerous for
    # retention save and co :( even if it's more
    # extensive
    # The setstate function do the inverse
    def __getstate__(self):
        cls = self.__class__
        # id is not in *_properties
        res = { 'id' : self.id }
        for prop in cls.properties:
            if hasattr(self, prop):
                res[prop] = getattr(self, prop)
        for prop in cls.running_properties:
            if hasattr(self, prop):
                res[prop] = getattr(self, prop)
        return res

    # Inversed function of __getstate__
    def __setstate__(self, state):
        cls = self.__class__
        self.id = state['id']
        for prop in cls.properties:
            if prop in state:
                setattr(self, prop, state[prop])
        for prop in cls.running_properties:
            if prop in state:
                setattr(self, prop, state[prop])


    # Register the son in my child_dependencies, and
    # myself in its parent_dependencies
    def register_son_in_parent_child_dependencies(self, son):
        # So we register it in our list
        self.child_dependencies.add(son)

        # and us to its parents
        son.parent_dependencies.add(self)



    # Add a flapping change, but no more than 20 states
    # Then update the self.is_flapping bool by calling update_flapping
    def add_flapping_change(self, b):
        cls = self.__class__

        # If this element is not in flapping check, or
        # the flapping is globally disable, bailout
        if not self.flap_detection_enabled or not cls.enable_flap_detection:
            return

        self.flapping_changes.append(b)

        # Keep just 20 changes (global flap_history value)
        flap_history = cls.flap_history

        if len(self.flapping_changes) > flap_history:
            self.flapping_changes.pop(0)

        # Now we add a value, we update the is_flapping prop
        self.update_flapping()


    # We update the is_flapping prop with value in self.flapping_states
    # Old values have less weight than new ones
    def update_flapping(self):
        flap_history = self.__class__.flap_history
        # We compute the flapping change in %
        r = 0.0
        i = 0
        for b in self.flapping_changes:
            i += 1
            if b:
                r += i*(1.2-0.8)/flap_history + 0.8
        r = r / flap_history
        r *= 100

        # We can update our value
        self.percent_state_change = r

        # Look if we are full in our states, because if not
        # the value is not accurate
        is_full = len(self.flapping_changes) >= flap_history

        # Now we get the low_flap_threshold and high_flap_threshold values
        # They can be from self, or class
        (low_flap_threshold, high_flap_threshold) = (self.low_flap_threshold, self.high_flap_threshold)
        if low_flap_threshold == -1:
            cls = self.__class__
            low_flap_threshold = cls.global_low_flap_threshold
        if high_flap_threshold  == -1:
            cls = self.__class__
            high_flap_threshold = cls.global_high_flap_threshold

        # Now we check is flapping change, but only if we got enouth
        # states to llok at the value accurancy
        if self.is_flapping and r < low_flap_threshold and is_full:
            self.is_flapping = False
            # We also raise a log entry
            self.raise_flapping_stop_log_entry(r, low_flap_threshold)
            # and a notification
            self.remove_in_progress_notifications()
            self.create_notifications('FLAPPINGSTOP')
            # And update our status for modules
            b = self.get_update_status_brok()
            self.broks.append(b)

        if not self.is_flapping and r >= high_flap_threshold and is_full:
            self.is_flapping = True
            # We also raise a log entry
            self.raise_flapping_start_log_entry(r, high_flap_threshold)
            # and a notification
            self.remove_in_progress_notifications()
            self.create_notifications('FLAPPINGSTART')
            # And update our status for modules
            b = self.get_update_status_brok()
            self.broks.append(b)



    # Add an attempt but cannot be more than max_check_attempts
    def add_attempt(self):
        self.attempt += 1
        self.attempt = min(self.attempt, self.max_check_attempts)


    # Return True if attempt is at max
    def is_max_attempts(self):
        return self.attempt >= self.max_check_attempts


    # Call by scheduler to see if last state is older than
    # freshness_threshold if check_freshness, then raise a check
    # even if active check is disabled
    def do_check_freshness(self):
        now = time.time()
        # Before, check if class (host or service) have check_freshness OK
        # Then check if item whant fressness, then check fressness
        cls = self.__class__
        if not self.in_checking:
            if cls.global_check_freshness:
                if self.check_freshness and self.freshness_threshold != 0:
                    if self.last_state_update < now - (self.freshness_threshold + cls.additional_freshness_latency):
                        # Raise a log
                        self.raise_freshness_log_entry(int(now-self.last_state_update), int(now-self.freshness_threshold))
                        # And a new check
                        return self.launch_check(now)
        return None


    # Raise all impact from my error. I'm setting myself
    # as a problem, and I register myself as this in all
    # hosts/services that depend_on_me. So they are now my
    # impacts
    def set_myself_as_problem(self):
        now = time.time()

        self.is_problem = True
        # we should warn potentials impact of our problem
        # and they should be cool to register them so I've got
        # my impacts list
        for (impact, status, dep_type, tp, inh_par) in self.act_depend_of_me:
            # Check if the status is ok for impact
            for s in status:
                if self.is_state(s):
                    # now check if we should bailout because of a
                    # not good timeperiod for dep
                    if tp is None or tp.is_time_valid(now):
                        new_impacts = impact.register_a_problem(self)
                        self.impacts.extend(new_impacts)
                        # Make element unique in this list
                        self.impacts = list(set(self.impacts))

        # We can update our business_impact value now
        self.update_business_impact_value()

        # And we register a new broks for update status
        b = self.get_update_status_brok()
        self.broks.append(b)


    # We update our 'business_impact' value with the max of
    # the impacts business_impact if we got impacts. And save our 'configuration'
    # business_impact if we do not have do it before
    # If we do not have impacts, we revert our value
    def update_business_impact_value(self):
        # First save our business_impact if not already do
        if self.my_own_business_impact == -1:
            self.my_own_business_impact = self.business_impact

        # We look at our crit modulations. If one apply, we take apply it
        # and it's done
        in_modulation = False
        for cm in self.business_impact_modulations:
            now = time.time()
            period = cm.modulation_period
            if period is None or period.is_time_valid(now):                    
                #print "My self", self.get_name(), "go from crit", self.business_impact, "to crit", cm.business_impact
                self.business_impact = cm.business_impact
                in_modulation = True
                # We apply the first available, that's all
                break

        # If we trully have impacts, we get the max business_impact
        # if it's huge than ourselve
        if len(self.impacts) != 0:
            self.business_impact = max(self.business_impact, max([e.business_impact for e in self.impacts]))
            return

        # If we are not a problem, we setup our own_crit if we are not in a 
        # modulation period
        if self.my_own_business_impact != -1 and not in_modulation:
            self.business_impact = self.my_own_business_impact
            


    # Look for my impacts, and remove me from theirs problems list
    def no_more_a_problem(self):
        was_pb = self.is_problem
        if self.is_problem:
            self.is_problem = False

            # we warn impacts that we are no more a problem
            for impact in self.impacts:
                impact.deregister_a_problem(self)

            # we can just drop our impacts list
            self.impacts = []

        # We update our business_impact value, it's not a huge thing :)
        self.update_business_impact_value()

        # If we were a problem, we say to everyone
        # our new status, with good business_impact value
        if was_pb:
            # And we register a new broks for update status
            b = self.get_update_status_brok()
            self.broks.append(b)



    # call recursively by potentials impacts so they
    # update their source_problems list. But do not
    # go below if the problem is not a real one for me
    # like If I've got multiple parents for examples
    def register_a_problem(self, pb):
        now = time.time()
        was_an_impact = self.is_impact
        # Our father already look of he impacts us. So if we are here,
        # it's that we really are impacted
        self.is_impact = True

        impacts = []
        # Ok, if we are impacted, we can add it in our
        # problem list
        # TODO : remove this unused check
        if self.is_impact:
            # Maybe I was a problem myself, now I can say : not my fault!
            if self.is_problem:
                self.no_more_a_problem()

            # Ok, we are now an impact, we should take the good state
            # but only when we just go in impact state
            if not was_an_impact:
                self.set_impact_state()

            # Ok now we can be a simple impact
            impacts.append(self)
            if pb not in self.source_problems:
                self.source_problems.append(pb)
            # we should send this problem to all potential impact that
            # depend on us
            for (impact, status, dep_type, tp, inh_par) in self.act_depend_of_me:
                # Check if the status is ok for impact
                for s in status:
                    if self.is_state(s):
                        # now check if we should bailout because of a
                        # not good timeperiod for dep
                        if tp is None or tp.is_time_valid(now):
                            new_impacts = impact.register_a_problem(pb)
                            impacts.extend(new_impacts)

            # And we register a new broks for update status
            b = self.get_update_status_brok()
            self.broks.append(b)

        # now we return all impacts (can be void of course)
        return impacts


    # Just remove the problem from our problems list
    # and check if we are still 'impacted'. It's not recursif because problem
    # got the lsit of all its impacts
    def deregister_a_problem(self, pb):
        self.source_problems.remove(pb)

        # For know if we are still an impact, maybe our dependencies
        # are not aware of the remove of the impact state because it's not ordered
        # so we can just look at if we still have some problem in our list
        if len(self.source_problems) == 0:
            self.is_impact = False
            # No more an impact, we can unset the impact state
            self.unset_impact_state()

        # And we register a new broks for update status
        b = self.get_update_status_brok()
        self.broks.append(b)


    # When all dep are resolved, this function say if
    # action can be raise or not by viewing dep status
    # network_dep have to be all raise to be no action
    # logic_dep : just one is enouth
    def is_no_action_dependent(self):
        # Use to know if notif is raise or not
        # no_action = False
        parent_is_down = []
        # So if one logic is Raise, is dep
        # is one network is no ok, is not dep
        # at the end, raise no dep
        for (dep, status, type, tp, inh_par) in self.act_depend_of:
            # For logic_dep, only one state raise put no action
            if type == 'logic_dep':
                for s in status:
                    if dep.is_state(s):
                        return True
            # more complicated: if none of the states are match, the host is down
            # so -> network_dep
            else:
                p_is_down = False
                dep_match = [dep.is_state(s) for s in status]
                #check if the parent match a case, so he is down
                if True in dep_match:
                    p_is_down = True
                parent_is_down.append(p_is_down)
        # if a parent is not down, no dep can explain the pb
        if False in parent_is_down:
            return False
        else:# every parents are dead, so... It's not my fault :)
            return True


    # We check if we are no action just because of ours parents (or host for
    # service)
    # TODO : factorize with previous check?
    def check_and_set_unreachability(self):
        parent_is_down = []
        # We must have all parents raised to be unreachable
        for (dep, status, type, tp, inh_par) in self.act_depend_of:
            # For logic_dep, only one state raise put no action
            if type == 'network_dep':
                p_is_down = False
                dep_match = [dep.is_state(s) for s in status]
                if True in dep_match:#the parent match a case, so he is down
                    p_is_down = True
                parent_is_down.append(p_is_down)

        # if a parent is not down, no dep can explain the pb
        # or if we do'nt have any parents
        if len(parent_is_down) == 0 or False in parent_is_down:
            return
        else:# every parents are dead, so... It's not my fault :)
            self.set_unreachable()
            return


    # Use to know if I raise dependency for soneone else (with status)
    # If I do not raise dep, maybe my dep raise me. If so, I raise dep.
    # So it's a recursive function
    def do_i_raise_dependency(self, status, inherit_parents):
        # Do I raise dep?
        for s in status:
            if self.is_state(s):
                return True

        # If we do not inherit parent, we have no reason to be blocking
        if not inherit_parents:
            return False

        # Ok, I do not raise dep, but my dep maybe raise me
        now = time.time()
        for (dep, status, type, tp, inh_parent) in self.chk_depend_of:
            if dep.do_i_raise_dependency(status, inh_parent):
                if tp is None or tp.is_time_valid(now):
                    return True

        # No, I relly do not raise...
        return False


    # Use to know if my dep force me not to be checked
    # So check the chk_depend_of if they raise me
    def is_no_check_dependent(self):
        now = time.time()
        for (dep, status, type, tp, inh_parent) in self.chk_depend_of:
            if tp is None or tp.is_time_valid(now):
                if dep.do_i_raise_dependency(status, inh_parent):
                    return True
        return False


    # call by a bad consume check where item see that he have dep
    # and maybe he is not in real fault.
    def raise_dependencies_check(self, ref_check):
        now = time.time()
        cls = self.__class__
        checks = []
        for (dep, status, type, tp, inh_par) in self.act_depend_of:
            # If the dep timeperiod is not valid, do notraise the dep,
            # None=everytime
            if tp is None or tp.is_time_valid(now):
                # if the update is 'fresh', do not raise dep,
                # cached_check_horizon = cached_service_check_horizon for service
                if dep.last_state_update < now - cls.cached_check_horizon:
                    i = dep.launch_check(now, ref_check)
                    if i is not None:
                        checks.append(i)
#                else:
#                    print "DBG: **************** The state is FRESH", dep.host_name, time.asctime(time.localtime(dep.last_state_update))
        return checks


    # Main scheduling function
    # If a check is in progress, or active cehck are disabled, do
    # not schedule a check.
    # The check interval change with HARD state or not:
    # SOFT: retry_interval
    # HARD: check_interval
    # The first scheduling is a little random, so all checks
    # are not launch in the same time...
    def schedule(self, force=False, force_time=None):
        # if last_chk == 0 put in a random way so all checks
        # are not in the same time

        # next_chk il already set, do not change
        # unless we force the check or the time
        if self.in_checking and not (force or force_time):
            return None

        cls = self.__class__
        # if no active check and no force, no check
        if (not self.active_checks_enabled or not cls.execute_checks) and not force:
            return None

        # If check_interval is 0, we should not add it for a service
        # but suppose a 5min sched for hosts
        if self.check_interval == 0 and not force:
            if cls.my_type == 'service':
                return None
            else: # host
                self.check_interval = 300 / cls.interval_length

        # Interval change is in a HARD state or not
        # If the retry is 0, take the normal value
        if self.state_type == 'HARD' or self.retry_interval == 0:
            interval = self.check_interval * cls.interval_length
        else: #TODO : if no retry_interval?
            interval = self.retry_interval * cls.interval_length

        # The next_chk is pass so we need a new one
        # so we got a check_interval
        if self.next_chk == 0:
            # At the start, we cannot have a interval more than cls.max_check_spread
            # is service_max_check_spread or host_max_check_spread in config
            interval = min(interval, cls.max_check_spread * cls.interval_length)
            r = interval * (random.random() - 0.5)
            time_add = interval/2 + r
        else:
            time_add = interval

        # If not force_time, try to schedule
        if force_time is None:
            now = time.time()
            # Maybe we already got a next_chk that is in the future
            # like from a previous run (load from retention). If so, use it
            # by default it's 0, so there is no problem
            if self.next_chk < now:
                # maybe we do not have a check_period, if so, take always good (24x7)
                if self.check_period:
                    self.next_chk = self.check_period.get_next_valid_time_from_t(now + time_add)
                else:
                    self.next_chk = int(now + time_add)
            # else: keep the self.next_chk value in the future
        else:
            self.next_chk = int(force_time)

        # If next time is None, do not go
        if self.next_chk is None:
            # Nagios do not raise it, I'm wondering if we should
            # self.raise_no_next_check_log_entry()
            return None

        # Get the command to launch, and put it in queue
        self.launch_check(self.next_chk)


    # If we've got a system time change, we need to compensate it
    # If modify all past value. For active one like next_chk, it's the current
    # checks that will give us the new value
    def compensate_system_time_change(self, difference):
        # We only need to change some value
        for p in on_time_change_update:
            val = getattr(self, p) # current value
            #Do not go below 1970 :)
            val = max(0, val + difference) #diff can be -
            setattr(self, p, val)

    # For disabling active checks, we need to set active_checks_enabled
    # to false, but also make a dummy current checks attempts so the
    # effect is imediate.
    def disable_active_checks(self):
        self.active_checks_enabled = False
        for c in self.checks_in_progress:
            c.status = 'waitconsume'
            c.exit_status = self.state_id
            c.output = self.output
            c.check_time = time.time()
            c.execution_time = 0
            c.perf_data = self.perf_data


    def remove_in_progress_check(self, c):
        # The check is consume, uptade the in_checking propertie
        if c in self.checks_in_progress:
            self.checks_in_progress.remove(c)
        self.update_in_checking()


    # Is in checking if and ony if there are still checks no consumed
    def update_in_checking(self):
        self.in_checking = (len(self.checks_in_progress) != 0)


    # Del just a notification that is retured
    def remove_in_progress_notification(self, n):
        if n.id in self.notifications_in_progress:
            n.status = 'zombie'
            del self.notifications_in_progress[n.id]


    # We do not need ours currents pending notifications,
    # so we zombify them and clean our list
    def remove_in_progress_notifications(self):
        for n in self.notifications_in_progress.values():
            self.remove_in_progress_notification(n)


    # Get a event handler if item got an event handler
    # command. It must be enabled locally and globally
    def get_event_handlers(self, externalcmd=False):
        cls = self.__class__

        # The external command always pass
        # if not, only if we enable them (auto launch)
        if self.event_handler is None or ((not self.event_handler_enabled or not cls.enable_event_handlers) and not externalcmd):
            return
        
        # If we do not force and we are in downtime, bailout
        # if the no_event_handlers_during_downtimes is 1 in conf
        if cls.no_event_handlers_during_downtimes and not externalcmd and self.in_scheduled_downtime:
            return

        m = MacroResolver()
        data = self.get_data_for_event_handler()
        cmd = m.resolve_command(self.event_handler, data)
        rt = self.event_handler.reactionner_tag
        e = EventHandler(cmd, timeout=cls.event_handler_timeout, \
                             ref=self, reactionner_tag=rt)
        #print "DBG: Event handler call created"
        #print "DBG: ",e.__dict__
        self.raise_event_handler_log_entry(self.event_handler)

        # ok we can put it in our temp action queue
        self.actions.append(e)


    # Whenever a non-ok hard state is reached, we must check whether this
    # host/service has a flexible downtime waiting to be activated
    def check_for_flexible_downtime(self):
        status_updated = False
        for dt in self.downtimes:
            # activate flexible downtimes (do not activate triggered downtimes)
            if dt.fixed == False and dt.is_in_effect == False and dt.start_time <= self.last_chk and self.state_id != 0 and dt.trigger_id == 0:
                n = dt.enter() # returns downtimestart notifications
                if n is not None:
                    self.actions.append(n)
                status_updated = True
        if status_updated == True:
            self.broks.append(self.get_update_status_brok())


    # UNKNOWN during a HARD state are not so important, and they should
    # ot raise notif about it
    def update_hard_unknown_phase_state(self):
        self.was_in_hard_unknown_reach_phase = self.in_hard_unknown_reach_phase
        
        # We do not care about SOFT state at all
        # and we are sure we are no more in such a phase
        if self.state_type != 'HARD' or self.last_state_type != 'HARD':
            self.in_hard_unknown_reach_phase = False

        # So if we are not in already in such a phase, we check for
        # a start or not. So here we are sure to be in a HARD/HARD following
        # state
        if not self.in_hard_unknown_reach_phase:
            if self.state == 'UNKNOWN' and self.last_state != 'UNKNOWN' \
            or self.state == 'UNREACHABLE' and self.last_state != 'UNREACHABLE':
                self.in_hard_unknown_reach_phase = True
                # We also backup with which state we was before enter this phase
                self.state_before_hard_unknown_reach_phase = self.last_state
                return
        else:
            # if we were already in such a phase, look for its end
            if self.state != 'UNKNOWN' and self.state != 'UNREACHABLE':
                self.in_hard_unknown_reach_phase = False
            
        # If we just exit the phase, look if we exit with a different state
        # than we enter or not. If so, li and say we were not in such pahse
        # because we need so to raise a new notif
        if not self.in_hard_unknown_reach_phase and self.was_in_hard_unknown_reach_phase:
            if self.state != self.state_before_hard_unknown_reach_phase:
                self.was_in_hard_unknown_reach_phase = False



    # consume a check return and send action in return
    # main function of reaction of checks like raise notifications
    # Special case:
    # is_flapping : immediate notif when problem
    # is_in_scheduled_downtime : no notification
    # is_volatile : notif immediatly (service only)
    def consume_result(self, c):
        OK_UP = self.__class__.ok_up #OK for service, UP for host

        # Protect against bad type output
        # if str, go in unicode
        if isinstance(c.output, str):
            c.output = c.output.decode('utf8', 'ignore')
            c.long_output = c.long_output.decode('utf8', 'ignore')

        # Same for current output
        # TODO : remove in future version, this is need only for
        # migration from old shinken version, that got output as str
        # and not unicode
        # if str, go in unicode
        if isinstance(self.output, str):
            self.output = self.output.decode('utf8', 'ignore')
            self.long_output = self.long_output.decode('utf8', 'ignore')

        if isinstance(c.perf_data, str):
            c.perf_data = c.perf_data.decode('utf8', 'ignore')

        # We check for stalking if necessery
        # so if check is here
        self.manage_stalking(c)

        # Latency can be <0 is we get a check from the retention file
        # so if <0, set 0
        try:
            self.latency = max(0, c.check_time - c.t_to_go)
        except TypeError:
            pass

        # Ok, the first check is done
        self.has_been_checked = 1

        # Now get data from check
        self.execution_time = c.execution_time
        self.last_chk = int(c.check_time)

        # Get output and forgot bad UTF8 values for simple str ones
        # (we can get already unicode with external commands)
        self.output = c.output
        self.long_output = c.long_output

        # Get the perf_data only if we want it in the configuration
        if self.__class__.process_performance_data and self.process_perf_data:
            self.last_perf_data = self.perf_data
            self.perf_data = c.perf_data

        # Before set state, module thems
        for rm in self.resultmodulations:
            if rm is not None:
                c.exit_status = rm.module_return(c.exit_status)

        # If we got a bad result on a normal check, and we have dep,
        # we raise dep checks
        # put the actual check in waitdep and we return all new checks
        if c.exit_status != 0 and c.status == 'waitconsume' and len(self.act_depend_of) != 0:
            c.status = 'waitdep'
            # Make sure the check know about his dep
            # C is my check, and he wants dependencies
            checks_id = self.raise_dependencies_check(c)
            for check_id in checks_id:
                # Get checks_id of dep
                c.depend_on.append(check_id)
            # Ok, no more need because checks are not
            # take by host/service, and not returned

        # remember how we was before this check
        self.last_state_type = self.state_type

        self.set_state_from_exit_status(c.exit_status)

        # we change the state, do whatever we are or not in
        # an impact mode, we can put it
        self.state_changed_since_impact = True

        # The check is consume, uptade the in_checking propertie
        self.remove_in_progress_check(c)

        # C is a check and someone wait for it
        if c.status == 'waitconsume' and c.depend_on_me != []:
            c.status = 'havetoresolvedep'

        # if finish, check need to be set to a zombie state to be removed
        # it can be change if necessery before return, like for dependencies
        if c.status == 'waitconsume' and c.depend_on_me == []:
            c.status = 'zombie'

        # Use to know if notif is raise or not
        no_action = False

        # C was waitdep, but now all dep are resolved, so check for deps
        if c.status == 'waitdep':
            if c.depend_on_me != []:
                c.status = 'havetoresolvedep'
            else:
                c.status = 'zombie'
            # Check deps
            no_action = self.is_no_action_dependent()
            # We recheck just for network_dep. Maybe we are just unreachable
            # and we need to overide the state_id
            self.check_and_set_unreachability()

        # OK following a previous OK. perfect if we were not in SOFT
        if c.exit_status == 0 and self.last_state in (OK_UP, 'PENDING'):
            #print "Case 1 (OK following a previous OK) : code:%s last_state:%s" % (c.exit_status, self.last_state)
            self.unacknowledge_problem()
            # action in return can be notification or other checks (dependencies)
            if (self.state_type == 'SOFT') and self.last_state != 'PENDING':
                if self.is_max_attempts() and self.state_type == 'SOFT':
                    self.state_type = 'HARD'
                else:
                    self.state_type = 'SOFT'
            else:
                self.attempt = 1
                self.state_type = 'HARD'

        # OK following a NON-OK.
        elif c.exit_status == 0 and self.last_state not in (OK_UP, 'PENDING'):
            self.unacknowledge_problem()
            #print "Case 2 (OK following a NON-OK) : code:%s last_state:%s" % (c.exit_status, self.last_state)
            if self.state_type == 'SOFT':
                # OK following a NON-OK still in SOFT state
                self.add_attempt()
                self.raise_alert_log_entry()
                # Eventhandler gets OK;SOFT;++attempt, no notification needed
                self.get_event_handlers()
                # Internally it is a hard OK
                self.state_type = 'HARD'
                self.attempt = 1
            elif self.state_type == 'HARD':
                # OK following a HARD NON-OK
                self.raise_alert_log_entry()
                # Eventhandler and notifications get OK;HARD;maxattempts
                # Ok, so current notifications are not need, we 'zombie' thems
                self.remove_in_progress_notifications()
                if not no_action:
                    self.create_notifications('RECOVERY')
                self.get_event_handlers()
                # Internally it is a hard OK
                self.state_type = 'HARD'
                self.attempt = 1

                #self.update_hard_unknown_phase_state()
                # I'm no more a problem if I was one
                self.no_more_a_problem()

        # Volatile part
        # Only for service
        elif c.exit_status != 0 and getattr(self, 'is_volatile', False):
            #print "Case 3 (volatile only)"
            # There are no repeated attempts, so the first non-ok results
            # in a hard state
            self.attempt = 1
            self.state_type = 'HARD'
            # status != 0 so add a log entry (before actions that can also raise log
            # it is smarter to log error before notification)
            self.raise_alert_log_entry()
            self.check_for_flexible_downtime()
            self.remove_in_progress_notifications()
            if not no_action:
                self.create_notifications('PROBLEM')
            # Ok, event handlers here too
            self.get_event_handlers()

            #PROBLEM/IMPACT
            # I'm a problem only if I'm the root problem,
            # so not no_action:
            if not no_action:
                self.set_myself_as_problem()

        # NON-OK follows OK. Everything was fine, but now trouble is ahead
        elif c.exit_status != 0 and self.last_state in (OK_UP, 'PENDING'):
            #print "Case 4 : NON-OK follows OK : code:%s last_state:%s" % (c.exit_status, self.last_state)
            if self.is_max_attempts():
                # if max_attempts == 1 we're already in deep trouble
                self.state_type = 'HARD'
                self.raise_alert_log_entry()
                self.remove_in_progress_notifications()
                self.check_for_flexible_downtime()
                if not no_action:
                    self.create_notifications('PROBLEM')
                # Oh? This is the typical go for a event handler :)
                self.get_event_handlers()

                # PROBLEM/IMPACT
                # I'm a problem only if I'm the root problem,
                # so not no_action:
                if not no_action:
                    self.set_myself_as_problem()

            else:
                # This is the first NON-OK result. Initiate the SOFT-sequence
                # Also launch the event handler, he might fix it.
                self.attempt = 1
                self.state_type = 'SOFT'
                self.raise_alert_log_entry()
                self.get_event_handlers()

        # If no OK in a no OK : if hard, still hard, if soft,
        # check at self.max_check_attempts
        # when we go in hard, we send notification
        elif c.exit_status != 0 and self.last_state != OK_UP:
            #print "Case 5 (no OK in a no OK) : code:%s last_state:%s state_type:%s" % (c.exit_status, self.last_state,self.state_type)
            if self.state_type == 'SOFT':
                self.add_attempt()
                if self.is_max_attempts():
                    # Ok here is when we just go to the hard state
                    self.state_type = 'HARD'
                    self.raise_alert_log_entry()
                    self.remove_in_progress_notifications()
                    # There is a request in the Nagios trac to enter downtimes
                    # on soft states which does make sense. If this becomes
                    # the default behavior, just move the following line
                    # into the else-branch below.
                    self.check_for_flexible_downtime()
                    if not no_action:
                        self.create_notifications('PROBLEM')
                    # So event handlers here too
                    self.get_event_handlers()

                    # PROBLEM/IMPACT
                    # I'm a problem only if I'm the root problem,
                    # so not no_action:
                    if not no_action:
                        self.set_myself_as_problem()

                else:
                    self.raise_alert_log_entry()
                    # eventhandler is launched each time during the soft state
                    self.get_event_handlers()
            else:
                # Send notifications whenever the state has changed. (W -> C)
                # but not if the current state is UNKNOWN (hard C-> hard U -> hard C should
                # not retart notifications)
                if self.state != self.last_state:
                    self.update_hard_unknown_phase_state()
                    #print self.last_state, self.last_state_type, self.state_type, self.state
                    if not self.in_hard_unknown_reach_phase and not self.was_in_hard_unknown_reach_phase:
                        self.unacknowledge_problem_if_not_sticky()
                        self.raise_alert_log_entry()
                        self.remove_in_progress_notifications()
                        if not no_action:
                            self.create_notifications('PROBLEM')

                        # PROBLEM/IMPACT
                        # Maybe our new state can raise the problem
                        # when the last one was not
                        # I'm a problem only if I'm the root problem,
                        # so not no_action:
                        if not no_action:
                            self.set_myself_as_problem()

                elif self.in_scheduled_downtime_during_last_check == True:
                    # during the last check i was in a downtime. but now
                    # the status is still critical and notifications
                    # are possible again. send an alert immediately
                    self.remove_in_progress_notifications()
                    if not no_action:
                        self.create_notifications('PROBLEM')

        self.update_hard_unknown_phase_state()
        # Reset this flag. If it was true, actions were already taken
        self.in_scheduled_downtime_during_last_check = False

        # now is the time to update state_type_id
        # and our last_hard_state
        if self.state_type == 'HARD':
            self.state_type_id = 1
            self.last_hard_state = self.state
            self.last_hard_state_id = self.state_id
        else:
            self.state_type_id = 0

        # Fill last_hard_state_change to now
        # if we just change from SOFT->HARD or
        # in HARD we change of state (Warning->critical, or critical->ok, etc etc)
        if self.state_type == 'HARD' and (self.last_state_type == 'SOFT' or self.last_state != self.state):
            self.last_hard_state_change = int(time.time())

        # update event/problem-counters
        self.update_event_and_problem_id()
        self.broks.append(self.get_check_result_brok())
        self.get_obsessive_compulsive_processor_command()
        self.get_perfdata_command()




    def update_event_and_problem_id(self):
        OK_UP = self.__class__.ok_up #OK for service, UP for host
        if ( self.state != self.last_state and self.last_state != 'PENDING' 
                or self.state != OK_UP and self.last_state == 'PENDING' ):
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
                # State transitions between non-OK states
                # (e.g. WARNING to CRITICAL) do not cause
                # this problem id to increase.
                pass
            elif self.state == OK_UP:
                # If the service is currently in an OK state,
                # this macro will be set to zero (0).
                self.last_problem_id = self.current_problem_id
                self.current_problem_id = 0
            else:
                # Every time a service (or host) transitions from
                # an OK or UP state to a problem state, a global
                # problem ID number is incremented by one (1).
                SchedulingItem.current_problem_id += 1
                self.last_problem_id = self.current_problem_id
                self.current_problem_id = SchedulingItem.current_problem_id


    # Called by scheduler when a notification is
    # ok to be send (so fuilly prepared to be send
    # to reactionner). Here we update the command with
    # status of now, and we add the contact to set of
    # contact we notified. And we raise the log entry
    def prepare_notification_for_sending(self, n):
        if n.status == 'inpoller':
            self.update_notification_command(n)
            self.notified_contacts.add(n.contact)
            self.raise_notification_log_entry(n)


    # Just update the notification command by resolving Macros
    # And because we are just launching the notification, we can say
    # that this contact have been notified
    def update_notification_command(self, n):
        cls = self.__class__
        m = MacroResolver()
        data = self.get_data_for_notifications(n.contact, n)
        n.command = m.resolve_command(n.command_call, data)
        if not cls.use_large_installation_tweaks and cls.enable_environment_macros:
            n.env = m.get_env_macros(data)



    # See if an escalation is eligible at t and notif nb=n
    def is_escalable(self, n):
        cls = self.__class__

        # We search since when we are in notification for escalations
        # that are based on time
        in_notif_time = time.time() - n.creation_time

        # Check is an escalation match the current_notification_number
        for es in self.escalations:
            if es.is_eligible(n.t_to_go, self.state, n.notif_nb, in_notif_time, cls.interval_length):
                return True
        return False


    # Give for a notification the next notification time
    # by taking the standard notification_interval or ask for
    # our escalation if one of them need a smaller value to escalade
    def get_next_notification_time(self, n):
        res = None
        now = time.time()
        cls = self.__class__

        # Get the standard time like if we got no escalations
        std_time = n.t_to_go + self.notification_interval * cls.interval_length
        # standard time is a good one
        res = std_time
        
        creation_time = n.creation_time
        in_notif_time = now - n.creation_time

        for es in self.escalations:
            # If the escalation was alrady raised, we do not look for a new "early start"
            if es.get_name() not in n.already_start_escalations:
                r = es.get_next_notif_time(std_time, self.state, creation_time, cls.interval_length)
                # If we got a real result (time base escalation), we add it
                if r is not None and r < res:
                    res = r

        # And we take the minimum of this result. Can be standard or escalation asked
        return res


    # Get all contacts (uniq) from eligible escalations
    def get_escalable_contacts(self,n):
        cls = self.__class__

        # We search since when we are in notification for escalations
        # that are based on this time
        in_notif_time = time.time() - n.creation_time
        
        contacts = set()
        for es in self.escalations:
            if es.is_eligible(n.t_to_go, self.state, n.notif_nb, in_notif_time, cls.interval_length):
                contacts.update(es.contacts)
                # And we tag this escalations as started now
                n.already_start_escalations.add(es.get_name())

        return list(contacts)


    # Create a "master" notification here, which will later
    # (immediately before the reactionner gets it) be split up
    # in many "child" notifications, one for each contact.
    def create_notifications(self, type, t_wished = None):
        cls = self.__class__
        # t_wished==None for the first notification launch after consume
        # here we must look at the self.notification_period
        if t_wished is None:
            now = time.time()
            t_wished = now
            # if first notification, we must add first_notification_delay
            if self.current_notification_number == 0 and type == 'PROBLEM':
                last_time_non_ok_or_up = self.last_time_non_ok_or_up()
                if last_time_non_ok_or_up == 0:
                    # this happens at initial
                    t_wished = now + self.first_notification_delay * cls.interval_length
                else:
                    t_wished = last_time_non_ok_or_up + self.first_notification_delay * cls.interval_length
            if self.notification_period is None:
                t = int(now)
            else:
                t = self.notification_period.get_next_valid_time_from_t(t_wished)
        else:
            # We follow our order
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

        # Keep a trace in our notifications queue
        self.notifications_in_progress[n.id] = n
        # and put it in the temp queue for scheduler
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
                contacts = list(self.notified_contacts)
            self.notified_contacts.clear()
        else:
            # Check is an escalation match. If yes, get all contacts from escalations
            if self.is_escalable(n):
                contacts = self.get_escalable_contacts(n)
            # else take normal contacts
            else:
                contacts = self.contacts

        for contact in contacts:
            # Get the property name for notif commands, like
            # service_notification_commands for service
            notif_commands = contact.get_notification_commands(cls.my_type)

            for cmd in notif_commands:
                rt = cmd.reactionner_tag
                child_n = Notification(n.type, 'scheduled', 'VOID', cmd, self,
                    contact, n.t_to_go, timeout=cls.notification_timeout,
                    notif_nb=n.notif_nb, reactionner_tag=rt, module_type=cmd.module_type)
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


    # return a check to check the host/service
    # and return id of the check
    def launch_check(self, t, ref_check = None, force=False):
        c = None
        cls = self.__class__

        # if I'm already in checking, Why launch a new check?
        # If ref_check_id is not None , this is a dependency_ check
        # If none, it might be a forced check, so OK, I do a new
        if not force and (self.in_checking and ref_check is not None):
            now = time.time()
            c_in_progress = self.checks_in_progress[0] #0 is OK because in_checking is True
            if c_in_progress.t_to_go > now: #Very far?
                c_in_progress.t_to_go = now #No, I want a check right NOW
            c_in_progress.depend_on_me.append(ref_check)
            return c_in_progress.id

        if force or (not self.is_no_check_dependent()):
            # Get the command to launch
            m = MacroResolver()
            data = self.get_data_for_checks()
            command_line = m.resolve_command(self.check_command, data)

            # By default env is void
            env = {}

            # And get all environnement varialbe only if need
            if not cls.use_large_installation_tweaks and cls.enable_environment_macros:
                env = m.get_env_macros(data)

            # Make the Check object and put the service in checking
            # Make the check inherit poller_tag from the command
            # And reactionner_tag too
            c = Check('scheduled', command_line, self, t, ref_check, \
                          timeout=cls.check_timeout, \
                          poller_tag=self.check_command.poller_tag, \
                          env=env, \
                          module_type=self.check_command.module_type)

            # We keep a trace of all checks in progress
            # to know if we are in checking_or not
            self.checks_in_progress.append(c)
        self.update_in_checking()

        # We need to put this new check in our actions queue
        # so scheduler can take it
        if c is not None:
            self.actions.append(c)
            return c.id
        # None mean I already take it into account
        return None


    # Get the perfdata command with macro resolved for this
    def get_perfdata_command(self):
        cls = self.__class__
        if not cls.process_performance_data or not self.process_perf_data:
            return

        if cls.perfdata_command is not None:
            m = MacroResolver()
            data = self.get_data_for_event_handler()
            cmd = m.resolve_command(cls.perfdata_command, data)
            reactionner_tag = cls.perfdata_command.reactionner_tag
            e = EventHandler(cmd, timeout=cls.perfdata_timeout,
                             ref=self, reactionner_tag=reactionner_tag)

            # ok we can put it in our temp action queue
            self.actions.append(e)


    # Create the whole business rule tree
    # if we need it
    def create_business_rules(self, hosts, services):
        cmdCall = getattr(self, 'check_command', None)

        # If we do not have a command, we bailout
        if cmdCall is None:
            return

        # we get our based command, like
        # check_tcp!80 -> check_tcp
        cmd = cmdCall.call
        elts = cmd.split('!')
        base_cmd = elts[0]

        # If it's bp_rule, we got a rule :)
        if base_cmd == 'bp_rule':
            #print "Got rule", elts, cmd
            self.got_business_rule = True
            rule = ''
            if len(elts) >= 2:
                rule = '!'.join(elts[1:])

            fact = DependencyNodeFactory()
            node = fact.eval_cor_patern(rule, hosts, services)
            #print "got node", node
            self.business_rule = node


    # We ask us to manage our own internal check,
    # like a business based one
    def manage_internal_check(self, c):
        #print "DBG, ask me to manage a check!"
        if c.command.startswith('bp_'):
            state = self.business_rule.get_state()
        elif c.command == '_internal_host_up':
            state = 0
            c.execution_time = 0
            c.output = 'Host assumed to be UP'
            c.long_output = c.output
        c.check_time = time.time()
        c.exit_status = state
        #print "DBG, setting state", state


    # If I'm a business rule service/hsot, I register myself to the
    # elements I will depend on, so They will have ME as an impact
    def create_business_rules_dependencies(self):
        if self.got_business_rule:
            #print "DBG: ask me to register me in my dependencies", self.get_name()
            elts = self.business_rule.list_all_elements()
            # I will register myself in this
            for e in elts:
                #print "I register to the element", e.get_name()
                # all states, every timeperiod, and inherit parents
                e.add_business_rule_act_dependency(self, ['d', 'u', 's', 'f', 'c', 'w'], None, True)


    def rebuild_ref(self):
        """ Rebuild the possible reference a schedulingitem can have """
        for g in self.comments, self.downtimes:
            for o in g:
                o.ref = self
