#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

import csv
import sys
import optparse
import MySQLdb
import os
import gzip

con = None
output_dir = None
gzip_enabled = False

def connect(mysql_server, mysql_user, mysql_password, mysql_db):
    global con
    try:
        con = MySQLdb.connect(mysql_server, mysql_user, mysql_password, mysql_db)
        cur = con.cursor()
        cur.execute("SELECT VERSION()")        
        data = cur.fetchone()
        print "Database version : %s " % data

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)


def get_hosts():
    res = []
    cur = con.cursor()
    cur.execute("select distinct(host_name) from index_data order by host_name;")
    rows = cur.fetchall()
    for row in rows:
        #print row[0]
        res.append(row[0])


def list_hosts():
    hosts = get_hosts()
    for h in hosts:
        print h
        

def get_host(hname):
    services = []
    cur = con.cursor()
    cur.execute("select service_description from index_data where host_name='%s';" % hname)
    rows = cur.fetchall()
    for row in rows:
        #print row[0]
        services.append(row[0])
    return services

        
def list_host(hname):
    services = get_host(hname)
    for s in services:
        print s


def get_metrics(hname, sdesc):
    metrics = []
    cur = con.cursor()
    cur.execute("select id from index_data where host_name='%s' and service_description='%s';" % (hname, sdesc))
    s_id = cur.fetchone()[0]
    print "SERVICE ID", s_id
    cur.execute("select metric_name from metrics where index_id=%s;" % s_id)
    rows = cur.fetchall()
    for row in rows:
        metrics.append(row[0])
    
    return metrics


def list_service(hname, sdesc):
    metrics = get_metrics(hname, sdesc)
    for m in metrics:
        print m


def save_metric_file(hname, sdesc, metric, datas):
    global output_dir
    global gzip_enabled
    
    p = '%s.%s.%s.csv' % (hname, sdesc, metric)
    pth = os.path.join(output_dir, p)

    if gzip_enabled:
        #print "GZIP compression enable"
        pth = pth+'.gz'
        print "AS FILE", pth
        f = gzip.open(pth, "wb")
    else:
        print "AS FILE", pth
        f = open(pth, "wb")
    
    c = csv.writer(f, delimiter=';')
    c.writerow(["#%s"%hname,"%s"%sdesc,"%s"%metric])
    
    for row in datas:
        #print row
        c.writerow(row)
    
    
def dump_metric(hname, sdesc, metric):
    cur = con.cursor()
    cur.execute("select id from index_data where host_name='%s' and service_description='%s';" % (hname, sdesc))
    s_id = cur.fetchone()[0]
    #print "SERVICE ID", s_id
    cur.execute("select metric_id from metrics where index_id='%s' and metric_name='%s';" % (s_id, metric))
    try:
        m_id = cur.fetchone()[0]
    except TypeError:
        print " NO ENTRY FOR", "select metric_id from metrics where index_id='%s' and metric_name='%s';" % (s_id, metric)
    #print "Metric id", m_id

    cur.execute("select count(*) from data_bin where id_metric=%s;" % m_id)
    count = cur.fetchone()[0]
    print 'DUMPING %s %s %s (' % (hname, sdesc, metric), count, "entries)"

    
    cur.execute("select ctime, value from data_bin where id_metric=%s order by ctime;" % m_id)
    rows = cur.fetchall()

    save_metric_file(hname, sdesc, metric, rows)

    
def dump_service(hname, sdesc):
    metrics = get_metrics(hname, sdesc)
    for m in metrics:
        dump_metric(hname, sdesc, m)


def dump_host(hname):
    services = get_host(hname)
    for sdesc in services:
        dump_service(hname, sdesc)

        

if __name__ == '__main__':
        parser = optparse.OptionParser(
            "%prog [options]", version="%prog " + '0.1')
        parser.add_option('-M', '--mysql_server',
                          dest="mysql_server",
                          help='Host name of the mysql server')
        parser.add_option('-u', '--user',
                          dest="mysql_user",
                          help='Mysql user name')
        parser.add_option('-p', '--password',
                          dest="mysql_password",
                          help='Mysql user password')
        parser.add_option('-d', '--database',
                          dest="mysql_db",
                          help='Centstorage DB')
        parser.add_option('-H', '--host_name',
                          dest="host_name",
                          help="Hostname to dump")
        parser.add_option('-s', '--service_description',
                          dest="service_description",
                          help="Service description to dump")
        parser.add_option('-m', '--metric',
                          dest="metric",
                          help="Metric to dump")
        parser.add_option('-l', '--list',
                          dest="list_only", action='store_true',
                          help="Only list the elment metrics")
        parser.add_option('-f', '--full',
                          dest="full_dump", action='store_true',
                          help="Do a full dump of the database. Prepare disk space!")
        parser.add_option('-o', '--output_dir',
                          dest="output_dir",
                          help="Directory where to save the data")
        parser.add_option('-z', '--enable-gip',
                          dest="gzip_enabled", action='store_true',
                          help="Enable the gzip compression of csv files (output as csv.gz)")
        opts, args = parser.parse_args()

        mysql_server = opts.mysql_server or 'localhost'
        mysql_user = opts.mysql_server or 'root'
        mysql_password = opts.mysql_password or ''
        mysql_db = opts.mysql_db or 'centstorage'
        hname = opts.host_name
        sdesc =  opts.service_description
        metric = opts.metric
        list_only = opts.list_only
        full_dump = opts.full_dump
        output_dir = opts.output_dir or '.'
        gzip_enabled = opts.gzip_enabled
        connect(mysql_server, mysql_user, mysql_password, mysql_db)

        if list_only:
            if not hname:
                list_hosts()
                sys.exit(0)
            if hname and not sdesc:
                list_host(hname)
                sys.exit(0)
            if hname and sdesc and not metric:
                list_service(hname, sdesc)
                sys.exit(0)
            sys.exit(0)

        if hname and not sdesc:
            dump_host(hname)
            sys.exit(0)

        if hname and sdesc and not metric:
            dump_service(hname, sdesc)
            sys.exit(0)
            
        if hname and sdesc and metric:
            dump_metric(hname, sdesc, metric)
            sys.exit(0)

        if not hname and not sdesc and not metric:
            print "YOU ARE A MORON that want it's server to go down!"
