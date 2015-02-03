'''shinken.pollerlink is deprecated. Please use shinken.objects.pollerlink now.'''

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import pollerlink

make_deprecated_daemon_link(pollerlink)
