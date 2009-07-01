import time

class Acknowledge:
    id = 0

    #Allows you to acknowledge the current problem for the specified service. By acknowledging
    #the current problem, future notifications (for the same servicestate) are disabled.
    #If the "sticky" option is set to one (1), the acknowledgement will remain until the
    #service returns to an OK state. Otherwise the acknowledgement will automatically be removed
    #when the service changes state. If the "notify" option is set to one (1), a notification will
    #be sent out to contacts indicating that the current service problem has been acknowledged. If
    #the "persistent" option is set to one (1), the comment associated with the acknowledgement
    #will survive across restarts of the Nagios process. If not, the comment will be deleted
    #the next time Nagios restarts.
    def __init__(self, ref, sticky, notify, persistent, author, comment):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.ref = ref #pointer to srv or host we are apply
        self.trigger_me = [] #The trigger i need to activate
        self.start_time = start_time
        if fixed:
            self.end_time = end_time
        else:
            self.end_time = self.start_time + duration
        if trigger_downtime is not None:
            trigger_downtime.trigger_me(self)
        self.author = author
        self.comment = comment


    def trigger_me(self, other_downtime):
        self.active_me.append(other_downtime)


    def is_in_downtime(self):
        now = time.time()
        return self.start_time <= now <= self.end_time
