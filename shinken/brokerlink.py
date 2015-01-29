'''shinken.brokerlink is deprecated. Please use shinken.objects.brokerlink now.'''

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import brokerlink

make_deprecated_daemon_link(brokerlink)
