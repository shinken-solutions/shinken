

class Helper(object):
    def __init__(self):
        pass

    def gogo(self):
        return 'HELLO'


    def act_inactive(self, b):
        if b:
            return 'ACTIVE'
        else:
            return 'INACTIVE'

helper = Helper()
