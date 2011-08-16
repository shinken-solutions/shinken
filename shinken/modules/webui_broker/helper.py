
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

    # T is in sec, need to print something like
    # 1h 3m 33s, or 2d 1h 3m 33s
    def print_duration(self, t):
        if t == 0 or t == None:
            return 'N/A'
        t = int(t)
        sec = t % 60
        minutes = t % 3600
        


    def print_duration(self, t):
        if t == 0 or t == None:
            return 'N/A'
        print "T", t
        seconds = int(time.time()) - int(t)
        seconds = abs(seconds)
        print "sec", seconds
        seconds = long(round(seconds))
        print "Sec2", seconds
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, _ = divmod(days, 30)
        years, days = divmod(days, 365.242199)
 
        minutes = long(minutes)
        hours = long(hours)
        days = long(days)
        years = long(years)
 
        duration = []
        if years > 0:
            duration.append('%d y' % years + 's'*(years != 1))
        else:
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
        return ' '.join(duration)


helper = Helper()
