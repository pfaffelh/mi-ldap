# We delete everything in an LDAP below People and Groups

import netrc, pymongo, datetime, argparse
from ldap3 import Server, Connection, ALL, SUBTREE, BASE
from ldap3.core.exceptions import LDAPException, LDAPEntryAlreadyExistsResult

# Keine Ausgabe falls --quiet
parser = argparse.ArgumentParser()
parser.add_argument("--quiet", action="store_true", help="Unterdrücke Ausgaben")
parser.add_argument("--local", action="store_true", help="Benutze lokale Datenbank")
args = parser.parse_args()

print = (lambda *a, **k: None) if args.quiet else print

if args.local:
    LDAP_URI = 'ldap://localhost:389'
else:
    LDAP_URI = 'ldap://www3.mathematik.privat' 

# LDAP_URI_www2 = 'ldap://home.mathematik.uni-freiburg.de' 

# This is the MongoDB
cluster = pymongo.MongoClient("mongodb://127.0.0.1:27017")
mongo_db = cluster["vvz"]
per = mongo_db["person"]
percode = mongo_db["personencode"]
percodekategorie = mongo_db["personencodekategorie"]

try:
    persons = list(per.find({"$or": [
                    {"ausstiegsdatum": None},
                    {"ausstiegsdatum": {"$gt": datetime.datetime.now()}}
                ]}))
    codes = list(percode.find({}))
    # p[groups] enthält die Abteilungen/Codes, zu denen p gehört
    for p in persons:
        p["groups"] = [c["name"] for c in codes if c["_id"] in p["code"]]
except: 
    raise RuntimeError("**Verbindung zur MongoDB nicht möglich!**  \nKontaktieren Sie den Administrator.")

netrc = netrc.netrc()

ldap_username, ldap_account, ldap_password = netrc.authenticators(LDAP_URI)
BIND_DN = f"cn={ldap_username},dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
BIND_PW = ldap_password  

BASE_DN = "dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
PEOPLE_DN = f"ou=People,{BASE_DN}"

server = Server(LDAP_URI)

def delete():
    conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

    # Alle Einträge unterhalb suchen
    conn.search(
        search_base=PEOPLE_DN,
        search_filter="(objectClass=*)",
        search_scope=SUBTREE
    )

    # DNs sammeln
    dns = [entry.entry_dn for entry in conn.entries if entry.entry_dn != BASE_DN]

    # Tiefste Einträge zuerst löschen
    for dn in sorted(dns, key=lambda x: x.count(","), reverse=True):
        print("Lösche:", dn)
        conn.delete(dn)
    print("Alles unterhalb People gelöscht!.")


# We write data from the MongoDB into the LDAP
def insert_data():
    server = Server(LDAP_URI, get_info=ALL)

    # Simple Bind
    conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

    # Insert People
    for p in persons:
        # print(p)
        if p.get('name', "") != "" and p.get('vorname', '') != "":
            dn = f"cn={str(p['_id'])},{PEOPLE_DN}"
            #print(p.get('tel1', ''))
            attributes = {
                    'cn' : str(p['_id']),
                    'sn': p.get('name', ""),
                    'givenName': p.get('vorname', ''),                  
                    'displayName': f"{p.get('name')}, {p.get('vorname')}", 
                    'mail': p.get('email1')
                }
            if p["tel1"] != "":
                attributes["telephoneNumber"] = p.get('tel1', '')
            if p["tel2"] != "":
                attributes["homePhone"] = p.get('tel2', '')
            if p['groups'] != []:
                attributes["employeeType"] = p['groups']
            ok = conn.add(
                dn=dn,
                object_class=["top", "inetOrgPerson"],
                attributes = attributes)
            if ok:
                print(f"Neuer Eintrag: {p.get('name')}, {p.get('vorname')}")
            else:
                print(f"Error inserting {p.get('name')}, {p.get('vorname')}")
                #print(attributes)
                #print(dn)        
                #print(conn.result)

if __name__ == "__main__":
    delete()
    insert_data()

# Alle Einträge gibt es lokal mit
# ldapsearch -x -H ldap://localhost:389 -b "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de"   -s sub "(objectClass=*)"

# Alle Einträge gibt es auf www3 mit
# ldapsearch -x -H ldap://www3.mathematik.privat -b "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de" -s sub "(objectClass=*)"

# nur RM gibt es mit 
# ldapsearch -x -H ldap://localhost:389 -b "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de"   -s sub "(employeeType=RM)"

# bzw
# ldapsearch -x -H ldap://www3.mathematik.privat -b "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de"   -s sub "(employeeType=RM)"

