# -*- coding: iso-8859-1 -*-
# Copyright 2003-2005 University of Oslo, Norway
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

""""""

import random

import re
import cereconf
from mx import DateTime
from Cerebrum import Account
from Cerebrum import Errors
from Cerebrum.modules import Email
from Cerebrum.modules import PasswordHistory
from Cerebrum.modules.no.uio.DiskQuota import DiskQuota
from Cerebrum.modules.bofhd.utils import BofhdRequests
from Cerebrum.Utils import pgp_encrypt, Factory

class AccountUiOMixin(Account.Account):
    """Account mixin class providing functionality specific to UiO.

    The methods of the core Account class that are overridden here,
    ensure that any Account objects generated through
    Cerebrum.Utils.Factory.get() provide functionality that reflects
    the policies of the University of Oslo.

    """

    def add_spread(self, spread):
        #
        # Pre-add checks
        #
        spreads = [int(r['spread']) for r in self.get_spread()]
        # All users in the 'ifi' NIS domain must also exist in the
        # 'uio' NIS domain.
        if spread == self.const.spread_ifi_nis_user \
               and int(self.const.spread_uio_nis_user) not in spreads:
            raise self._db.IntegrityError, \
                  "Can't add ifi spread to an account without uio spread."
        #
        # Gather information on present state, to be used later.  Note
        # that this information gathering must be done before we pass
        # control to our superclass(es), as the superclass methods
        # might change the state.
        state = {}
        if spread == self.const.spread_uio_imap:
            # Is this account already associated with an Cyrus
            # EmailTarget?
            et = Email.EmailTarget(self._db)
            try:
                et.find_by_target_entity(self.entity_id)
                if et.email_server_id:
                    state['email_server_id'] = et.email_server_id
            except Errors.NotFoundError:
                pass
        #
        # (Try to) perform the actual spread addition.
        ret = self.__super.add_spread(spread)
        #
        # Additional post-add magic
        #
        if spread == self.const.spread_uio_imap:
            # Unless this account already has been associated with an
            # Cyrus EmailTarget, we need to do so.
            if et.email_server_id:
                old_server = et.email_server_id
            et = self._UiO_update_email_server(self.const.email_server_type_cyrus)
            # this is no longer necessary because we have changed
            # _UiO_update_email_server.
            # TODO: rewrite this, jazz 2008-08-20
            # 
            # if et.email_server_id != old_server:
            # self._UiO_order_cyrus_action(self.const.bofh_email_create,
            #                            et.email_server_id)
            
            # Make sure that Cyrus is told about the quota, the
            # previous call probably didn't change the database value
            # and therefore didn't add a request.
            # this is not very good, we should do something about
            # update_email_quota not using order_cyrus_action and
            # order_cyrus_action in general.
            self.update_email_quota(force=True)
            # register default spam and filter settings
            self._UiO_default_spam_settings(et)
            self._UiO_default_filter_settings(et)
            # The user's email target is now associated with an email
            # server; try generating email addresses connected to the
            # target.
            self.update_email_addresses()
        elif spread == self.const.spread_ifi_nis_user:
            # Add an account_home entry pointing to the same disk as
            # the uio spread
            try:
                tmp = self.get_home(self.const.spread_uio_nis_user)
                self.set_home(spread, tmp['homedir_id'])
            except Errors.NotFoundError:
                pass  # User has no homedir for this spread yet
        elif spread == self.const.spread_uio_notes_account:
            if self.owner_type == self.const.entity_group:
                raise self._db.IntegrityError, \
                      "Cannot add Notes-spread to a non-personal account."
        return ret

    def create(self, owner_type, owner_id, np_type, creator_id,
               expire_date=None, parent=None, name=None):
        """UiO specific functionality for creating a regular account."""
        self.__super.create(name=name, owner_type=owner_type, owner_id=owner_id,
                            np_type=np_type, creator_id=creator_id,
                            expire_date=expire_date, parent=parent)
        # TODO: use BofhdRequest

    def set_home(self, spread, homedir_id):
        ret = self.__super.set_home(spread, homedir_id)
        spreads = [int(r['spread']) for r in self.get_spread()]
        if spread == self.const.spread_uio_nis_user \
           and int(self.const.spread_ifi_nis_user) in spreads:
            self.__super.set_home(self.const.spread_ifi_nis_user, homedir_id)

    def _UiO_default_filter_settings(self, email_target):
        t_id = email_target.entity_id
        tt_str = str(Email._EmailTargetCode(email_target.email_target_type))
        # Set default filters if none found on this target
        etf = Email.EmailTargetFilter(self._db)
        if cereconf.EMAIL_DEFAULT_FILTERS.has_key(tt_str):
            for f in cereconf.EMAIL_DEFAULT_FILTERS[tt_str]:
                f_id = int(Email._EmailTargetFilterCode(f))
                try:
                    etf.clear()
                    etf.find(t_id, f_id)
                except Errors.NotFoundError:
                    etf.clear()
                    etf.populate(f_id, parent=email_target)
                    etf.write_db()
        
    def _UiO_default_spam_settings(self, email_target):
        t_id = email_target.entity_id
        tt_str = str(Email._EmailTargetCode(email_target.email_target_type))
        # Set default spam settings if none found on this target
        esf = Email.EmailSpamFilter(self._db)
        if cereconf.EMAIL_DEFAULT_SPAM_SETTINGS.has_key(tt_str):
            if not len(cereconf.EMAIL_DEFAULT_SPAM_SETTINGS[tt_str]) == 2:
                raise Errors.CerebrumError, "Error in " +\
                      "cereconf.EMAIL_DEFAULT_SPAM_SETTINGS. Expected 'key': " +\
                      "('val', 'val')"
            l, a = cereconf.EMAIL_DEFAULT_SPAM_SETTINGS[tt_str]
            lvl = int(Email._EmailSpamLevelCode(l))
            act = int(Email._EmailSpamActionCode(a))
            try:
                esf.find(t_id)
            except Errors.NotFoundError:
                esf.clear()
                esf.populate(lvl, act, parent=email_target)
                esf.write_db()

    def _UiO_order_cyrus_action(self, action, destination, state_data=None):
        br = BofhdRequests(self._db, self.const)
        # If there are any registered BofhdRequests for this account
        # that would conflict with 'action', remove them.
        for anti_action in br.get_conflicts(action):
            for r in br.get_requests(entity_id=self.entity_id,
                                     operation=anti_action):
                self.logger.info("Removing BofhdRequest #%d: %r",
                                 r['request_id'], r)
                br.delete_request(request_id=r['request_id'])
        # If the ChangeLog module knows who the user requesting this
        # change is, use that knowledge.  Otherwise, set requestor to
        # None; it's the best we can do.
        requestor = getattr(self._db, 'change_by', None)
        # Register a BofhdRequest to create the mailbox.
        reqid = br.add_request(requestor,
                               br.now, action, self.entity_id, destination,
                               state_data=state_data)

    def set_password(self, plaintext):
        # Override Account.set_password so that we get a copy of the
        # plaintext password
        self.__plaintext_password = plaintext
        self.__super.set_password(plaintext)

    def populate(self, name, owner_type, owner_id, np_type, creator_id,
                 expire_date, parent=None):
        """Override to check that the account name is not already taken by a
        group.
        """
        gr = Factory.get('Group')(self._db)
        try:
            gr.find_by_name(name)
        except Errors.NotFoundError:
            pass
        else:
            raise Errors.CerebrumError('Account name taken by group: %s' % name)
        return self.__super.populate(name, owner_type, owner_id, np_type,
                                     creator_id, expire_date, parent=parent)

    def write_db(self):
        try:
            plain = self.__plaintext_password
        except AttributeError:
            plain = None
        ret = self.__super.write_db()
        if plain is not None:
            ph = PasswordHistory.PasswordHistory(self._db)
            ph.add_history(self, plain)
        return ret

    def _UiO_update_email_server(self, server_type):
        """Due to diverse legacy stuff and changes in server types as
           well as requirements for assigning e-mail accounts this
           process is getting rather complicated. The email servers are
           now assigned as follows:

            - create on new server, update target_type = CNS
            - create on old server, update target_type = COS
            - move to new server   = MNS

       t_type/srv_type| none| cyrus, active| cyrus,non-active| non-cyrus 
       ------------------------------------------------------------------
       target_deleted | CNS | COS          | CNS             | CNS
       ------------------------------------------------------------------
       target_account | MNS | PASS         | MNS             | MNS
       ------------------------------------------------------------------
        """

        et = Email.EmailTarget(self._db)
        es = Email.EmailServer(self._db)
        new_server = None
        old_server = None
        srv_is_cyrus = False
        email_server_in_use = False
        target_type = self.const.email_target_account
        # Find the account's EmailTarget
        try:
            et.find_by_target_entity(self.entity_id)
            if et.email_target_type == self.const.email_target_deleted:
                target_type = self.const.email_target_deleted
        except Errors.NotFoundError:
            # No EmailTarget found for account, creating one
            et.populate(self.const.email_target_account,
                        self.entity_id,
                        self.const.entity_account)
            et.write_db()
        # Find old server id and type
        try:
            old_server = et.email_server_id
            es.find(old_server)
            if es.email_server_type == self.const.email_server_type_cyrus:
                srv_is_cyrus = True
            email_server_in_use = es.get_trait(self.const.trait_email_server_weight)
        except Errors.NotFoundError:
            pass
        # Different actions for target_type deleted and account
        if target_type == self.const.email_target_account:
            if srv_is_cyrus and email_server_in_use:
                # both target and server type er ok, do nothing
                pass
            elif old_server == None:
                # EmailTarget with no registered server
                new_server = self._pick_email_server()
                et.email_server_id = new_server
                et.write_db()
                self._UiO_order_cyrus_action(self.const.bofh_email_create,
                                             new_server)
            else:
                # cyrus_nonactive or non_cyrus
                new_server = self._pick_email_server()
                et.email_server_id = new_server
                et.write_db()
                self._UiO_order_cyrus_action(self.const.bofh_email_move,
                                             new_server)
        elif target_type == self.const.email_target_deleted:
            if srv_is_cyrus and email_server_in_use:
                # Create cyrus account on active server
                self._UiO_order_cyrus_action(self.const.bofh_email_create,
                                             old_server)
            else:
                # Pick new server and create cyrus account
                new_server = self._pick_email_server()
                et.email_server_id = new_server
                et.write_db()
                self._UiO_order_cyrus_action(self.const.bofh_email_create,
                                             new_server)
        return et


    def _pick_email_server(self):
            # We try to spread the usage across servers, but want a
            # random component to the choice of server.  The choice is
            # weighted, although the determination of weights happens
            # externally to Cerebrum since it is a relatively
            # expensive operation (can take several seconds).
            # Typically the weight will vary with the amount of users
            # already assigned, the disk space available or similar
            # criteria.
            #
            # Servers MUST have a weight trait to be considered for
            # allocation.
        es = Email.EmailServer(self._db)
        user_weight = {}
        total_weight = 0
        for row in es.list_traits(self.const.trait_email_server_weight):
            total_weight += row['numval']
            user_weight[row['entity_id']] = row['numval']
            
        pick = random.randint(0, total_weight - 1)
        for svr_id in user_weight:
            pick -= user_weight[svr_id]
            if pick <= 0:
                break
        return svr_id
        
    def illegal_name(self, name):
        # Avoid circular import dependency
        from Cerebrum.modules.PosixUser import PosixUser

        if isinstance(self, PosixUser):
            # TODO: Kill the ARsystem user to limit range og legal characters
            if len(name) > 8:
                return "too long (%s)" % name
            if re.search("^[^A-Za-z]", name):
                return "must start with a character (%s)" % name
            # Satisfy the LDAP syntax for usernames in netgroups (RFC 2307).
            if re.search("[^A-Za-z0-9\-]", name):
                return "contains illegal characters (%s)" % name
        return False

    def validate_new_uname(self, domain, uname):
        """Check that the requested username is legal and free"""
        # TBD: will domain ever be anything else?
        if domain == self.const.account_namespace:
            ea = Email.EmailAddress(self._db)
            for row in ea.search(local_part=uname, filter_expired=False):
                return False
        return self.__super.validate_new_uname(domain, uname)

    def delete_spread(self, spread):
        #
        # Pre-remove checks
        #
        spreads = [int(r['spread']) for r in self.get_spread()]
        if not spread in spreads:  # user doesn't have this spread
            return
        # All users in the 'ifi' NIS domain must also exist in the
        # 'uio' NIS domain.
        if spread == self.const.spread_uio_nis_user \
               and int(self.const.spread_ifi_nis_user) in spreads:
            raise self._db.IntegrityError, \
                  "Can't remove uio spread to an account with ifi spread."

        if spread == self.const.spread_ifi_nis_user \
               or spread == self.const.spread_uio_nis_user:
            self.clear_home(spread)

        # Remove IMAP user
        # TBD: It is currently a bit uncertain who and when we should
        # allow this.  Currently it should only be used when deleting
        # a user.
        if (spread == self.const.spread_uio_imap and
            int(self.const.spread_uio_imap) in spreads):
            et = Email.EmailTarget(self._db)
            et.find_by_target_entity(self.entity_id)
            self._UiO_order_cyrus_action(self.const.bofh_email_delete,
                                         et.email_server_id)
            # TBD: should we also perform a "cascade delete" from EmailTarget?
        #
        # (Try to) perform the actual spread removal.
        ret = self.__super.delete_spread(spread)
        return ret


    def update_email_addresses(self):
        # The "cast" into PosixUser causes this function to be called
        # twice in the typical case, so the "pre" code must be idempotent.

        # Make sure the email target of this account is associated
        # with an appropriate email server.  We must do this before
        # super, since without an email server, no target or address
        # will be created.
        spreads = [r['spread'] for r in self.get_spread()]
        if self.const.spread_uio_imap in spreads:
            self._UiO_update_email_server(self.const.email_server_type_cyrus)
            self.update_email_quota()

        # Avoid circular import dependency
        from Cerebrum.modules.PosixUser import PosixUser

        # Try getting the PosixUser-promoted version of self.  Failing
        # that, use self unpromoted.
        userobj = self
        if not isinstance(self, PosixUser):
            try:
                # We use the PosixUser object to get access to GECOS.
                # TODO: This ought to be in a mixin class for Account
                # for installations where both the PosixUser and the
                # Email module is in use.  For now we'll just put it
                # in the UiO specific code.
                tmp = PosixUser(self._db)
                tmp.find(self.entity_id)
                userobj = tmp
            except Errors.NotFoundError:
                # This Account hasn't been promoted to PosixUser yet.
                pass

        return userobj.__super.update_email_addresses()

    def is_employee(self):
        for r in self.get_account_types():
            if r['affiliation'] == self.const.affiliation_ansatt:
                return True
        return False

    def wants_auth_type(self, method):
        if method == self.const.Authentication("PGP-guest_acc"):
            # only store this type for guest accounts
            return self.get_trait(self.const.trait_guest_owner) is not None
        return self.__super.wants_auth_type(method)

    def clear_home(self, spread):
        """Remove disk quota before clearing home."""

        try:
            homeinfo = self.get_home(spread)
        except Errors.NotFoundError:
            pass
        else:
            dq = DiskQuota(self._db)
            dq.clear(homeinfo['homedir_id'])
        return self.__super.clear_home(spread)

    def _clear_homedir(self, homedir_id):
        # Since disk_quota has a FK to homedir, we need this override
        dq = DiskQuota(self._db)
        dq.clear(homedir_id)
        return self.__super._clear_homedir(homedir_id)

    def set_homedir(self, *args, **kw):
        """Remove quota information when the user is moved to a disk
        without quotas or where the default quota is larger than his
        existing explicit quota."""
        
        ret = self.__super.set_homedir(*args, **kw)
        if kw.get('current_id') and kw.get('disk_id'):
            disk = Factory.get("Disk")(self._db)
            disk.find(kw['disk_id'])
            def_quota = disk.get_default_quota()
            dq = DiskQuota(self._db)
            try:
                info = dq.get_quota(kw['current_id'])
            except Errors.NotFoundError:
                pass
            else:
                if def_quota is False:
                    # No quota on new disk, so remove the quota information.
                    dq.clear(kw['current_id'])
                elif def_quota is None:
                    # No default quota, so keep the quota information.
                    pass
                else:
                    if (info['override_expiration'] and
                        DateTime.now() < info['override_expiration']):
                        old_quota = info['override_quota']
                    else:
                        old_quota = info['quota']
                    if old_quota <= def_quota:
                        dq.clear(kw['current_id'])
        return ret

# arch-tag: 7bc3f7a8-183f-45c7-8a8f-f2ffff5029c5
