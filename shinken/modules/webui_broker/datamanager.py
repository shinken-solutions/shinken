

class DataManager(object):
    def __init__(self):
        self.rg = None

    def load(self, rg):
        self.rg = rg

    def get_host(self, hname):
        return self.rg.hosts.find_by_name(hname)

    def get_service(self, hname, sdesc):
        return self.rg.services.find_srv_by_name_and_hostname(hname, sdesc)
    

    def get_hosts(self):
        return self.rg.hosts

    def get_services(self):
        return self.rg.services


    def get_important_impacts(self):
        res = []
        for s in self.rg.services:
            if s.is_impact and s.state not in ['OK', 'PENDING']:
                if s.business_impact > 2:
                    res.append(s)
        for h in self.rg.hosts:
            if h.is_impact and h.state not in ['UP', 'PENDING']:
                if h.business_impact > 2:
                    res.append(h)
        return res
                

datamgr = DataManager()
