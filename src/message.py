

class Message:
    """A simple message class"""
    _type = None
    _data = None
    _from = None
    def __init__(self, id, type, data=None):
        self._type = type
        self._data = data
        self._from = id

    def get_type(self):
        return self._type
    def get_data(self):
        return self._data
    def get_from(self):
        return self._from
    def str(self):
        return "Message from %d, Type: %s Data: %s" % (self._from, self._type, self._data)
