# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 1.14.17
#
# --------------------------------------|~~~~~~~~|--------------------------------------


from getpass import getpass
from fabric.api import sudo, run, env


# Helper functions
# --------------------------------------------------------------------------
def install_native(packages):
    cmd = 'apt-get update'
    sudo(cmd)

    cmd = 'apt-get -qy install %s' % ' '.join(packages)
    sudo(cmd)

def get_passwd(username):
    tries = 3
    first_pw = getpass('Enter password for %s: ' % (username))
    second_pw = getpass('Renter the password for %s: ' % (username))

    for _ in range(tries):
        if first_pw == second_pw:
            return first_pw

    raise ValueError

def get_user_home_dir(username):
    path = None

    cmd = 'grep {} /etc/passwd'.format(username)
    output = run(cmd)
    tokens = output.split(':')

    if len(tokens) > 5:
        path = tokens[5]
   
    return path

def get_passwords(users):
    for user in users:
    	if not user.password:
	        try:
	            user.password = get_passwd(user.name)
	        except ValueError:
	            pass

def switch_user(user, password):
    env.user = user
    env.password = password

def get_ha_user(user_info):
    users = user_info['accounts']
    ha_user = [u for u in users if u.home_assistant_user == True][0]

    return ha_user

def get_admin_user(user_info):
    users = user_info['accounts']
    admin_user = [u for u in users if u.home_assistant_user == False][0]

    return admin_user