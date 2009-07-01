from itemgroup import Itemgroup, Itemgroups

class Contactgroup(Itemgroup):
    id = 0

    macros = {
        'CONTACTGROUPALIAS' : 'alias',
        'CONTACTGROUPMEMBERS' : 'get_members'
        }
    
    def get_contacts(self):
        return self.members#.split(',')

    
    def get_contactgroup_members(self):
        if self.has('contactgroup_members'):
            return self.contactgroup_members.split(',')
        else:
            return []

    #We fillfull properties with template ones if need
    def get_contacts_by_explosion(self, contactgroups):
        cg_mbrs = self.get_contactgroup_members()
        for cg_mbr in cg_mbrs:
            cg = contactgroups.find_by_name(cg_mbr)
            if cg is not None:
                value = cg.get_contacts_by_explosion(contactgroups)
                if value is not None:
                    self.add_string_member(value)
        if self.has('members'):
            return self.members
        else:
            return ''


class Contactgroups(Itemgroups):
    name_property = "contactgroup_name" # is used for finding contactgroup


    def get_members_by_name(self, cgname):
        id = self.find_id_by_name(cgname)
        if id == None:
            return []
        return self.itemgroups[id].get_contacts()


    def add_contactgroup(self, cg):
        self.itemgroups[cg.id] = cg


    def linkify(self, contacts):
        self.linkify_cg_by_cont(contacts)


    #We just search for each host the id of the host
    #and replace the name by the id
    def linkify_cg_by_cont(self, contacts):
        for id in self.itemgroups:
            mbrs = self.itemgroups[id].get_contacts()

            #The new member list, in id
            new_mbrs = []
            for mbr in mbrs:
                new_mbrs.append(contacts.find_by_name(mbr))

            #We find the id, we remplace the names
            self.itemgroups[id].replace_members(new_mbrs)


    #Add a contact string to a contact member
    #if the contact group do not exist, create it
    def add_member(self, cname, cgname):
        id = self.find_id_by_name(cgname)
        #if the id do not exist, create the cg
        if id == None:
            cg = Contactgroup({'contactgroup_name' : cgname, 'alias' : cgname, 'members' :  cname})
            self.add_contactgroup(cg)
        else:
            self.itemgroups[id].add_string_member(cname)


    #Use to fill members with contactgroup_members
    def explode(self):
        for id in self.itemgroups:
            cg = self.itemgroups[id]
            if cg.has('contactgroup_members'):
                cg.get_contacts_by_explosion(self)
