from itemgroup import Itemgroup, Itemgroups

class Hostgroup(Itemgroup):
    id = 0

    macros = {
        'HOSTGROUPALIAS' : 'alias',
        'HOSTGROUPMEMBERS' : 'members',
        'HOSTGROUPNOTES' : 'notes',
        'HOSTGROUPNOTESURL' : 'notes_url',
        'HOSTGROUPACTIONURL' : 'action_url'
        }

    def get_hosts(self):
        print "Searching hosts", self.members
        return self.members


    def get_hostgroup_members(self):
        if self.has('hostgroup_members'):
            return self.hostgroup_members.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    def get_hosts_by_explosion(self, hostgroups):
        hg_mbrs = self.get_hostgroup_members()
        for hg_mbr in hg_mbrs:
            hg = hostgroups.find_by_name(hg_mbr)
            if hg is not None:
                value = hg.get_hosts_by_explosion(hostgroups)
                if value is not None:
                    self.add_string_member(value)
            else:
                pass
        if self.has('members'):
            return self.members
        else:
            return ''


class Hostgroups(Itemgroups):
    name_property = "hostgroup_name" # is used for finding hostgroups
    

    def get_members_by_name(self, hgname):
        id = self.find_id_by_name(hgname)
        if id == None:
            return []
        return self.itemgroups[id].get_hosts()


    def linkify(self, hosts=None):
        self.linkify_hg_by_hst(hosts)

    
    #We just search for each hostgroup the id of the hosts 
    #and replace the name by the id
    def linkify_hg_by_hst(self, hosts):
        for hg in self.itemgroups.values():
            mbrs = hg.get_hosts()
            #The new member list, in id
            new_mbrs = []
            for mbr in mbrs:
                new_mbrs.append(hosts.find_by_name(mbr))
            #We find the id, we remplace the names
            hg.replace_members(new_mbrs)


    #Add a host string to a hostgroup member
    #if the host group do not exist, create it
    def add_member(self, hname, hgname):
        id = self.find_id_by_name(hgname)
        #if the id do not exist, create the hg
        if id == None:
            hg = Hostgroup({'hostgroup_name' : hgname, 'alias' : hgname, 'members' :  hname})
            self.add(hg)
        else:
            self.itemgroups[id].add_string_member(hname)


    #Use to fill members with hostgroup_members
    def explode(self):
        for hg in self.itemgroups.values():
            if hg.has('hostgroup_members'):
                hg.get_hosts_by_explosion(self)

