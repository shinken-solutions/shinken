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



import time, math
#EXP_1=1/math.exp(5/60.0)
#EXP_5=1/math.exp(5/(5*60.0))
#EXP_15=1/math.exp(5/(15*60.0))

#From advance load average's code (another of my projects :) )
#def calc_load_load(load, exp,n):
#        load = n + exp*(load - n)
#        return (load, exp)


#This class if for having a easy Load calculation
#without having to send value at regular interval
#(but it's more efficient if you do this :) ) and not
#having a list and all. Just an object, an update and a get
#You can define m : the average is for m minutes. The val is 
#the initial value. It's better if it's 0 but you can choice.


class Load:
    def __init__(self, m=1, val=0):
        self.exp = 0 #first exp
        self.m = m #Number of minute of the avg
        self.last_update = 0 #last update of the value
        self.val = val #first value


    def update_load(self, new_val):
        #The first call do not change the value, just tag
        #the begining of last_update
        if self.last_update == 0:
            self.last_update = time.time()
            return
        now = time.time()
        diff = now - self.last_update
        self.exp = 1/math.exp(diff/ (self.m*60.0))
        self.val = new_val + self.exp*(self.val - new_val)
        self.last_update = now

    
    def get_load(self):
        return self.val


if __name__ == '__main__':
    l = Load()
    t = time.time()
    for i in xrange(1, 300):
        l.update_load(1)
        print '[', int(time.time() - t), ']', l.get_load(), l.exp
        time.sleep(5)
