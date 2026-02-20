from ldap3 import Server, Connection, ALL, SUBTREE
import json

# writes ldap.json

# Subsequently, this can be used in mi-vvz/change20260301.py in order to get the data into the mongodb

# URL des öffentlichen LDAP-Servers
ldap_server = 'ldap://home.mathematik.uni-freiburg.de'  # Beispiel für einen öffentlichen LDAP-Server

# LDAP-Baum und Suchbasis
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

with open('ldap.json', 'w') as json_file:
    json.dump(result_list, json_file, indent=4)
