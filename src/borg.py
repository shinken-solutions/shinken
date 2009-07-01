# here is the new-style Borg (not much more complex then the "old-style")

class Borg(object):
    __shared_state = {}
    def __init__(self):
        #print "Init Borg", self.__dict__, self.__class__.__shared_state
        self.__dict__ = self.__class__.__shared_state
