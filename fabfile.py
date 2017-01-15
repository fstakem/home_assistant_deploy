# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.12.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

import os

import fabric
from fabric.api import local, env, run, task, prefix, sudo

from config import config
from data_structures import DeployException
from data_structures import User
from helper import install_native
from helper import get_passwd
from helper import get_user_home_dir
from helper import get_passwords
from helper import switch_user
from helper import get_ha_user
from helper import get_admin_user


# Globals
# --------------------------------------------------------------------------
debug = False
root_path = os.path.dirname(os.path.realpath(__file__))


# Environment
# --------------------------------------------------------------------------
install_user = 'pi'
install_password = 'raspberry'
env.hosts = [config['system']['hostname']]
env.shell = "/bin/sh -c"
env.warn_only = True

switch_user(install_user, install_password)


# Setup functions
# --------------------------------------------------------------------------
@task
def install_system_apps():
    system_apps = config['system_apps']
    switch_user(install_user, install_password)
    install_native(system_apps)

@task
def install_python_libs():
    python_system_libs = config['python_system_libs']
    switch_user(install_user, install_password)
    install_native(python_system_libs)

@task
def create_users():
    users   = config['user']['accounts']
    dirs    = user_info['dirs']

    get_passwords(users)

    for user in users:
        switch_user(install_user, install_password)
        create_user(user)

        if not user.home_assistant_user:
            switch_user(user.name, user.password)
            create_user_dirs(user, dirs)

def create_user(user):
    if user.home_assistant_user:
        cmd = 'useradd -m -r %s' % (user.name)
        sudo(cmd)
    else:
        cmd = 'useradd -m %s -G sudo' % (user.name)
        sudo(cmd)

    cmd = 'echo "%s:%s" | sudo chpasswd' % (user.name, user.password)
    sudo(cmd)

def create_user_dirs(user, user_dirs):
    for dir in user_dirs:
        path = '/home/%s/%s' % (user.name, dir)
        cmd = 'mkdir -p %s' % path
        sudo(cmd)

    user_home = path = '/home/%s' % (user.name)
    cmd = 'chown -R %s:%s %s' % (user.name, user.name, user_home)
    sudo(cmd)

@task
def create_all_aliases():
    users       = config['user']['accounts']

    get_passwords(users)

    for user in users:
        switch_user(user.name, user.password)
        create_user_alias(user)

def create_user_alias(user):
    home_path   = get_user_home_dir(user.name)
    bashrc = os.path.join(home_path, '.bashrc')

    cmd = """echo '' >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo '# Aliases >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo 'alias ll=ls -l' >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo 'alias la=ls -la' >> {}""".format(bashrc)
    run(cmd)

@task
def cleanup_opt():
    unwanted_apps = ['minecraft-pi', 'sonic-pi', 'Wolfram']
    switch_user(install_user, install_password)

    for app in unwanted_apps:
        app_path = os.path.join('/opt', app)
        cmd = 'rm -rf {}'.format(app_path)
        sudo(cmd)

@task
def remove_pi_user():
    user_info = config['user']
    admin_user = get_admin_user(user_info)

    switch_user(admin_user.name, admin_user.password)

    cmd = 'deluser -r pi'
    sudo(cmd)

@task
def install_pyenv():
    user_info       = config['user']
    pyenv           = config['pyenv']
    python          = config['python']
    users           = user_info['accounts']
    git_url         = pyenv['git_url']
    git_update_url  = pyenv['update_git_url']
    
    pi_user = User(install_user, False)
    pi_user.password = install_password
    users.append(pi_user)
    get_passwords(users)

    for user in users:
        switch_user(user.name, user.password)

        home_path   = get_user_home_dir(user.name)
        pyenv_path  = os.path.join(home_path, '.pyenv')
        update_path = os.path.join(pyenv_path, 'plugins', 'pyenv-update')

        cmd = 'mkdir %s' % (pyenv_path)
        run(cmd)

        cmd = 'git clone %s %s' % (git_url, pyenv_path)
        run(cmd)

        update_path = os.path.join(pyenv_path, 'plugins', 'pyenv-update')
        cmd = 'git clone %s %s' % (git_update_url, update_path)
        run(cmd)

        setup_pyenv(user)
        setup_python(user, python)

def setup_pyenv(user):
    home_path = get_user_home_dir(user.name)
    bashrc = os.path.join(home_path, '.bashrc')

    cmd = """echo '' >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo '# Pyenv setup' >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo 'export PYENV_ROOT="$HOME/.pyenv"' >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo 'eval "$(pyenv init -)"' >> {}""".format(bashrc)
    run(cmd)

def setup_python(user, python):
    home_path       = get_user_home_dir(user.name)
    pyenv_path      = os.path.join(home_path, '.pyenv')
    versions        = python['versions']
    current_version = python['current_version']

    if current_version not in versions:
        raise DeployException('Current version of python not in python list')

    cmd1 = 'PYENV_ROOT="{}"'.format(pyenv_path)
    cmd2 = 'PATH="$PYENV_ROOT/bin:$PATH"'
    cmd3 = 'eval "$(pyenv init -)"'
    cmd_str = '{}; {}; {}'.format(cmd1, cmd2, cmd3)

    with prefix(cmd_str):
        for version in versions:
            cmd = 'pyenv install %s' % (version)
            run(cmd)

        cmd = 'pyenv global %s' % (current_version)
        run(cmd)

@task
def install_home_assistant():
    user_info       = config['user']
    home_assistant  = config['home_assistant']
    git_src_url     = home_assistant['git_src_url']
    root_path       = home_assistant['root_dir']
    source_dir      = home_assistant['source_dir']
    venv_dir        = home_assistant['venv_dir']
    config_dir      = home_assistant['config_dir']
    git_config_url  = home_assistant['git_config_url']
    ha_user         = get_ha_user(user_info)

    switch_user(install_user, install_password)

    ha_path = os.path.join('/srv', root_path)
    cmd = 'mkdir %s' % (ha_path)
    sudo(cmd)

    cmd = 'chown -R {}:{} {}'.format(ha_user.name, ha_user.name, ha_path)
    sudo(cmd)

    switch_user(ha_user.name, ha_user.password)

    src_path = os.path.join(ha_path, source_dir)
    cmd = 'mkdir %s' % (src_path)
    run(cmd)

    cmd = 'git clone %s %s' % (git_src_url, src_path)
    run(cmd)

    config_path = os.path.join(ha_path, config_dir)
    cmd = 'mkdir %s' % (config_path)
    run(cmd)

    if git_config_url:
        cmd = 'git clone %s %s' % (git_config_url, config_path)
        run(cmd)

    install_home_assistant_deps()

@task
def install_home_assistant_deps():
    user_info       = config['user']
    home_assistant  = config['home_assistant']
    venv_dir        = home_assistant['venv_dir']
    root_path       = home_assistant['root_dir']
    source_dir      = home_assistant['source_dir']
    pyenv           = config['pyenv']
    python          = config['python']
    ha_user         = get_ha_user(user_info)
    home_path       = get_user_home_dir(ha_user.name)
    pyenv_path      = os.path.join(home_path, '.pyenv')
    ha_path         = os.path.join('/srv', root_path)
    src_path        = os.path.join(ha_path, source_dir)

    switch_user(ha_user.name, ha_user.password)

    cmd1 = 'PYENV_ROOT="{}"'.format(pyenv_path)
    cmd2 = 'PATH="$PYENV_ROOT/bin:$PATH"'
    cmd3 = 'eval "$(pyenv init -)"'
    cmd_str = '{}; {}; {}'.format(cmd1, cmd2, cmd3)

    with prefix(cmd_str):
        cmd = 'pip install virtualenv'
        run(cmd)

        cmd = 'cd {}'.format(ha_path)

        with prefix(cmd):
            cmd = 'virtualenv %s' % (venv_dir)
            run(cmd)

            venv_path = os.path.join(ha_path, venv_dir)
            venv_activate = os.path.join(venv_path, 'bin', 'activate')
            cmd = '. {}'.format(venv_activate)

            with prefix(cmd):
                cmd = 'pip install -e %s' % (src_path)
                run(cmd)

def setup_sysd(service_file):
    fabric.api.put(service_file, '/etc/systemd/system', use_sudo=True)

    cmd = 'systemctl enable home-assistant'
    sudo(cmd)

    cmd = 'systemctl start home-assistant'
    sudo(cmd)

def setup_firewall(firewall):
    packages = ['ufw', 'GUFW']
    install_native(packages)

    cmd = 'ufw default deny incoming'
    sudo(cmd)

    cmd = 'ufw default allow outgoing'
    sudo(cmd)

    for app in firewall['allowed']:
        cmd = 'ufw allow %s' % (app)
        sudo(cmd)

    cmd = 'ufw enable'
    sudo(cmd)

def setup_smb(user_info, smb):
    packages = ['samba', 'samba-common-bin']
    install_native(packages)
    # passwords
    # TODO

    cmd = 'echo >> /etc/samba/smb.conf'
    sudo(cmd)

    cmd = 'echo [%s] >> /etc/samba/smb.conf' % (ha_folder_name)
    sudo(cmd)

    cmd = 'echo path = %s >> /etc/samba/smb.conf' % (ha_path)
    sudo(cmd)

    valid_users = [user.name for user in users]
    user_str = ' '.join(valid_users)
    cmd = 'echo valid users = %s >> /etc/samba/smb.conf' % (user_str)
    sudo(cmd)

    cmd = 'echo read only = no >> /etc/samba/smb.conf'
    sudo(cmd)

    cmd = 'echo browseable = yes >> /etc/samba/smb.conf'
    sudo(cmd)

    cmd = 'service samba restart'
    sudo(cmd)

def setup_monit():
    packages = ['monit']
    install_native(packages)

@task
def test():
    with prefix('. /home/pi/test_env/bin/activate'):
        run('which python')

    switch_user('fstakem', 'f')
    run('pwd')

    switch_user('hass', 'f')
    run('pwd')

    switch_user(install_user, install_password)
    run('pwd')
    


# Main
# --------------------------------------------------------------------------
@task
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
    #   9.  Overclock pi

    create_users()
    create_all_aliases()
    install_system_apps()
    install_python_libs()
    cleanup_opt()
    install_pyenv()
    install_home_assistant()
    install_home_assistant_deps()
    #setup_sysd(service_file)

    if firewall['enable']:
        setup_firewall(firewall)

    if smb['enable']:
        setup_smb(user_info, smb)
    
    if monit['enable']:
        setup_monit()

    #reboot()
    #remove_pi_user()
    


