#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Copyright 2006-2011 University of Oslo, Norway
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

import cerebrum_path
import cereconf
import xmlrpclib
import re

from Cerebrum.Utils import Factory, read_password


class ADutil(object):

    def __init__(self, db, co, logger,
                 host=cereconf.AD_SERVER_HOST, port=cereconf.AD_SERVER_PORT,
                 url=None, ad_ldap=cereconf.AD_LDAP, dry_run=False):
        """
        Initialize AD syncronization, i.e. connect to AD service on
        given host.
        """
        self.db = db
        self.co = co
        self.logger = logger
        ad_domain_admin = cereconf.AD_DOMAIN_ADMIN_USER
        try:
            if url is None:
                password = read_password(ad_domain_admin, host)
                url = "https://%s:%s@%s:%i" % (ad_domain_admin, password,
                                               host, port)
            else:
                m = re.match(r'([^:]+)://([^:]+):(\d+)', url)
                if not m:
                    raise ValueError, "Error parsing URL: %s" % url
                protocol = m.group(1)
                host = m.group(2)
                port = m.group(3)
                password = read_password(ad_domain_admin, host)
                url = "%s://%s:%s@%s:%s" % (
                    protocol,
                    ad_domain_admin,
                    password,
                    host,
                    port)
            self.server = xmlrpclib.Server(url)
        except IOError, e:
            if not dry_run:
                raise e
            self.logger.critical(e)
            self.logger.error(
                "No AD connection, so dryrunning cerebrum code only")
            from Cerebrum.modules.ad import ADTesting
            self.server = ADTesting.MockADServer(self.logger)
        self.ad_ldap = ad_ldap

    def run_cmd(self, command, dry_run, arg1=None, arg2=None, arg3=None):

        if dry_run:
            nr_args = 0
            for i in (arg1, arg1, arg2):
                if i:
                    nr_args += 1
            self.logger.debug(
                'Dryrun of server.%s(%d args)' %
                (command, nr_args))
            # Assume success on all changes.
            # Note that some commands are required to return a tuple of either
            # two or three, so this might not always work.
            return (True, command, None)
        else:
            cmd = getattr(self.server, command)
            try:
                if arg1 is None:
                    ret = cmd()
                elif arg2 is None:
                    ret = cmd(arg1)
                elif arg3 is None:
                    ret = cmd(arg1, arg2)
                else:
                    ret = cmd(arg1, arg2, arg3)
            except xmlrpclib.ProtocolError, xpe:
                self.logger.critical("Error connecting to AD service. Giving up!: %s %s" %
                                     (xpe.errcode, xpe.errmsg))
                return [None]
            except Exception, e:
                self.logger.error("Unexpected exception", exc_info=1)
                self.logger.debug(
                    "Command: %s" %
                    repr((command, dry_run, arg1, arg2, arg3)))
                return [None]
            return ret

    def get_default_ou(self, change=None):
        """Returns the default OU in AD. Note that self.ad_ldap is always
        appended. This is normally retrieved from cereconf.AD_LDAP.

        """
        return "CN=Users,%s" % self.ad_ldap

    def move_object(self, chg, dry_run):
        ret = self.run_cmd('moveObject', dry_run, chg['OU'])
        if not ret[0]:
            self.logger.warning("moveObject on %s failed: %r" %
                               (chg['distinguishedName'], ret))

    def delete_object(self, chg, dry_run):
        self.logger.debug('DELETE %s', chg)
        ret = self.run_cmd('deleteObject', dry_run)
        if not ret[0]:
            self.logger.warning("%s on %s failed: %r" %
                               (chg['type'], chg['distinguishedName'], ret))

    def create_object(self, chg, dry_run):
        self.logger.debug('CREATE %s', chg)
        ret = self.run_cmd('createObject', dry_run, 'Group', chg['OU'],
                           chg['sAMAccountName'])
        if not ret[0]:
            self.logger.warn(ret[1])

    def alter_object(self, chg, dry_run):

        distName = chg['distinguishedName']
        # Already binded,we do not want too sync the defaultvalues
        del chg['type']
        del chg['distinguishedName']

        ret = self.run_cmd('putProperties', dry_run, chg)
        if not ret[0]:
            self.logger.warning("putproperties on %s failed: %r" %
                               (distName, ret))
        else:
            ret = self.run_cmd('setObject', dry_run)
            if not ret[0]:
                self.logger.warning("setObject on %s failed: %r" %
                                   (distName, ret))

    def perform_changes(self, changelist, dry_run):
        if isinstance(changelist, dict):
            changelist = (changelist,)
        for chg in changelist:
            self.logger.debug("Process change: %s" % repr(chg))
            if chg['type'] == 'create_object':
                self.create_object(chg, dry_run)
            else:
                ret = self.run_cmd('bindObject', dry_run,
                                   chg['distinguishedName'])
                if not ret[0]:
                    self.logger.warning("bindObject on %s failed: %r" %
                                       (chg['distinguishedName'], ret))
                else:
                    func = getattr(self, chg['type'])
                    func(chg, dry_run)

    def full_sync(self, type, delete, spread, dry_run, user_spread=None):

        self.logger.info("Starting %s-sync(delete = %s, dry_run = %s)" %
                        (type, delete, dry_run))

        # Fetch cerebrum data.
        self.logger.debug("Fetching cerebrum data...")
        cerebrumdump = self.fetch_cerebrum_data(spread)
        self.logger.info("Fetched %i cerebrum %ss" % (len(cerebrumdump), type))

        # Fetch AD-data.
        self.logger.debug("Fetching AD data...")
        addump = self.fetch_ad_data()
        self.logger.info("Fetched %i ad-%ss" % (len(addump), type))

        # compare cerebrum and ad-data.
        changelist = self.compare(delete, cerebrumdump, addump)
        self.logger.info("Found %i number of changes" % len(changelist))

        # Cleaning up.
        addump = None
        if type == 'user':
            cerebrumdump = None

        # Perform changes.
        self.perform_changes(changelist, dry_run)

        if type == 'group':
            self.logger.info("Starting sync of group members")
            self.sync_groups(cerebrumdump, spread,
                             user_spread, dry_run)

        self.logger.info("Finished %s-sync" % type)


class ADgroupUtil(ADutil):

    def __init__(self, *args, **kwargs):
        super(ADgroupUtil, self).__init__(*args, **kwargs)
        self.group = Factory.get('Group')(self.db)

    def fetch_cerebrum_data(self, spread):
        return list(self.group.search(spread=spread))

    def fetch_ad_data(self):
        return self.server.listObjects('group', True)

    def sync_groups(self, cerebrumgroups, group_spread, user_spread, dry_run):
        # To reduce traffic, we send current list of groupmembers to AD, and the
        # server ensures that each group have correct members.

        const = Factory.get("Constants")(self.db)
        entity2name = dict([(x["entity_id"], x["entity_name"]) for x in
                           self.group.list_names(const.account_namespace)])
        entity2name.update([(x["entity_id"], x["entity_name"]) for x in
                           self.group.list_names(const.group_namespace)])

        for (grp_id, grp_name, grp_desc) in cerebrumgroups:
            # Only interested in union members(believe this is only type in
            # use)
            grp_name = unicode(grp_name, 'ISO-8859-1')
            self.logger.debug("Sync group %s" % grp_name)

            # TODO: How to treat quarantined users???, some exist in AD,
            # others do not. They generate errors when not in AD. We still
            # want to update group membership if in AD.
            members = list()
            for usr in self.group.search_members(group_id=grp_id,
                                                 member_spread=user_spread):
                user_id = usr["member_id"]
                if user_id not in entity2name:
                    self.logger.debug(
                        "Missing name for account id=%s",
                        user_id)
                    continue
                members.append(entity2name[user_id])
                self.logger.debug2("Try to sync member account id=%s, name=%s",
                                   user_id, entity2name[user_id])

            for grp in self.group.search_members(group_id=grp_id,
                                                 member_spread=group_spread):
                group_id = grp["member_id"]
                if group_id not in entity2name:
                    self.logger.debug("Missing name for group id=%s", group_id)
                    continue
                members.append('%s%s' % (entity2name[group_id],
                                         cereconf.AD_GROUP_POSTFIX))
                self.logger.debug2("Try to sync member group id=%s, name=%s",
                                   group_id, entity2name[group_id])

            dn = self.server.findObject('%s%s' %
                                        (grp_name, cereconf.AD_GROUP_POSTFIX))
            if not dn:
                self.logger.debug("unknown group: %s%s",
                                  grp_name, cereconf.AD_GROUP_POSTFIX)
            elif dry_run:
                self.logger.debug("Dryrun: don't sync members")
            else:
                self.server.bindObject(dn)
                res = self.server.syncMembers(members, False, False)
                if not res[0]:
                    self.logger.warn("syncMembers %s failed for:%r" %
                                    (dn, res[1:]))
                # Sync description
                if grp_desc is None:
                    grp_desc = "Not available"
                self.server.setObjectProperties(
                    {'Description': unicode(grp_desc, 'ISO-8859-1')})
                self.server.setObject()

    def compare(self, delete_groups, cerebrumgrp, adgrp):
        changelist = []
        for (grp_id, grp, description) in cerebrumgrp:
            ou = self.get_default_ou(grp_id)
            grp = unicode(grp, 'ISO-8859-1')

            if 'CN=%s%s,%s' % (grp, cereconf.AD_GROUP_POSTFIX, ou) in adgrp:
                adgrp.remove('CN=%s%s,%s' % (
                    grp, cereconf.AD_GROUP_POSTFIX, ou))
            else:
                # Group not in AD,or wrong OU create.
                ou_in_ad = self.server.findObject('%s%s' % (
                    grp, cereconf.AD_GROUP_POSTFIX))

                if not ou_in_ad:
                    # Not in AD, create.
                    changelist.append({'type': 'create_object',
                                       'sAMAccountName': '%s%s' %
                                       (grp, cereconf.AD_GROUP_POSTFIX),
                                       'OU': ou,
                                       'description': description})
                else:
                    # In AD, wrong OU.
                    changelist.append({'type': 'move_object',
                                       'distinguishedName': ou_in_ad,
                                       'OU': ou})

        # TODO: Builtin can be listed in AD_DO_NOT_TOUCH as well, so
        #       one line can be removed below
        # The remaining groups is surplus in AD.
        for adg in adgrp:
            # Assume that cereconf.AD_DO_NOT_TOUCH is a list
            # Check if at least one of the list elements is a substring of adg
            # If delete_groups is False, then don't delete the group

            if re.search('CN=Builtin,', adg):
                continue

            match = None
            for dont in cereconf.AD_DO_NOT_TOUCH:
                if re.search(dont, adg):
                    match = True
                    break

            if match:
                continue

            if not delete_groups:
                self.logger.debug(
                    "delete is False. Don't delete group: %s",
                    adg)
            else:
                self.logger.debug("delete_groups = %s, deleting group %s",
                                  delete_groups, adg)
                changelist.append({'type': 'delete_object',
                                   'distinguishedName': adg})

        return changelist


class ADuserUtil(ADutil):

    def __init__(self, *args, **kwargs):
        super(ADuserUtil, self).__init__(*args, **kwargs)
        self.ac = Factory.get('Account')(self.db)

    def fetch_ad_data(self):
        # Setting the userattributes to be fetched.
        self.server.setUserAttributes(cereconf.AD_ATTRIBUTES,
                                      cereconf.AD_ACCOUNT_CONTROL)

        return self.server.listObjects('user', True)

    def fetch_cerebrum_data(self, spread):
        """
        Return a dict of dicts with the sAMAccountName as key. The key
        contain a dict with the keys found in the AD_ATTRIBUTES list.
        This method is left empty for each institution to override
        with local settings.

        Mandatory values in dict is: distinguishedName.

        The value OU is optional, and is not an AD_ATTRIBUTE value, if
        OU is present it will override the get_default_OU method. If
        homeDrive attribute is present it will override the
        get_homedrive method. If the value of an AD_ATTRIBUTE in the
        dict is a list it is assumed to be a multivalued attribute in
        AD when syncronizing.
        """
        pass

    def get_home_drive(self, cerebrum_usrdict):
        # Returns default home drive in AD.
        return cerebrum_usrdict.get('homeDrive', cereconf.AD_HOME_DRIVE)

    def create_object(self, chg, dry_run):

        if chg.has_key('OU'):
            ou = chg['OU']
        else:
            ou = self.get_default_ou(chg)

        ret = self.run_cmd('createObject', dry_run, 'User', ou,
                           chg['sAMAccountName'])

        if not ret[0]:
            self.logger.warning("create user %s failed: %r" %
                                (chg['sAMAccountName'], ret))
        else:
            if not dry_run:
                self.logger.info("created user %s" % ret)

            pw = unicode(self.ac.make_passwd(chg['sAMAccountName']),
                         'iso-8859-1')

            ret = self.run_cmd('setPassword', dry_run, pw)
            if not ret[0]:
                self.logger.warning("setPassword on %s failed: %s" %
                                    (chg['sAMAccountName'], ret))
            else:
                # Important not to enable a new account if setPassword
                # fail, it will have a blank password.

                uname = ""
                del chg['type']
                if chg.has_key('distinguishedName'):
                    del chg['distinguishedName']
                if chg.has_key('sAMAccountName'):
                    uname = chg['sAMAccountName']
                    del chg['sAMAccountName']

                # Setting default for undefined AD_ACCOUNT_CONTROL values.
                for acc, value in cereconf.AD_ACCOUNT_CONTROL.items():
                    if not chg.has_key(acc):
                        chg[acc] = value

                ret = self.run_cmd('putProperties', dry_run, chg)
                if not ret[0]:
                    self.logger.warning("putproperties on %s failed: %r" %
                                       (uname, ret))

                ret = self.run_cmd('setObject', dry_run)
                if not ret[0]:
                    self.logger.warning(
                        "setObject on %s failed: %r",
                        uname,
                        ret)

    # FIXME: Rewrite this mess. This is just ... ugly :(
    # what is this I don't even
    def compare(self, delete_users, cerebrumusrs, adusrs):
        # Keys in dict from cerebrum must match fields to be populated in AD.

        changelist = []

        for usr, dta in adusrs.items():
            changes = {}
            if cerebrumusrs.has_key(usr):
                # User is both places, we want to check correct data.

                # Checking for correct OU.
                if cerebrumusrs[usr].has_key('OU'):
                    ou = cerebrumusrs[usr]['OU']
                else:
                    tmp = self.get_default_ou(cerebrumusrs[usr])
                    ou = tmp
                dn = 'cn=%s,%s' % (usr, ou)
                if adusrs[usr]['distinguishedName'].lower() != dn.lower():
                    changes['type'] = 'move_object'
                    changes['OU'] = ou
                    changes['distinguishedName'] = \
                        adusrs[usr]['distinguishedName']
                    # Submit list and clean.
                    changelist.append(changes)
                    changes = {}

                for attr in cereconf.AD_ATTRIBUTES:
                    # Catching special cases.
                    # Check against home drive.
                    if attr == 'homeDrive':
                        home_drive = self.get_home_drive(cerebrumusrs[usr])
                        if adusrs[usr].get('homeDrive') != home_drive:
                            changes['homeDrive'] = home_drive

                    # Treating general cases
                    else:
                        if cerebrumusrs[usr].has_key(attr) and \
                                adusrs[usr].has_key(attr):
                            if isinstance(cerebrumusrs[usr][attr], (list)):
                                # Multivalued, it is assumed that a
                                # multivalue in cerebrumusrs always is
                                # represented as a list.
                                Mchange = False

                                if isinstance(adusrs[usr][attr], (str, int, long, unicode)):
                                    # Transform single-value to a list for
                                    # comparison.
                                    val2list = []
                                    val2list.append(adusrs[usr][attr])
                                    adusrs[usr][attr] = val2list

                                for val in cerebrumusrs[usr][attr]:
                                    if val not in adusrs[usr][attr]:
                                        Mchange = True

                                if Mchange:
                                    changes[attr] = cerebrumusrs[usr][attr]
                            else:
                                if adusrs[usr][attr] != cerebrumusrs[usr][attr]:
                                    changes[attr] = cerebrumusrs[usr][attr]
                        else:
                            if cerebrumusrs[usr].has_key(attr):
                                # A blank value in cerebrum and <not
                                # set> in AD -> do nothing.
                                if cerebrumusrs[usr][attr] != "":
                                    changes[attr] = cerebrumusrs[usr][attr]
                            elif adusrs[usr].has_key(attr):
                                # Delete value
                                changes[attr] = ''

                for acc, value in cereconf.AD_ACCOUNT_CONTROL.items():
                    if cerebrumusrs[usr].has_key(acc):
                        if adusrs[usr].has_key(acc) and \
                                adusrs[usr][acc] == cerebrumusrs[usr][acc]:
                            pass
                        else:
                            changes[acc] = cerebrumusrs[usr][acc]

                    else:
                        if adusrs[usr].has_key(acc) and adusrs[usr][acc] == \
                                value:
                            pass
                        else:
                            changes[acc] = value

                # Submit if any changes.
                if len(changes):
                    changes['distinguishedName'] = 'CN=%s,%s' % (usr, ou)
                    changes['type'] = 'alter_object'

                # after processing we delete from array.
                del cerebrumusrs[usr]

            else:
                # Account not in Cerebrum, but in AD.
                if [s for s in cereconf.AD_DO_NOT_TOUCH if
                        adusrs[usr]['distinguishedName'].find(s) >= 0]:
                    pass
                elif adusrs[usr]['distinguishedName'].find(cereconf.AD_PW_EXCEPTION_OU) >= 0:
                    # Account do not have AD_spread, but is in AD to
                    # register password changes, do nothing.
                    pass
                else:
                    # ac.is_deleted() or ac.is_expired() pluss a small rest of
                    # accounts created in AD, but that do not have AD_spread.
                    if bool(delete_users):
                        changes['type'] = 'delete_object'
                        changes[
                            'distinguishedName'] = adusrs[
                                usr][
                                    'distinguishedName']
                    else:
                        # Disable account.
                        if not bool(adusrs[usr]['ACCOUNTDISABLE']):
                            changes[
                                'distinguishedName'] = adusrs[
                                    usr][
                                        'distinguishedName']
                            changes['type'] = 'alter_object'
                            changes['ACCOUNTDISABLE'] = True
                            # commit changes
                            changelist.append(changes)
                            changes = {}
                        # Moving account.
                        if adusrs[usr]['distinguishedName'] != "CN=%s,OU=%s,%s" % \
                                (usr, cereconf.AD_LOST_AND_FOUND, self.ad_ldap):
                            changes['type'] = 'move_object'
                            changes[
                                'distinguishedName'] = adusrs[
                                    usr][
                                        'distinguishedName']
                            changes['OU'] = "OU=%s,%s" % \
                                (cereconf.AD_LOST_AND_FOUND, self.ad_ldap)

            # Finished processing user, register changes if any.
            if len(changes):
                changelist.append(changes)

        # The remaining items in cerebrumusrs is not in AD, create user.
        for cusr, cdta in cerebrumusrs.items():
            changes = {}
            # TBD: Should quarantined users be created?
            if cerebrumusrs[cusr]['ACCOUNTDISABLE']:
                # Quarantined, do not create.
                pass
            else:
                # New user, create.
                changes = cdta
                changes['type'] = 'create_object'
                changes['sAMAccountName'] = cusr
                changes['homeDrive'] = self.get_home_drive(cdta)
                changelist.append(changes)

        return changelist
