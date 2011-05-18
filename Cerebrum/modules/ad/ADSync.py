#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 University of Oslo, Norway
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

"""
Generic module for AD synchronisation

This module contains functionality for a generic AD synchronisation
script. A sync script must create a sync type instance, configure the
sync by sending a dict with configuration variables and run the
fullsync method. E.g.:

  sync = ADUserSync(db, logger, host, port, ad_domain_admin)
  sync.configure(config_args)
  sync.fullsync()

If the configuration mechanism doesn't offer enough flexibility just
write a subclass and overwrite the methods neccessary for a custom
sync.

"""


import cerebrum_path
import cereconf
from Cerebrum.Utils import Factory
from Cerebrum.modules.ad.CerebrumData import CerebrumUser, CerebrumGroup
from Cerebrum.modules.ad.ADUtils import ADUserUtils, ADGroupUtils
from Cerebrum import Errors


class ADUserSync(ADUserUtils):
    def __init__(self, db, logger, host, port, ad_domain_admin):
        """
        Connect to AD agent on host:port and initialize user sync.

        @param db: Connection to Cerebrum database
        @type db: Cerebrum.CLDatabase.CLDatabase
        @param logger: Cerebrum logger
        @type logger: Cerebrum.modules.cerelog.CerebrumLogger
        @param host: Server where AD agent runs
        @type host: str
        @param port: port number
        @type port: int
        @param ad_domain_admin: The user we connect to the AD agent as
        @type ad_domain_admin: str
        """

        ADUserUtils.__init__(self, logger, host, port, ad_domain_admin)
        self.db = db
        self.co = Factory.get("Constants")(self.db)
        self.ac = Factory.get("Account")(self.db)
        self.pe = Factory.get("Person")(self.db)
        self.accounts = dict()
        self.id2uname = dict()


    def configure(self, config_args):
        """
        Read configuration options from args and cereconf to decide
        which data to sync.

        @param config_args: Configuration data from cereconf and/or
                            command line options.
        @type config_args: dict
        """
        self.logger.info("Starting user-sync")
        # Sync settings for this module
        for k in ("user_spread", "user_exchange_spread", "forward_sync",
                  "exchange_sync", "delete_users", "dryrun", "ad_domain",
                  "ad_ldap", "store_sid", "ad_subset", "cb_subset"):
            if k in config_args:
                setattr(self, k, config_args.pop(k))
        
        # Set which attrs that are to be compared with AD
        self.sync_attrs = cereconf.AD_ATTRIBUTES
        if self.exchange_sync:
            self.sync_attrs += cereconf.AD_EXCHANGE_ATTRIBUTES

        self.logger.info("Configuration done. Will compare attributes: %s" %
                         ", ".join(self.sync_attrs))
        

    def fullsync(self):
        """
        This method defines what will be done in the sync.
        """
        # Fetch AD-data for users.     
        self.logger.debug("Fetching AD user data...")
        addump = self.fetch_ad_data()
        self.logger.info("Fetched %i AD users" % len(addump))

        # Fetch cerebrum data. store in self.accounts
        self.logger.debug("Fetching cerebrum user data...")
        self.fetch_cerebrum_data()
        # Calculate attribute values based on Cerebrum data for
        # comparison with AD
        for acc in self.accounts.itervalues():
            acc.calc_ad_attrs(exchange=self.exchange_sync)

        # TBD: move these two for loops to compare method?
        # Compare AD data with Cerebrum data
        for uname, ad_user in addump.iteritems():
            if uname in self.accounts:
                self.accounts[uname].in_ad = True
                self.compare(ad_user, self.accounts[uname])
            else:
                dn = ad_user["distinguishedName"]
                self.logger.debug("User %s in AD, but not in Cerebrum" % dn)
                # User in AD, but not in Cerebrum:
                # If user is in Cerebrum OU then deactivate
                if dn.upper().endswith(self.ad_ldap.upper()):
                    self.deactivate_user(ad_user)

        # Users exist in Cerebrum and has ad spread, but not in AD.
        # Create user if it's not quarantined
        for acc in self.accounts.itervalues():
            if acc.in_ad is False and acc.quarantined is False:
                sid = self.create_ad_account(acc.ad_attrs,
                                             self.get_default_ou())
                if sid and self.store_sid:
                    self.store_ext_sid(acc.account_id, sid)

        # Sync forward addresses and forward distribution groups if
        # forward sync option is true
        if self.forward_sync:
            self.fullsync_forward()
            
        # Update Exchange if exchange sync option is true
        if self.exchange_sync:
            #self.logger.debug("Sleeping for 5 seconds to give ad-ldap time to update") 
            #time.sleep(5)
            for acc in self.accounts.itervalues():
                if acc.update_recipient:
                    self.update_Exchange(acc.uname)
        
        self.logger.info("User-sync finished")


    def fullsync_forward(self):
        #Fetch ad data
        self.logger.debug("Fetching ad data about contact objects...")
        ad_contacts = self.fetch_ad_data_contacts()
        self.logger.info("Fetched %i ad forwards" % len(ad_contacts))

        # Fetch forward_info
        self.logger.debug("Fetching forwardinfo from cerebrum...")
        self.fetch_forward_info()
        for acc in self.accounts.itervalues():
            for fwd in acc.contact_objects:
                fwd.calc_forward_attrs()
        # Compare forward info 
        self.compare_forwards(ad_contacts)

        # Fetch ad dist group data
        self.logger.debug("Fetching ad data about distrubution groups...")
        ad_dist_groups = self.fetch_ad_data_distribution_groups()
        # create a distribution group for each cerebrum user with
        # forward addresses
        for acc in self.accounts.itervalues():
            if acc.contact_objects:
                acc.create_dist_group()
        # Compare dist group info
        # TBD: dist group sync should perhaps be a sub class of group
        # sync?
        self.compare_dist_groups(ad_dist_groups)
        self.sync_dist_group_members()


    def fetch_cerebrum_data(self):
        """
        Fetch users, name and email information for all users with the
        given spread. Create CerebrumUser instances and store in
        self.accounts.
        """
        # Find all users with relevant spread
        for row in self.ac.search(spread=self.user_spread):
            uname = row["name"].strip()
            # For testing or special cases where we only want to sync
            # a subset
            if self.cb_subset and uname not in self.cb_subset:
                continue
            self.accounts[uname] = self.cb_account(int(row["account_id"]),
                                                   int(row["owner_id"]),
                                                   uname)
            # We need to map account_id -> CerebrumUser as well 
            # TBD: join self.accounts and self.id2uname? 
            self.id2uname[int(row["account_id"])] = uname
        self.logger.info("Fetched %i cerebrum users with spread %s" % (
            len(self.accounts), self.user_spread))

        # Remove/mark quarantined users
        self.filter_quarantines()
        self.logger.info("Found %i quarantined users" % len(
            [1 for v in self.accounts.itervalues() if v.quarantined]))

        # fetch names
        self.logger.debug("..fetch name information..")
        self.fetch_names()
        
        # fetch contact info: phonenumber and title
        self.logger.debug("..fetch contact info..")
        self.fetch_contact_info()

        # fetch email info
        self.logger.debug("..fetch email info..")
        self.fetch_email_info()

        # Fetch exchange data and calculate attributes
        if self.exchange_sync:
            self.fetch_exchange_info()
    

    def cb_account(self, account_id, owner_id, uname):
        "wrapper func for easier subclassing"
        return CerebrumUser(account_id, owner_id, uname, self.ad_domain,
                            self.get_default_ou())


    def filter_quarantines(self):
        """
        Mark quarantined accounts for disabling/deletion.
        """
        quarantined_accounts = [int(row["entity_id"]) for row in
                                self.ac.list_entity_quarantines(only_active=True)]
        # Set quarantine flag
        for a_id in set(self.id2uname) & set(quarantined_accounts):
            self.logger.debug("Quarantine flag is set for %s" %
                              self.accounts[self.id2uname[a_id]])
            self.accounts[self.id2uname[a_id]].quarantined = True


    def fetch_names(self):
        """
        Fetch person names 
        """
        # Fetch names from Cerebrum for all persons
        # TBD: getdict_persons_names might be faster
        pid2names = {}
        for row in self.pe.list_persons_name(
            source_system = self.co.system_cached,
            name_type     = [self.co.name_first,
                             self.co.name_last]):
            pid2names.setdefault(int(row["person_id"]), {})[
                int(row["name_variant"])] = row["name"]
        # And set names for those relevant  
        for acc in self.accounts.itervalues():
            names = pid2names.get(acc.owner_id)
            if names:
                acc.name_first = names.get(int(self.co.name_first), "")
                acc.name_last = names.get(int(self.co.name_last), "")
            else:
                self.logger.warn("No name information for user " + acc.uname)
        

    def fetch_contact_info(self):
        """
        Get contact info: phonenumber and title. Personal title takes precedence.
        """
        pid2data = {}
        # Get phone number
        for row in self.pe.list_contact_info(source_system=self.co.system_sap,
                                             entity_type=self.co.entity_person,
                                             contact_type=self.co.contact_phone):
            pid2data.setdefault(int(row["entity_id"]), {})[
                int(row["contact_type"])] = row["contact_value"]
        # Get title
        for row in self.pe.list_persons_name(
            source_system = self.co.system_sap,
            name_type     = [self.co.name_personal_title,
                             self.co.name_work_title]):
            pid2data.setdefault(int(row["person_id"]), {})[
                int(row["name_variant"])] = row["name"]
        # set data
        for acc in self.accounts.itervalues():
            data = pid2data.get(acc.owner_id)
            if data:
                acc.contact_phone = data.get(int(self.co.contact_phone), "")
                acc.title = (data.get(int(self.co.name_personal_title), "") or
                             data.get(int(self.co.name_work_title), ""))
                

    def fetch_email_info(self):
        "Get primary email addresses from Cerebrum. "
        for uname, prim_mail in self.ac.getdict_uname2mailaddr(
            filter_expired=True, primary_only=True).iteritems():
            acc = self.accounts.get(uname, None)
            if acc:
                acc.email_addrs.append(prim_mail)


    def fetch_exchange_info(self):
        "Find all valid email addresses" 
        for uname, all_mail in self.ac.getdict_uname2mailaddr(
            filter_expired=True, primary_only=False).iteritems():
            acc = self.accounts.get(uname)
            if acc:
                acc.email_addrs.extend(all_mail)


    def fetch_forward_info(self):
        """
        Fetch forward info for all users with both AD and exchange spread.
        """ 
        from Cerebrum.modules.Email import EmailDomain, EmailTarget, EmailForward
        etarget = EmailTarget(self.db)
        rewrite = EmailDomain(self.db).rewrite_special_domains
        eforward = EmailForward(self.db)

        # We need a email target -> entity_id mapping
        target_id2target_entity_id = {}
        for row in etarget.list_email_targets_ext():
            if row['target_entity_id']:
                te_id = int(row['target_entity_id'])
                target_id2target_entity_id[int(row['target_id'])] = te_id

        # Check all email forwards
        for row in eforward.list_email_forwards():
            te_id = target_id2target_entity_id.get(int(row['target_id']))
            acc = self.get_account(account_id=te_id)
            # We're only interested in those with AD and exchange spread
            if acc.to_exchange:
                acc.add_forward(row['forward_to'])
                   

    def fetch_ad_data(self):
        """
        Fetch all or a subset of users in search_ou from AD.
        
        @return: AD attributes and values for AD objects of type
                 'user' in search_ou and child ous of this ou.
        @rtype: dict (uname -> {attr type: value} mapping)
        """
        # Setting the user attributes to be fetched.
        self.server.setUserAttributes(self.sync_attrs,
                                      cereconf.AD_ACCOUNT_CONTROL)
        ret = self.server.listObjects("user", True, self.ad_ldap)
        if self.ad_subset:
            return dict(zip(self.ad_subset,
                            (ret.get(u) for u in self.ad_subset)))
        return ret


    def fetch_ad_data_contacts(self):
        """
        Returns full LDAP path to AD objects of type 'contact' and prefix
        indicating it is used for forwarding.

        @return: a dict of dicts wich maps contact obects name to that
                 objects properties (dict)
        @rtype: dict
        """
        ret = dict()
        self.server.setContactAttributes(cereconf.AD_CONTACT_FORWARD_ATTRIBUTES)
        ad_contacts = self.server.listObjects('contact', True, self.ad_ldap)
        if ad_contacts:
            # Only deal with forwarding contact objects. 
            for object_name, properties in ad_contacts.iteritems():
                # TBD: cereconf-var?
                if object_name.startswith("Forward_for_"):
                    ret[object_name] = properties
        return ret
    

    def fetch_ad_data_distribution_groups(self):
        """
        Returns full LDAP path to AD objects of type 'group' and prefix
        indicating it is to hold forward contact objects.

        @rtype: dict
        @return: a dict of dict wich maps distribution group names to
                 distribution groupproperties (dict)
        """        
        ret = dict()
        self.server.setGroupAttributes(cereconf.AD_DIST_GRP_ATTRIBUTES)
        ad_dist_grps = self.server.listObjects('group', True, self.ad_ldap)
        if ad_dist_grps:
            # Only deal with forwarding groups. Groupsync deals with other groups.
            for grp_name, properties in ad_dist_grps.iteritems():
                if grp_name.startswith(cereconf.AD_FORWARD_GROUP_PREFIX):
                    ret[grp_name] = properties
        return ret


    def compare(self, ad_user, cb_user):
        """
        Compare Cerebrum user with the AD attributes listed in
        self.sync_attrs and decide if AD should be updated or not.

        @param ad_user: attributes for a user fetched from AD
        @type ad_user: dict 
        @param cb_user: CerebrumUser instance
        @type cb_user: CerebrumUser
        """
        cb_attrs = cb_user.ad_attrs
        # First check if user is quarantined. If so, disable
        if cb_attrs["ACCOUNTDISABLE"] and not ad_user["ACCOUNTDISABLE"]:
            self.disable_user(ad_user["distinguishedName"])
        
        # Check if user has correct OU. If not, move user
        if ad_user["distinguishedName"] != cb_attrs["distinguishedName"]:
            self.move_user(ad_user["distinguishedName"], cb_attrs["ou"])
            
        # Sync attributes
        for attr in self.sync_attrs:
            # Now, compare values from AD and Cerebrum
            cb_attr = cb_attrs.get(attr)
            ad_attr = ad_user.get(attr)
            if cb_attr and ad_attr:
                # value both in ad and cerebrum => compare
                result = self.attr_cmp(cb_attr, ad_attr)
                if result: 
                    self.logger.debug("Changing attr %s from %s to %s",
                                      attr, ad_attr, cb_attr)
                    cb_user.add_change(attr, result)
            elif cb_attr:
                # attribute is not in AD and cerebrum value is set => update AD
                cb_user.add_change(attr, cb_attr)
            elif ad_attr:
                # value only in ad => delete value in ad
                # TBD: is this correct behavior?
                cb_user.add_change(attr,"")

        # Special AD control attributes
        for attr, value in cereconf.AD_ACCOUNT_CONTROL.iteritems():
            if attr not in ad_user or ad_user[attr] != value:
                cb_user.add_change(attr, value)
                
        # Commit changes
        if cb_user.changes:
            self.commit_changes(ad_user["distinguishedName"], **cb_user.changes)


    def compare_forwards(self, ad_contacts):
        """
        Compare forward objects from AD with forward info in Cerebrum.

        @param ad_contacts: a dict of dicts wich maps contact obects
                            name to that objects properties (dict)
        @type ad_contacts: dict
        """
        for acc in self.accounts.itervalues():
            for contact in acc.contact_objects:
                cb_fwd = contact.forward_attrs
                ad_fwd = ad_contacts.pop(cb_fwd['sAMAccountName'], None)
                if not ad_fwd:
                    # Create AD contact object
                    self.create_ad_contact(cb_fwd, self.default_ou)
                    continue
                # contact object is in AD and Cerebrum -> compare OU
                # TBD: should OU's be compared?
                ou = "OU=%s,%s" % (cereconf.AD_CONTACT_OU, self.ad_ldap)
                cb_dn = 'CN=%s,%s' % (cb_fwd['sAMAccountName'], ou)
                if ad_fwd['distinguishedName'] != cb_dn:
                    self.move_contact(cb_dn, ou)

                # Compare other attributes
                for attr_type, cb_fwd_attr in fwd.iteritems():
                    ad_fwd_attr = ad_fwd.get(attr_type)
                    if cb_fwd_attr and ad_fwd_attr:
                        # value both in ad and cerebrum => compare
                        result = self.attr_cmp(cb_fwd_attr, ad_fwd_attr)
                        if result: 
                            self.logger.debug("Changing attr %s from %s to %s",
                                              attr, ad_fwd_attr, cb_fwd_attr)
                            cb_user.add_change(attr, result)
                    elif cb_fwd_attr:
                        # attribute is not in AD and cerebrum value is set => update AD
                        cb_user.add_change(attr, cb_fwd_attr)
                    elif ad_fwd_attr:
                        # value only in ad => delete value in ad
                        # TBD: is this correct behavior?
                        cb_user.add_change(attr,"")

            # Remaining contacts in AD should be deleted
            for ad_fwd in ad_contacts.itervalues():
                self.delete_contact()
                

    def get_default_ou(self):
        "Return default user ou"
        return "%s,%s" % (cereconf.AD_USER_OU, self.ad_ldap)
    

    def get_default_contacts_ou(self):
        "Return default user ou"
        return "%s,%s" % (cereconf.AD_CONTACT_OU, self.ad_ldap)
    

    def store_ext_sid(self, account_id, sid):
        self.ac.clear()
        self.ac.find(account_id)
        self.ac.affect_external_id(self.co.system_ad, 
                                   self.co.externalid_accountsid)
        self.ac.populate_external_id(self.co.system_ad, 
                                     self.co.externalid_accountsid, sid)
        self.ac.write_db()




class ADGroupSync(ADGroupUtils):
    def __init__(self, db, logger, host, port, ad_domain_admin):
        """
        Connect to AD agent on host:port and initialize group sync.

        @param db: Connection to Cerebrum database
        @type db: Cerebrum.CLDatabase.CLDatabase
        @param logger: Cerebrum logger
        @type logger: Cerebrum.modules.cerelog.CerebrumLogger
        @param host: Server where AD agent runs
        @type host: str
        @param port: port number
        @type port: int
        @param ad_domain_admin: The user we connect to the AD agent as
        @type ad_domain_admin: str
        """
        ADGroupUtils.__init__(self, logger, host, port, ad_domain_admin)
        self.db = db
        self.co = Factory.get("Constants")(self.db)
        self.group = Factory.get("Group")(self.db)
        self.groups = dict()
        

    def configure(self, config_args):
        """
        Read configuration options from args and cereconf to decide
        which data to sync.

        @param config_args: Configuration data from cereconf and/or
                            command line options.
        @type config_args: dict
        """
        # Settings for this module
        for k in ("group_spread", "group_exchange_spread", "user_spread"):
            # Group.search() must have spread constant or int to work,
            # unlike Account.search()
            if k in config_args:
                setattr(self, k, self.co.Spread(config_args[k]))
        for k in ("exchange_sync", "delete_groups", "dryrun", "store_sid",
                  "ad_ldap"):
            setattr(self, k, config_args[k])

        # Set which attrs that are to be compared with AD
        self.sync_attrs = cereconf.AD_GRP_ATTRIBUTES

        #CerebrumGroup.initialize(self.get_default_ou(),
        #                         config_args.get("ad_domain"))
        self.logger.info("Configuration done. Will compare attributes: %s" %
                         str(self.sync_attrs))


    def fullsync(self):
        """
        This method defines what will be done in the sync.
        """
        self.logger.info("Starting group-sync")
        # Fetch AD-data 
        self.logger.debug("Fetching AD group data...")
        addump = self.fetch_ad_data()
        self.logger.info("Fetched %i AD groups" % len(addump))

        #Fetch cerebrum data.
        self.logger.debug("Fetching cerebrum data...")
        self.fetch_cerebrum_data()

        # Compare AD data with Cerebrum data (not members)
        for gname, ad_group in addump.iteritems():
            if not gname.startswith(cereconf.AD_GROUP_PREFIX):
                self.logger.debug("Group %s doesn't start with correct prefix" %
                                  (gname))
                continue
            gname = gname[len(cereconf.AD_GROUP_PREFIX):]
            if gname in self.groups:
                self.groups[gname].in_ad = True
                self.compare(ad_group, self.groups[gname])
            else:
                self.logger.debug("Group %s in AD, but not in Cerebrum" % gname)
                # Group in AD, but not in Cerebrum:
                # Delete group if it's in Cerebrum OU and delete flag is True
                if (self.delete_groups and
                    ad_group["distinguishedName"].upper().endswith(self.ad_ldap.upper())):
                    self.delete_group(ad_group["distinguishedName"])

        # Create group if it exists in Cerebrum but is not in AD
        for grp in self.groups.itervalues():
            if grp.in_ad is False and grp.quarantined is False:
                sid = self.create_ad_group(grp.ad_attrs, self.get_default_ou())
                if sid and self.store_sid:
                    self.store_ext_sid(grp.group_id, sid)
            
        #Syncing group members
        self.logger.info("Starting sync of group members")
        self.sync_group_members()
        
        #updating Exchange
        #if self.exchange_sync:
        #    self.update_Exchange([g.name for g in self.groups.itervalues()
        #                          if g.update_recipient])
        
        #Commiting changes to DB (SID external ID) or not.
        if self.store_sid:
            if self.dryrun:
                self.db.rollback()
            else:
                self.db.commit()
            
        self.logger.info("Finished group-sync")


    def store_ext_sid(self, group_id, sid):
        self.group.clear()
        self.group.find(group_id)
        self.group.affect_external_id(self.co.system_ad, 
                                      self.co.externalid_groupsid)
        self.group.populate_external_id(self.co.system_ad, 
                                        self.co.externalid_groupsid, sid)
        self.group.write_db()


    def fetch_ad_data(self):
        """Get list of groups with  attributes from AD 
        
        @return: group name -> group info mapping
        @rtype: dict
        """
        self.server.setGroupAttributes(self.sync_attrs)
        return self.server.listObjects('group', True, self.get_default_ou())


    def fetch_cerebrum_data(self):
        """
        Fetch relevant cerebrum data for groups with the given spread.
        Create CerebrumGroup instances and store in self.groups.
        """
        # Fetch name, id and description
        for row in self.group.search(spread=self.group_spread):
            # TBD: Skal gruppenavn kunne være utenfor latin-1?
            gname = unicode(row["name"], cereconf.ENCODING)
            self.groups[gname] = CerebrumGroup(gname, row["group_id"],
                                               row["description"])
        self.logger.info("Fetched %i groups with spread %s",
                         len(self.groups), self.group_spread)
        # Fetch groups with exchange spread
        for row in self.group.search(spread=self.group_exchange_spread):
            g = self.groups.get(row["name"])
            if g:
                g.to_exchange = True
        self.logger.info("Fetched %i groups with both spread %s and %s" % 
                         (len([1 for g in self.groups.itervalues() if g.to_exchange]),
                          self.group_spread, self.group_exchange_spread))
        # Set attr values for comparison with AD
        for g in self.groups.itervalues():
            g.calc_ad_attrs()


    def compare(self, ad_group, cb_group):
        """
        Compare Cerebrum group with the AD attributes listed in
        self.sync_attrs and decide if AD should be updated or not.

        @param ad_group: attributes for a group fetched from AD
        @type ad_group: dict 
        @param cb_group: CerebrumGroup instance
        @type cb_group: CerebrumGroup
        """
        cb_attrs = cb_group.ad_attrs
        for attr in self.sync_attrs:            
            cb_attr = cb_attrs.get(attr)
            ad_attr   = ad_group.get(attr)
            #self.logger.debug("attr: %s, c: %s, %s, a: %s, %s" % (
            #    attr, type(cb_attr), cb_attr, type(ad_attr), ad_attr))
            if cb_attr and ad_attr:
                # value both in ad and cerebrum => compare
                result = self.attr_cmp(cb_attr, ad_attr)
                if result: 
                    self.logger.debug("Changing attr %s from %s to %s",
                                      attr, ad_attr, cb_attr)
                    cb_group.add_change(attr, result)
            elif cb_attr:
                # attribute is not in AD and cerebrum value is set => update AD
                cb_group.add_change(attr, cb_attr)
            elif ad_attr:
                # value only in ad => delete value in ad
                cb_group.add_change(attr,"")
                
        # Commit changes
        if cb_group.changes:
            self.commit_changes(ad_group["distinguishedName"], **cb_group.changes)


    def get_default_ou(self):
        """
        Return default OU for groups.
        """
        return "%s,%s" % (cereconf.AD_GROUP_OU, self.ad_ldap)


    def sync_group_members(self):
        """
        Update group memberships in AD.
        """
        # TBD: Should we compare before sending members or just send them all?
        # Check all cerebrum groups with given spread
        for grp in self.groups.itervalues():
            # Find account members
            members = list()
            for usr in self.group.search_members(group_id=grp.group_id,
                                                 member_spread=self.user_spread,
                                                 include_member_entity_name=True):
                uname = usr['member_name']
                if uname:
                    members.append(uname)
            
            # Find group members
            for memgrp in self.group.search_members(group_id=grp.group_id,
                                                    member_spread=self.group_spread):
                gname = memgrp.get('member_name')
                if gname:
                    members.append('%s%s' % (cereconf.AD_GROUP_PREFIX, gname))
            
            # Sync members
            self.sync_members(grp.ad_attrs.get("distinguishedName"), members)

