#!/usr/bin/env python2.6

#
# This file is used to test timeperiods
#


#It's ugly I know....
from shinken_test import *
from timeperiod import Timeperiod

class TestTimeperiods(ShinkenTest):
    def setUp(self):
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_1r_1h_1s.cfg']
        self.conf = Config()
        self.conf.read_config(self.config_files)
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.clean_useless()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependancies()
        self.conf.explode_global_conf()
        self.conf.is_correct()
        self.confs = self.conf.cut_into_parts()
        self.dispatcher = Dispatcher(self.conf, self.me)
        self.sched = Scheduler(None)
        m = MacroResolver()
        m.init(self.conf)
        self.sched.load_conf(self.conf)
        e = ExternalCommand(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        self.sched.schedule()



    def test_simple_timeperiod(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        #Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_12

        #First a false test, no results
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, '1999-01-28  00:00-24:00')
        t_next = t.get_next_valid_time_from_t(now)
        self.assert_(t_next == None)

        #Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'tuesday 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print t_next
        self.assert_(t_next == "Tue Jul 13 16:30:00 2010")




    def test_simple_timeperiod_with_exclude(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        #Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_12

        #First a false test, no results
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, '1999-01-28  00:00-24:00')
        t_next = t.get_next_valid_time_from_t(now)
        self.assert_(t_next == None)

        #Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'tuesday 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print t_next
        self.assert_(t_next == "Tue Jul 13 16:30:00 2010")

        #Now we add this timeperiod an exception
        t2 = Timeperiod()
        t2.timeperiod_name = ''
        t2.resolve_daterange(t2.dateranges, 'tuesday 08:30-21:00')
        t.exclude = [t2]
        #So the next will be after 16:30 and not before 21:00. So
        #It will be 21:01

        #we clean the cache of previous calc of t ;)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "T exclude:", t_next
        self.assert_(t_next == "Tue Jul 13 21:01:00 2010")


    def test_dayweek_timeperiod_with_exclude(self):
        self.print_header()
        now = time.time()
        #Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        #Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday 2 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        self.assert_(t_next == "Tue Jul 13 16:30:00 2010")

        #Now we add this timeperiod an exception
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'tuesday 00:00-23:58')
        t.exclude = [t2]
        #We are a bad boy : first time period want a tuesday
        #but exclude do not want it until 23:58. So next is 59 :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)
        
        print "T next raw", t_next
        t_next = time.asctime(time.localtime(t_next))
        print "TOTO T next", t_next
        
        self.assert_(t_next == 'Tue Jul 13 23:59:00 2010')


    def test_mondayweek_timeperiod_with_exclude(self):
        self.print_header()
        now = time.time()
        #Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        #Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday 2 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        self.assert_(t_next == "Tue Jul 13 16:30:00 2010")

        #Now we add this timeperiod an exception
        #And a good one : from april (so before so agust (after), and full time.
        #But the 17 is a tuesday, but the 3 of august, so the next 2 tuesday is
        #..... the Tue Sep 14 :) Yes, we should wait quite a lot :)
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'april 1 - august 16 00:00-24:00')
        #print t2.__dict__
        t.exclude = [t2]
        #We are a bad boy : first time period want a tuesday
        #but exclude do not want it until 23:58. So next is 59 :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        #print "Check from", time.asctime(time.localtime(july_the_12))
        #t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)
        #print "T2 next valid", time.asctime(time.localtime(t_exclude))
        print "Next invalid T2", time.asctime(time.localtime(t_exclude_inv))
        
        print "T next raw", t_next
        print "T next?", time.asctime(time.localtime(t_next))
        t_next = time.asctime(time.localtime(t_next))
        
        self.assert_(t_next == 'Tue Sep 14 16:30:00 2010')





    def test_mondayweek_timeperiod_with_exclude_bis(self):
        self.print_header()
        now = time.time()
        #Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        #Then a funny daterange
        print "Testing daterange", 'tuesday -1 - monday 1  16:30-24:00'
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday -1 - monday 1  16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next without exclude", t_next
        self.assert_(t_next == "Tue Jul 27 16:30:00 2010")

        #Now we add this timeperiod an exception
        #And a good one : from april (so before so agust (after), and full time.
        #But the 27 is nw not possible? So what next? Add a month! 
        #last tuesday of august, the 31 :)
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'april 1 - august 16 00:00-24:00')
        #print t2.__dict__
        t.exclude = [t2]
        #We are a bad boy : first time period want a tuesday
        #but exclude do not want it until 23:58. So next is 59 :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        #print "Check from", time.asctime(time.localtime(july_the_12))
        #t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)
        #print "T2 next valid", time.asctime(time.localtime(t_exclude))
        print "Next invalid T2", time.asctime(time.localtime(t_exclude_inv))
        
        print "T next raw", t_next
        print "T next?", time.asctime(time.localtime(t_next))
        t_next = time.asctime(time.localtime(t_next))
        
        self.assert_(t_next == 'Tue Aug 31 16:30:00 2010')



    def test_funky_mondayweek_timeperiod_with_exclude_and_multiple_daterange(self):
        self.print_header()
        now = time.time()
        #Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        #Then a funny daterange
        print "Testing daterange", 'tuesday -1 - monday 1  16:30-24:00'
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday -1 - monday 1  16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next without exclude", t_next
        self.assert_(t_next == "Tue Jul 27 16:30:00 2010")

        #Now we add this timeperiod an exception
        #And a good one : from april (so before so agust (after), and full time.
        #But the 27 is nw not possible? So what next? Add a month! 
        #But maybe it's not enoutgth? :)
        #The withoutthe 2nd exclude, it's the Tues Aug 31, btu it's inside
        #saturday -1 - monday 1 because saturday -1 is the 28 august, so no.
        #in september saturday -1 is the 25, and tuesday -1 is 28, so still no
        #A month again! So now tuesday -1 is 26 and saturday -1 is 30. So ok
        #for this one! that was quite long isn't it? And funky ! :)
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'april 1 - august 16 00:00-24:00')
        #Oups, I add a inner daterange ;)
        t2.resolve_daterange(t2.dateranges, 'saturday -1 - monday 1  16:00-24:00')
        t.exclude = [t2]
        #We are a bad boy : first time period want a tuesday
        #but exclude do not want it until 23:58. So next is 59 :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        #print "Check from", time.asctime(time.localtime(july_the_12))
        #t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)
        #print "T2 next valid", time.asctime(time.localtime(t_exclude))
        print "Next invalid T2", time.asctime(time.localtime(t_exclude_inv))
        
        print "T next raw", t_next
        print "T next?", time.asctime(time.localtime(t_next))
        t_next = time.asctime(time.localtime(t_next))
        
        self.assert_(t_next == 'Tue Oct 26 16:30:00 2010')
        print "Finish this Funky test :)"
        


if __name__ == '__main__':
    unittest.main()
