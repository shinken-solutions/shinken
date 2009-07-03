#!/usr/bin/env python

import os
import sys
import graph


# Graph creation
g = graph.digraph()
g.add_node(1)
g.add_node(2)
g.add_node(3)
g.add_node(4)
g.add_edge(1,2)
g.add_edge(2,3)
g.add_edge(3,1)
g.add_edge(4,1)
g.add_edge(2,4)
g.add_edge(2,1)


print dir(g)


print "Cycle:",g.find_cycle()

# Write to a dot file
dot = g.write(fmt='dot')
f = open('graph.dot', 'w')
f.write(dot)
f.close()

# Draw as a png (note: this requires the graphiz 'dot' program to be installed)
os.system('dot graph.dot -Tpng > europe.png')


# Then, draw the breadth first search spanning tree rooted in Switzerland
#st, order = g.breadth_first_search(root="Switzerland")
#gst = graph.digraph()

#gst.add_spanning_tree(st)

#dot = gst.write(fmt='dot')

#f = open('graph-st.dot', 'w')
#f.write(dot)
#f.close()

# Draw as a png
os.system('dot graph-st.dot -Tpng > europe-st.png')

