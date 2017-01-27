# --------------------------------------< HEADER >--------------------------------------
#
#       Home Assistant Installer for Raspberry Pi
#       By: Fredrick Stakem
#       Date: 12.19.16
#
# --------------------------------------|~~~~~~~~|--------------------------------------


class User(object):

    def __init__(self, name, home_assistant_user, admin_user):
        self.name = name
        self.home_assistant_user = home_assistant_user
        self.admin_user = admin_user
        self.password = None

        if self.home_assistant_user:
            self.admin_user = False

        if self.admin_user:
            self.home_assistant_user = False

    def __repr__(self):
        return 'User(%s, %s, %s)' % (self.name, self.home_assistant_user, self.admin_user)

    def __str__(self):
        return 'User<%s>' % (self.name)

class MosquittoUser(object):

    def __init__(self, name):
        self.name = name
        self.password = None

class DeployException(Exception):
    pass
