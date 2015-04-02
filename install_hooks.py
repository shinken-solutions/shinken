import os 
import sys
import re
import fileinput
import getpass

#########################################################################
# ugly
import pwd
import grp
import itertools


def recursive_chown(path, uid, gid, owner, group):
    print("Changing owner of %s to %s:%s" % (path, owner, group))
    os.chown(path, uid, gid)
    if os.path.isdir(path):
        for dirname, dirs, files in os.walk(path):
            for path in itertools.chain(dirs, files):
                path = os.path.join(dirname, path)
                os.chown(path, uid, gid)

def get_uid(user_name):
    try:
        return pwd.getpwnam(user_name)[2]
    except KeyError, exp:
        return None

def get_gid(group_name):
    try:
        return grp.getgrnam(group_name)[2]
    except KeyError, exp:
        return None

def check_user_shinken(config):
    user = "shinken"
    group = "shinken"
    uid = get_uid(user)
    gid = get_gid(group)
    if not os.environ.get('TRAVIS', False) and getpass.getuser() == 'root' and uid is None or gid is None:
        raise Exception("Error: the user/group %s/%s is unknown. Please create it first 'useradd %s'" % (user,group, user))

# end ugly
###########################################################################

def get_init_scripts(config):
    """ Add init scripts in data_files for install """
    data_files = config['files']['data_files']
    if 'win' in sys.platform:
        pass
    elif 'linux' in sys.platform or 'sunos5' in sys.platform:
        data_files = data_files + "\n/etc/init.d = bin/init.d/*"
        data_files = data_files + "\n/etc/default = bin/default/shinken.in"
    elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
        data_files = data_files + "\n/usr/local/etc/rc.d = bin/rc.d/*"
    else:
        raise "Unsupported platform, sorry"
        data_files = []
    config['files']['data_files'] = data_files

def fix_data_files_path(config):
    """ This is an ugly ugly ugly patch to handle
    a none standard python installation
    """
    ## ugly
    if getpass.getuser() == 'root' and config.root is None and 'bsd' not in sys.platform and 'dragonfly' not in sys.platform:
        config.root = "/"
    if config.root  and 'bsd' not in sys.platform and 'dragonfly' not in sys.platform:
        config.install_dir = config.root
    if not config.root and 'bsd' not in sys.platform and 'dragonfly' not in sys.platform:
        config.data_files = [(os.path.join(config.install_dir, folder[0].strip("/")),
                             folder[1]) for folder in config.data_files]
    if 'bsd' in sys.platform or 'dragonfly' in sys.platform:
        config.data_files = [(folder[0].strip("/"),
                             folder[1]) for folder in config.data_files]
    ## end ugly

def fix_shinken_cfg(config):
    """ Fix paths, user and group in shinken.cfg and daemons/*.ini """
    ## ugly
    # This is an ugly ugly ugly patch to handle
    # a none standard python installation
    if config.root:
        config.install_dir = config.root
    ## end ugly

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
        default_users['SHINKENUSER'] = 'shinken'
        default_users['SHINKENGROUP'] = 'shinken'
        default_users['HOME'] = '`grep ^$SHINKENUSER: /etc/passwd | cut -d: -f 6`'

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

    # Handle default/shinken
    if 'linux' in sys.platform or 'sunos5' in sys.platform:
        old_name = os.path.join(config.install_dir, "etc", "default", "shinken.in")
        new_name = os.path.join(config.install_dir, "etc", "default", "shinken")
        os.rename(old_name, new_name)
        default_paths = {
            'ETC': '/etc/shinken',
            'VAR': '/var/lib/shinken',
            'BIN': '/bin',
            'RUN': '/var/run/shinken',
            'LOG': '/var/log/shinken',
            }

        ## ugly
        if getpass.getuser() == 'root' and config.root == "/":
            default_paths["BIN"] = "/usr/bin"
        ## end ugly

        pattern = "|".join(default_paths.keys())
        changing_path = re.compile("^(%s) *= *" % pattern)
        for line in fileinput.input(new_name,  inplace=True):
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

        ## ugly
        # If we are root
        # We make some chown
        if not os.environ.get('TRAVIS', False) and getpass.getuser() == 'root' and config.root == "/":
            uid = get_uid(default_users['shinken_user'])
            gid = get_gid(default_users['shinken_group'])
            for path in default_paths.values():
                recursive_chown(path, uid, gid, default_users['shinken_user'], default_users['shinken_group'])
        ## end ugly

    # Add ENV vars only if we are in virtualenv
    # in order to get init scripts working
    if 'VIRTUAL_ENV' in os.environ:
        activate_file = os.path.join(os.environ.get("VIRTUAL_ENV"), 'bin', 'activate')
        try:
            afd = open(activate_file, 'r+')
        except Exception as exp:
            print(exp)
        env_config = ("""export PYTHON_EGG_CACHE=.\n"""
                      """export SHINKEN_DEFAULT_FILE=%s/etc/default/shinken\n"""
                      % os.environ.get("VIRTUAL_ENV"))
        if afd.read().find(env_config) == -1:
            afd.write(env_config)
            print("\n"
                  "=======================================================================================================\n"
                  "==                                                                                                   ==\n"
                  "==  You need to REsource env/bin/activate in order to set appropriate variables to use init scripts  ==\n"
                  "==                                                                                                   ==\n"
                  "=======================================================================================================\n"
                  )
