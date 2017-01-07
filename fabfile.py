# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.12.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

import os
import fabric
from fabric.api import local, env
#from fabric.operations import put
from collections import namedtuple
from getpass import getpass


from settings import config
from data_structures import DeployException

# Globals
# --------------------------------------------------------------------------
debug = False
root_path = os.path.dirname(os.path.realpath(__file__))


# Environment
# --------------------------------------------------------------------------
env.user = 'pi'
env.hosts = [config['system']['hostname']]
env.password = 'pi'
#env.password = 'raspberry'


# Helper functions
# --------------------------------------------------------------------------
def sudo(cmd, debug=False):
    if debug:
        print('Run: {}'.format(cmd))
    else:
        fabric.api.sudo(cmd)

def install_native(packages):
    cmd = 'apt-get update'
    sudo(cmd, debug)
    
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
def setup_users(user_info):
    users   = user_info['accounts']
    dirs    = user_info['dirs']

    get_passwords(users)

    for user in users:
        create_account(user)

        if user.account_type == 'admin':
            create_dirs(user, dirs)

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

    cmd = 'echo "%s:%s" | sudo chpasswd' % (user.name, user.password)
    sudo(cmd, debug)

def create_dirs(user, user_dirs):
    for dir in user_dirs:
        path = '/home/%s/%s' % (user.name, dir)
        cmd = 'mkdir -p %s' % path
        sudo(cmd, debug)

        cmd = 'chown %s:%s %s' % (user.name, user.name, path)
        sudo(cmd, debug)

def remove_pi_user():
    cmd = 'deluser -r pi'
    sudo(cmd, debug)

def get_ha_user(user_info):
    users = user_info['accounts']
    ha_user = [u for u in users if u.home_assistant_user == True][0]

    return ha_user

def setup_pyenv(user_info, pyenv):
    ha_user         = get_ha_user(user_info)
    pyenv_path      = pyenv['dir']
    git_url         = pyenv['git_url']
    shortcuts       = pyenv['shortcuts']
    git_update_url  = pyenv['update_git_url']

    cmd = 'su %s' % (ha_user.name)
    sudo(cmd, debug)

    cmd = 'mkdir %s' % (pyenv_path)
    sudo(cmd, debug)

    cmd = 'git clone %s %s' % (git_url, pyenv_path)
    sudo(cmd, debug)

    update_path = os.path.join(pyenv_path, 'plugins', 'pyenv-update')
    cmd = 'git clone %s %s' % (git_update_url, update_path)
    sudo(cmd, debug)

    cmd = 'exit'
    sudo(cmd, debug)
    
    add_pyenv_system_shortcuts(shortcuts)
    users = [u for u in user_info['accounts'] if u.account_type != 'system']
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

def setup_python(user_info, python):
    ha_user         = get_ha_user(user_info)
    versions        = python['versions']
    current_version = python['current_version']

    if current_version not in versions:
        raise DeployException('Current version of python not in python list')

    cmd = 'su %s' % (ha_user.name)
    sudo(cmd, debug)

    cmd = 'source /etc/bash.bashrc'
    sudo(cmd, debug)

    for version in versions:
        cmd = 'pyenv install %s' % (version)
        sudo(cmd, debug)

    cmd = 'pyenv global %s' % (current_version)
    sudo(cmd, debug)

    cmd = 'exit'
    sudo(cmd, debug)

def setup_home_assistant(user_info, home_assistant):
    ha_user         = get_ha_user(user_info)
    git_src_url     = home_assistant['git_src_url']
    root_path       = home_assistant['root_dir']
    source_dir      = home_assistant['source_dir']
    venv_dir        = home_assistant['venv_dir']
    config_dir      = home_assistant['config_dir']
    git_config_url  = home_assistant['git_config_url']

    cmd = 'su %s' % (ha_user.name)
    sudo(cmd, debug)

    ha_path = os.path.join('/srv', root_path)
    cmd = 'mkdir %s' % (ha_path)
    sudo(cmd, debug)

    src_path = os.path.join(ha_path, source_dir)
    cmd = 'mkdir %s' % (src_path)
    sudo(cmd, debug)

    cmd = 'git clone %s %s' % (git_src_url, src_path)
    sudo(cmd, debug)

    config_path = os.path.join(ha_path, config_dir)
    cmd = 'mkdir %s' % (config_path)
    sudo(cmd, debug)

    if git_config_url:
        cmd = 'git clone %s %s' % (git_config_url, config_path)
        sudo(cmd, debug)

    venv_path = os.path.join(ha_path, venv_dir)
    cmd = 'virtualenv %s' % (venv_path)
    sudo(cmd, debug)

    activate_path = os.path.join(venv_path, 'bin', 'activate')
    cmd = 'source %s' % (activate_path)
    sudo(cmd, debug)

    cmd = 'pip install -e %s' % (src_path)
    sudo(cmd, debug)

    cmd = 'exit'
    sudo(cmd, debug)

def setup_sysd(service_file):
    fabric.api.put(service_file, '/etc/systemd/system', use_sudo=True)

    cmd = 'systemctl enable home-assistant'
    sudo(cmd, debug)

    cmd = 'systemctl start home-assistant'
    sudo(cmd, debug)

def setup_firewall(firewall):
    packages = ['ufw', 'GUFW']
    install_native(packages)

    cmd = 'ufw default deny incoming'
    sudo(cmd, debug)

    cmd = 'ufw default allow outgoing'
    sudo(cmd, debug)

    for app in firewall['allowed']:
        cmd = 'ufw allow %s' % (app)
        sudo(cmd, debug)

    cmd = 'ufw enable'
    sudo(cmd, debug)

def setup_smb(user_info, smb):
    packages = ['samba', 'samba-common-bin']
    install_native(packages)
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
    packages = ['monit']
    install_native(packages)


# Main
# --------------------------------------------------------------------------
def install_all():
    # Manual steps(sudo raspi-config):
    #   1.  Expand filesystem
    #   2.  Change hostname
    #   3.  Enable ssh
    #   4.  Change locale
    #   5.  Change timezone
    #   6.  Change keyboard layout
    #   7.  Change wifi country
    #   8.  Setup wifi password

    user_info           = config['user']
    system_apps         = config['system_apps']
    python_system_libs  = config['python_system_libs']
    pyenv               = config['pyenv']
    python              = config['python']
    home_assistant      = config['home_assistant']
    firewall            = config['firewall']
    smb                 = config['smb']
    monit               = config['monit']
    
    setup_users(user_info)
    install_native(system_apps)
    install_native(python_system_libs)
    setup_pyenv(user_info, pyenv)
    setup_python(user_info, python)
    setup_home_assistant(user_info, home_assistant)
    #setup_sysd(service_file)

    if firewall['enable']:
        setup_firewall(firewall)

    if smb['enable']:
        setup_smb(user_info, smb)
    
    if monit['enable']:
        setup_monit()

    #reboot()
    #remove_pi_user()
    


