# This is a how to set up ldap in order to fill in person data

# 1) For a local computer which does not have ldap yet:

sudo apt update
sudo apt install slapd ldap-utils

sudo dpkg-reconfigure slapd

# de
# uni-freiburg.de
# cgibin-Passwort: siehe netrc
# angeben

sudo systemctl status slapd
# sollte running anzeigen

ldapsearch -x -LLL -H ldap://localhost -b dc=uni-freiburg,dc=de
# ist noch leer

# sudo dpkg-reconfigure slapd

# Hier wird das base.ldif geladen
# admin-Passwort aus netrc
ldapadd -x -D "cn=admin,dc=de" -W -f base.ldif

# Add write access to cgibin

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f write.ldif

# 2) Read ldap from www2 and store the result in mi-ldap.json





# Create groups
python3 ldap.init.py 

# Der Rest passiert in python

