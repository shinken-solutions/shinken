

class DataManager(object):
    def __init__(self):
        self.rg = None

    def load(self, rg):
        self.rg = rg

    def get_host(self, hname):
        return self.rg.hosts.find_by_name(hname)

    

datamgr = DataManager()
