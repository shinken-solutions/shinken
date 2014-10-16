from functools import partial
import mock

from shinken.modules.livestatus_broker import livestatus
from shinken.modules.livestatus_broker.livestatus_client_thread import LiveStatusClientThread
from shinken.modules.livestatus_broker.livestatus_response import LiveStatusListResponse

#

old_livestatus_handle_request = livestatus.LiveStatus.handle_request
def mocked_livestatus_handle_request(*a, **kw):
    '''Implement an extended version of LiveStatus.handle_request where we return
      the response flattened in case it was a LiveStatusListResponse'''
    response, keepalive = old_livestatus_handle_request(*a, **kw)
    if isinstance(response, LiveStatusListResponse):
        response = ''.join(response)
    return response, keepalive
#
# could have also mocked the LiveStatus class itself but then
# it would need to be done when the module is NOT yet imported elsewhere.
# Because there are places/modules (like in shinken_test) where this is done:
# '''
# from shinken.modules.livestatus_broker.livestatus import LiveStatus
# '''
# and so this imported LiveStatus is "unbound" from its module. If the mock.patch
# occurs after such statement then the place where this imported LiveStatus
# name would still use the NOT patched method, simply because it would still
# uses the NOT patched LiveStatus class.
# See below mock_LiveStatus().
#
def mock_livestatus_handle_request(obj):
    '''
    :type obj: Could be a class or a function/method.
    :return: The object with the mocked LiveStatus.handle_request
    '''
    return mock.patch('shinken.modules.livestatus_broker.livestatus.LiveStatus.handle_request',
               mocked_livestatus_handle_request)(obj)


def mock_LiveStatus():
    ''' If one wants to mock the LiveStatus class itself. '''
    class LiveStatus(livestatus.LiveStatus):
        mock_livestatus_handle_request = mocked_livestatus_handle_request
    livestatus.LiveStatus = LiveStatus


#
# New LiveStatusClientThread :
#
def mocked_livestatus_client_thread_send_data(self, data):
    # instead of using a socket, simply accumulate the result in a list:
    if not hasattr(self, '_test_buffer_output'):
        self._test_buffer_output = []
    self._test_buffer_output.append(data)

orig_livestatus_client_thread_handle_request = LiveStatusClientThread.handle_request
def mocked_livestatus_client_thread_handle_request(self, response):

    # while the handle_request() from LiveStatus class itself is still mocked because
    # its used by the tests, we need to temporarily replace it the original one:
    prev = self.livestatus.handle_request
    self.livestatus.handle_request = partial(old_livestatus_handle_request, self.livestatus)
    orig_livestatus_client_thread_handle_request(self, response)
    # restore the previous livestatus.handle_request:
    self.livestatus.handle_request = prev
    # then just construct the full response by joining the list which was
    # built within mocked_livestatus_client_thread_send_data
    res = ''.join(self._test_buffer_output)
    del self._test_buffer_output
    return res, None

