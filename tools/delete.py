# We delete everything in an LDAP below People and Groups

from ldap3 import Server, Connection, SUBTREE
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

# Die Einträge unterhalb dieser BASE_DNs sollen gelöscht werden
BASE_DN = "dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
PEOPLE_DN = f"ou=People,{BASE_DN}"
GROUPS_DN = f"ou=Groups,{BASE_DN}"

server = Server(LDAP_URI)

def delete():
    for BASE_DN in [GROUPS_DN, PEOPLE_DN]:
        conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

        # Alle Einträge unterhalb suchen
        conn.search(
            search_base=BASE_DN,
            search_filter="(objectClass=*)",
            search_scope=SUBTREE
        )

        # DNs sammeln
        dns = [entry.entry_dn for entry in conn.entries if entry.entry_dn != BASE_DN]

        # Tiefste Einträge zuerst löschen
        for dn in sorted(dns, key=lambda x: x.count(","), reverse=True):
            print("Lösche:", dn)
            conn.delete(dn)

    print("Alles unterhalb People, Groups gelöscht!.")


