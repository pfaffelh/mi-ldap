import netrc
from ldap3 import Server, Connection, ALL, SUBTREE, BASE
from ldap3.core.exceptions import LDAPException, LDAPEntryAlreadyExistsResult

netrc = netrc.netrc()

# LDAP_URI = "ldap://www3.mathematik.privat"
LDAP_URI = "ldap://localhost:389"
ldap_username, ldap_account, ldap_password = netrc.authenticators(LDAP_URI)
print(ldap_username)
abteilungen = ["PA", "D", "Di", "RM", "AM", "MSt", "ML"]
BIND_DN = f"cn={ldap_username},dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
BIND_PW = ldap_password  # besser: aus ENV lesen

BASE_DN = "dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
PEOPLE_DN = f"ou=People,{BASE_DN}"
GROUPS_DN = f"ou=Groups,{BASE_DN}"

def ensure_add(conn, dn, object_classes, attributes):
    # Existenzcheck: BASE-Scope, keine Attribute anfordern
    ok = conn.search(
        search_base=dn,
        search_filter="(objectClass=*)",
        search_scope=BASE,
        attributes=["1.1"],   # "no attributes"
    )
    if ok and conn.entries:
        return False  # exists

    ok = conn.add(dn, object_classes, attributes)
    if not ok:
        raise LDAPException(f"Add failed for {dn}: {conn.result}")
    return True

def main():
    server = Server(LDAP_URI, get_info=ALL)

    # Simple Bind
    conn = Connection(server, user=BIND_DN, password=BIND_PW, auto_bind=True)

    # 1) Base DN (Root-Entry)
    ensure_add(
        conn,
        BASE_DN,
        ["top", "dcObject", "organization"],
        {"dc": "home", "o": "Mathematik Uni Freiburg (home)"}
    )

    # 2) OUs
    ensure_add(conn, PEOPLE_DN, ["top", "organizationalUnit"], {"ou": "People"})
    ensure_add(conn, GROUPS_DN, ["top", "organizationalUnit"], {"ou": "Groups"})

    # 3) Leere Abteilungen via Dummy uniqueMember
    for a in abteilungen:
        abteilung_dn = f"cn={a},{GROUPS_DN}"
        ensure_add(
            conn,
            abteilung_dn,
            ["top", "groupOfUniqueNames"],
            {
                "cn": a,
                "uniqueMember": [f"cn=dummy,{BASE_DN}"],  # Dummy (Pflichtattribut)
            }
        )

    print("Done. Base/OUs/Group ensured.")

if __name__ == "__main__":
    main()
