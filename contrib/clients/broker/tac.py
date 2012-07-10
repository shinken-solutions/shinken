#!/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import urwid

sys.path.append('../../../thrift/gen-py')
from org.shinkenmonitoring.broker import Broker
from org.shinkenmonitoring.broker.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

REFRESH_INTERVAL = 5


def handle_keypress(input):
    if input in ('q', 'Q'):
        raise urwid.ExitMainLoop()


class TacModel:
    def __init__(self):
        transport = TSocket.TSocket('localhost', 40000)
        self.transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.shinken = Broker.Client(protocol)
        self.transport.open()

    def get_data_hosts(self):
        q = GetRequest()
        r = GetResponse()
        q.table = Table.hosts
        q.stats = [StatRequest("state", "=", "0"),
             StatRequest("state", "=", "1"),
             StatRequest("state", "=", "2"),
             StatRequest("state", "=", "3")]

        r = self.shinken.get(q)

        return r.result_table[0]

    def get_data_services(self):
        q = GetRequest()
        r = GetResponse()
        q.table = Table.services
        q.stats = [StatRequest("state", "=", "0"),
             StatRequest("state", "=", "1"),
             StatRequest("state", "=", "2"),
             StatRequest("state", "=", "3")]

        r = self.shinken.get(q)

        return r.result_table[0]

    def close(self):
        self.transport.close()


class TacView(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface
    """
    palette = [
        ('banner', 'black', 'light gray', 'standout,underline'),
        ('header', 'black', 'dark gray', 'standout'),
        ('button', 'black', 'light gray'),
        ('pg normal',   'white',       'dark gray', 'standout'),
        ('pg complete', 'white',       'light green'),
        ('pg smooth',   'light green', 'dark gray'),
        ('bg', 'white', 'black'),]

    def __init__(self, controller):
        self.controller = controller
        self.bHosts = {}
        self.bServices = {}
        urwid.WidgetWrap.__init__(self, self.main_window())

    def update(self):
        data = self.controller.get_data()

        hosts = data['hosts']
        self.bHosts['down'].set_label(('button', "%s Down" % hosts[2]))
        self.bHosts['unreachable'].set_label(('button', "%s Unreachable" % hosts[1]))
        self.bHosts['up'].set_label(('button', "%s Up" % hosts[0]))
        self.bHosts['pending'].set_label(('button', "%s Pending" % hosts[3]))
        self.health_hosts.set_completion(
            100 * int(hosts[0]) / (int(hosts[0]) + int(hosts[1]) + int(hosts[2]) + int(hosts[3])))

        services = data['services']
        self.bServices['critical'].set_label(('button', "%s Critical" % services[2]))
        self.bServices['warning'].set_label(('button', "%s Warning" % services[1]))
        self.bServices['unknown'].set_label(('button', "%s Unknown" % services[3]))
        self.bServices['ok'].set_label(('button', "%s Ok" % services[0]))
        self.health_services.set_completion(
            100 * int(services[0]) / (int(services[0]) + int(services[1]) + int(services[2]) + int(services[3])))

        self.last_update.set_text(('button', "Last Updated: %s" % time.strftime('%d/%m/%y %H:%M:%S', time.localtime())))

    def main_window(self):
        self.last_update = urwid.Text(('button', "Last Updated: %s" % "Never"))

        self.outages = urwid.Button(('button', "Outages"))
        network_outages = urwid.Pile([
            urwid.Text(('header', "Network Outages")),
            self.outages])

        self.health_hosts = urwid.ProgressBar('pg normal', 'pg complete', 100, satt='pg smooth')
        self.health_services = urwid.ProgressBar('pg normal', 'pg complete', 30, satt='progress')
        network_health = urwid.Pile([
            urwid.Text(('header', "Network Health")),
            self.health_hosts,
            self.health_services
        ])

        network = urwid.Columns([network_outages, network_health])

        self.bHosts['down'] = urwid.Button(('button', "Down"))
        self.bHosts['unreachable'] = urwid.Button(('button', "Unreachable"))
        self.bHosts['up'] = urwid.Button(('button', "Up"))
        self.bHosts['pending'] = urwid.Button(('button', "Pending"))
        self.hosts_state = urwid.Columns([
            self.bHosts['down'],
            self.bHosts['unreachable'],
            self.bHosts['up'],
            self.bHosts['pending']])

        self.bServices['critical'] = urwid.Button(('button', "Critical"))
        self.bServices['warning'] = urwid.Button(('button', "Warning"))
        self.bServices['unknown'] = urwid.Button(('button', "Unknown"))
        self.bServices['ok'] = urwid.Button(('button', "Ok"))
        self.bServices['pending'] = urwid.Button(('button', "Pending"))
        self.services_state = urwid.Columns([
            self.bServices['critical'],
            self.bServices['warning'],
            self.bServices['unknown'],
            self.bServices['ok'],
            self.bServices['pending']])

        pile = urwid.Pile([
            urwid.LineBox(urwid.Pile([
                self.last_update,
                urwid.Text(('button', "Updated every %s seconds" % REFRESH_INTERVAL))])),
            urwid.Divider(bottom=2),
            network,
            urwid.Divider(),
            urwid.Text(('header', "Hosts")),
            self.hosts_state,
            urwid.Divider(),
            urwid.Text(('header', "Services")),
            self.services_state])

        header = urwid.Text(('banner', "Tactical Monitoring Overview"), align='center')
        footer = urwid.Text("Q to quit")
        fill = urwid.Filler(pile, 'middle')
        view = urwid.Frame(fill, header=header, footer=footer)
        map1 = urwid.AttrMap(view, 'bg')

        return map1


class TacController:
    """
    A class responsible for setting up the model and view and running
    the application
    """

    def __init__(self):
        self.refresh_alarm = None
        self.model = TacModel()
        self.view = TacView(self)

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.view.palette, unhandled_input=handle_keypress)
        self.refresh()
        self.loop.run()

    def get_data(self):
        """Provide data to our view"""
        data = {}
        data['hosts'] = self.model.get_data_hosts()
        data['services'] = self.model.get_data_services()
        return data

    def refresh(self, loop=None, user_data=None):
        self.view.update()
        self.refresh_alarm = self.loop.set_alarm_in(REFRESH_INTERVAL, self.refresh)


def main():
    TacController().main()

if '__main__' == __name__:
    main()
