# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.12.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

import os
from fabric.api import local
from collections import namedtuple
from getpass import getpass


# Data structures
# --------------------------------------------------------------------------
class User(object):

    def __init__(self, name, account_type, home_assistant_user):
        self.name = name
        self.account_type = account_type
        self.home_assistant_user = home_assistant_user
        self.password = None

    def __repr__(self):
        return 'User(%s, %s, %s)' % (self.name, self.account_type, self.home_assistant_user)

    def __str__(self):
        return 'User<%s>' % (self.name)


# Data
# --------------------------------------------------------------------------
system_libs = """
vim
tmux
gedit
kate
tig
ufw
GUFW
htop
samba
monit
libreadline-dev
libnursesw5-dev
libssl-dev
libgdbm-dev
libsqlite3-dev
libbz2-dev
liblzma-dev
libdb-dev
tk-dev
"""

user_dirs = """
projects
software
notes
tmp
docs
"""
users = [ 
            User('hass', 'system', True), 
            User('fstakem', 'admin', False)
        ]

user_aliases = """
alias ll='ls -la'
alias cd..='cd ..'
alias ..='cd ..'
"""

pyenv_git_url = 'https://github.com/yyuu/pyenv'

pyenv_shortcuts = """
export PYENV_ROOT="/srv/pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
"""

python_versions = """
3.5.2
"""

current_python = '3.5.2'
ha_url = 'https://github.com/home-assistant/home-assistant'
ha_folder_name = 'home_assistant'
ha_path = os.path.join('/srv', ha_folder_name)
src_dir_name = 'src'
venv_dir_name = 'ha_env'
config_dir_name = 'config'
config_url = 'https://github.com/fstakem/home_assistant_config'

firewall_allowed = """
ssh
http
https
5123/tcp
2812/tcp
"""
# Missing samba


# Helper functions
# --------------------------------------------------------------------------
def apt_get(packages):
    cmd = 'apt-get -qy install %s' % ' '.join(packages)
    print(cmd)
    #sudo(cmd, shell=False)

def get_passwd(username):
    tries = 3
    first_pw = getpass('Enter password for %s: ' % (username))
    second_pw = getpass('Renter the password for %s: ' % (username))

    for _ in range(tries):
        if first_pw == second_pw:
            return first_pw

    raise ValueError

   
# Setup functions
# --------------------------------------------------------------------------
def setup_users(users, user_dirs, aliases):
    get_passwords(users)
    create_system_aliases(aliases)

    for user in users:
        create_account(user)
        create_dirs(user, user_dirs)
        create_aliases(user, aliases)

def get_passwords(users):
    for user in users:
        try:
            user.password = get_passwd(user.name)
        except ValueError:
            pass

def create_account(user):
    if user.account_type == 'admin':
        cmd = 'useradd -m %s -G sudo' % (user.name)
        print(cmd)
    elif user.account_type == 'system':
        cmd = 'useradd -r %s' % (user.name)
        print(cmd)

    #sudo(cmd, shell=False)
    cmd = 'echo %s | passwd %s --stdin' % (user.password, user.name)
    print(cmd)
    #sudo(cmd, shell=False)

def create_dirs(user, user_dirs):
    if not user.account_type == 'admin':
        return

    for dir in user_dirs:
        path = '/home/%s/%s' % (user.name, dir)
        cmd = 'mkdir %s' % path
        #sudo(cmd, shell=False) 
        print(cmd)
        cmd = 'chown %s:%s %s' % (user.name, user.name, path)
        #sudo(cmd, shell=False) 
        print(cmd)

def create_system_aliases(aliases):
    cmd = 'echo # Aliases >> /etc/bash.bashrc'
    print(cmd)
    #sudo(cmd, shell=False)

    for alias in aliases:
        cmd = 'echo %s > /etc/bash.bashrc' % (alias)
        print(cmd)
        #sudo(cmd, shell=False)

    cmd = ''
    print(cmd)
    #sudo(cmd, shell=False)

def create_aliases(user, aliases):
    if not user.account_type == 'admin':
        return

    cmd = 'echo # Aliases >> /home/%s/.bashrc' % (user.name)
    print(cmd)
    #sudo(cmd, shell=False)

    for alias in aliases:
        cmd = 'echo %s >> /home/%s/.bashrc' % (alias, user.name)
        print(cmd)
        #sudo(cmd, shell=False)

    cmd = ''
    print(cmd)
    #sudo(cmd, shell=False)

def remove_pi_user():
    cmd = 'deluser -r pi'
    print(cmd)
    #sudo(cmd, shell=False)

def setup_pyenv(ha_user, users, git_url, shortcuts):
    cmd = 'su %s' % (ha_user.name)
    print(cmd)
    #sudo(cmd, shell=False)

    path = '/srv/pyenv'
    cmd = 'mkdir %s' % (path)
    cmd = 'git clone %s %s' % (git_url, path)

    cmd = 'exit'
    print(cmd)
    #sudo(cmd, shell=False)
    
    add_pyenv_system_shortcuts(shortcuts)
    for user in users:
        add_pyenv_shortcuts(user, shortcuts)

def add_pyenv_system_shortcuts(shortcuts):
    cmd = 'echo # Pyenv setup >> /etc/bash.bashrc'
    print(cmd)
    #sudo(cmd, shell=False)

    for shortcut in shortcuts:
        cmd = 'echo %s >> /etc/bash.bashrc' % (shortcut)
        print(cmd)
        #sudo(cmd, shell=False)

    cmd = ''
    print(cmd)
    #sudo(cmd, shell=False)

def add_pyenv_shortcuts(user, shortcuts):
    cmd = 'echo # Pyenv setup >> /home/%s/.bashrc' % (user.name)
    print(cmd)
    #sudo(cmd, shell=False)

    for shortcut in shortcuts:
        cmd = 'echo %s >> /home/%s/.bashrc' % (shortcut, user.name)
        print(cmd)
        #sudo(cmd, shell=False)

    cmd = ''
    print(cmd)
    #sudo(cmd, shell=False)

def setup_python(ha_user, versions, current_python):
    cmd = 'su %s' % (ha_user.name)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'source /etc/bash.bashrc'
    print(cmd)
    #sudo(cmd, shell=False)

    for version in versions:
        cmd = 'pyenv install %s' % (version)
        print(cmd)
        #sudo(cmd, shell=False)

    cmd = 'pyenv global %s' % (current_python)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'exit'
    print(cmd)
    #sudo(cmd, shell=False)

def setup_home_assistant(ha_user, ha_path, ha_url, src_dir_name, config_dir_name, venv_dir_name, config_url):
    cmd = 'su %s' % (ha_user.name)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'mkdir %s' % (ha_path)
    print(cmd)
    #sudo(cmd, shell=False)

    src_path = os.path.join(ha_path, src_dir_name)
    cmd = 'mkdir %s' % (src_path)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'git clone %s %s' % (ha_url, src_path)
    print(cmd)
    #sudo(cmd, shell=False)

    config_path = os.path.join(ha_path, config_dir_name)
    cmd = 'mkdir %s' % (config_path)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'git clone %s %s' % (config_url, config_path)
    print(cmd)
    #sudo(cmd, shell=False)

    venv_path = os.path.join(ha_path, venv_dir_name)
    cmd = 'virtualenv %s' % (venv_path)
    print(cmd)
    #sudo(cmd, shell=False)

    activate_path = os.path.join(venv_path, 'bin', 'activate')
    cmd = 'source %s' % (activate_path)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'pip install -e %s' % (src_path)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'exit'
    print(cmd)
    #sudo(cmd, shell=False)

def setup_firewall(apps_allowed):
    cmd = 'ufw default deny incoming'
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'ufw default allow outgoing'
    print(cmd)
    #sudo(cmd, shell=False)

    for app in apps_allowed:
        cmd = 'ufw allow %s' % (app)
        print(cmd)
        #sudo(cmd, shell=False)

    cmd = 'ufw enable'
    print(cmd)
    #sudo(cmd, shell=False)

def setup_smb(users, ha_path, ha_folder_name):
    # passwords
    # TODO

    cmd = 'echo >> /etc/samba/smb.conf'
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'echo [%s] >> /etc/samba/smb.conf' % (ha_folder_name)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'echo path = %s >> /etc/samba/smb.conf' % (ha_path)
    print(cmd)
    #sudo(cmd, shell=False)

    valid_users = [user.name for user in users]
    user_str = ' '.join(valid_users)
    cmd = 'echo valid users = %s >> /etc/samba/smb.conf' % (user_str)
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'echo read only = no >> /etc/samba/smb.conf'
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'echo browseable = yes >> /etc/samba/smb.conf'
    print(cmd)
    #sudo(cmd, shell=False)

    cmd = 'service samba restart'
    print(cmd)
    #sudo(cmd, shell=False)

def setup_monit():
    pass

def setup_sysd():
    pass


# Main
# --------------------------------------------------------------------------
def install_all():
    # setup wifi
    # allow ssh
    # set hostname/timezone/keyboard/wifi country/locale
    # make sure doesn't automatically login as pi

    libs = system_libs.split()
    dirs = user_dirs.split()
    aliases = user_aliases.split('\n')[1:-1]
    shortcuts = pyenv_shortcuts.split('\n')[1:-1]
    versions = python_versions.split()
    ha_user = [u for u in users if u.home_assistant_user == True][0]
    apps_allowed = firewall_allowed.split()

    apt_get(libs)
    setup_users(users, dirs, aliases)
    setup_pyenv(ha_user, users, pyenv_git_url, shortcuts)
    setup_python(ha_user, versions, current_python)
    setup_home_assistant(ha_user, ha_path, ha_url, src_dir_name, config_dir_name, venv_dir_name, config_url)
    setup_firewall(apps_allowed)
    setup_smb(users, ha_path, ha_folder_name)

    #reboot()
    remove_pi_user()
    


