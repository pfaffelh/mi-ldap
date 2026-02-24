import tools.delete as delete
import tools.write as write

# Delete all entries from LDAP
delete.delete()
# Insert data from the MongoDB into LDAP
write.insert_data()

