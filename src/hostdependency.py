#from itemgroup import Itemgroup, Itemgroups
from util import to_int, to_char, to_split, to_bool
from item import Item, Items

class Hostdependency(Item):
    id = 0
    
#F is dep of D
#host_name			Host B
#	service_description		Service D
#	dependent_host_name		Host C
#	dependent_service_description	Service F
#	execution_failure_criteria	o
#	notification_failure_criteria	w,u
#       inherits_parent		1
#       dependency_period       24x7

    properties={'dependent_host_name' : {'required':True},
                'dependent_hostgroup_name' : {'required':False, 'default' : ''},
                'host_name' : {'required':True},
                'hostgroup_name' : {'required':False, 'default' : ''},
                'inherits_parent' : {'required':False, 'default' : '0', 'pythonize' : to_bool},
                'execution_failure_criteria' : {'required':False, 'default' : 'n', 'pythonize' : to_split},
                'notification_failure_criteria' : {'required':False, 'default' : 'n', 'pythonize' : to_split},
                'dependency_period' : {'required':False, 'default' : ''}
                }


#    #return a copy of a service, but give him a new id
#    def copy(self):
#        hd = deepcopy(self)
#        hd.id = Hostdependency.id
#        Hostdependency.id = Hostdependency.id + 1
#        return hd



class Hostdependencies(Items):
    def delete_hostsdep_by_id(self, ids):
        for id in ids:
            del self.items[id]


    #We create new servicedep if necessery (host groups and co)
    def explode(self):
        #The "old" services will be removed. All services with 
        #more than one host or a host group will be in it
        hstdep_to_remove = []
        
        #Then for every host create a copy of the service with just the host
        hostdeps = self.items.keys() #because we are adding services, we can't just loop in it
        for id in hostdeps:
            hd = self.items[id]
            hnames = hd.dependent_host_name.split(',')
            if len(hnames) >= 2:
                for hname in hnames:
                    hname = hname.strip()
                    new_hd = hd.copy()
                    new_hd.dependent_host_name = hname
                    self.items[new_hd.id] = new_hd
                hstdep_to_remove.append(id)        
        self.delete_hostsdep_by_id(hst_to_remove)


    def linkify(self, hosts, timeperiods):
        self.linkify_hd_by_tp(timeperiods)
        self.linkify_h_by_hd()


    #We just search for each srvdep the id of the srv
    #and replace the name by the id
    def linkify_sd_by_tp(self, timeperiods):
        for hd in self:#.items:
            try:
                tp_name = hd.dependency_period
                tp = timeperiods.find_by_name(tp_name)
                hd.dependency_period = tp
            except AttributeError as exp:
                print exp


    #We backport service dep to service. So SD is not need anymore
    def linkify_h_by_hd(self):
        for hd in self:#.items:
            h = hd.dependent_host_name
            if h is not None:
                if hd.has('dependency_period'):
                    h.add_host_act_dependancy(hd.host_name, hd.notification_failure_criteria, hd.dependency_period)
                else:
                    h.add_host_act_dependancy(hd.host_name, hd.notification_failure_criteria, None)

