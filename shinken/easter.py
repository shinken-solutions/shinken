#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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


from shinken.log import logger

def episode_iv():
    hst = 'towel.blinkenlights.nl'

    from telnetlib import Telnet

    t = Telnet(hst)
    while True:
        buf = t.read_until('mesfesses', 0.1)
        logger.info(buf)


def perdu():
    import urllib
    f = urllib.urlopen("http://www.perdu.com")
    logger.info(f.read())


def myip():
    import urllib
    f = urllib.urlopen("http://whatismyip.org/")
    logger.info(f.read())


def naheulbeuk():
    import os
    import urllib2
    from cStringIO import StringIO

    from PIL import Image
    import aalib

    if os.getenv('TERM') == 'linux':
        screen = aalib.LinuxScreen
    else:
        screen = aalib.AnsiScreen
    screen = screen(width=128, height=128)
    fp = StringIO(urllib2.urlopen(
        'http://www.penofchaos.com/warham/bd/images/NBK-win7portrait-Nain02.JPG').read())
    image = Image.open(fp).convert('L').resize(screen.virtual_size)
    screen.put_image((0, 0), image)
    logger.info(screen.render())



def what_it_make_me_think(subject):
    import hashlib
    if hashlib.md5(subject.lower()).hexdigest() == '6376e9755f8047391621b577ae03966a':
        print "Thanks to %s now I feel like this:  https://youtu.be/efTZslkr5Fs?t=60" % subject


def dark():
    r"""
                       .-.
                      |_:_|
                     /(_Y_)\
                    ( \/M\/ )
 '.               _.'-/'-'\-'._
   ':           _/.--'[[[[]'--.\_
     ':        /_'  : |::"| :  '.\
       ':     //   ./ |oUU| \.'  :\
         ':  _:'..' \_|___|_/ :   :|
           ':.  .'  |_[___]_|  :.':\
            [::\ |  :  | |  :   ; : \
             '-'   \/'.| |.' \  .;.' |
             |\_    \  '-'   :       |
             |  \    \ .:    :   |   |
             |   \    | '.   :    \  |
             /       \   :. .;       |
            /     |   |  :__/     :  \\
           |  |   |    \:   | \   |   ||
          /    \  : :  |:   /  |__|   /|
      snd |     : : :_/_|  /'._\  '--|_\
          /___.-/_|-'   \  \
                         '-'

"""
    logger.info(dark.__doc__)


def get_coffee():
    r"""

                        (
                          )     (
                           ___...(-------)-....___
                       .-""       )    (          ""-.
                 .-'``'|-._             )         _.-|
                /  .--.|   `""---...........---""`   |
               /  /    |                             |
               |  |    |                             |
                \  \   |                             |
                 `\ `\ |                             |
                   `\ `|                             |
                   _/ /\                             /
                  (__/  \                           /
               _..---""` \                         /`""---.._
            .-'           \                       /          '-.
           :               `-.__             __.-'              :
           :                  ) ""---...---"" (                 :
            '._               `"--...___...--"`              _.'
          jgs \""--..__                              __..--""/
               '._     "'"----.....______.....----"'"     _.'
                  `""--..,,_____            _____,,..--""`
                                `"'"----"'"`


"""
    logger.info(get_coffee.__doc__)
