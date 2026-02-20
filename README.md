# mi-ldap

Here are tools in order to get the ldap of the institute running and updated.

* read.py: Uses all entries from the old (by 2026) LDAP and writes them in mi-ldap.json.
* import.py: Takes mi-ldap.json and updates the MongoDB 
* delete.py: Deletes all entries below People, Groups in a current LDAP
* write.py: Uses the data from the MongoDB and fills in People and Groups
* main.py: combine delete.py and write.py for nightly usage


