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
# This file is used to test reading and processing of config files
#

import os
import sys
import time

from shinken_test import ShinkenTest, unittest, time_hacker
from shinken.action import Action


class TestAction(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_1r_1h_1s.cfg')
        time_hacker.set_real_time()

    def wait_finished(self, a, size=8012):
        start = time.time()
        while True:
            # Do the job
            if a.status == 'launched':
                #print a.process.poll()
                a.check_finished(size)
                time.sleep(0.01)
            #print a.status
            if a.status != 'launched':
                #print "Finish", a.status
                return
            # 20s timeout
            if time.time() - start > 20:
                print "COMMAND TIMEOUT AT 20s"
                return


    def test_action(self):
        a = Action()
        a.timeout = 10
        a.env = {}

        if os.name == 'nt':
            a.command = r'libexec\\dummy_command.cmd'
        else:
            a.command = "libexec/dummy_command.sh"
        self.assertEqual(False, a.got_shell_characters())
        a.execute()
        self.assertEqual('launched', a.status)
        # Give also the max output we want for the command
        self.wait_finished(a)
        self.assertEqual(0, a.exit_status)
        self.assertEqual('done', a.status)
        print a.output
        self.assertEqual("Hi, I'm for testing only. Please do not use me directly, really", a.output)
        self.assertEqual("Hip=99% Bob=34mm", a.perf_data)

    def test_echo_environment_variables(self):
        if os.name == 'nt':
            return

        a = Action()
        a.timeout = 10
        a.env = {}  # :fixme: this sould be pre-set in Action.__init__()

        a.command = "echo $TITI"

        self.assertNotIn('TITI', a.get_local_environnement())
        a.env = {'TITI': 'est en vacance'}
        self.assertIn('TITI', a.get_local_environnement())
        self.assertEqual(a.get_local_environnement()['TITI'],
                         'est en vacance' )
        a.execute()
        self.wait_finished(a)
        self.assertEqual(a.output, 'est en vacance')

    def test_grep_for_environment_variables(self):
        if os.name == 'nt':
            return

        a = Action()
        a.timeout = 10
        a.env = {}  # :fixme: this sould be pre-set in Action.__init__()

        a.command = "/usr/bin/env | grep TITI"

        self.assertNotIn('TITI', a.get_local_environnement())
        a.env = {'TITI': 'est en vacance'}
        self.assertIn('TITI', a.get_local_environnement())
        self.assertEqual(a.get_local_environnement()['TITI'],
                         'est en vacance' )
        a.execute()
        self.wait_finished(a)
        self.assertEqual(a.output, 'TITI=est en vacance')


    def test_environment_variables(self):

        class ActionWithoutPerfData(Action):
            def get_outputs(self, out, max_len):
                # do not cut the outputs into perf_data to avoid
                # problems with enviroments containing a dash like in
                # `LESSOPEN=|/usr/bin/lesspipe.sh %s`
                self.output = out

        if os.name == 'nt':
            return

        a = ActionWithoutPerfData()
        a.timeout = 10
        a.command = "/usr/bin/env"

        a.env = {}  # :fixme: this sould be pre-set in Action.__init__()
        self.assertNotIn('TITI', a.get_local_environnement())

        a.env = {'TITI': 'est en vacance'}

        self.assertEqual(False, a.got_shell_characters())

        self.assertIn('TITI', a.get_local_environnement())
        self.assertEqual(a.get_local_environnement()['TITI'],
                         'est en vacance' )
        a.execute()

        self.assertEqual('launched', a.status)
        # Give also the max output we want for the command
        self.wait_finished(a, size=20*1024)
        titi_found = False
        for l in a.output.splitlines():
            if l == 'TITI=est en vacance':
                titi_found = True
        self.assertTrue(titi_found)



    # Some commands are shell without bangs! (like in Centreon...)
    # We can show it in the launch, and it should be managed
    def test_noshell_bang_command(self):
        a = Action()
        a.timeout = 10
        a.command = "libexec/dummy_command_nobang.sh"
        a.env = {}
        if os.name == 'nt':
            return
        self.assertEqual(False, a.got_shell_characters())
        a.execute()

        self.assertEqual('launched', a.status)
        self.wait_finished(a)
        print "FUck", a.status, a.output
        self.assertEqual(0, a.exit_status)
        self.assertEqual('done', a.status)

    def test_got_shell_characters(self):
        a = Action()
        a.timeout = 10
        a.command = "libexec/dummy_command_nobang.sh && echo finished ok"
        a.env = {}
        if os.name == 'nt':
            return
        self.assertEqual(True, a.got_shell_characters())
        a.execute()

        self.assertEqual('launched', a.status)
        self.wait_finished(a)
        print "FUck", a.status, a.output
        self.assertEqual(0, a.exit_status)
        self.assertEqual('done', a.status)

    def test_got_pipe_shell_characters(self):
        a = Action()
        a.timeout = 10
        a.command = "libexec/dummy_command_nobang.sh | grep 'Please do not use me directly'"
        a.env = {}
        if os.name == 'nt':
            return
        self.assertEqual(True, a.got_shell_characters())
        a.execute()

        self.assertEqual('launched', a.status)
        self.wait_finished(a)
        print "FUck", a.status, a.output
        self.assertEqual(0, a.exit_status)
        self.assertEqual('done', a.status)

    def test_got_unclosed_quote(self):
        # https://github.com/naparuba/shinken/issues/155
        a = Action()
        a.timeout = 10
        a.command = "libexec/dummy_command_nobang.sh -a 'wwwwzzzzeeee"
        a.env = {}
        if os.name == 'nt':
            return
        a.execute()

        self.wait_finished(a)
        self.assertEqual('done', a.status)
        print "FUck", a.status, a.output
        if sys.version_info < (2, 7):
            # cygwin: /bin/sh: -c: line 0: unexpected EOF while looking for matching'
            # ubuntu: /bin/sh: Syntax error: Unterminated quoted string
            self.assertTrue(a.output.startswith("/bin/sh"))
            self.assertEqual(3, a.exit_status)
        else:
            self.assertEqual('Not a valid shell command: No closing quotation', a.output)
            self.assertEqual(3, a.exit_status)

    # We got problems on LARGE output, more than 64K in fact.
    # We try to solve it with the fcntl and non blocking read
    # instead of "communicate" mode. So here we try to get a 100K
    # output. Should NOT be in a timeout
    def test_huge_output(self):
        a = Action()
        a.timeout = 5
        a.env = {}

        if os.name == 'nt':
            a.command = r"""python -c 'print "A"*1000000'"""
            # FROM NOW IT4S FAIL ON WINDOWS :(
            return
        else:
            a.command = r"""python -u -c 'print "A"*100000'"""
        print "EXECUTE"
        a.execute()
        print "EXECUTE FINISE"
        self.assertEqual('launched', a.status)
        # Give also the max output we want for the command
        self.wait_finished(a, 10000000000)
        print "Status?", a.exit_status
        self.assertEqual(0, a.exit_status)
        print "Output", len(a.output)
        self.assertEqual(0, a.exit_status)
        self.assertEqual('done', a.status)
        self.assertEqual("A"*100000, a.output)
        self.assertEqual("", a.perf_data)

    def test_execve_fail_with_utf8(self):
        if os.name == 'nt':
            return

        a = Action()
        a.timeout = 10
        a.env = {}  # :fixme: this sould be pre-set in Action.__init__()

        a.command = u"/bin/echo Wiadomo\u015b\u0107"

        a.execute()
        self.wait_finished(a)
        #print a.output
        self.assertEqual(a.output.decode('utf8'), u"Wiadomo\u015b\u0107")

    def test_non_zero_exit_status_empty_output_but_non_empty_stderr(self):
        a = Action()
        a.command = "echo hooo >&2 ; exit 1"
        a.timeout = 10
        a.env = {}  # :fixme: this sould be pre-set in Action.__init__()
        a.execute()
        self.wait_finished(a)
        self.assertEqual(a.output, "hooo")


if __name__ == '__main__':
    unittest.main()
