# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.19.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------

import os
import json

from data_structures import User
from data_structures import MosquittoUser
from helper import get_passwords

# Read config json
config = None
config_file = 'config.json'
with open(config_file) as config_data:    
    config = json.load(config_data)

# Create users
users = []

for raw_user in config['user']['accounts']:
    user = User(raw_user['name'], raw_user['ha_user'], raw_user['admin_user'])
    users.append(user)

get_passwords(users)

config['user']['accounts'] = users


# Create mosquitto users
users = []

for raw_name in config['mqtt']['users']:
    user = MosquittoUser(raw_name)
    users.append(user)

get_passwords(users)

config['mqtt']['users'] = users
