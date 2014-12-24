import os 
import re
import fileinput


def main(config):
    """ function called before any actions in python setup.py install """
    print "ASAAAAAAAAA"
    pass


def fix_shinken_cfg(config):
    """ Fix paths in shinken.cfg """
    default_values = {
        'lock_file': '/var/run/shinken/arbiterd.pid',
        'local_log': '/var/log/shinken/arbiterd.log',
        'pidfile': '/var/run/shinken/arbiterd.pid',
        'workdir': '/var/run/shinken',
        'pack_distribution_file': '/var/lib/shinken/pack_distribution.dat',
        'modules_dir': '/var/lib/shinken/modules',
        'ca_cert': '/etc/shinken/certs/ca.pem',
        'server_cert': '/etc/shinken/certs/server.cert',
        'server_key': '/etc/shinken/certs/server.key',
        'logdir': '/var/log/shinken',
        }

    if not config.root:
        # Prepare pattern for shinken.cfg
        pattern = "|".join(default_values.keys())
        changing_attr = re.compile("^(%s) *= *" % pattern)
        # Fix shinken.cfg
        shinken_cfg_path = os.path.join(config.install_dir, "etc", "shinken.cfg")
        for line in fileinput.input(shinken_cfg_path, inplace=True):
            line = line.strip()
            attr_name = changing_attr.match(line)
            if attr_name:
                new_path = os.path.join(config.install_dir, default_values[attr_name.group(1)].strip("/"))
                print "%s=%s" % (attr_name.group(1), new_path)
            else:
                print line

        # Handle daemons ini files
        for ini_file in ["brokerd.ini", "schedulerd.ini", "pollerd.ini", "reactionnerd.ini", "receiverd.ini"]:
            # Prepare pattern for ini files
            daemon_name = ini_file.strip(".ini")
            default_values['lock_file'] = '/var/run/shinken/%s.pid' % daemon_name
            default_values['local_log'] = '/var/log/shinken/%s.log' % daemon_name
            default_values['pidfile'] = '/var/run/shinken/%s.pid' % daemon_name
            pattern = "|".join(default_values.keys())
            changing_attr = re.compile("^(%s) *= *" % pattern)
            # Fix ini file
            shinken_cfg_path = os.path.join(config.install_dir, "etc", "daemons", ini_file)
            for line in fileinput.input(shinken_cfg_path, inplace=True):
                line = line.strip()
                attr_name = changing_attr.match(line)
                if attr_name:
                    new_path = os.path.join(config.install_dir, default_values[attr_name.group(1)].strip("/"))
                    print "%s=%s" % (attr_name.group(1), new_path)
                else:
                    print line
