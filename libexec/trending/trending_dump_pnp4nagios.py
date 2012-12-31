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

from lxml.etree import parse
from pprint import pprint
import os
import sys
import optparse
import csv
import rrdtool
import gzip

# Some globals vars
output_dir = None
gzip_enabled = False


def parse_xml(xml_path):
    x = {}
    tree = parse(xml_path)

    x['hname'] = tree.find('NAGIOS_HOSTNAME').text
    x['sdesc'] = tree.find('NAGIOS_SERVICEDESC').text
    x['ds'] = []
    for ds in tree.findall('DATASOURCE'):
        v = {}
        v['id'] = ds.find('DS').text
        v['metric'] = ds.find('NAME').text
        v['rrdfile'] = ds.find('RRDFILE').text
        #print v
        x['ds'].append(v)
    return x


def get_day_value(rrdfile, day, ds_id):
    res = []
    c_start = '-s -%s' % (day+1)
    c_start += 'd'
    c_end = '-e -%s' % day
    c_end += 'd'
    #print c_start, c_end
    v = rrdtool.fetch(rrdfile, 'AVERAGE', '-r 300', c_start, c_end)
    #print v
    period = v[0]
    dss = list(v[1])
    values = v[2]
    #print "VALUES", day, len(values)
    start = period[0]
    step = period[2]
    idx = dss.index(ds_id)
    #print "INDEX", idx
    pos = start
    for c in values:
        timestamp = pos
        #print timestamp, c[idx]
        res.append( (timestamp,  c[idx]) )
        pos += step
    return res


def save_metric_file(hname, sdesc, metric, datas):
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


if __name__ == '__main__':
    parser = optparse.OptionParser(
        "%prog [options]", version="%prog " + '0.1')
    parser.add_option('-x', '--xml',
                      dest="xml_path",
                      help='Path of the PNP4Nagios xml file to import')
    parser.add_option('-l', '--list',
                      dest="list_only", action='store_true',
                      help="Only list the elment metrics")
    parser.add_option('-o', '--output_dir',
                      dest="output_dir",
                      help="Directory where to save the data")
    parser.add_option('-z', '--enable-gip',
                      dest="gzip_enabled", action='store_true',
                      help="Enable the gzip compression of csv files (output as csv.gz)")
    opts, args = parser.parse_args()

    xml_path = opts.xml_path
    output_dir = opts.output_dir or '.'
    gzip_enabled = opts.gzip_enabled

    if not xml_path:
        print "ERROR : no xml file set (-x). Exiting"
        sys.exit(2)

    x = parse_xml(xml_path)
    #print x

    for ds in x['ds']:
        values = []
        rrdfile = ds['rrdfile']
        dsid = ds['id']
        inverse_days = range(1, 180)
        inverse_days.reverse()
        for day in inverse_days:
            res = get_day_value(rrdfile, day, dsid)
            values.extend(res)
        #print "VALUES", values

        #for c in values:
        #    print c

        save_metric_file(x['hname'], x['sdesc'], ds['metric'], values)
