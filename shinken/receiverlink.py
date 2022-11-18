'''shinken.receiverlink is deprecated. Please use shinken.objects.receiverlink now.'''

from __future__ import absolute_import, division, print_function, unicode_literals

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import receiverlink

make_deprecated_daemon_link(receiverlink)
