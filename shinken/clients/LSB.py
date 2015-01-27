#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Nicolas Dupeux, nicolas.dupeux@arkea.com
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

import sys
import time
import asyncore
import getopt
sys.path.append("..")
sys.path.append("../..")
from livestatus import LSAsynConnection, Query

""" Benchmark of the livestatus broker"""


class QueryGenerator(object):
    """Generate a livestatus query"""

    def get(self):
        pass


class SimpleQueryGenerator(QueryGenerator):
    def __init__(self, querys, name="sqg"):
        self.querys = querys
        self.name = name
        self.i = 0

    def get(self):
        query = self.querys[self.i]
        query_class = "%s-%s" % (self.name, self.i)
        self.i += 1
        if self.i >= len(self.querys):
            self.i = 0
        return (query_class, query)


class FileQueryGenerator(SimpleQueryGenerator):
    def __init__(self, filename):
        f = open(filename, "r")
        querys = []
        for query in f:
            query = query.replace("\\n", "\n")
            querys.append(query)
        SimpleQueryGenerator.__init__(self, querys, filename)


def usage():
    print " -n requests     Number of requests to perform [Default: 10]"
    print " -c concurrency  Number of multiple requests to make [Default: 1]"


def mean(numberList):
    if len(numberList) == 0:
        return float('nan')

    floatNums = [float(x) for x in numberList]
    return sum(floatNums) / len(numberList)


def median(numberList):
    sorted_values = sorted(numberList)

    if len(sorted_values) % 2 == 1:
        return sorted_values[(len(sorted_values) + 1) / 2 - 1]
    else:
        lower = sorted_values[len(sorted_values) / 2 - 1]
        upper = sorted_values[len(sorted_values) / 2]

    return (float(lower + upper)) / 2


def run(url, requests, concurrency, qg):
    if (concurrency > requests):
        concurrency = requests

    remaining = requests

    conns = []
    queries_durations = {}
    if url.startswith('tcp:'):
        url = url[4:]
        addr = url.split(':')[0]
        port = int(url.split(':')[1])
    else:
        return

    for x in xrange(0, concurrency):
        conns.append(LSAsynConnection(addr=addr, port=port))
        (query_class, query_str) = qg.get()
        q = Query(query_str)
        q.query_class = query_class
        conns[x].stack_query(q)

    print "Start queries"
    t = time.time()
    while remaining > 0:
        asyncore.poll(timeout=1)
        for c in conns:
            if c.is_finished():
                # Store query duration to compute stats
                q = c.results.pop()
                duration = q.duration
                if q.query_class not in queries_durations:
                    queries_durations[q.query_class] = []
                queries_durations[q.query_class].append(q.duration)
                sys.stdout.flush()
                remaining -= 1

                # Print a dot every 10 completed queries
                if (remaining % 10 == 0):
                    print '.',
                    sys.stdout.flush()

                # Run another query
                (query_class, query_str) = qg.get()
                q = Query(query_str)
                q.query_class = query_class
                c.stack_query(q)
    running_time = time.time() - t
    print "End queries"

    print "\n==============="
    print "Execution report"
    print "==============="
    print "Running time is %04f s" % running_time
    print "Query Class          nb  min      max       mean     median"
    for query_class, durations in queries_durations.items():
        print "%s %03d %03f %03f %03f %03f" % (query_class.ljust(20), len(durations),
                                               min(durations), max(durations), mean(durations),
                                               median(durations))


def main(argv):
    # Defaults values
    concurrency = 5
    requests = 20
    url = "tcp:localhost:50000"

    try:
        opts, args = getopt.getopt(argv, "hc:n:", "help")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == "-c":
            concurrency = int(arg)
        elif opt == "-n":
            requests = int(arg)

    if len(args) >= 1:
        url = args[0]

    print "Running %s queries on %s" % (requests, url)
    print "Concurrency level %s " % (concurrency)

    qg = FileQueryGenerator("thruk_tac.queries")

    run(url, requests, concurrency, qg)

if __name__ == "__main__":
    main(sys.argv[1:])
