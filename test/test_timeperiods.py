#!/usr/bin/env python
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#
# This file is used to test timeperiods
#

from shinken_test import *
from shinken.objects.timeperiod import Timeperiod


class TestTimeperiods(ShinkenTest):

    def test_simple_timeperiod(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_12

        # First a false test, no results
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, '1999-01-28  00:00-24:00')
        t_next = t.get_next_valid_time_from_t(now)
        self.assertIs(None, t_next)

        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'tuesday 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print t_next
        self.assertEqual("Tue Jul 13 16:30:00 2010", t_next)

    def test_simple_with_multiple_time(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_12

        # First a false test, no results
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, '1999-01-28  00:00-07:00,21:30-24:00')
        t_next = t.get_next_valid_time_from_t(now)
        self.assertIs(None, t_next)

        # Then a simple same day
        print "Cheking validity for", time.asctime(time.localtime(july_the_12))
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'tuesday 00:00-07:00,21:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "RES:", t_next
        self.assertEqual("Tue Jul 13 00:00:00 2010", t_next)

        # Now ask about at 00:00 time?
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 00:00:00", "%d %b %Y %H:%M:%S"))
        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'tuesday 00:00-07:00,21:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next?", t_next
        self.assertEqual("Tue Jul 13 00:00:00 2010", t_next)

    def test_simple_with_multiple_time_mutltiple_days(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_12

        # First a false test, no results
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, '1999-01-28  00:00-07:00,21:30-24:00')
        t_next = t.get_next_valid_time_from_t(now)
        self.assertIs(None, t_next)

        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        # monday          00:00-07:00,21:30-24:00
        # tuesday         00:00-07:00,21:30-24:00
        print "Cheking validity for", time.asctime(time.localtime(july_the_12))
        t.resolve_daterange(t.dateranges, 'monday 00:00-07:00,21:30-24:00')
        t.resolve_daterange(t.dateranges, 'tuesday 00:00-07:00,21:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "RES:", t_next
        self.assertEqual("Mon Jul 12 21:30:00 2010", t_next)
        # what about the next invalid?
        t_next_inv = t.get_next_invalid_time_from_t(july_the_12)
        t_next_inv = time.asctime(time.localtime(t_next_inv))
        print "RES:", t_next_inv
        self.assertEqual("Mon Jul 12 15:00:00 2010", t_next_inv)
        # what about a valid time and ask next invalid? Like at 22:00h?
        print "GO" * 10
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 22:00:00", "%d %b %Y %H:%M:%S"))
        t_next_inv = t.get_next_invalid_time_from_t(july_the_12)
        t_next_inv = time.asctime(time.localtime(t_next_inv))
        print "RES:", t_next_inv #, t.is_time_valid(july_the_12)
        self.assertEqual("Tue Jul 13 07:01:00 2010", t_next_inv)

        # Now ask about at 00:00 time?
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 00:00:00", "%d %b %Y %H:%M:%S"))
        print "Cheking validity for", time.asctime(time.localtime(july_the_12))
        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'monday 00:00-07:00,21:30-24:00')
        t.resolve_daterange(t.dateranges, 'tuesday 00:00-07:00,21:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next?", t_next
        self.assertEqual("Mon Jul 12 00:00:00 2010", t_next)

        # Now look for the never case
        print "24x7" * 10
        t = self.conf.timeperiods.find_by_name('24x7')
        self.assertIsNot(t, None)
        t_next_inv = t.get_next_invalid_time_from_t(july_the_12)
        t_next_inv = time.asctime(time.localtime(t_next_inv))
        print "RES:", t_next_inv #, t.is_time_valid(july_the_12)
        self.assertEqual('Wed Jul 13 00:01:00 2011', t_next_inv)

    def test_simple_timeperiod_with_exclude(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_12

        # First a false test, no results
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, '1999-01-28  00:00-24:00')
        t_next = t.get_next_valid_time_from_t(now)
        self.assertIs(None, t_next)

        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, 'tuesday 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print t_next
        self.assertEqual("Tue Jul 13 16:30:00 2010", t_next)

        # Now we add this timeperiod an exception
        t2 = Timeperiod()
        t2.timeperiod_name = ''
        t2.resolve_daterange(t2.dateranges, 'tuesday 08:30-21:00')
        t.exclude = [t2]
        # So the next will be after 16:30 and not before 21:00. So
        # It will be 21:00:01 (first second after invalid is valid)

        # we clean the cache of previous calc of t ;)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "T nxt with exclude:", t_next
        self.assertEqual("Tue Jul 13 21:00:01 2010", t_next)

    def test_dayweek_timeperiod_with_exclude(self):
        self.print_header()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday 2 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "T next", t_next
        self.assertEqual("Tue Jul 13 16:30:00 2010", t_next)

        # Now we add this timeperiod an exception
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'tuesday 00:00-23:58')
        t.exclude = [t2]
        # We are a bad boy: first time period want a tuesday
        # but exclude do not want it until 23:58. So next is 58 + 1second :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)

        print "T next raw", t_next
        t_next = time.asctime(time.localtime(t_next))
        print "TOTO T next", t_next

        self.assertEqual('Tue Jul 13 23:58:01 2010', t_next)

    def test_mondayweek_timeperiod_with_exclude(self):
        self.print_header()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        # Then a simple same day
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday 2 16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        self.assertEqual("Tue Jul 13 16:30:00 2010", t_next)

        # Now we add this timeperiod an exception
        # And a good one: from april (so before so agust (after), and full time.
        # But the 17 is a tuesday, but the 3 of august, so the next 2 tuesday is
        # ..... the Tue Sep 14 :) Yes, we should wait quite a lot :)
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'april 1 - august 16 00:00-24:00')
        #print t2.__dict__
        t.exclude = [t2]
        # We are a bad boy: first time period want a tuesday
        # but exclude do not want it until 23:58. So next is 59 :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        #print "Check from", time.asctime(time.localtime(july_the_12))
        #t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)
        #print "T2 next valid", time.asctime(time.localtime(t_exclude))
        print "Next invalid T2", time.asctime(time.localtime(t_exclude_inv))

        print "T next raw JEAN", t_next
        print "T next?", time.asctime(time.localtime(t_next))
        t_next = time.asctime(time.localtime(t_next))

        self.assertEqual('Tue Sep 14 16:30:00 2010', t_next)

    def test_mondayweek_timeperiod_with_exclude_bis(self):
        self.print_header()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        # Then a funny daterange
        print "Testing daterange", 'tuesday -1 - monday 1  16:30-24:00'
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday -1 - monday 1  16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next without exclude", t_next
        self.assertEqual("Tue Jul 27 16:30:00 2010", t_next)

        # Now we add this timeperiod an exception
        # And a good one: from april (so before so agust (after), and full time.
        # But the 27 is nw not possible? So what next? Add a month!
        # last tuesday of august, the 31 :)
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'april 1 - august 16 00:00-24:00')
        #print t2.__dict__
        t.exclude = [t2]
        # We are a bad boy: first time period want a tuesday
        # but exclude do not want it until 23:58. So next is 59 :)
        t.cache = {}
        t_next = t.get_next_valid_time_from_t(july_the_12)
        #print "Check from", time.asctime(time.localtime(july_the_12))
        #t_exclude = t2.get_next_valid_time_from_t(july_the_12)
        t_exclude_inv = t2.get_next_invalid_time_from_t(july_the_12)
        #print "T2 next valid", time.asctime(time.localtime(t_exclude))
        print "Next invalid T2", time.asctime(time.localtime(t_exclude_inv))

        print "T next raw JEAN2", t_next
        print "T next?", time.asctime(time.localtime(t_next))
        t_next = time.asctime(time.localtime(t_next))

        self.assertEqual('Tue Aug 31 16:30:00 2010', t_next)

    def test_funky_mondayweek_timeperiod_with_exclude_and_multiple_daterange(self):
        self.print_header()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        # Then a funny daterange
        print "Testing daterange", 'tuesday -1 - monday 1  16:30-24:00'
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday -1 - monday 1  16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next without exclude", t_next
        self.assertEqual("Tue Jul 27 16:30:00 2010", t_next)

        # Now we add this timeperiod an exception
        # And a good one: from april (so before so agust (after), and full time.
        # But the 27 is nw not possible? So what next? Add a month!
        # But maybe it's not enoutgth? :)
        # The withoutthe 2nd exclude, it's the Tues Aug 31, btu it's inside
        # saturday -1 - monday 1 because saturday -1 is the 28 august, so no.
        # in september saturday -1 is the 25, and tuesday -1 is 28, so still no
        # A month again! So now tuesday -1 is 26 and saturday -1 is 30. So ok
        # for this one! that was quite long isn't it? And funky! :)
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'april 1 - august 16 00:00-24:00')
        # Oups, I add a inner daterange ;)
        t2.resolve_daterange(t2.dateranges, 'saturday -1 - monday 1  16:00-24:00')
        t.exclude = [t2]
        # We are a bad boy: first time period want a tuesday
        # but exclude do not want it until 23:58. So next is 59 :)
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

        self.assertEqual('Tue Oct 26 16:30:00 2010', t_next)
        print "Finish this Funky test :)"

    def test_monweekday_timeperiod_with_exclude(self):
        self.print_header()
        now = time.time()
        # Get the 12 of july 2010 at 15:00, monday
        july_the_12 = time.mktime(time.strptime("12 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))

        # Then a funny daterange
        print "Testing daterange", 'tuesday -1 july - monday 1 august  16:30-24:00'
        t = Timeperiod()
        t.timeperiod_name = 'T1'
        t.resolve_daterange(t.dateranges, 'tuesday -1 july - monday 1 september  16:30-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_12)
        t_next = time.asctime(time.localtime(t_next))
        print "Next without exclude", t_next
        self.assertEqual("Tue Jul 27 16:30:00 2010", t_next)

        # Now we add this timeperiod an exception
        # and from april (before) to august monday 3 (monday 16 august),
        # so Jul 17 is no more possible. So just after it, Tue 17
        t2 = Timeperiod()
        t2.timeperiod_name = 'T2'
        t2.resolve_daterange(t2.dateranges, 'thursday 1 april - monday 3 august 00:00-24:00')
        print t2.dateranges[0].__dict__
        t.exclude = [t2]
        # We are a bad boy: first time period want a tuesday
        # but exclude do not want it until 23:58. So next is 59 :)
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

        self.assertEqual('Tue Aug 17 16:30:00 2010', t_next)

    def test_dayweek_exclusion_timeperiod(self):
        self.print_header()
        t = Timeperiod()
        now = time.time()
        # Get the 13 of july 2010 at 15:00, tuesday
        july_the_13 = time.mktime(time.strptime("13 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_13

        # Now we add this timeperiod an exception
        t2 = Timeperiod()
        t2.timeperiod_name = ''
        t2.resolve_daterange(t2.dateranges, 'tuesday 00:00-24:00')
        t.exclude = [t2]
	
        t.resolve_daterange(t.dateranges, 'monday 00:00-24:00')
        t.resolve_daterange(t.dateranges, 'tuesday 00:00-24:00')
        t.resolve_daterange(t.dateranges, 'wednesday 00:00-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_13)
        t_next = time.asctime(time.localtime(t_next))
        print "T next", t_next
        self.assertEqual("Wed Jul 14 00:00:00 2010", t_next)

    def test_dayweek_exclusion_timeperiod_with_day_range(self):
        self.print_header()
        t = Timeperiod()
        # Get the 13 of july 2010 at 15:00, tuesday
        july_the_13 = time.mktime(time.strptime("13 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_13

        # Now we add this timeperiod an exception
        t2 = Timeperiod()
        t2.timeperiod_name = ''
        t2.resolve_daterange(t2.dateranges, 'tuesday 00:00-24:00')
        t.exclude = [t2]

        t.resolve_daterange(t.dateranges, '2010-03-01 - 2020-03-01 00:00-24:00')
        t_next = t.get_next_valid_time_from_t(july_the_13)
        t_next = time.asctime(time.localtime(t_next))

        now = time.time()
        now = time.asctime(time.localtime(now))

        print "T next", t_next
    #    print "T now", now
    #    self.assertEqual(now, t_next)
        self.assertEqual("Wed Jul 14 00:00:01 2010", t_next)

    # short test to check the invalid function of timeranges
    def test_next_invalid_day(self):
        self.print_header()

        # Get the 13 of july 2010 at 15:00, tuesday
        july_the_13 = time.mktime(time.strptime("13 Jul 2010 15:00:00", "%d %b %Y %H:%M:%S"))
        print july_the_13

        t = Timeperiod()
        t.timeperiod_name = 'test_next_invalid_day'
        t.resolve_daterange(t.dateranges, 'tuesday 00:00-24:00')
        t.exclude = []

        t_next_invalid = t.get_next_invalid_time_from_t(july_the_13)
        t_next_invalid = time.asctime(time.localtime(t_next_invalid))
        print "T next invalid", t_next_invalid
        self.assertEqual("Wed Jul 14 00:00:01 2010", t_next_invalid)


    def test_issue_1385(self):
        '''
        https://github.com/naparuba/shinken/issues/1385
        '''
        tp = Timeperiod()
        tp.timeperiod_name = 'mercredi2-22-02'
        tp.resolve_daterange(tp.dateranges, 'wednesday 2              00:00-02:00,22:00-24:00')
        tp.resolve_daterange(tp.dateranges, 'thursday 2                00:00-02:00,22:00-24:00')

        valid_times = (
            (2014, 11, 12, 1, 0),  # second wednesday of november @ 01:00
            (2014, 11, 12, 23, 0), # same @23:00
            (2014, 11, 13, 0, 0), # second thursday @ 00:00
            # in december:
            (2014, 12, 10, 1, 0),
            (2014, 12, 10, 23, 0),
            (2014, 12, 11, 1, 0),
            (2014, 12, 11, 23, 0),

        )
        for valid in valid_times:
            dt = datetime.datetime(*valid)
            valid_tm = time.mktime(dt.timetuple())
            self.assertTrue(tp.is_time_valid(valid_tm))

        invalid_times = (
            (2014, 11, 3, 1, 0), # first wednesday ..
            (2014, 11, 4, 1, 0),  # first thursday
            (2014, 11, 17, 1, 0),   # third ..
            (2014, 11, 18, 1, 0),
            # in december:
            (2014, 12, 5, 3, 0),
            (2014, 12, 17, 1, 0),
            (2014, 12, 18, 1, 0),
            (2014, 12, 24, 1, 0),
            (2014, 12, 25, 1, 0),
            (2014, 12, 31, 1, 0),
        )
        for invalid in invalid_times:
            dt = datetime.datetime(*invalid)
            invalid_tm = time.mktime(dt.timetuple())
            self.assertFalse(tp.is_time_valid(invalid_tm))





if __name__ == '__main__':
    unittest.main()
