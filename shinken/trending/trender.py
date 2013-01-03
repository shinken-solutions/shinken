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

"""This Class is an helper for al trending things, for computing
smoothing average
"""
import math

from shinken.load import Load


# By deault no debug messages
do_debug = False

def debug(*args):
    if do_debug:
        print ' '.join([str(s) for s in args])


class Trender:
    def __init__(self, chunk_interval):
        self.chunk_interval = chunk_interval
        self.nb_chunks = int(math.ceil(86400.0/self.chunk_interval))


        # Ok a quick and dirty load computation
    def quick_update(self, prev_val, new_val, m, interval):
        l = Load(m=m, initial_value=prev_val)
        l.update_load(new_val, interval)
        return l.get_load()


    def get_previous_chunk(self, wday, chunk_nb):
        if chunk_nb == 0:
            chunk_nb = self.nb_chunks - 1
            wday -= 1
        else:
            chunk_nb -= 1
        wday = wday % 7
        return (wday, chunk_nb)


    def get_key(self, hname, sdesc, metric, wday, chunk_nb):
        return hname+'.'+sdesc+'.'+metric+'.'+'week'+'.'+str(wday)+'.'+'Vtrend'+'.'+str(chunk_nb)



    # Get the current doc and the previous one in just one query
    def get_doc_and_prev_doc(self, coll, key, prev_key):
        doc = None
        prev_doc = None

        cur = coll.find({'_id' : {'$in': [key, prev_key]}})
        for d in cur:
            if d['_id'] == key:
                doc = d
            if d['_id'] == prev_key:
                prev_doc = d

        return doc, prev_doc


    



    # Get the average entries, create them if need, and save the new computed value.
    def update_avg(self, coll, vtime, wday, chunk_nb, l1, hname, sdesc, metric, CHUNK_INTERVAL):

        # Ok first try to see our current chunk, and get our doc entry, and the previous one to compute
        # the averages
        key = self.get_key(hname, sdesc, metric, wday, chunk_nb)
        _prev_wday, _prev_chunk_nb = self.get_previous_chunk(wday, chunk_nb)
        prev_key = self.get_key(hname, sdesc, metric, _prev_wday, _prev_chunk_nb)
        doc, prev_doc = self.get_doc_and_prev_doc(coll, key, prev_key)
    
        # Maybe we are in a new chunk, if so, just create a new block and bail out
        if not doc or not 'Vevolution' in doc:
            doc = {'hname':hname, 'sdesc':sdesc, 'metric':metric, 'cycle':'week',
                   'wday':wday, 'chunk_nb':chunk_nb, 'Vtrend':l1, '_id':key,
                   'VtrendSmooth':l1, 'VcurrentSmooth':l1, 'Vcurrent':l1,
                   'Vevolution' : 0, 'VevolutionSmooth' : 0, 'last_update' : vtime,
                   'valid_evolution' : False
                   }
            coll.save(doc)
            return

        # Ok old one
        
        # If evolution is already valid, keep it
        valid_evolution = doc['valid_evolution']
        
        # Maybe we are just too early since the last update, if so, do not
        # update the "evolution" part because by definition there won't be
        # evolution since the last week value, but the current one, last minutes
        # one....
        last_update = doc['last_update']
        update_evol = True
        if vtime - last_update < CHUNK_INTERVAL:
            update_evol = False

        #### Smoothing over the weeks part
        
        # Ok save some values
        prev_raw_val = doc['Vcurrent']
        prev_val = doc['Vtrend']
        prev_evolution = doc['Vevolution']

        # Compute the trending and the evolution curve since the last week so.
        new_Vtrend = self.quick_update(prev_val, l1, 5, 5)

        # Now the evolution one, but only one a chunk time
        if update_evol:
            # ok we will update it, so now it will be valid
            valid_evolution = True

            # The new evolution diff value is
            diff = l1 - prev_raw_val
            # maybe the doc we got is the first one, if so, do not use the Vevolution value
            # but initialise it now instead
            if not doc['valid_evolution']:
                new_Vevolution = diff
            else:
                new_Vevolution = self.quick_update(prev_evolution, diff, 5, 5)
        else:            # ok, touch nothing
            new_Vevolution = prev_evolution

        ###  Smoothing over the chunks part
        
        # Now we smooth with the last value
        # And by default, we are using the current value
        new_VtrendSmooth = doc['VtrendSmooth']
        new_VevolutionSmooth = doc['VevolutionSmooth']

        # We are looking for the previous chunk value, but by default we will use the
        # current chunk one
        prev_val = doc['VtrendSmooth']
        prev_val_short = doc['VcurrentSmooth']
        prev_evolution_smooth = doc['VevolutionSmooth']

        if prev_doc:
            prev_val = prev_doc['VtrendSmooth']
            prev_val_short = prev_doc['VcurrentSmooth']
            prev_evolution_smooth = doc['VevolutionSmooth']
        else:
            debug("OUPS, the key", key, "do not have a previous entry", wday, chunk_nb)

        
        # Ok really update the value now
        new_VtrendSmooth = self.quick_update(prev_val, new_Vtrend, 1, 5)

        # We will also smooth the evolution parameter with the last chunk value, but only if we should
        if update_evol:
            # Maybe we do not have a stable situation from our chunk or the previous, so
            # put current value instead
            if not doc['valid_evolution'] or not prev_doc or not prev_doc['valid_evolution']:
                new_VevolutionSmooth = new_Vevolution
            else: # ok both chunks are stable, so really compute the average
                new_VevolutionSmooth = self.quick_update(prev_evolution_smooth, new_Vevolution, 1, 15)


        # Ok and now last minutes trending smoothing over the chunks
        new_VcurrentSmooth = self.quick_update(prev_val_short, l1, 1, 15)

        # All is ok? Let's update the DB value
        coll.update({'_id' : key}, {'$set' : { 'Vtrend': new_Vtrend, 'VtrendSmooth': new_VtrendSmooth, 'VcurrentSmooth' : new_VcurrentSmooth, 'Vcurrent':l1,
                                               'Vevolution' : new_Vevolution, 'VevolutionSmooth' : new_VevolutionSmooth, 'last_update' : vtime,
                                               'valid_evolution': valid_evolution}})



