# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.12.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

from fabric.api import local
from collections import namedtuple
from getpass import getpass


# Data
# --------------------------------------------------------------------------
system_libs = """
vim
tmux
gedit
kate
tig
ufw
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

User = namedtuple('User', 'name, user_type')
users = (User('hass', 'service'), User('fstakem', 'admin'))


# Helper functions
# --------------------------------------------------------------------------
def apt_get(packages):
    cmd = 'apt-get -qy install %s' % ' '.join(packages)
    print(cmd)
    #sudo(cmd, shell=False)

def get_passwd(username):
    first_pw = getpass('Enter password for %s: ' % (username))
    second_pw = getpass('Renter the password for %s: ' % (username))

    if first_pw != second_pw:
        pass


# Setup functions
# --------------------------------------------------------------------------
def setup_users():
    pass

# remove pi user


# install libs for python
def setup_python_required():
    pass

# install pyenv
def setup_pyenv():
    pass

# install python
def setup_python():
    pass

# install home assistant
def setup_ha_code():
    pass

# install home assistant config
def setup_ha_config():
    pass

# install smb
def setup_smb():
    pass

# Setup and install firewall(ufw)
def setup_firewall():
    apt_get('ufw')

# install monit
def setup_monit():
    pass


# Main
# --------------------------------------------------------------------------
def install_all():
    get_passwd('testy')
    apt_get(system_libs.split())


