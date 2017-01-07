# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.19.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------


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

class DeployException(Exception):
    pass
