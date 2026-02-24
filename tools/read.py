# We are reading the data from the www2-ldap and store it in mi-ldap.json

from ldap3 import Server, Connection, ALL, SUBTREE
import json

# URL des öffentlichen LDAP-Servers
LDAP_URI_local = 'ldap://localhost:389'  
LDAP_URI_www2 = 'ldap://home.mathematik.uni-freiburg.de' 
LDAP_URI_www3 = 'ldap://www3.mathematik.privat' 
LDAP_URI = LDAP_URI_www3

# LDAP-Baum und Suchbasis für "People"
search_base = 'ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de'  # Der Startpunkt für die LDAP-Suche
search_filter = '(objectClass=*)'  # Beispielhafter Filter, um alle Personenobjekte zu suchen

# Verbindung zum LDAP-Server ohne Authentifizierung herstellen (anonyme Bindung)
server = Server(LDAP_URI, get_info=ALL)
conn = Connection(server, auto_bind=True)  # Keine Anmeldeinformationen erforderlich
if LDAP_URI == LDAP_URI_www2:
    attributes = ['cn', 'sn', 'ou', 'eduPersonPrimaryAffiliation','mail', 'labeledURI', 'givenName', 'objectClass', 'eduPersonPrimaryAffiliation', 'street', 'telephoneNumber', 'roomNumber', 'personalTitle'] 
if LDAP_URI == LDAP_URI_local:
    attributes = ['cn', 'sn', 'mail', 'givenName', 'objectClass', 'telephoneNumber', "member"] 


# Suche im LDAP-Baum durchführen
conn.search(search_base, search_filter, search_scope=SUBTREE, attributes=attributes)

# Liste für die Ergebnisse
result_list = []

# Ergebnisse in eine Liste von Dictionaries umwandeln
for entry in conn.entries:
    entry_dict = {attr: entry[attr].value for attr in attributes if attr in entry}
    result_list.append(entry_dict)

# Verbindung beenden
conn.unbind()

# Ergebnisse anzeigen
print(result_list)

with open('mi-ldap.json', 'w') as json_file:
    json.dump(result_list, json_file, indent=4)


