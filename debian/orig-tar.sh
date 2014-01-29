#!/bin/sh
# This script will create the following tarball:
# shinken_1.4.orig.tar.gz
set -e

CURRENT_DIR="$( dirname "$(readlink -f $0)" )"

MAJOR_VERSION=1.4

SHINKEN_URL=https://github.com/naparuba/shinken

GIT_CMD="git clone"

# Shinken
SHINKEN_TARGET=shinken_${MAJOR_VERSION}
$GIT_CMD $SHINKEN_URL $SHINKEN_TARGET -b ${MAJOR_VERSION}

# Get missing sources
wget http://code.jquery.com/jquery-1.6.4.js -O $SHINKEN_TARGET/shinken/webui/htdocs/js/jquery-1.6.4.js
wget https://jquery-jsonp.googlecode.com/files/jquery.jsonp-2.2.1.js -O $SHINKEN_TARGET/shinken/webui/htdocs/js/jquery.jsonp-2.2.1.js
wget http://mobile-web-development-with-phonegap.eclipselabs.org.codespot.com/svn-history/r163/trunk/com.mds.apg/resources/jqm/jquery.mobile/jquery.mobile-1.1.0.js -O $SHINKEN_TARGET/shinken/webui/htdocs/js/jquery.mobile-1.1.0.js
wget https://raw.github.com/joequery/Stupid-Table-Plugin/master/stupidtable.js -O $SHINKEN_TARGET/shinken/webui/htdocs/js/stupidtable.js
wget http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.17/jquery-ui.js -O $SHINKEN_TARGET/shinken/webui/htdocs/js/jquery-ui-1.8.17.custom.js
wget https://raw2.github.com/fgnass/spin.js/85275f5fe82ba816b80f1155a96f08884cf98fbb/dist/spin.js -O $SHINKEN_TARGET/shinken/webui/htdocs/js/spin.js
# Delete useless files and plugins
rm -f $SHINKEN_TARGET/doc/architecture.*

# Prepare source
tar czfv shinken_${MAJOR_VERSION}.orig.tar.gz $SHINKEN_TARGET
rm -rf $SHINKEN_TARGET

PATH_DEBIAN="$(pwd)/$(dirname $0)/../"
echo "going into $PATH_DEBIAN"
export DEBFULLNAME="Thibault Cohen"
export DEBEMAIL="thibault.cohen@savoirfairelinux.com"
cd $PATH_DEBIAN

if test -z "$DISTRIBUTION"; then
    DISTRIBUTION="experimental"
fi
dch --distribution $DISTRIBUTION --newversion 1:${MAJOR_VERSION}-1~exp1 "New version release"

exit 0
