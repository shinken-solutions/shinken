'''shinken.satellitelink is deprecated. Please use shinken.objects.satellitelink now.'''

from __future__ import absolute_import, division, print_function, unicode_literals

from shinken.old_daemon_link import deprecation, make_deprecated

deprecation(__doc__)

from shinken.objects.satellitelink import (
    SatelliteLink,
    SatelliteLinks,
)

SatelliteLink = make_deprecated(SatelliteLink)
SatelliteLinks = make_deprecated(SatelliteLinks)
