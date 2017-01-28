# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.12.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

import os

import fabric
from fabric.api import local, env, run, task, prefix, sudo, cd
from fabric.operations import put

from config import config
from data_structures import DeployException
from data_structures import User
from helper import install_native
from helper import get_user_home_dir
from helper import get_mosquitto_user

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
env.use_ssh_config = False

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
    user_info   = config['user']
    users       = user_info['accounts']
    dirs        = user_info['dirs']

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

    cmd = """echo "alias ll='ls -l'" >> {}""".format(bashrc)
    run(cmd)

    cmd = """echo "alias la='ls -la'" >> {}""".format(bashrc)
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
    
    pi_user = User(install_user, False, True)
    pi_user.password = install_password
    users.append(pi_user)

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
    use_git_config  = home_assistant['use_git_config']
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

    if use_git_config and git_config_url:
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

@task
def install_service():
    service_file = config['service_file']

    switch_user(install_user, install_password)
    put(service_file, '/etc/systemd/system/home-assistant.service', use_sudo=True)

    cmd = 'systemctl enable home-assistant'
    sudo(cmd)

    cmd = 'systemctl start home-assistant'
    sudo(cmd)

@task
def install_firewall():
    firewall = config['firewall']

    if firewall['enable']:
        switch_user(install_user, install_password)
        packages = ['ufw', 'GUFW']
        install_native(packages)

        cmd = 'ufw default deny incoming'
        sudo(cmd)

        cmd = 'ufw default allow outgoing'
        sudo(cmd)

        for app in firewall['allowed']:
            cmd = 'ufw allow %s' % (app)
            sudo(cmd)

        cmd = """echo "y" | sudo ufw enable"""
        run(cmd)

@task
def install_openzwave():
    user_info               = config['user']
    openzwave               = config['openzwave']
    openzwave_system_libs   = openzwave['system_libs']
    openzwave_python_libs   = openzwave['python_libs']
    openzwave_git_url       = openzwave['git_url']
    openzwave_dir           = openzwave['dir']
    home_assistant          = config['home_assistant']
    venv_dir                = home_assistant['venv_dir']
    root_path               = home_assistant['root_dir']
    ha_user                 = get_ha_user(user_info)
    ha_path                 = os.path.join('/srv', root_path)
    home_path               = get_user_home_dir(ha_user.name)
    pyenv_path              = os.path.join(home_path, '.pyenv')

    switch_user(install_user, install_password)
    install_native(openzwave_system_libs)

    openzwave_path = os.path.join('/srv', openzwave_dir)
    cmd = 'mkdir {}'.format(openzwave_path)
    sudo(cmd)

    cmd = 'chown -R {}:{} {}'.format(ha_user.name, ha_user.name, openzwave_path)
    sudo(cmd)

    switch_user(ha_user.name, ha_user.password)

    cmd1 = 'PYENV_ROOT="{}"'.format(pyenv_path)
    cmd2 = 'PATH="$PYENV_ROOT/bin:$PATH"'
    cmd3 = 'eval "$(pyenv init -)"'
    cmd_str = '{}; {}; {}'.format(cmd1, cmd2, cmd3)

    with prefix(cmd_str):
        cmd = 'cd {}'.format(ha_path)

        with prefix(cmd):
            cmd = 'virtualenv %s' % (venv_dir)
            run(cmd)

            venv_path = os.path.join(ha_path, venv_dir)
            venv_activate = os.path.join(venv_path, 'bin', 'activate')
            cmd = '. {}'.format(venv_activate)

            with prefix(cmd):
                cmd = 'pip install {}'.format(openzwave_python_libs)

            cmd = 'cd {}'.format(openzwave_path)

            with prefix(cmd_str):
                cmd = 'git clone {}'.format(openzwave_git_url)

                with cd("python-openzwave"):
                    cmd = 'git checkout --track origin/python3'
                    run(cmd)

                    cmd = 'make build'
                    run(cmd)

                    cmd = 'make install'
                    run(cmd)

@task
def install_micro_httpd():
    user_info               = config['user']
    home_assistant          = config['home_assistant']
    root_path               = home_assistant['root_dir']
    admin_user              = get_admin_user(user_info)
    libmicrohttpd           = config['libmicrohttpd']
    install_dir             = libmicrohttpd['install_dir']
    lib                     = libmicrohttpd['lib']
    ftp_site                = libmicrohttpd['ftp_site']
    system_libs             = libmicrohttpd['system_libs']

    switch_user(install_user, install_password)
    install_native(system_libs)

    install_path = os.path.join('/opt', install_dir)
    cmd = 'mkdir {}'.format(install_path)
    sudo(cmd)

    cmd = 'chown -R {}:{} {}'.format(admin_user.name, admin_user.name, install_path)
    sudo(cmd)

    switch_user(admin_user.name, admin_user.password)

    with cd(install_path):
        ftp_path = os.path.join(ftp_site, lib)
        cmd = 'wget {}'.format(ftp_path)
        run(cmd)

        cmd = 'tar zxvf {}'.format(lib)
        run(cmd)

        lib_dir = '.'.join(lib.split('.')[:-2])

        with cd(lib_dir):
            run('./configure')
            run('make')
            sudo('make install')

@task
def install_openzwave_ctrl():
    user_info               = config['user']
    ha_user                 = get_ha_user(user_info)
    ha_path                 = os.path.join('/srv', root_path)
    openzwave_ctrl          = config['openzwave_ctrl']
    install_dir             = openzwave_ctrl['install_dir']
    git_url                 = openzwave_ctrl['git_url']

    # TODO

    switch_user(install_user, install_password)
    
    install_path = os.path.join('/srv', install_dir)
    cmd = 'mkdir {}'.format(install_path)
    sudo(cmd)

    cmd = 'chown -R {}:{} {}'.format(ha_user.name, ha_user.name, install_path)
    sudo(cmd)

    switch_user(ha_user.name, ha_user.password)

    with cd(install_path):
        cmd = 'git clone {}'.format(git_url)
        run(cmd)

        with cd('open-zwave-control-panel'):
            put('./files/openzwave_ctrl_makefile', 'Makefile')
            run("make")

@task
def install_mqtt():
    user_info               = config['user']
    admin_user              = get_admin_user(user_info)
    mos_srv_user            = get_mosquitto_user(user_info)
    mqtt                    = config['mqtt']
    app_dir                 = mqtt['dir']
    system_libs             = mqtt['system_libs']
    users                   = mqtt['users']

    switch_user(admin_user.name, admin_user.password)

    app_path = os.path.join('/opt', app_dir)
    cmd = 'mkdir {}'.format(app_path)
    sudo(cmd)

    with cd(app_path):
        run("wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key")
        sudo("apt-key add mosquitto-repo.gpg.key")

        with cd("/etc/apt/sources.list.d/"):
            sudo("wget http://repo.mosquitto.org/debian/mosquitto-jessie.list")
            install_native(system_libs)

            with cd("/etc/mosquitto"):
                put("./files/mosquitto.conf", "mosquitto.conf", use_sudo=True)
                sudo('chown root:root mosquitto.conf')
                sudo("touch pwfile")

                cmd = 'chown {}:{} pwfile'.format(mos_srv_user.name, mos_srv_user.name)
                sudo(cmd)
                sudo("chmod 0600 pwfile")

                switch_user(mos_srv_user.name, mos_srv_user.password)

                for user in users:
                    cmd = 'sudo mosquitto_passwd -b pwfile {} {}'.format(user.name, user.password)
                    sudo(cmd)

    cmd = 'chown -R {}:{} {}'.format(mos_srv_user.name, mos_srv_user.name, app_path)
    sudo(cmd)

@task
def test():
    switch_user(install_user, install_password)
    with cd("/etc/mosquitto"):
        put("./files/mosquitto.conf", "test.conf", use_sudo=True)
    


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

    create_users()
    create_all_aliases()
    install_system_apps()
    install_python_libs()
    cleanup_opt()
    install_pyenv()
    install_home_assistant()
    install_home_assistant_deps()
    install_service()
    install_firewall()
    install_openzwave()
    install_micro_httpd()
    #install_openzwave_ctrl()
    install_mqtt()

@task
def deploy_dev():
    pass

@task
def deploy_prod():
    pass


# Testing OPENZWAVE-CTRL
# 1. Install sys libs libmicrohttpd
# 2. Install libmicrohttpd
# 3. Install sys libs openzwave-ctrl
# 4. Install openzwave-ctrl
    


