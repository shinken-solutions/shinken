try:
    from cStringIO import StringIO
    import cPickle as cpickle
    import ConfigParser
    from Queue import Empty
except ImportError:  # Python3
    from io import StringIO
    import pickle as cpickle
    import configparser as ConfigParser
    from queue import Empty