'''shinken.reactionnerlink is deprecated. Please use shinken.objects.reactionnerlink now.'''

from shinken.old_daemon_link import make_deprecated_daemon_link

from shinken.objects import reactionnerlink

make_deprecated_daemon_link(reactionnerlink)
