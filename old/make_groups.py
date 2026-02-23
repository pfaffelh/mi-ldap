from ldap3 import Server, Connection, ALL
import netrc

# URL des öffentlichen LDAP-Servers
LDAP_URI_local = 'ldap://localhost:389'  
LDAP_URI_www2 = 'ldap://home.mathematik.uni-freiburg.de' 
LDAP_URI_www3 = 'ldap://www3.mathematik.privat' 
LDAP_URI = LDAP_URI_local

netrc = netrc.netrc()
ldap_username, ldap_account, ldap_password = netrc.authenticators(LDAP_URI)
print(f"Username: {ldap_username}")
BIND_DN = f"cn={ldap_username},dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
BIND_PW = ldap_password  

server = Server(LDAP_URI)

conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

# Der DN für den Container
BASE_DN = "dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
#GROUPS_DN = f"ou=Groups,ou=People,{BASE_DN}"
GROUPS_DN = f"ou=Groups,{BASE_DN}"

# Attribute für eine Organizational Unit
ou_attrs = {
    'objectClass': ['top', 'organizationalUnit'],
    'description': 'Container für alle Benutzergruppen'
}

# Ausführung
if conn.add(GROUPS_DN, attributes=ou_attrs):
    print("Container 'ou=Groups' wurde erfolgreich erstellt.")
else:
    # Falls die OU schon existiert, bekommst du 'entryAlreadyExists' (Result 68)
    print(f"Fehler: {conn.result}")
