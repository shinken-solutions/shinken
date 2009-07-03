

class Itemgroup:
    id = 0
    def __init__(self, params={}):
        self.id = self.__class__.id
        self.__class__.id += 1
        for key in params:
            setattr(self, key, params[key])


    def clean(self):
        pass


    def pythonize(self):
        mbrs = self.members.split(',')        
        self.members = []
        for mbr in mbrs:
            self.members.append(mbr.strip())


    def replace_members(self, members):
        self.members = members


    def add_string_member(self, member):
        self.members += ','+member


    def __str__(self):
        return str(self.__dict__)+'\n'


    def __iter__(self):
        return self.members.__iter__()#values()


    #a host group is correct if all members actually exists
    def is_correct(self):
        if not None in self.members:
            return True
        else:
            return False


    def has(self, prop):
        return hasattr(self, prop)


class Itemgroups:
    def __init__(self, itemgroups):
        self.itemgroups = {}
        for ig in itemgroups:
            self.itemgroups[ig.id] = ig


    def find_id_by_name(self, name):
        for id in self.itemgroups:
            name_property = self.__class__.name_property
            if getattr(self.itemgroups[id], name_property) == name:
                return id
        return None


    def find_by_name(self, name):
        id = self.find_id_by_name(name)
        if id is not None:
            return self.itemgroups[id]
        else:
            return None


    def __str__(self):
        s = ''
        for id in self.itemgroups:
            s += str(self.itemgroups[id])+'\n'
        return s

    def __iter__(self):
        return self.itemgroups.itervalues()


    def add(self, ig):
        self.itemgroups[ig.id] = ig


    def pythonize(self):
        for id in self.itemgroups:
            ig = self.itemgroups[id]
            ig.pythonize()


    def is_correct(self):
        for id in self.itemgroups:
            self.itemgroups[id].is_correct()
