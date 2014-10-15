#!/bin/sh

# Copyright 2003 University of Oslo, Norway
#
# This file is part of Cerebrum.
#
# Cerebrum is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Cerebrum is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cerebrum; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

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

