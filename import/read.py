# We are reading the data from the www2-ldap and store it in mi-ldap.py

from ldap3 import Server, Connection, ALL, SUBTREE
import json

# URL des öffentlichen LDAP-Servers
ldap_server = 'ldap://home.mathematik.uni-freiburg.de'  # Beispiel für einen öffentlichen LDAP-Server

# LDAP-Baum und Suchbasis für "People"
search_base = 'ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de'  # Der Startpunkt für die LDAP-Suche
search_filter = '(objectClass=*)'  # Beispielhafter Filter, um alle Personenobjekte zu suchen

# Verbindung zum LDAP-Server ohne Authentifizierung herstellen (anonyme Bindung)
server = Server(ldap_server, get_info=ALL)
conn = Connection(server, auto_bind=True)  # Keine Anmeldeinformationen erforderlich
attributes = ['cn', 'sn', 'ou', 'eduPersonPrimaryAffiliation','mail', 'labeledURI', 'givenName', 'objectClass', 'eduPersonPrimaryAffiliation', 'street', 'telephoneNumber', 'roomNumber', 'personalTitle'] 

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
