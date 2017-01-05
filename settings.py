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


config_file = 'config.json'
with open(config_file) as config_data:    
    config = json.load(config_data)

config['ha_path'] = os.path.join('/srv', config['ha_folder_name'])

users = []

for raw_user in config['users']:
    user = User(raw_user['name'], raw_user['type'], raw_user['ha_user'])
    users.append(user)

config['users'] = users



