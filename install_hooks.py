import os 
import re
import fileinput
import getpass


def main(config):
    """ function called before any actions in python setup.py install """
    pass


def fix_shinken_cfg(config):
    """ Fix paths, user and group in shinken.cfg and daemons/*.ini """
    default_paths = {
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

    # Changing default user/group if root
    default_users = {}
    if getpass.getuser() == 'root':
        default_users['shinken_user'] = 'shinken'
        default_users['shinken_group'] = 'shinken'
        default_users['user'] = 'shinken'
        default_users['group'] = 'shinken'

    # Prepare pattern for shinken.cfg
    pattern = "|".join(default_paths.keys())
    changing_path = re.compile("^(%s) *= *" % pattern)
    pattern = "|".join(default_users.keys())
    changing_user = re.compile("^#(%s) *= *" % pattern)
    # Fix shinken.cfg
    shinken_cfg_path = os.path.join(config.install_dir,
                                    "etc",
                                    "shinken",
                                    "shinken.cfg")

    for line in fileinput.input(shinken_cfg_path, inplace=True):
        line = line.strip()
        path_attr_name = changing_path.match(line)
        user_attr_name = changing_user.match(line)
        if path_attr_name:
            new_path = os.path.join(config.install_dir,
                                    default_paths[path_attr_name.group(1)].strip("/"))
            print("%s=%s" % (path_attr_name.group(1),
                             new_path))
        elif user_attr_name:
            print("%s=%s" % (user_attr_name.group(1),
                             default_users[user_attr_name.group(1)]))
        else:
            print(line)

    # Handle daemons ini files
    for ini_file in ["brokerd.ini", "schedulerd.ini", "pollerd.ini", "reactionnerd.ini", "receiverd.ini"]:
        # Prepare pattern for ini files
        daemon_name = ini_file.strip(".ini")
        default_paths['lock_file'] = '/var/run/shinken/%s.pid' % daemon_name
        default_paths['local_log'] = '/var/log/shinken/%s.log' % daemon_name
        default_paths['pidfile'] = '/var/run/shinken/%s.pid' % daemon_name
        pattern = "|".join(default_paths.keys())
        changing_path = re.compile("^(%s) *= *" % pattern)
        # Fix ini file
        shinken_cfg_path = os.path.join(config.install_dir,
                                        "etc",
                                        "shinken",
                                        "daemons",
                                        ini_file)
        for line in fileinput.input(shinken_cfg_path, inplace=True):
            line = line.strip()
            path_attr_name = changing_path.match(line)
            user_attr_name = changing_user.match(line)
            if path_attr_name:
                new_path = os.path.join(config.install_dir,
                                        default_paths[path_attr_name.group(1)].strip("/"))
                print("%s=%s" % (path_attr_name.group(1),
                                 new_path))
            elif user_attr_name:
                print("%s=%s" % (user_attr_name.group(1),
                                 default_users[user_attr_name.group(1)]))
            else:
                print(line)

    # Add shinken_cli.ini
    shinken_cli_ini_path = os.path.join(config.install_dir,
                                        "etc",
                                        "shinken",
                                        "shinken_cli.ini")
    from shinken.bin.shinken_cli import main
    try:
        main(["--init", "-c", shinken_cli_ini_path])
    except SystemExit:
        pass
    # Fix shinken_cli.ini
    default_clipaths = {'etc': '/etc/shinken',
                        'lib': '/var/lib/shinken',
                       }

    pattern = "|".join(default_clipaths.keys())
    changing_clipath = re.compile("^(%s) *= *" % pattern)
    for line in fileinput.input(shinken_cli_ini_path, inplace=True):
        line = line.strip()
        clipath_attr_name = changing_clipath.match(line)
        if clipath_attr_name:
            new_path = os.path.join(config.install_dir,
                                    default_clipaths[clipath_attr_name.group(1)].strip("/"))
            print("%s=%s" % (clipath_attr_name.group(1),
                             new_path))
        else:
            print(line)
