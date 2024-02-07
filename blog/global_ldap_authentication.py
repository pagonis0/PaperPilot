from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError

import ssl,re
from ldap3.core.tls import Tls


def global_ldap_authentication(user_name, user_pwd):
    """
      Function: global_ldap_authentication
       Purpose: Make a connection to encrypted LDAP server.
       :params: ** Mandatory Positional Parameters
                1. user_name - LDAP user Name
                2. user_pwd - LDAP User Password
       :return: None
    """

    ldap_user_name = user_name.strip()
    ldap_user_pwd = user_pwd.strip()
    tls_configuration = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
    server = Server('ldaps://rodc.thi.de:636', use_ssl=True, tls=tls_configuration)
    conn = Connection(server, user=ldap_user_name, password=ldap_user_pwd, authentication=NTLM,
                      auto_referrals=False)
    if not conn.bind():
        print(f" *** Cannot bind to ldap server: {conn.last_error} ")
        return ' ** Failed Authentication}: {conn.last_error}'
    else:
        print(f" *** Successful bind to ldap server")
        return 'Success'
    return

def global_ldap_authentication_uid(user_name, user_pwd, login_username):
    """
      Function: global_ldap_authentication
       Purpose: Make a connection to encrypted LDAP server.
       :params: ** Mandatory Positional Parameters
                1. user_name - LDAP user Name
                2. user_pwd - LDAP User Password
       :return: None
    """

    ldap_user_name = user_name.strip()
    ldap_user_pwd = user_pwd.strip()
    tls_configuration = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
    server = Server('ldaps://rodc.thi.de:636', use_ssl=True, tls=tls_configuration)
    conn = Connection(server, user=ldap_user_name, password=ldap_user_pwd, authentication=NTLM,
                      auto_referrals=False)
    if not conn.bind():
        print(f" *** Cannot bind to ldap server: {conn.last_error} ")
        return 'Fail!'
    else:
        print(f" *** Successful bind to ldap server")
        conn.search('dc=rz,dc=fh-ingolstadt,dc=de','(cn=%s)'%login_username,attributes = ['uidNumber'])
        search_result = str(conn.entries)
        pattern = r"uidNumber:\s*(\d+)"
        match = re.search(pattern, search_result)
        if match:
            uid_number = int(match.group(1))
            print(uid_number)
        return uid_number
    return



def global2_ldap_authentication(user_name, user_pwd):
    """
      Function: global_ldap_authentication
       Purpose: Make a connection to encrypted LDAP server.
       :params: ** Mandatory Positional Parameters
                1. user_name - LDAP user Name
                2. user_pwd - LDAP User Password
       :return: None
    """

    # fetch the username and password
    ldap_user_name = user_name.strip()
    ldap_user_pwd = user_pwd.strip()

    # ldap server hostname and port
    ldsp_server = f"ldaps://rodc.thi.de:636"

    # dn
    root_dn = "dc=example,dc=org"

    # user
    user = f'cn={ldap_user_name},{root_dn}'

    print(user)
    server = Server(ldsp_server, get_info=ALL)

    connection = Connection(server,
                            user=user,
                            password=ldap_user_pwd)
    if not connection.bind():
        print(f" *** Cannot bind to ldap server: {connection.last_error} ")
        l_success_msg = f' ** Failed Authentication: {connection.last_error}'
    else:
        print(f" *** Successful bind to ldap server")
        l_success_msg = 'Success'

    return l_success_msg
