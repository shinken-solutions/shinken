
import re
import time


from shinken.log import logger


from .collectd_parser import (
    CollectdException,
    Reader,
    Values as _Values, Data as _Data, Notification as _Notification,
    _BUFFER_SIZE
)



class Data(_Data):

    def __init__(self, *a, **kw):
        self.grouped_collectd_plugins = kw.pop('grouped_collectd_plugins', [])
        super(Data, self).__init__(*a, **kw)


    def get_srv_desc(self):
        '''
        :param item: A collectd Data instance.
        :return: The Shinken service name related by this collectd stats item.
        '''
        res = self.plugin
        if self.plugin not in self.grouped_collectd_plugins:
            if self.plugininstance:
                res += '-' +self.plugininstance
        # Dirty fix for 1.4.X:
        return re.sub(r'[' + "`~!$%^&*\"|'<>?,()=" + ']+', '_', res)

    def get_metric_name(self):
        res = self.type
        if self.plugin in self.grouped_collectd_plugins:
            if self.plugininstance:
                res += '-' + self.plugininstance
        if self.typeinstance:
            res += '-' + self.typeinstance
        return res

    def get_name(self):
        return '%s;%s' % (self.host, self.get_srv_desc())



class Notification(Data, _Notification):

    _severity_2_retcode = {
        _Notification.OKAY:      0,
        _Notification.WARNING:   1,
        _Notification.FAILURE:   2,
    }

    def get_message_command(self):
        """ Return data severity (exit code) from collectd datas
        """
        now = int(time.time())
        retcode = self._severity_2_retcode.get(self.severity, 3)
        return '[%d] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s' % (
            now, self.host, self.get_srv_desc(), retcode, self.message)


class Values(Data, _Values):
    pass



class ShinkenCollectdReader(Reader):


    def __init__(self, *a, **kw):
        self.grouped_collectd_plugins = kw.pop('grouped_collectd_plugins', [])
        super(ShinkenCollectdReader, self).__init__(*a, **kw)

    def Values(self):
        return Values(grouped_collectd_plugins=self.grouped_collectd_plugins)

    def Notification(self):
        return Notification(grouped_collectd_plugins=self.grouped_collectd_plugins)

