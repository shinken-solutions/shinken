#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


#This class is an application for launch checks
#The poller listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will take checks.
#When already launch and have a conf, poller still listen to arbiter (one a timeout)
#if arbiter whant it to have a new conf, poller forgot old cheduler (and checks into)
#take new ones and do the (new) job.

from actionner import Actionner


#Our main APP class
class Poller (Actionner):
	do_checks = True
	do_actions = False


#lets go to the party
if __name__ == '__main__':
	poller = Poller()
	poller.main()
