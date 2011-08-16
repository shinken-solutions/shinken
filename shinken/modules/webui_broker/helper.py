
import time

class Helper(object):
    def __init__(self):
        pass

    def gogo(self):
        return 'HELLO'


    def act_inactive(self, b):
        if b:
            return 'Active'
        else:
            return 'Inactive'

    def yes_no(self, b):
        if b:
            return 'Yes'
        else:
            return 'No'

    def print_float(self, f):
        return '%.2f' % f

    def ena_disa(self, b):
        if b:
            return 'Enabled'
        else:
            return 'Disabled'

    # For a unix time return something like
    # Tue Aug 16 13:56:08 2011
    def print_date(self, t):
        if t == 0 or t == None:
            return 'N/A'
        return time.asctime(time.localtime(t))


    # For a time, print something like
    # 10m 37s  (just duration = True)
    # N/A if got bogus number (like 1970 or None)
    # 1h 30m 22s ago (if t < now)
    # Now (if t == now)
    # in 1h 30m 22s
    # Or in 1h 30m (no sec, if we ask only_x_elements=2, 0 means all)
    def print_duration(self, t, just_duration=False, x_elts=0):
        if t == 0 or t == None:
            return 'N/A'
        print "T", t
        # Get the difference between now and the time of the user
        seconds = int(time.time()) - int(t)
        
        # If it's now, say it :)
        if seconds == 0:
            return 'Now'

        in_future = False

        # Remember if it's in the future or not
        if seconds < 0:
            in_future = True
        
        # Now manage all case like in the past
        seconds = abs(seconds)
        print "In future?", in_future

        print "sec", seconds
        seconds = long(round(seconds))
        print "Sec2", seconds
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)
        months, weeks = divmod(weeks, 4)
        years, months = divmod(months, 12)
 
        minutes = long(minutes)
        hours = long(hours)
        days = long(days)
        weeks = long(weeks)
        months = long(months)
        years = long(years)
 
        duration = []
        if years > 0:
            duration.append('%dy' % years)
        else:
            if months > 0:
                duration.append('%dM' % months)
            if weeks > 0:
                duration.append('%dw' % weeks)
            if days > 0:
                duration.append('%dd' % days)
            if hours > 0:
                duration.append('%dh' % hours)
            if minutes > 0:
                duration.append('%dm' % minutes)
            if seconds > 0:
                duration.append('%ds' % seconds)

        print "Duration", duration
        # Now filter the number of printed elements if ask
        if x_elts >= 1:
            duration = duration[:x_elts]

        # Maybe the user just want the duration
        if just_duration:
            return ' '.join(duration)

        # Now manage the future or not print
        if in_future:
            return 'in '+' '.join(duration)
        else: # past :)
            return ' '.join(duration) + ' ago'


helper = Helper()
