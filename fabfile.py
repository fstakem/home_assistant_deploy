# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.12.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

import os
import fabric
from fabric.api import local
from collections import namedtuple
from getpass import getpass


from settings import config

# Globals
# --------------------------------------------------------------------------
debug = True


# Helper functions
# --------------------------------------------------------------------------
def sudo(cmd, debug=False):
    if debug:
        print(cmd)
    else:
        fabric.api.sudo(cmd)

def apt_get(packages):
    cmd = 'apt-get -qy install %s' % ' '.join(packages)
    sudo(cmd, debug)

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
        sudo(cmd, debug)
    elif user.account_type == 'system':
        cmd = 'useradd -r %s' % (user.name)
        sudo(cmd, debug)

    cmd = 'echo %s | passwd %s --stdin' % (user.password, user.name)
    sudo(cmd, debug)

def create_dirs(user, user_dirs):
    if not user.account_type == 'admin':
        return

    for dir in user_dirs:
        path = '/home/%s/%s' % (user.name, dir)
        cmd = 'mkdir %s' % path
        sudo(cmd, debug)

        cmd = 'chown %s:%s %s' % (user.name, user.name, path)
        sudo(cmd, debug)

def create_system_aliases(aliases):
    cmd = 'echo # Aliases >> /etc/bash.bashrc'
    sudo(cmd, debug)

    for alias in aliases:
        cmd = 'echo %s > /etc/bash.bashrc' % (alias)
        sudo(cmd, debug)

    cmd = ''
    sudo(cmd, debug)

def create_aliases(user, aliases):
    if not user.account_type == 'admin':
        return

    cmd = 'echo # Aliases >> /home/%s/.bashrc' % (user.name)
    sudo(cmd, debug)

    for alias in aliases:
        cmd = 'echo %s >> /home/%s/.bashrc' % (alias, user.name)
        sudo(cmd, debug)

    cmd = ''
    sudo(cmd, debug)

def remove_pi_user():
    cmd = 'deluser -r pi'
    sudo(cmd, debug)

def setup_pyenv(ha_user, users, git_url, shortcuts):
    cmd = 'su %s' % (ha_user.name)
    sudo(cmd, debug)

    path = '/srv/pyenv'
    cmd = 'mkdir %s' % (path)
    sudo(cmd, debug)

    cmd = 'git clone %s %s' % (git_url, path)
    sudo(cmd, debug)

    cmd = 'exit'
    sudo(cmd, debug)
    
    add_pyenv_system_shortcuts(shortcuts)
    for user in users:
        add_pyenv_shortcuts(user, shortcuts)

def add_pyenv_system_shortcuts(shortcuts):
    cmd = 'echo # Pyenv setup >> /etc/bash.bashrc'
    sudo(cmd, debug)

    for shortcut in shortcuts:
        cmd = 'echo %s >> /etc/bash.bashrc' % (shortcut)
        sudo(cmd, debug)

    cmd = ''
    sudo(cmd, debug)

def add_pyenv_shortcuts(user, shortcuts):
    cmd = 'echo # Pyenv setup >> /home/%s/.bashrc' % (user.name)
    sudo(cmd, debug)

    for shortcut in shortcuts:
        cmd = 'echo %s >> /home/%s/.bashrc' % (shortcut, user.name)
        sudo(cmd, debug)

    cmd = ''
    sudo(cmd, debug)

def setup_python(ha_user, versions, current_python):
    cmd = 'su %s' % (ha_user.name)
    sudo(cmd, debug)

    cmd = 'source /etc/bash.bashrc'
    sudo(cmd, debug)

    for version in versions:
        cmd = 'pyenv install %s' % (version)
        sudo(cmd, debug)

    cmd = 'pyenv global %s' % (current_python)
    sudo(cmd, debug)

    cmd = 'exit'
    sudo(cmd, debug)

def setup_home_assistant(ha_user, ha_path, ha_url, src_dir_name, config_dir_name, venv_dir_name, config_url):
    cmd = 'su %s' % (ha_user.name)
    sudo(cmd, debug)

    cmd = 'mkdir %s' % (ha_path)
    sudo(cmd, debug)

    src_path = os.path.join(ha_path, src_dir_name)
    cmd = 'mkdir %s' % (src_path)
    sudo(cmd, debug)

    cmd = 'git clone %s %s' % (ha_url, src_path)
    sudo(cmd, debug)

    config_path = os.path.join(ha_path, config_dir_name)
    cmd = 'mkdir %s' % (config_path)
    sudo(cmd, debug)

    cmd = 'git clone %s %s' % (config_url, config_path)
    sudo(cmd, debug)

    venv_path = os.path.join(ha_path, venv_dir_name)
    cmd = 'virtualenv %s' % (venv_path)
    sudo(cmd, debug)

    activate_path = os.path.join(venv_path, 'bin', 'activate')
    cmd = 'source %s' % (activate_path)
    sudo(cmd, debug)

    cmd = 'pip install -e %s' % (src_path)
    sudo(cmd, debug)

    cmd = 'exit'
    sudo(cmd, debug)

def setup_firewall(apps_allowed):
    cmd = 'ufw default deny incoming'
    sudo(cmd, debug)

    cmd = 'ufw default allow outgoing'
    sudo(cmd, debug)

    for app in apps_allowed:
        cmd = 'ufw allow %s' % (app)
        sudo(cmd, debug)

    cmd = 'ufw enable'
    sudo(cmd, debug)

def setup_smb(users, ha_path, ha_folder_name):
    # passwords
    # TODO

    cmd = 'echo >> /etc/samba/smb.conf'
    sudo(cmd, debug)

    cmd = 'echo [%s] >> /etc/samba/smb.conf' % (ha_folder_name)
    sudo(cmd, debug)

    cmd = 'echo path = %s >> /etc/samba/smb.conf' % (ha_path)
    sudo(cmd, debug)

    valid_users = [user.name for user in users]
    user_str = ' '.join(valid_users)
    cmd = 'echo valid users = %s >> /etc/samba/smb.conf' % (user_str)
    sudo(cmd, debug)

    cmd = 'echo read only = no >> /etc/samba/smb.conf'
    sudo(cmd, debug)

    cmd = 'echo browseable = yes >> /etc/samba/smb.conf'
    sudo(cmd, debug)

    cmd = 'service samba restart'
    sudo(cmd, debug)

def setup_monit():
    pass

def setup_sysd(service_file):
    fabric.api.put(service_file, '/etc/systemd/system')

    cmd = 'systemctl enable home-assistant'
    sudo(cmd, debug)

    cmd = 'systemctl start home-assistant'
    sudo(cmd, debug)


# Main
# --------------------------------------------------------------------------
def install_all():
    # setup wifi
    # allow ssh
    # set hostname/timezone/keyboard/wifi country/locale
    # make sure doesn't automatically login as pi

    libs = config['system_libs']
    users = config['users']
    dirs = config['user_dirs']
    aliases = config['user_aliases']
    shortcuts = pyenv_shortcuts.split('\n')[1:-1]
    versions = python_versions.split()
    ha_user = [u for u in users if u.home_assistant_user == True][0]
    apps_allowed = config['firewall_allowed']

    apt_get(libs)
    setup_users(users, dirs, aliases)
    setup_pyenv(ha_user, users, pyenv_git_url, shortcuts)
    setup_python(ha_user, versions, current_python)
    setup_home_assistant(ha_user, ha_path, ha_url, src_dir_name, config_dir_name, venv_dir_name, config_url)
    setup_firewall(apps_allowed)
    setup_smb(users, ha_path, ha_folder_name)
    setup_sysd(service_file)



    #reboot()
    remove_pi_user()
    


