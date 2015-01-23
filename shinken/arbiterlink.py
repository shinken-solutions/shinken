'''shinken.arbiterlink is deprecated. Please use shinken.objects.arbiterlink now.'''

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import arbiterlink

make_deprecated_daemon_link(arbiterlink)
