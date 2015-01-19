'''shinken.schedulerlink is deprecated. Please use shinken.objects.schedulerlink now.'''

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import schedulerlink


make_deprecated_daemon_link(schedulerlink)
