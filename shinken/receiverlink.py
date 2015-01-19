'''shinken.receiverlink is deprecated. Please use shinken.objects.receiverlink now.'''

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import receiverlink

make_deprecated_daemon_link(receiverlink)
