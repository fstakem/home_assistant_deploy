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

# Read config json
config = None
config_file = 'config.json'
with open(config_file) as config_data:    
    config = json.load(config_data)

# Create users
users = []

for raw_user in config['user']['accounts']:
    user = User(raw_user['name'], raw_user['type'], raw_user['ha_user'])
    users.append(user)

config['user']['accounts'] = users


