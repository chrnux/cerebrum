# -*- coding: iso-8859-1 -*-

# Copyright 2004, 2005 University of Oslo, Norway
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

""" Directory-based backend - in this case LDAP """

import re,string,sys

import ldap,ldif,dsml
import urllib
from ldap import modlist
from ldif import LDIFParser,LDIFWriter
from dsml import DSMLParser,DSMLWriter 


import unittest
from errors import ServerError

import config

def ldapDict(s):
    """Oracle Internet Directory suck bigtime. if we insert with lowercase, 
    we might get camelCase back. Helperfunction for easier comparison of 
    dicts with attributes and values. This function lowercases all keys
    in a dictionary and keeps the values untouched.
    """
    for key, val in s.items():
        del s[key]
        s[key.lower()] = val
    return s

class LdapConnectionError(ServerError):
    pass

class DsmlHandler(DSMLParser):
    """Class for a DSMLv1 parser. Overrides method handle from class dsml.DSMLParser"""

    def handle(self):
        """Do something meaningful """
        pass

class LdifHandler(LDIFParser):
    """Class for LDIF records"""

class DsmlBack( DSMLParser ):
    """XML-based files. xmlns:dsml=http://www.dsml.org/DSML """
    def __init_(self,output_file=None,input_file=None,base64_attrs=None,cols=76,line_sep='\n'):
        self.output_file = output_file
        self._input_file = input_file
        self.base64_attrs = base64_attrs
        self.cols = cols
        self.line_sep = line_sep

    def handler(self,*args,**kwargs):
        pass

    def readin(self,srcfile,type="dsml"):
        """Default, the dsml.DSMLParser only wants to parse LDIF-files
        to convert it into DSML before we save it as <filenam>.dsml.
        This function will do both
        """
        pass
    
    def writeout(self):
        dsml.DSMLWriter.writeHeader()
        for record in self.records:
            dsml.DSMLWriter.writeRecord(record.dn,record.entry)
        dsml.DSMLWriter.writeFooter()

class LdifBack( object ):
    """LDIF-based files. 
    """
    def __init__(self,output_file=None, base64_attrs=None,cols=76,line_sep='\n'):
        self.output_file = output_file # or rather from a config-file or something
        self.base64_attrs = base64_attrs
        self.cols = cols
        self.line_sep = line_sep

    def readin(self,srcfile):
        self.file = srcfile
        try:
            file = open(self.file)
            self.records = ldif.ParseLDIF(file) # ldif.ParseLDIF is deprecated... re-implement later
            file.close() 
        except IOError,e:
            print "An error occured while importing file: ", srcfile
            print e

    def writeout(self):
        self.outfile = open(self.output_file,"w")
        for entry in self.records:
            self.outfile.write(ldif.CreateLDIF(entry[0],entry[1],self.base64_attrs,self.cols))
        self.outfile.close()
        
class LdapBack:
    """
    All default values such as basedn for each type of object shall be fetch
    from a configuration file. If config is misconfigured, this module should
    log this in somewhat human readable form.

    PosixUser,PosixGroup etc will inherit this class.
    """
    l = None

    def __init__(self):
        self.l = None # Holds the authenticated ldapConnection object

    def iso2utf(str):
        """ Return utf8-encoded string """
        return unicode(str, "iso-8859-1").encode("utf-8")
        
    def utf2iso(str):
        "Return decoded utf8-string"
        return unicode(str,"utf-8").encode("iso-8859-1")

    def begin(self,incr=False,uri=None,binddn=None,bindpw=None):
        """
        If incr is true, updates will be incremental, ie the 
        original content will be preserved, and can be updated by
        update() and delete()

        begin() opens a connection to the server running LDAP and 
        tries to authenticate
        """
        self.incr = incr
        if uri == None:
            self.uri = config.sync.get("ldap","uri")
        if binddn == None:
            self.binddn = config.sync.get("ldap","binddn")
        if bindpw == None:
            self.bindpw = config.sync.get("ldap","bindpw")
        try:
            self.l = ldap.initialize(self.uri)
            self.l.simple_bind_s(self.binddn,self.bindpw)
            self.insync = []
        except ldap.LDAPError,e:
            #raise LdapConnectionError
            print "Error connecting to server: %s" % (e)

    def close(self):
        """
        Syncronize current base if incr=False, then
        close ongoing operations and disconnect from server
        """
        if not self.incr :
            self.syncronize()
        try:
            self.l.unbind_s()
        except ldap.LDAPError,e:
            print "Error occured while closing LDAPConnection: %s" % (e)

    def _cmp(self,x,y):
        """Comparator for sorting hierarchical DNs for ldapsearch-result"""
        x = x.count(",")
        y = y.count(",")
        if x < y : return 1
        elif x == y : return 0
        else: return -1

    def syncronize(self):
        """ Deletes objects not to be found in given base.
        Only for use when incr is set to False.
        """
        if not self.incr:
            print "Syncronizing LDAP database"
            self.indirectory = []
            for (dn,attrs) in self.search(filterstr=self.filter,attrlist=["dn"]):
                self.indirectory.append(dn)
            for entry in self.insync:
                try:
                    self.inderectory.remove(entry)
                except:
                    info("Info: Didn't find entry: %s." % entry)
            self.indirectory.sort(self._cmp)
            for entry in self.indirectory:
                # FIXME - Fetch list of DNs not to be touched
                self.delete(dn=entry)
                info("Info: Found %s in database.. should not be here.. removing" % entry)
            print "Done syncronizing"

    def abort(self):
        """
        Close ongoing operations and disconnect from server
        """
        try:
            self.l.unbind_s()
        except ldap.LDAPError,e:
            print "Error occured while closing LDAPConnection: %s" % (e)

    def add(self, obj, ignore_attr_types=['',]):
        """
        Add object into LDAP. If the object exist, we update all attributes given.
        """
        dn=self.get_dn(obj)
        attrs=self.get_attributes(obj)
        try:
            self.l.add_s(dn,modlist.addModlist(attrs,ignore_attr_types))
            self.insync.append(dn)
        except ldap.ALREADY_EXISTS,e:
            print "%s already exist. Trying update instead..." % (obj.name)
            self.update(obj)
        except ldap.LDAPError,e:
            print "An error occured while adding %s: e" % (dn,e)

    def update(self,obj,old=None,ignore_attr_types=[], ignore_oldexistent=0):
        """
        Update object in LDAP. If the object does not exist, we add the object. 
        """
        dn=self.get_dn(obj)
        attrs=self.get_attributes(obj)
        if old == None:
            # Fetch old values from LDAP
            res = self.search(base=dn) # using dn as base, and fetch first record
            if not res:
                self.add(obj)
                return
            old_attrs = res[0][1]
        else:
            old_attrs = {}
        mod_attrs = modlist.modifyModlist(ldapDict(old_attrs),ldapDict(attrs),ignore_attr_types,ignore_oldexistent)
        try:
            self.l.modify_s(dn,mod_attrs)
            self.insync.append(dn)
            print "%s updated successfully" % (obj.name)
        except ldap.LDAPError,e:
            print "An error occured while modifying %s" % (dn)

    def delete(self,obj=None,dn=None):
        """
        Delete object from LDAP. 
        """
        if obj:
            dn=self.get_dn(obj)
        try:
            self.l.delete_s(dn)
        except ldap.NO_SUCH_OBJECT,e:
            print "%s not found when trying to remove from database" % (dn)
        except ldap.LDAPError,e:
            print "Error occured while trying to remove %s from database: %s" % (dn,e)

    def search(self,base=None,scope=ldap.SCOPE_SUBTREE,filterstr='(objectClass=*)',attrslist=None,attrsonly=0):
        if base == None:
            base = self.base
        try:
            result = self.l.search_s(base,scope,filterstr,attrslist,attrsonly)
        except ldap.LDAPError,e:
            print "Error occured while searching with filter: %s" % (filterstr)
            return [] # Consider raise exception later
        return result

###
###
###


class PosixUser(LdapBack):
    """Stub object for representation of an account."""
    def __init__(self,conn=None,base=None):
        if base == None:
            self.base = config.sync.get("ldap","user_base")
        else:
            self.base = base
        self.filter = config.sync.get("ldap","userfilter")
        # Need 'person' for structural-objectclass
        self.obj_class = ['top','person','posixAccount','shadowAccount'] 

    def get_attributes(self,obj):
        """Convert Account-object to map ldap-attributes"""
        s = {}
        s['objectClass'] = self.obj_class
        s['cn'] = iso2utf(obj.gecos)
        s['sn'] = iso2utf(obj.gecos.split()[len(obj.gecos.split())-1]) # presume last name, is surname
        s['uid'] = obj.name
        s['uidNumber'] = str(obj.posix_uid)
        s['userPassword'] = '{MD5}' + obj.password # until further notice, presume md5-hash
        s['gidNumber'] = str(obj.primary_group.posix_gid)
        s['gecos'] = self.gecos(obj.gecos)
        s['homeDirectory'] = obj.homedir
        s['loginShell'] = obj.shell
        return s

    def gecos(self,s,default=1):
        # Taken from cerebrum/contrib/generate_ldif.py and then modified.
        # Maybe use latin1_to_iso646_60 from Cerebrum.utils?
        """  Convert special chars to 7bit ascii for gecos-attribute. """
        if default == 1:
            translate = {'�' : 'Ae', '�' : 'ae', '�' : 'Aa', '�' : 'aa','�' : 'Oe','�' : 'oe' }
        elif default == 2:
            translate = {'�' : 'A', '�' : 'a', '�' : 'A', '�' : 'a','�' : 'O','�' : 'o' }
        elif default == 3:
            translate = {'�' : '[', '�' : '{', '�' : ']', '�' : '}','�' : '\\','�' : '|' }
        s = string.join(map(lambda x:translate.get(x, x), s), '')
        return s

    def get_dn(self,obj):
        # Maybe generalize this to LdapBack instead
        return "uid=" + obj.name + "," + self.base

class PosixGroup(LdapBack):
    '''Abstraction of a group of accounts'''
    def __init__(self,base=None):
        if base == None:
            self.base = config.sync.get("ldap","group_base")
        else:
            self.base = base
        self.filter = config.sync.get("ldap","groupfilter")
        self.obj_class = ['top','posixGroup']
        # posixGroup supports attribute memberUid, which is multivalued (i.e. can be a list, or string)

    def get_attributes(self,obj):
        s = {}
        s['objectClass'] = self.obj_class
        s['cn'] = obj.name
        if (len(obj.membernames) > 0):
            s['memberUid'] = obj.membernames
        if (len(obj.description) > 0):
            s['description'] = obj.description
        s['gidNumber'] = str(obj.posix_gid)
        return s

    def get_dn(self,obj):
        return "cn=" + obj.name + "," + self.base

class NetGroup(LdapBack):
    ''' '''
    def __init__(self,base=None):
        if base == None:
            self.base = config.sync.get("ldap","netgroup_base")
        else:
            self.base = base
        self.filter = config.sync.get("ldap","netgroupfilter")
        self.obj_class = ('top', 'nisNetGroup')

    def get_dn(self,obj):
        return "cn=" + obj.name + "," + self.base

    def get_attributes(self,obj):
        s = {}
        s['objectClass'] = self.obj_class
        s['cn'] = (obj.name)
        s['nisNetGroupTriple'] = [] # Which attribute to fetch? FIXME
        s['memberNisNetgroup'] = [] # Which attribute to fetch? FIXME
        return s


class Person(LdapBack):
    def __init__(self,base="ou=People,dc=ntnu,dc=no"):
        self.base = base
        self.filter = config.sync.get("ldap","peoplefilter")
        self.obj_class = ['top','person','organizationalPerson','inetorgperson','eduperson','noreduperson']

    def get_dn(self,obj):
        return "uid=" + obj.name + "," + self.base

    def get_attributes(self,obj):
        s = {}
        s['objectClass'] = self.obj_class
        s['cn'] = iso2utf(obj.full_name)
        s['sn'] = iso2utf(obj.full_name.split()[len(obj.full_name)-1]) # presume last name, is surname
        s['uid'] = obj.name
        s['userPassword'] = '{' + config.sync.get('ldap','hash').upper() + '}' + obj.password 
        s['eduPersonPrincipalName'] = obj.name + "@" + config.sync.get('ldap','eduperson_realm')
        s['norEduPersonBirthDate'] = str(obj.birth_date) # Norwegian "Birth date" FIXME 
        s['norEduPersonNIN'] = str(obj.birth_date) # Norwegian "Birth number" / SSN FIXME
        s['mail'] = s['eduPersonPrincipalName'] # FIXME 
        s['description'] = obj.description
        return s

class Alias:
    """ Mail aliases, for setups that store additional mailinglists and personal aliases in ldap.
    rfc822 mail address of group member(s)
    Depends on rfc822-MailMember.schema

    Decide which schema you want to follow, and change objectclass-chain and attribute-names.
    Some prefer to use attribute mailDrop, mailHost etc from ISPEnv2.schema
    """
    def __init__(self,base=None):
        if base == None:
            self.base = config.sync.get("ldap","mail_base")
        else:
            self.base = base
        self.filter = config.sync.get("ldap","mailfilter")
        self.obj_class = ('top','nisMailAlias')

    def get_dn(self,obj):
        return "cn=" + obj.name + "," + self.base

    def get_attributes(self,obj):
        s = {}
        s['objectClass'] = self.obj_class
        s['cn'] = obj.name
        s['rfc822MailMember'] = obj.membernames()
        return s


class OU:
    """ OrganizationalUnit, where people work or students follow studyprograms.
    Needs name,id and parent as minimum.
    """

    def __init__(self,base=None):
        self.ou_dict = {}
        if base == None:
            self.base = config.sync.get("ldap","ou_base")
        else:
            self.base = base
        self.filter = config.sync.get("ldap","oufilter")
        self.obj_class = ['top','organizationalUnit']

    def get_dn(self,obj):
        base = self.base
        filter = 'norEduOrgUnitUniqueNumber=%s' % obj.parent_id 
        if (self.ou_dict.has_key[obj.parent_id]):
            parentdn = self.ou_dict[obj.parent_id]
        else:
            parentdn = self.search(base=base,filterstr=filter)[0][0]
        dn = "ou=" + obj.name + parentdn
        self.ou_dict['obj.id'] = dn # Local cache to speed things up.. 
        return dn

    def get_attributes(self,obj):
        #FIXME: add support for storing unit-id,parent-id and rootnode-id
        s = {}
        s['objectClass'] = ('top','organizationalUnit','norEduOrgUnit')
        s['ou'] = obj.name
        s['cn'] = obj.full_name
        s['description'] = obj.description
        s['norEduOrgUniqueNumber'] = config.sync.get('ldap','norEduOrgUniqueNumber')
        s['norEduOrgUnitUniqueNumber'] = obj.id
        #s['norEduOrgAcronym'] = obj.acronyms
        return s



###
### UnitTesting is good for you
###
class _testObject:
    def __init__(self):
        pass

class testLdapBack(unittest.TestCase):
    
    def setUp(self):
        self.lback = LdapBack()
        self.lback.begin()

    def tearDown(self):
        self.lback.close()

    def testSetup(self):
        pass

    def testBeginFails(self):
        self.assertRaises(LdapConnectionError, self.lback.begin, hostname='doesnotexist.bizz')

    def testClose(self):
        self.lback.close()

    def testAdd(self):
        user = _testObject()
        self.add(user)
        self.lback.close()

    def testUpdate(self):
        user = _testObject()
        self.update(user)
        self.lback.close()

    def testDelete(self):
        user = _testObject()
        self.delete(user)
        self.lback.close()


    # Test-cases to be added:
    # Search (find root-node from config-file)
    # Add,Update,Delete
    # sync a test-tree
    # strange characters in gecos-attribute.. 

if __name__ == "__main__":
    unittest.main()

# arch-tag: ec6c9186-9e3a-4c18-b467-a72d0d8861fc
