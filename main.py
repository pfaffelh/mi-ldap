import socket, os, netrc
import pymongo
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE, ALL, BASE
import datetime

# TODO: Update groups!

# This is the MongoDB
cluster = pymongo.MongoClient("mongodb://127.0.0.1:27017")
mongo_db = cluster["vvz"]
per = mongo_db["person"]
percode = mongo_db["personencode"]

try:
    persons = list(per.find({"ldap" : True, "$or": [
                    {"ausstiegsdatum": None},
                    {"ausstiegsdatum": {"$gt": datetime.datetime.now()}}
                ]}))
    codes = list(percode.find({}))
    groups = {c["name"] : [str(p["_id"]) for p in per.find({"code" : c["_id"]})] for c in codes}
except: 
    raise RuntimeError("**Verbindung zur MongoDB nicht möglich!**  \nKontaktieren Sie den Administrator.")

# Get password for writing in LDAP
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
if (ip_address == "127.0.1.1"):
    netrc = netrc.netrc()
elif os.getcwd() == "/home/flask-reader/mi-hp":
    netrc = netrc.netrc("/home/flask-reader/netrc")
else:
    netrc = netrc.netrc("/usr/local/lib/mi-hp/.netrc")

# Here are the coordinates for LDAP
# LDAP_URI = "ldap://www3.mathematik.privat"
LDAP_URI = "ldap://localhost:389"
ldap_username, ldap_account, ldap_password = netrc.authenticators(LDAP_URI)
BIND_DN = f"cn={ldap_username},dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
BIND_PW = ldap_password 

BASE_DN = "dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
PEOPLE_DN = f"ou=People,{BASE_DN}"
GROUPS_DN = f"ou=Groups,{BASE_DN}"

def _norm_values(v):
    """ldap3 expects lists for multi-valued attributes in modify operations."""
    if v is None:
        return []  # replace with [] => remove attribute
    if isinstance(v, str):
        return [v]
    if isinstance(v, (list, tuple, set)):
        return [str(x) for x in v]
    return [str(v)]

# Update or insert an item cn for connection conn using attributes
def upsert_item(*, conn, cn, ou_dn, attributes, object_classes = None):
    """
    Upsert by cn:
      - search (cn=<cn>) under base_dn
      - if 1 match: modify (replace given attributes)
      - if 0 match: add under cn=<cn>,ou_dn with objectClasses and attributes
      - if >1 match: error

    Returns DN of the updated/created entry.
    """
    if object_classes is None:
        object_classes = [
            "top",
            "inetOrgPerson"
        ]

    # 1) SEARCH
    conn.search(search_base=BASE_DN, search_filter=f"(cn={cn})", search_scope=SUBTREE, attributes=None)

    if conn.result["result"] != 0:
        raise RuntimeError(f"LDAP search failed: {conn.result}")

    if len(conn.entries) > 1:
        dns = [e.entry_dn for e in conn.entries]
        raise RuntimeError(f"Mehr als ein Eintrag mit cn={cn}: {dns}")

    # Ensure required attributes exist for inetOrgPerson/person
    # (sn is usually mandatory; cn is mandatory too)
    add_attributes = dict(attributes)
    add_attributes.setdefault("cn", cn)
    add_attributes.setdefault("sn", cn)  # fallback; better set real surname

    # 2) UPDATE
    if len(conn.entries) == 1:
        dn = conn.entries[0].entry_dn
        # print(f"Update {dn}")
        changes = {k: [(MODIFY_REPLACE, _norm_values(v))] for k, v in attributes.items()}

        ok = conn.modify(dn, changes)
        if not ok:
            raise RuntimeError(f"LDAP modify failed: {conn.result}")
        return dn

    # 3) INSERT
    # print("Insert!")
    dn = f"cn={cn},{ou_dn}"
    # For add(), ldap3 accepts scalars or lists; we'll pass scalars for single values, lists for multi.
    normalized = {}
    for k, v in add_attributes.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple, set)):
            normalized[k] = [str(x) for x in v]
        else:
            normalized[k] = str(v)

    ok = conn.add(dn, object_classes, normalized)
    if not ok:
        raise RuntimeError(f"LDAP add failed: {conn.result}")
    return dn


def delete_unused_persons(*, conn):
    """
    Delete if cn not element of Upsert by cn:
      - search (cn=<cn>) under base_dn
      - if 1 match: modify (replace given attributes)
      - if 0 match: add under cn=<cn>,people_ou_dn with objectClasses and attributes
      - if >1 match: error

    Returns DN of the updated/created entry.
    """

    # Liste der erlaubten CNs (Sollzustand)
    valid_cns = [str(a["_id"]) for a in persons]

    # alle aktuellen Einträge holen
    conn.search(
        search_base=PEOPLE_DN,
        search_filter="(objectClass=inetOrgPerson)",
        search_scope=SUBTREE,
        attributes=["cn"]
    )

    for entry in conn.entries:
        cn = str(entry.cn)

        if cn not in valid_cns:
            print("Deleting:", entry.entry_dn)

            conn.delete(entry.entry_dn)

            if not conn.result["description"] == "success":
                print("Delete failed:", conn.result)

def synchonize_ldap():
    server = Server(LDAP_URI, get_info=ALL)

    # Simple Bind
    conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

    for p in persons:
        attributes = {
            'objectClass': ['top', 'inetOrgPerson'],
            'sn': p.get('name'),                                # Pflichtfeld
            'givenName': p.get('vorname', ''),                  # Vorname für die Suche
            'displayName': f"{p.get('name')}, {p.get('vorname')}", # Das zeigt der Drucker an
            'ou': p.get('ou', None),                   # Abteilung
            'mail': p.get('email')                              # Ziel für Scan-to-Email
        }
        dn = upsert_item(
            conn=conn,
            cn=str(p['_id']),
            ou_dn = PEOPLE_DN,
            attributes=attributes,
        )

    # TODO: upsert groups
    for g in groups:
        attributes = {
            'objectClass': ['top', 'inetOrgPerson'],
            'sn': p.get('name'),                                # Pflichtfeld
            'givenName': p.get('vorname', ''),                  # Vorname für die Suche
            'displayName': f"{p.get('name')}, {p.get('vorname')}", # Das zeigt der Drucker an
            'ou': p.get('ou', None),                   # Abteilung
            'mail': p.get('email')                              # Ziel für Scan-to-Email
        }
        dn = upsert_item(
            conn=conn,
            cn=str(p['_id']),
            ou_dn = GROUPS_DN,
            attributes=attributes,
        )

        continue
        # print("OK:", dn)

    for group, members in groups.items():
        group_dn = f"cn={group},{GROUPS_DN}"

        # gewünschte Members
        desired = {f"cn={cn},{PEOPLE_DN}" for cn in members}

        # aktuelle Members aus LDAP holen
        conn.search(group_dn, "(objectClass=*)", BASE, attributes=["uniqueMember"])

        if not conn.entries:
            print("Group not found:", group_dn)
            current = set()
        else:
            entry = conn.entries[0]
            current = set(entry.uniqueMember.values if "uniqueMember" in entry else [])

        to_add    = list(desired - current)
        to_delete = list(current - desired)

        changes = {}

        if to_add:
            changes["uniqueMember"] = [(MODIFY_ADD, to_add)]

        if to_delete:
            changes.setdefault("uniqueMember", [])
            changes["uniqueMember"].append((MODIFY_DELETE, to_delete))

        if changes:
            conn.modify(group_dn, changes)

        print(group, conn.result)

    delete_unused_persons(conn=conn)

if __name__ == "__main__":
    synchonize_ldap()


# ldapsearch -x -H ldap://localhost:389   -b "cn=RM,ou=Groups,dc=home,dc=mathematik,dc=uni-freiburg,dc=de" -s base "(objectClass=groupOfUniqueNames)" uniqueMember
# liefert jetzt zB alle Mitglieder der RM

