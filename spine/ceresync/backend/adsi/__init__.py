# -*- coding: windows-1252 -*-
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

# Windows/ActiveDirectory-only
import sys
import os
from ceresync.backend.adsi.ad_types import constants
from ceresync.backend.adsi import ad_errors
from ceresync.backend.adsi import active_directory as ad
# Wrapped version that catches ADSI errors
ad = ad_errors.wrapComError(ad)
from ceresync import errors

try:
    set()
except:
    from sets import Set as set

import unittest
import tempfile
import win32pipe
import time
import StringIO
import win32com.client
from ceresync.syncws import Pgp
from ceresync import config

log=config.logger

def str2int(s):
    s= s.strip()
    if s.startswith('0x'):
        return int(s, base=16)
    if s.startswith('0') and s.isdigit():
        return int(s, base=8)
    return int(s)

class _Dummy(object):
    """A dummy object to simulate an account object"""
    def __init__(self,name):
        self.name= name

class WrongClassError(errors.AlreadyExistsError):
    """Already exists in OU, but is wrong objectClass"""    

class OutsideOUError(errors.AlreadyExistsError):
    """Already exists outside managed OU"""

class _AdsiBack(object):
    """
    Generalized class representing common data for working with adsi objects.
    In general, working with Active Directory, you can either use WinNT:// or
    LDAP:// to search,add,modify,delete objects.
    """
    objectClass = "top"
    def __init__(self, ou_path=None):
        """Initalizes an AD connection. 

           ou_path specifies which OU this backend should manage
           objects.  The backend expects all objects inside this OU to
           be handled by itself, so any unknown objects in this OU will
           be deleted in begin(incr=False).
    
           Specify ou_path as a full LDAP URI, example::

             a = AdsiBack("LDAP://OU=Groups,OU=MyDivision,DC=domain,DC=no")
           
           The actual LDAP connection will not be made until begin() is
           called.  
           """
        self.ou_path = ou_path   
    
    def _prefix(self, uri=None):
        """Returns the URI prefix of the given URI. 
           If the uri parameter is not given, the prefix of self.ou is
           returned.
           The URI prefix is either "LDAP://" or "LDAP://some.server/".
        """   
           
        if uri is None:
            uri = self.ou.ADsPath
        # avoid searching after cn=
        uri = uri.split("=")[0]
        protocol,server = uri.split("://")[:2]
        if not "/" in server:
            # LDAP://cn=psdkm,dc=akdjs,dc=akjdsk
            # -> LDAP://
            return protocol + "://"
        # LDAP://some.server/cn=sdkm,dc=akdjs,dc=akjdsk
        # -> LDAP://some.server/
        server = server.split("/")[0]
        return "%s://%s/" % (protocol, server)
    prefix = property(_prefix)    
        
    def is_rid_manager(self):
        """Returns True if the current server is the RID manager."""    
        # The RID manager of an AD domain is the domain controller
        # responsible for giving out new IDs, and the idea is to 
        # only proceed to run the cerebrum sync if we are connected
        # to the RID manager. The AD administrators will anyway have
        # to manually switch over the current RID manager if that
        # server fails.
        root = self._domain()
        rid_ref = root.rIDManagerReference
        rid = ad.AD_object(path=self.prefix + rid_ref)
        ntds = ad.AD_object(path=self.prefix + rid.fSMORoleOwner)
        rid_manager = ntds.parent()

        # compare with ourself
        rootDSE = ad.GetObject(self.prefix + "rootDSE")
        our_server = rootDSE.serverName
        return our_server == rid_manager.distinguishedName
    is_rid_manager = property(is_rid_manager)     

    def _domain(self, obj=None):
        """Finds the domain of an AD object, ie. the root node. If
           obj is not specified, the domain of self.ou is returned."""
        if obj is None:
            obj = self.ou
        # Is it possible to do this without walking?    
        while not "domain" in obj.objectClass:
            obj = obj.parent()
        return obj    

    def _connect(self):
        """Connects to Active Directory"""
        if self.ou_path is None:
            # Use the root      
            self.ou = ad.root()
        else:
            self.ou = ad.AD_object(path=self.ou_path)

    def begin(self, encoding, incr=False, bulk_add=True, bulk_update=True, 
                    bulk_delete=True):
        """Initializes the Active Directory synchronization"""
        self.encoding= encoding
        self.incr = incr
        self.bulk = not incr
        self.do_add= incr or bulk_add
        self.do_update= incr or bulk_update
        self.do_delete= incr or bulk_delete
        self._connect()
        
        if self.bulk:
            self._remains = self._find_existing_objects()

    def _find_existing_objects(self):
        existing = set()
        # Don't touch objects of other classes than our
        # (Scenario: groups and users in same OU, both handled
        #  by different subclass)
        for o in self.ou.search("objectClass='%s'" %
                                self.objectClass):
            # FIXME: should use SUBTREE something to avoid returning
            # self.ou
            if not 'user' in o.objectClass:
                continue
            
            # Supports both cn=name, ou=name, etc.                    
            existing.add(o.name.split("=")[1])
        return existing

    def close(self):
        """Close the connection to AD"""
        if self.bulk:
            while self._remains:
                accountname= self._remains.pop()
                if self.do_delete:
                    log.info("Disabling %s",accountname)
                    self.delete(_Dummy(accountname))
        self._remains = None
        self.ou = None

    def abort(self):
        """ Abort any ongoing operations. """
        self._remains = None
        self.ou = None

    def _nuke(self, ad_obj):
        """Delete object from AD"""
        parent = ad_obj.parent()
        # for instance ou.remove("user", "cn=stain")
        parent.nuke(ad_obj.Class, ad_obj.name)

    def nuke(self, obj):
        ad_obj = self._find(obj.name)
        log.info("deleting '%s'.",obj.name)
        self._nuke(ad_obj)
        if self.bulk:
            if obj.name in self._remains:
                self._remains.remove(obj.name)

    def _move_to_target_ou(self, obj):
        ad_obj = self._find(obj.name)

        target_ou = self._get_target_ou(obj)

        # If an account has been added manually, the CN may be the full name
        # instead of username, and the full name may contain non-ascii chars.
        # FIXME: There's probably a better way to handle this
        target_ou.moveHere(ad_obj.path(), u'CN=%s' % (obj.name,))

        return self._find(obj.name)

class _ADAccount(_AdsiBack):                
    """Common abstract class for ADUser and ADGroup. 
       They both use saMAccountName as their unique name (with a shared
       namespace) - and that name is always equal to obj.name from
       Spine.
    """

    def _find(self, accountname, ou=None, objectClass=None):
        """Find an account or group by saMAccountName 
        (unique short-version of username in AD). 

        Searches from self.ou unless parameter ou is specified, which
        must be an OU object.

        Returns the matching AD object.

        Raises WrongClassError if the matched object doesn't 
        implement self.objectClass. (For instance, you're searching for
        a group, but found a username instead. As groups and users share
        the saMAccountName domain in AD, you can't have both). If you
        want to override this, specify the parameter objectClass.
        
        Raises OutsideOUError if a conflicting object with
        the given name exists outside our managed OU self.ou.
        saMAccountName is unique across the domain, so this could happen
        if you get an conflict with manual users in other OUs, like
        "Administrator".

        Returns None if the object is not found at all in AD. This means
        the username is available.
        """
        if not ou:
            ou = self.ou
        if not objectClass:
            objectClass = self.objectClass    

        query = "saMAccountName='%s'" % accountname
        for u in ou.search(query):
            # There's really just one hit, if any. So we can
            # raise/return from inside for-loop.

            #  Wait! Was it the correct class?
            if not objectClass in u.objectClass:
                raise WrongClassError, u
            # it's OK, return it    
            return u
        

        # Not found, might he be outside our ou? If so, raise an
        # OutsideOUError exception
        domain = self._domain()
        for u in domain.search(query):
            # There's only one, so let's raise it
            raise OutsideOUError, (u, accountname)
            
        # OK, it's really really not here
        return None   
    
    def add(self, obj):
        """Adds an object to AD. If it already exist, the existing
           AD object will be updated instead."""

        if self.bulk:
            if obj.name in self._remains:
                self._remains.remove(obj.name)

        try:
            already_exists = self._find(obj.name)
        except OutsideOUError, e:
            dn, accountname = e
            log.warning("Didn't add '%s', it exists outside the managed OU (%s).", accountname, dn)
            return None

        if already_exists:
            if self.do_update:
                log.info("Updating '%s'", obj.name)
                return self._update(obj)
            else:
                log.debug("Didn't add '%s', it already exists, skipping", obj.name)
                return None

        if self.do_add:
            log.info("Adding '%s'", obj.name)
            target_ou = self._get_target_ou(obj)
            ad_obj = target_ou.create(self.objectClass, "cn=%s" % obj.name)
            ad_obj.sAMAccountName = obj.name
            ad_obj.setInfo()

            # fetch object again for auto-generated values 
            ad_obj = self._find(obj.name)
            if ad_obj is None:
                log.warning("Failed to add account '%s'", obj.name)
                return None
            self._update_attributes(obj, ad_obj)
            return ad_obj

    def _get_target_ou(self, obj):
        return self.ou

    def _get_target_dn(self, obj):
        if not hasattr(obj, '__target_dn'):
            target_ou = self._get_target_ou(obj)
            obj.__target_dn = "CN=%s,%s" % (obj.name, target_ou.distinguishedName)

        return obj.__target_dn

    def _update(self, obj):
        """Will only be called by add."""
        ad_obj = self._find(obj.name)
        if ad_obj.distinguishedName != self._get_target_dn(obj):
            log.info(u"moving %s from %s to %s",
                obj.name,
                ad_obj.distinguishedName,
                self._get_target_dn(obj),
            )
            ad_obj = self._move_to_target_ou(obj)

        self._update_attributes(obj, ad_obj)
        return ad_obj    

    def _update_attributes(self, obj, ad_obj):
        pass

class ADUser(_ADAccount):
    objectClass = "user"
    """Backend for Users in Active Directory.
       Normally, users will be created flat directly in self.ou,
       with cn=username, ie. the same as saMAccountName.
    """
    # Reference: 
    # http://www.microsoft.com/windows2000/techinfo/howitworks/activedirectory/adsilinks.asp
    # http://search.microsoft.com/search/results.aspx?qu=adsi&View=msdn&st=b&c=4&s=1&swc=4

    def begin(self, *args, **kwargs):
        super(ADUser, self).begin(*args, **kwargs)
        self._ou_cache = {}

    def _update_attributes(self, obj, ad_obj):
        """Update the ad_object, ad_obj, with the fields from the spine object,
           obj.
        """
        full_name= unicode(obj.full_name or obj.gecos or ' ', self.encoding)
        try: 
            first_name, last_name= full_name.rsplit(None,1)
        except ValueError:
            first_name, last_name= ' ', full_name
        ad_obj.givenName= first_name
        ad_obj.sn= last_name
        ad_obj.displayName= full_name
        ad_obj.homeDirectory= obj.homedir
        ad_obj.userPrincipalName= '%s@%s' % (obj.name,obj.domain)
        ad_obj.profilePath= obj.profilepath
        ad_obj.scriptPath= obj.scriptpath

        password_ok = self._set_password(ad_obj, obj)
        if not password_ok:
            log.warning("No password on %s.", obj.name)

        ad_obj.setInfo()
        try:
            ad_obj.userAccountControl= str2int(obj.control_flags)
        except ad_errors.DSUnwillingToPerformError, e:
            log.warning(
                "Couldn't set userAccountControl for %s to %s" % (obj.name, obj.control_flags))

    def _set_password(self, ad_obj, obj):
        if not obj.passwd:
            return False
        
        dec = Pgp().decrypt(obj.passwd)
        try: 
            log.debug("Updating password on '%s'", obj.name)
            ad_obj.setPassword(dec)
            return True
        except Exception,e:
            log.warning("Failed to set password on '%s': %s", obj.name, e)
            return False

    def add(self, obj):
        """Adds an object to AD. If it already exist, the existing
           AD object will be updated instead."""
        
        if self._get_target_ou(obj) is None:
            log.warning("Not adding account '%s' with primary affiliation '%s'.  No configured OU for given affiliation.",
                obj.name, obj.primary_affiliation)
            return

        super(ADUser, self).add(obj)

    def _get_target_ou(self, obj):
        if not hasattr(obj, '__target_ou'):
            obj.__target_ou = config.get('affiliations', obj.primary_affiliation)

            # FIXME: I suspect that this code path is dead.
            if obj.__target_ou == 'None':
                obj.__target_ou = None

        return self._get_ou(obj.__target_ou)

    def _get_ou(self, dn):
        if dn is None:
            return None

        if not dn in self._ou_cache:
            objectPath = dn
            if not objectPath.lower().startswith("ldap://"):
                objectPath = u"LDAP://%s" % dn

            self._ou_cache[dn] = win32com.client.GetObject(objectPath)
        return self._ou_cache[dn]

    def delete(self, obj):
        try:
            ad_obj = self._find(obj.name)
        except OutsideOUError, e:
            dn, accountname = e
            log.warning("Didn't delete '%s', it is outside the managed OU (%s).", accountname, dn)
            return None
            
        if not ad_obj:
            return None
        ad_obj.getInfo()
        if not ad_obj.userAccountControl & 0x00002:
            ad_obj.userAccountControl |= 0x00002
        if self.bulk:
            if obj.name in self._remains:
                self._remains.remove(obj.name)


class ADGroup(_ADAccount):
    """Backend for Groups in Active Directory. 
       Normally, groups are set as "Global Security groups".
    """
    objectClass = "group"

    def _update(self, obj):
        ad_obj = super(ADGroup, self)._update(obj)
        ad_obj.groupType = (constants.ADS_GROUP_TYPE_SECURITY_ENABLED | 
                            constants.ADS_GROUP_TYPE_GLOBAL_GROUP)
        ad_obj.setInfo()

        old_members = set(ad_obj.members())
        old_names = set([m.saMAccountName for m in old_members])
        new_names = set(obj.members)

        names_to_add = new_names - old_names
        names_to_del = old_names - new_names
        
        if not (names_to_add or names_to_del):
            return ad_obj

        members_to_add = self._get_members(names_to_add)
        members_to_del = [m for m in old_members
                            if m.saMAccountName in names_to_del]

        for user in members_to_del:
            log.debug("Removing %s from group '%s'", user, obj.name)
            ad_obj.remove(user.ADsPath)

        for user in members_to_add:
            log.debug("Adding %s to group '%s'", user, obj.name)
            ad_obj.add(user.ADsPath)
        ad_obj.setInfo()

        return ad_obj

    def _get_members(self, names):
        # Ok, convert to nice ldap paths    
        domain = self._domain()
        # search in the whole domain, users only

        to_add= []
        for m in names:
            try:
                res= self._find(m, ou=domain, objectClass='user')
                if res:
                    to_add.append(res)
            except WrongClassError, e:
                log.warning("%s exists in AD, but is not a user.", m)
        return to_add

# The rest of the module is unit tests.
# TODO: Move out!

def cscript(script, type="vbs"):
    """Run a (VB)script using cscript and return the result.
       NOTE: This function should only be used for UNIT TESTS.
    """
    # We will use this to set up the AD environment and test it,
    # using known-to-work VBscript code instead of our own code.
    file = tempfile.mktemp(".%s" % type)
    open(file, "w").write(script)
    # popen4 will also include errors 
    i,o = win32pipe.popen4("cscript /nologo %s" % file)
    # Everything will be returned in the first read() =)
    return o.read().strip()



class TestCscript(unittest.TestCase):
    """Tests our cscript() interface"""
    def testEcho(self):
        self.assertEqual(cscript('Wscript.Echo "Hello world"'), 
                         "Hello world")

class TestAD(unittest.TestCase):
    """Checks that there really is an ldap/AD"""
    def testDefaultNamingContext(self):
        """Will only work on an AD server (?)"""
        context = cscript("""Wscript.Echo(GetObject("LDAP://rootDSE").Get("defaultNamingContext"))""")
        assert context.count("DC=")

class TestOUFramework(unittest.TestCase):
    """Helper functions for managing the AD and OU tests,
       mainly by calling small VBscripts.
    """
    # A separate OU will be created in the root on our test domain
    # server
    ou = "tempOU"
    def ou_uri(self):
        """Full URI for our OU"""
        return "LDAP://ou=%s,%s" % (self.ou, self.context)
    ou_uri = property(ou_uri)    

    def hostname(self):
        return cscript("""
        set rootDSE = GetObject("LDAP://rootDSE")
        Wscript.Echo(rootDSE.dnsHostName)
        """)
    hostname = property(hostname)       

    def deleteOU(self, ou=None):
        """Recusively deletes an ou with the given name.
        ou must be located in root.
        If parameter ou is not given, uses self.ou"""
        if ou is None:
            ou = self.ou
        self.assertEqual(cscript("""
        on error resume next
        set ou = GetObject("LDAP://OU=%s,%s")
        ou.DeleteObject 0
        """ % (ou, self.context)), "")
        
    def createOU(self, ou=None, root=None):
        """Creates a new (blank) ou with the given name, located in root.
        If parameter ou is not given, uses self.ou.
        If parameter root is given, that distinguishedName will be used,
        example: createOU(root="ou=someOU,dc=some,dc=domain,dc=com")
        WARNING: Will recursive delete if ou already exists."""
        if ou is None:
            ou = self.ou
        if root is None:
            root = self.context     
        # delete tempOU if already exist 
        self.deleteOU(ou)

        # Create our working temporary OU
        self.assertEqual(cscript("""
        set root = GetObject("LDAP://%s")
        set tempOU = root.Create("organizationalUnit", "ou=%s")
        tempOU.SetInfo()
        """ % (root, ou)), "")

    def setUp(self):
        # Find our root, ie dc=some,dc=doman,dc=com
        self.context = cscript("""
        Wscript.Echo(GetObject("LDAP://rootDSE").Get("defaultNamingContext"))
        """)
        self.createOU()
        self.prepareLogger()
    
    def tearDown(self):    
        self.deleteOU()

    def createUser(self, user="temp1337", ou=None):
        """Adds a user through vbscript"""
        if ou is None:
            ou = self.ou
        self.assertEqual(cscript("""
        set ou = GetObject("LDAP://ou=%s,%s")
        set user = ou.Create("user", "cn=%s")
        user.saMAccountName = "%s"
        user.SetInfo()
        """ % (ou, self.context, user, user)), "")

    def createGroup(self, group="temp1337", ou=None):
        """Adds a group through vbscript"""
        if ou is None:
            ou = self.ou
        self.assertEqual(cscript("""
        set ou = GetObject("LDAP://ou=%s,%s")
        set group = ou.Create("group", "cn=%s")
        group.saMAccountName = "%s"
        ' this seems to be the default anyway
        'group.groupType = ADS_GROUP_TYPE_SECURITY_ENABLED + ADS_GROUP_TYPE_GLOBAL_GROUP
        group.SetInfo()
        """ % (ou, self.context, group, group)), "")

    def addGroupMember(self, member, group="temp1337", ou=None):
        """Adds the given username to the given group.
           The member and group must both be in the given ou.
        """
        if ou is None:
            ou = self.ou
        context = self.context
        self.assertEqual(cscript("""
        set group = GetObject("LDAP://cn=%(group)s,ou=%(ou)s,%(context)s")
        group.add("LDAP://cn=%(member)s,ou=%(ou)s,%(context)s")
        group.setInfo()
        """ % locals()), "")
 
    
    def groupMembers(self, group="temp1337", ou=None):
        """Returns a (sorted) list of group members.
           Note that a member might be either a user or a group.
        """
        if ou is None:
            ou = self.ou
        members = cscript("""
        set group = GetObject("LDAP://cn=%s,ou=%s,%s")
        for each member in group.members
            Wscript.echo member.sAMAccountName
        next    
        """ % (group, ou, self.context))
        if not members: return []
        #result = [x.replace("CN=", "") for x in members.split("\n")]
        result = members.split("\n")
        result.sort()
        return result

    def hasNotAccount(self, account="temp1337", ou=None):      
        """Fails if the account exists"""
        if ou is None:
            ou = self.ou
        #  Should not find anything
        self.assertEqual(cscript("""
        On Error Resume Next
        set account = GetObject("LDAP://cn=%s,ou=%s,%s")
        Wscript.Echo(account.distinguishedName)
        """ % (account, ou, self.context)), "")

    def hasAccount(self, account="temp1337", ou=None):
        """Fails if the account does not exist"""
        if ou is None:
            ou = self.ou
        dn = "CN=%s,OU=%s,%s" % (account, ou, self.context) 
        self.assertEqual(cscript("""
        set account = GetObject("LDAP://%s")
        Wscript.Echo(account.distinguishedName)
        """ % dn), dn)
        self.assertEqual(cscript("""
        set account = GetObject("LDAP://%s")
        Wscript.Echo(account.sAMAccountName)
        """ % dn), account)

    def hasGroup(self, account="temp1337", ou=None):
        """Fails if the account does not exist"""
        if ou is None:
            ou = self.ou
        dn = "CN=%s,OU=%s,%s" % (account, ou, self.context) 

    def accountGID(self, account="temp1337", ou=None):
        """Fails if the account does not exist"""
        if ou is None:
            ou = self.ou
        dn = "CN=%s,OU=%s,%s" % (account, ou, self.context) 
        return cscript("""
        set account = GetObject("LDAP://%s")
        Wscript.Echo(account.GUID)
        """ % dn)
    
    def prepareLogger(self):
        """Makes logger use a buffer instead of stderr. 
           The lines logged (format: "WARNING: asdlksldk") can be
           fetched with the method lastLog.
        """
        self.logbuf = StringIO.StringIO()
        logger = logging.getLogger()
        loghandler = logging.StreamHandler(self.logbuf)
        loghandler.setLevel(logging.INFO)
        loghandler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        del logger.handlers[:] # any old ones goodbye
        logger.addHandler(loghandler)
        logger.setLevel(logging.INFO)

    def lastLog(self):
        """Returns what's been logged since last call."""
        last = self.logbuf.getvalue()
        self.logbuf.seek(0)
        self.logbuf.truncate()
        return last
        


class TestTestOUFramework(TestOUFramework):
    def testFramework(self):
        """Quick test of our testing framework"""
    
    def testOuURI(self):    
        assert "LDAP://" in self.ou_uri
        assert "ou=" in self.ou_uri
        assert "DC=" in self.ou_uri
         
    def testHostname(self):
        assert self.hostname.count(".")

    def testCreateHasHasNot(self):
        self.hasNotAccount()
        self.assertRaises(AssertionError, self.hasAccount)
        self.createUser()
        self.hasAccount()
        self.assertRaises(AssertionError, self.hasNotAccount)
    
    def testDeleteOU(self):    
        self.createOU()
        self.deleteOU()
        # should not fail if not exist    
        self.deleteOU()
        # Should fail if OU is missing
        self.assertRaises(AssertionError, self.hasAccount)
    
    def testCreateOUDeletes(self):
        self.createUser()
        # createOU should delete existing OU
        self.createOU()
        self.hasNotAccount()
    
    def testCreateOUOtherRoot(self):
        self.createOU()
        self.createOU("deep1337", root="ou=tempOU,%s" % self.context)
        self.deleteOU() # Should also delete sub-OUs
    
    def testCreateAnotherUser(self):
        self.createUser("fish1337")
        self.hasAccount("fish1337")
        self.hasNotAccount()
        self.assertRaises(AssertionError, self.hasNotAccount, "fish1337")

    def testAnotherOU(self):
        self.createOU("temp42")
        self.createUser("knott1337", ou="temp42")
        self.assertRaises(AssertionError, self.hasAccount, "knott1337")
        self.assertRaises(AssertionError, self.hasNotAccount, "knott1337", ou="temp42")
        self.hasAccount("knott1337", ou="temp42")
        self.deleteOU("temp42")
        self.createOU("temp42")
    
    def testCreateGroup(self):
        self.createGroup()
        self.hasAccount()
        

    def testAddGroupMember(self):
        self.createGroup()
        self.createUser("user1337")
        self.addGroupMember("user1337")

    def testGroupMembersEmpty(self):
        self.createGroup()
        self.assertEqual(self.groupMembers(), [])
        
    def testGroupMembers(self):    
        self.createGroup()
        self.createUser("user1337")
        self.createUser("user31337")
        self.addGroupMember("user1337")
        self.assertEqual(self.groupMembers(), ["user1337"])
        self.addGroupMember("user31337")
        self.assertEqual(self.groupMembers(), ["user1337", "user31337"])
        
    def testGroupMembersOther(self):
        self.createGroup()
        self.createGroup("other1337")
        self.createUser("user1337")
        self.createUser("user31337")
        self.addGroupMember("user1337")
        self.addGroupMember("user31337", "other1337")
        # add group temp1337 as member (!)
        self.addGroupMember("temp1337", "other1337")
        # member user1337 is "behind" group temp1337
        self.assertEqual(self.groupMembers("other1337"),
                         ["temp1337", "user31337"])

    def testAccountGid(self):
        self.createUser()
        gid = self.accountGID()
        self.assertEqual(len(gid), 32)
        self.createUser("test1442")
        self.assertNotEqual(gid,  self.accountGID("test1442"))

    def testLog(self):
        logging.error("Hello")
        self.assertEqual(self.lastLog(), "ERROR: Hello\n")
        self.assertEqual(self.lastLog(), "")

    def tearDown(self):
        super(TestTestOUFramework, self).tearDown()
        self.deleteOU("temp42")       


class TestOU(TestOUFramework):
    def testWasCreated(self):
        self.assertEqual(cscript("""
        set tempOU = GetObject("%s")
        Wscript.Echo tempOU.name""" % self.ou_uri),
        "ou=%s" % self.ou)

class TestADSIBack(TestOUFramework):
    def setUp(self):
        super(TestADSIBack, self).setUp()
        self.adsi = _AdsiBack(self.ou_uri)
        self.adsi.begin()
    
    def testBegin(self):    
        self.assertEqual(self.adsi.ou.distinguishedName,
            "OU=%s,%s" % (self.ou, self.context))
    
    def testBeginDefaultRoot(self):    
        # Test default constructor instead
        adsi = _AdsiBack()
        adsi.begin()
        # Should pick root, ie DC=..  without any OU=
        self.assertEqual(adsi.ou.distinguishedName,
                         self.context)
    
    def testPrefix(self):
        # Simplest case
        adsi = _AdsiBack()    
        self.assertEqual(adsi.prefix, "LDAP://")

        # OK, but what about with a hostname=
        my_hostname = cscript("""
        set rootDSE = GetObject("LDAP://rootDSE")
        Wscript.Echo(rootDSE.dnsHostName)
        """)
        assert my_hostname

        adsi = _AdsiBack("LDAP://%s/ou=%s,%s" % 
                (my_hostname, self.ou, self.context))
        self.assertEqual(adsi.prefix, 
                         "LDAP://%s/" % my_hostname)

        # And with port? 
        my_hostname += ":389"
        adsi = _AdsiBack("LDAP://%s/ou=%s,%s" % 
                (my_hostname, self.ou, self.context))
        self.assertEqual(adsi.prefix, 
                         "LDAP://%s/" % my_hostname)


        # And for the rest of the test, we test with manual parameters
        self.assertEqual(adsi._prefix("LDAP://"), "LDAP://") 
        self.assertEqual(adsi._prefix("LDAP://server/"), "LDAP://server/") 
        self.assertEqual(adsi._prefix("LDAP://dc=fish"), "LDAP://") 
        self.assertEqual(adsi._prefix("LDAP://some.host/dc=fish"), 
                                      "LDAP://some.host/") 
        # With nasty / in cn
        self.assertEqual(adsi._prefix("LDAP://cn=some/thing,dc=some,dc=domain"), 
                                      "LDAP://") 
        self.assertEqual(adsi._prefix("LDAP://fishy.com/cn=some/thing,dc=some,dc=domain"), 
                                      "LDAP://fishy.com/")
        # with user/pass/port 
        self.assertEqual(adsi._prefix("LDAP://user:pass@some.host:port/dc=fish"), 
                                      "LDAP://user:pass@some.host:port/")
    
    def testIsRIDManager(self):
        adsi = _AdsiBack()

        ridmanager = cscript("""
        set RID = GetObject("LDAP://CN=RID Manager$,CN=System,%s")
        RIDManager = RID.fSMORoleOwner
        set NTDS = GetObject("LDAP://" & RIDManager)
        set Comp = GetObject(NTDS.Parent)
        Wscript.Echo(Comp.dnsHostName)""" % self.context)

        my_name = cscript("""
        set rootDSE = GetObject("LDAP://rootDSE")
        hostname = rootDSE.dnsHostName
        Wscript.Echo(hostname)
        """)

        self.assertEqual(adsi.is_rid_manager, 
                         (ridmanager == my_name) )
    
    def testRemainsEmpty(self):
        self.assertEqual(self.adsi._remains, set())
    
    def testContainsUsers(self):
        self.createUser()
        self.adsi.begin() # reload _remains
        self.assertEqual(self.adsi._remains, set(["temp1337"]))
        self.hasAccount()

    def testCloseRemovesUnknown(self):
        self.createUser()
        self.hasAccount()
        self.adsi.begin() # reload _remains
        self.adsi.close() # Should delete the user we added
        #  Should not find anything
        self.hasNotAccount()
        self.assertEqual(self.adsi._remains, None)
        self.assertEqual(self.adsi.ou, None)
        
    def testAbortRemovesNothing(self):
        self.createUser()
        self.hasAccount()
        self.adsi.begin() # reload _remains
        self.adsi.abort() # Should not delete the user we added
        #  Should still find user
        self.hasAccount()
        self.assertEqual(self.adsi._remains, None)
        self.assertEqual(self.adsi.ou, None)

    def testDomain(self):
        self.assertEqual(self.adsi._domain().path(), 
                         "LDAP://%s" % self.context)     
            
class TestADAccount(TestOUFramework):
    def setUp(self):
        super(TestADAccount, self).setUp()
        self.adaccount = _ADAccount(self.ou_uri)
        self.adaccount.begin()

    def tearDown(self):    
        self.deleteOU(self.ou + "1337")
        super(TestADAccount, self).tearDown()

    def testRemoveAccount(self):
        class Account:
            """Dummy account object"""
            name = "temp1337"
        account = Account()    

        self.createUser()
        self.adaccount.begin() 
        # reload _remains to mimic containsUser
        self.adaccount.nuke(account)
        #  Should not find anything
        self.hasNotAccount()

        self.adaccount.begin() # reload _remains
        # now empty again
        self.assertEqual(self.adaccount._remains, set()) 

    def testRemoveAccount(self):
        class Account:
            """Dummy account object"""
            name = "temp1337"
        account = Account()    

        self.createUser()
        self.adaccount.begin() 
        # reload _remains to mimic containsUser
        self.adaccount.nuke(account)
        #  Should not find anything
        self.hasNotAccount()
        # Should no longer be in _remains
        self.assertEqual(self.adaccount._remains, set()) 

    def testFindAccount(self):
        # should not find before creation
        self.assertEqual(self.adaccount._find("temp1337"), None)
        self.createUser()
        account = self.adaccount._find("temp1337")
        self.assertEqual(account.distinguishedName, 
                         "CN=temp1337,OU=%s,%s" % (self.ou, self.context))
        # Should not find another name 
        self.assertEqual(self.adaccount._find("nottemp1337"), None)
    
    def testFindOutsideOU(self):     
        anotherOU = self.ou + "1337"
        self.createOU(anotherOU)
        self.createUser("outside1337", ou=anotherOU)
        self.assertRaises(OutsideOUError, self.adaccount._find, "outside1337")

        # But if we specify root as ou it should work 
        anotherOUobj = self.adaccount
        account = self.adaccount._find("outside1337", ad.root())
        self.assertEqual(account.distinguishedName, 
                         "CN=outside1337,OU=%s,%s" % (anotherOU, self.context))
         
    def testFindWrongClass(self):     
        self.createUser()
        # default is self.adaccount.objectClass, for _ADAccount this is
        # "top" - which every object is part of
        u = self.adaccount._find("temp1337")
        # temp1337 is a user
        self.adaccount._find("temp1337", objectClass="user")
        # but not a group
        self.assertRaises(WrongClassError,
                          self.adaccount._find, "temp1337", 
                          objectClass="group")
    # cannot test _ADAccount.add() here as both groups and users will
    # require another self.objectClass than "top" - ie. _ADAccount.add()
    # is an abstract method. 
 
class TestADUser(TestOUFramework):
    def setUp(self):
        super(TestADUser, self).setUp()
        self.aduser = ADUser(self.ou_uri)
        self.aduser.begin()

    def lastChangedPassword(self, user, ou=None):
        if not ou:
            ou = self.ou
        last_changed = cscript("""
        function iso_date(byval dt)
            dim y: y = year(dt)
            dim m: m=month(dt)
            dim d: d=day(dt)
            dim h: h=hour(dt)
            dim n: n=minute(dt)
            dim s: s=second(dt)

            if m < 10 then m="0" & m
            if d < 10 then d="0" & d
            if h < 10 then h="0" & h
            if n < 10 then n="0" & m
            if s < 10 then s="0" & s

            iso_date = y & "-" & m & "-" & d & " " & h & ":" & n & ":" & s
        end function
        set user = GetObject("LDAP://CN=%s,OU=%s,%s")
        dtmValue = user.PasswordLastChanged
        Wscript.Echo(iso_date(dtmValue))
        """ % ("user1337", ou, self.context))

        if "(null)" in last_changed:
            return None
            # C:\Scripts\Listing2.vbs(2, 1) (null): 0x8000500D
            # This is a common error message in ADSI. It means that an attribute
            # requested in the script cannot be found in the local property
            # cache. The name for this ADSI error code is
            # E_ADS_PROPERTY_NOT_FOUND.
        else:
            return last_changed
            
    def testAdd(self):
        class User:
            name = "user1337"    
            passwords = {}
            gecos = "The 1337 User"
        user = User()      
        self.aduser.add(user)
        self.hasAccount(user.name)
        self.assertEqual(self.lastChangedPassword(user.name), None)
        self.assertEqual(cscript("""
        set user = GetObject("LDAP://CN=%s,OU=%s,%s")
        Wscript.Echo user.saMAccountName
        """ % (user.name, self.ou, self.context)), user.name)
    
    def testAddWithPassword(self):     
        class User:
            name = "user1337"    
            passwords = {'cleartext': 'fishsoup'}
            gecos = "The 1337 User"
        user = User()      
        self.aduser.add(user)
        self.hasAccount(user.name)
        self.assertNotEqual(self.lastChangedPassword(user.name), None)

    def testUpdatePassword(self):     
        class User:
            name = "user1337"    
            passwords = {'cleartext': 'fishsoup'}
            gecos = "The 1337 User"
        user = User()      
        self.aduser.add(user)
        oldgid = self.accountGID(user.name)
        time.sleep(2) # Make sure we have time diff
        first_change = self.lastChangedPassword(user.name)
        self.aduser._update(user)
        last_change = self.lastChangedPassword(user.name)
        newgid = self.accountGID(user.name)
        self.assertEqual(oldgid, newgid)
        assert first_change < last_change
  
    def testAddDoesUpdate(self):
        class User:
            name = "user1337"    
            passwords = {'cleartext': 'fishsoup'}
            gecos = "The 1337 User"
        user = User()      
        self.aduser.add(user)
        oldgid = self.accountGID(user.name)
        time.sleep(2) # Make sure we have time diff
        first_change = self.lastChangedPassword(user.name)
        self.aduser.add(user)
        last_change = self.lastChangedPassword(user.name)
        newgid = self.accountGID(user.name)
        # if it was a real update, not an add, we should have the same GID
        self.assertEqual(oldgid, newgid)
        assert first_change < last_change
        # Should not report add -> update in non-incr
        self.assertEqual(self.lastLog(), "")
        # But if we are incr, we should not get an add on someone who
        # already exist
        self.aduser.begin(incr=True)
        self.aduser.add(user)
        self.assertEqual(self.lastLog(), 
        "WARNING: Already exists user1337, updating instead\n")
  
    def testUpdateDoesAdd(self):      
        class User:
            name = "user1337"    
            passwords = {'cleartext': 'fishsoup'}
            gecos = "The 1337 User"
        user = User()      
        self.aduser._update(user)
        self.hasAccount(user.name)
        self.assertEqual(self.lastLog(), 
        "WARNING: Did not exist user1337, adding instead\n")

class TestADGroup(TestOUFramework):
    def setUp(self):
        super(TestADGroup, self).setUp()
        self.adgroup = ADGroup(self.ou_uri)
        self.adgroup.begin()

    def testGroupInfo(self):
        class Group:
            name = "temp1337"
            members = []
        group = Group()    
        self.adgroup.add(group)    
        self.hasAccount()
        self.assertEqual(self.groupMembers(), [])
     
    def testGroupWithMember(self):
        self.createUser("user1337")
        class Group:
            name = "temp1337"
            members = ["user1337"]
        group = Group()    
        self.adgroup.add(group)    
        self.assertEqual(self.groupMembers(), group.members)
        
    def testGroupAddMember(self):
        self.createUser("user1337")
        self.createUser("user31337")
        self.createGroup()
        self.addGroupMember("user1337")
        old_gid = self.accountGID()
        class Group:
            name = "temp1337"
            members = ["user1337", "user31337"]
        group = Group()
        self.adgroup._update(group)    
        new_gid = self.accountGID()
        self.assertEqual(self.groupMembers(), group.members)
        self.assertEqual(old_gid, new_gid)
 
    def testGroupRemoveMember(self):
        self.createUser("user1337")
        self.createUser("user31337")
        self.createGroup()
        self.addGroupMember("user1337")
        self.addGroupMember("user31337")
        old_gid = self.accountGID()
        class Group:
            name = "temp1337"
            members = ["user31337"]
        group = Group()
        self.adgroup._update(group)
        new_gid = self.accountGID()
        self.assertEqual(self.groupMembers(), group.members)
        self.assertEqual(old_gid, new_gid)
 
    def testGroupAddUnknownAccount(self):
        self.createGroup()
        self.createUser("user31337") # but not user1337
        class Group:
            name = "temp1337"
            members = ["user1337", "user31337"]
        group = Group()
        self.adgroup.add(group)
        # did not fail, and did not include user1337 
        self.assertEqual(self.groupMembers(), ["user31337"])
       
    def testGroupAddUsersOutsideOu(self):
        self.createOU("other1337")
        # Even users outside our OU are to be included
        # (as we might (must!) have different OUs for groups and
        #  users)
        self.createUser("user1337", ou="other1337")
        self.createUser("user31337")
        self.createGroup() 
        class Group:
            name = "temp1337"
            members = ["user1337", "user31337"]
        group = Group()
        self.adgroup._update(group)
        self.assertEqual(self.groupMembers(), group.members)
    
    def testAddGroupAsMember(self):
        self.createGroup()    
        self.createGroup("other1337")
        self.createUser("user1337")
        class Group:
            name = "temp1337"
            members = ["user1337", "other31337"]
        group = Group()
        # should skip other31337 as group.members
        # is the EXPANDED list of members
        self.adgroup._update(group)
        # Actually supporting groups-in-groups requires 
        # spine support
        self.assertEqual(self.groupMembers(), ["user1337"])

    def testRemoveGroupAsMember(self):
        self.createGroup()    
        self.createGroup("other1337")
        self.createUser("user1337")
        self.addGroupMember("other1337")
        class Group:
            name = "temp1337"
            members = ["user1337"]
        group = Group()
        self.adgroup._update(group)
        self.assertEqual(self.groupMembers(), group.members)

    def tearDown(self):
        super(TestADGroup, self).tearDown()
        self.deleteOU("other1337")       

class TestHardcore(TestOUFramework):
    """More demanding and weird situations that we should handle."""

    def _testAddMany(self):
        """Adds 500 dummy users in a row to time AD operations.
        Disabled because this is a functional test, not a unit test.
        You can call it anyway like this:
            python adsi.py TestHardcore._testAddMany
        """
        adaccount = ADUser(self.ou_uri)
        adaccount.begin()
        class User:
            passwords = {'cleartext': 'fishsoup'}
            gecos = "The 1337 User"
        user = User()      
        bars = r"/-\|"
        for round in range(3):
            start = time.time()
            print " ",
            for x in xrange(500):
                if not(x % 5):
                    print "\010\010" + bars[(x/5)%4],
                user.name = "userX%s" % x
                if round == 3:
                    adaccount._update(user)
                else:    
                    adaccount.add(user)
            stop = time.time()    
            print "\010\010 "
            if round == 0:
                print "Added",
            elif round == 1:    
                print "Re-added",
            else:    
                print "Updated",
            print "500 users in %0.2f secs" % (stop-start)
        start = time.time()
        adaccount.begin()       
        adaccount.close() # Should delete those 500
        stop = time.time()
        print "Deleted 500 users in %0.2f secs" % (stop-start)
    
    def testUsernameIsReallyOU(self):
        """We might be asked to add a user that already exist as an OU"""
        self.createOU("temp1337", root="ou=tempOU,%s" % self.context)
        adaccount = ADUser(self.ou_uri)
        adaccount.begin()
        class User:
            passwords = {'cleartext': 'fishsoup'}
            gecos = "The 1337 User"
            name = "temp1337"
        user = User()      
        adaccount.add(user)
        adaccount.close()


if __name__ == "__main__":
    logging.warn("Note that these tests must be run as a domain administrator " 
    "locally on a domain controller to be able to create temporary OUs.")
    unittest.main()


# arch-tag: e76356d7-873f-4cb6-95a5-b852638f5524
