#!/bin/sh

# Oppdater LDAP databasen p� marvin og beeblebrox.

# Lag full.ldif
PT=/cerebrum/dumps/LDAP
cat $PT/org.ldif $PT/pers.ldif $PT/posixgroup.ldif $PT/posixnetgroup.ldif $PT/posixuser.ldif > $PT/full.ldif

# Sync filene p� beeblebrox og marvin
/local/bin/rsync -a /u2/dumps/LDAPv3/ldif/$LDIF marvin:/ldap/var/
/local/bin/rsync -a /u2/dumps/LDAPv3/ldif/$LDIF beeblebrox:/ldap/var/

# K�yr resten i bakgrunnen, updateLDAP.sh l�ser sj�lv.
/local/bin/ssh marvin     /ldap/sbin/updateLDAP.sh 
/local/bin/ssh beeblebrox /ldap/sbin/updateLDAP.sh 
