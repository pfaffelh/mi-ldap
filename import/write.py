# We write data from the MongoDB into the LDAP

import netrc, pymongo, datetime
from ldap3 import Server, Connection, ALL, SUBTREE, BASE
from ldap3.core.exceptions import LDAPException, LDAPEntryAlreadyExistsResult

# This is the MongoDB
cluster = pymongo.MongoClient("mongodb://127.0.0.1:27017")
mongo_db = cluster["vvz"]
per = mongo_db["person"]
percode = mongo_db["personencode"]
percodekategorie = mongo_db["personencodekategorie"]

try:
    persons = list(per.find({"ldap" : True, "$or": [
                    {"ausstiegsdatum": None},
                    {"ausstiegsdatum": {"$gt": datetime.datetime.now()}}
                ]}))

    # Nur Abteilungen geben Gruppen
    abt = percodekategorie.find_one({"name_de" : "Abteilung"})["_id"]
    codes = list(percode.find({"codekategorie" : abt}))
    groups = {c["name"] : [str(p["_id"]) for p in per.find({"code" : c["_id"]})] for c in codes}
except: 
    raise RuntimeError("**Verbindung zur MongoDB nicht möglich!**  \nKontaktieren Sie den Administrator.")

netrc = netrc.netrc()

LDAP_URI_local = 'ldap://localhost:389'  
LDAP_URI_www2 = 'ldap://home.mathematik.uni-freiburg.de' 
LDAP_URI_www3 = 'ldap://www3.mathematik.privat' 
LDAP_URI = LDAP_URI_local

ldap_username, ldap_account, ldap_password = netrc.authenticators(LDAP_URI)
print(f"Username: {ldap_username}")
BIND_DN = f"cn={ldap_username},dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
BIND_PW = ldap_password  

BASE_DN = "dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
PEOPLE_DN = f"ou=People,{BASE_DN}"
GROUPS_DN = f"ou=Groups,{BASE_DN}"

def insert_data():
    server = Server(LDAP_URI, get_info=ALL)

    # Simple Bind
    conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

    # Insert People
    for p in persons:
        ok = conn.add(
            dn=f"cn={str(p['_id'])},{GROUPS_DN}",
            object_class=["top", "inetOrgPerson"],
            attributes={
                'sn': p.get('name', ""),
                'givenName': p.get('vorname', ''),                  
                'displayName': f"{p.get('name')}, {p.get('vorname')}", 
                'mail': p.get('email1'),
                'tel': p.get('tel1')
            })

    # Insert groups
    for group, members in groups.items():
        if members != []:
            ok = conn.add(
                dn=f"cn={group},{GROUPS_DN}",
                object_class=["top", "groupOfNames"],
                attributes={
                    "cn": group,
                    "member": [f"cn={x},{PEOPLE_DN}" for x in members],
                }
            )

if __name__ == "__main__":
    insert_data()


