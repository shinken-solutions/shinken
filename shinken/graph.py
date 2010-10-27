#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#Graph is a class to make graph things like DFS checks or accessibility
#Why use an atomic bomb when a little hammer is enought?


class Graph:
    def __init__(self):
        self.nodes = {}


    #Do not call twice...
    def add_node(self, node):
        self.nodes[node] = []


    #Just loop over nodes
    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    #Add an edge to the graph from->to
    def add_edge(self, from_node, to_node):
        #Maybe to_node is unknown
        if to_node not in self.nodes:
            self.add_node(to_node)

        try:
            self.nodes[from_node].append(to_node)
        #If from_node do not exist, add it with it's son
        except KeyError:
            self.nodes[from_node] = [to_node]


    #Return all nodes that are in a loop. So if return [], no loop
    def loop_check(self):
        in_loop = []
        #Add the tag for dfs check
        for node in self.nodes:
            node.dfs_loop_status = 'DFS_UNCHECKED'

        #Now do the job
        for node in self.nodes:
            #Run the dfs only if the node is not already done */
            if node.dfs_loop_status == 'DFS_UNCHECKED':
                self.dfs_loop_search(node)
            #If LOOP_INSIDE, must be returned
            if node.dfs_loop_status == 'DFS_LOOP_INSIDE':
                in_loop.append(node)

        #Remove the tag
        for node in self.nodes:
            del node.dfs_loop_status

        return in_loop


    #DFS_UNCHECKED default value
    #DFS_TEMPORARY_CHECKED check just one time
    #DFS_OK no problem for node and it's childs
    #DFS_NEAR_LOOP has trouble sons
    #DFS_LOOP_INSIDE is a part of a loop!
    def dfs_loop_search(self, root):
        #Make the root temporary checkded
        root.dfs_loop_status = 'DFS_TEMPORARY_CHECKED'

        #We are scanning the sons
        for child in self.nodes[root]:
            child_status = child.dfs_loop_status
            #If a child is not checked, check it
            if child_status == 'DFS_UNCHECKED':
                self.dfs_loop_search(child)
                child_status = child.dfs_loop_status

            #If a child already temporary checked, its a problem,
            #loop inside, and its a acked status
            if child_status == 'DFS_TEMPORARY_CHECKED':
                child.dfs_loop_status = 'DFS_LOOP_INSIDE'
                root.dfs_loop_status = 'DFS_LOOP_INSIDE'

            #If a child already temporary checked, its a problem, loop inside
            if child_status == 'DFS_NEAR_LOOP' or child_status == 'DFS_LOOP_INSIDE':
                #if a node is know to be part of a loop, do not let it be less
                if root.dfs_loop_status != 'DFS_LOOP_INSIDE':
                    root.dfs_loop_status = 'DFS_NEAR_LOOP'
                #We already saw this child, it's a problem
                child.dfs_loop_status = 'DFS_LOOP_INSIDE'

        #If root have been modified, do not set it OK
        #A node is OK if and only if all of his childs are OK
        #if it does not have child, goes ok
        if root.dfs_loop_status == 'DFS_TEMPORARY_CHECKED':
            root.dfs_loop_status = 'DFS_OK'


    #Get accessibility packs of the graph : in one pack,
    #element are related in a way. Between packs, there is no relation
    #at all.
    #TODO : Get it work for directionnal graph too
    #Because for now, edge must be father->son AND son->father
    def get_accessibility_packs(self):
        packs = []
        #Add the tag for dfs check
        for node in self.nodes:
            node.dfs_loop_status = 'DFS_UNCHECKED'

        for node in self.nodes:
            #Run the dfs only if the node is not already done */
            if node.dfs_loop_status == 'DFS_UNCHECKED':
                packs.append(self.dfs_get_all_childs(node))

        #Remove the tag
        for node in self.nodes:
            del node.dfs_loop_status

        return packs


    #Return all mychilds, and all childs of my childs
    def dfs_get_all_childs(self, root):
        root.dfs_loop_status = 'DFS_CHECKED'

        ret = set()
        #Me
        ret.add(root)
        #And my sons
        ret.update(self.nodes[root])

        for child in self.nodes[root]:
            #I just don't care about already check childs
            if child.dfs_loop_status == 'DFS_UNCHECKED':
                ret.update(self.dfs_get_all_childs(child))

        return list(ret)
