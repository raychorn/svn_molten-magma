l_domains = []
l_domain_users = []

def is_running_locally():
    from vyperlogix.misc import _utils
    return _utils.getComputerName().lower() in ['rhorn-lap.ad.moltenmagma.com']

def is_running_securely():
    global l_domains
    from vyperlogix.win import computerSystem
    s = computerSystem.getComputerSystemSmartly()
    return s.UserName.lower().split('\\')[0] in l_domains

def is_running_securely_for_developers():
    global l_domain_users
    from vyperlogix.win import computerSystem
    s = computerSystem.getComputerSystemSmartly()
    return s.UserName.lower() in l_domain_users

