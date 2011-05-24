#!/usr/bin/env python
# -*- encoding: iso-8859-1 -*-
#
# Copyright 2009 University of Oslo, Norway
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

"""VirtHome bofhd extensions.

This module contains implementation of bofhd commands used in VirtHome.

It should be possible to use the jbofh client with this bofhd command set,
although the help strings won't be particularily useful.
"""

from mx.DateTime import now
from mx.DateTime import strptime
import pickle
import sys

import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum import Entity

from Cerebrum.modules.bofhd.bofhd_core import BofhdCommandBase
from Cerebrum.modules.bofhd.auth import BofhdAuthOpSet
from Cerebrum.modules.bofhd.auth import BofhdAuthRole
from Cerebrum.modules.bofhd.auth import BofhdAuthOpTarget

from Cerebrum.modules.bofhd.errors import CerebrumError
from Cerebrum.modules.bofhd.cmd_param import Command
from Cerebrum.modules.bofhd.cmd_param import AccountName
from Cerebrum.modules.bofhd.cmd_param import SimpleString
from Cerebrum.modules.bofhd.cmd_param import EmailAddress
from Cerebrum.modules.bofhd.cmd_param import Date
from Cerebrum.modules.bofhd.cmd_param import PersonName
from Cerebrum.modules.bofhd.cmd_param import FormatSuggestion
from Cerebrum.modules.bofhd.cmd_param import GroupName
from Cerebrum.modules.bofhd.cmd_param import EntityType
from Cerebrum.modules.bofhd.cmd_param import Id
from Cerebrum.modules.bofhd.cmd_param import Spread
from Cerebrum.modules.bofhd.cmd_param import QuarantineType

from Cerebrum.modules.virthome.bofhd_auth import BofhdVirtHomeAuth
from Cerebrum.modules.virthome.VirtAccount import VirtAccount 
from Cerebrum.modules.virthome.VirtAccount import FEDAccount
from Cerebrum.modules.virthome.PasswordChecker import PasswordGoodEnoughException
from Cerebrum.modules.virthome.PasswordChecker import PasswordChecker
from Cerebrum.modules.virthome.bofhd_virthome_help import arg_help





class BofhdVirthomeCommands(BofhdCommandBase):
    """Commands pertinent to user handling in VH."""

    all_commands = dict()


    # FIXME: Anytime *SOMETHING* from no/uio/bofhd_uio_cmds.py:BofhdExtension
    # is used here, pull that something into a separate BofhdCommon class and
    # stuff that into Cerebrum/modules/bofhd. Make
    # no/uio/bofhd_uio_cmds.py:BofhdExtension inherit that common
    # class. Refactoring, hell yeah!
    def __init__(self, server):
        super(BofhdVirthomeCommands, self).__init__(server)

        self.ba = BofhdVirtHomeAuth(self.db)
        self.virtaccount_class = VirtAccount
        self.fedaccount_class = FEDAccount
    # end __init__


    def get_help_strings(self):
        """Return a tuple of help strings for virthome bofhd.

        The help strings drive dumb clients' (such as jbofh) interface. The
        tuple values are dictionaries for (respectively) groups of commands,
        commands and arguments.
        """
        
        return ({}, {}, arg_help)
    # end get_help_strings


    def _get_account(self, identification, idtype=None):
        """Return the most specific account type for 'identification'.

        It could be either a generic Account, or a VirtAccount or a
        FEDAccount.
        """

        generic = super(BofhdVirthomeCommands,
                        self)._get_account(identification, idtype)
        if generic.np_type == self.const.fedaccount_type:
            result = self.fedaccount_class(self.db)
            result.find(generic.entity_id)
        elif generic.np_type == self.const.virtaccount_type:
            result = self.virtaccount_class(self.db)
            result.find(generic.entity_id)
        else:
            result = generic

        return result
    # end _get_account



    def _get_owner_name(self, account, name_type):
        """Fetch human owner's name, if account is of the proper type.

        For FA/VA return the human owner's name. For everything else return
        None.

        @param account: account proxy or account_id.

        @param name_type: which names to fetch
        """

        if isinstance(account, (int, long)):
            try:
                account = self._get_account(account)
            except Errors.NotFoundError:
                return None

        owner_name = None
        if account.np_type in (self.const.fedaccount_type,
                               self.const.virtaccount_type):
            owner_name = account.get_owner_name(name_type)

        return owner_name
    # end _get_owner_name


    def _get_group_resource(self, group):
        """Fetch a resource associated with group.

        This is typically a URL.

        @param group: group proxy or group_id.
        """

        if isinstance(group, (int, long)):
            try:
                group = self._get_group(group)
            except Errors.NotFoundError:
                return None

        resource = group.get_contact_info(self.const.system_virthome,
                                          self.const.virthome_group_url)
        if resource:
            # There cannot be more than 1
            resource = resource[0]["contact_value"]

        return resource
    # end _get_group_resource


    def _get_email_address(self, account):
        """Fetch account's e-mail address, if it exists.

        @param account: See _get_owner_name.
        """

        if isinstance(account, (int, long)):
            try:
                account = self._get_account(account)
            except Errors.NotFoundError:
                return None

        email = None
        if account.np_type in (self.const.fedaccount_type,
                               self.const.virtaccount_type):
            email = account.get_email_address()

        return email
    # end _get_email_address



    def __get_request(self, magic_key):
        """Return (decoded) about a request associated with magic_key.

        Raise an error if the request does not exist.
        """
        
        pcl = self.db
        try:
            event = pcl.get_pending_event(magic_key)
        except Errors.NotFoundError:
            raise CerebrumError("No event associated with key %s" % magic_key)

        if event["change_params"]:
            event["change_params"] = pickle.loads(event["change_params"])

        if "change_type_id" in event:
            event["change_type"] = str(
                self.const.ChangeType(event["change_type_id"]))
        return event
    # end __get_request



    def __setup_request(self, issuer_id, event_type, params=None):
        """Perform the necessary magic when creating a pending event.

        Also, see __process_account_confirmation.

        This method creates an entry in the pending_change_log framework to
        represent the pending request. A number of actions in VH require an
        explicit confirmation and this method is meant to capture the
        creation of state to represent a pending state (change).
        """

        magic_key = self.db.log_pending_change(issuer_id,
                                               event_type,
                                               None,
                                               # This will be
                                               # pickle.dumps()-ed by the
                                               # underlying API
                                               change_params=params)
        return magic_key
    # end __setup_request



    def __assign_default_user_spreads(self, account):
        """Assign all the default spreads for freshly created users.
        """

        for spread in getattr(cereconf, "BOFHD_NEW_USER_SPREADS", ()):
            tmp = self.const.human2constant(spread, self.const.Spread)
            if not account.has_spread(tmp):
                account.add_spread(tmp)
    # end __assign_default_user_spreads
            


    def __process_new_account_request(self, issuer_id, event):
        """Perform the necessary magic associated with confirming a freshly
        created account.
        """

        assert event["change_type_id"] == self.const.va_pending_create
        # Nuke the quarantine that locks this user out from bofhd
        account = self._get_account(event["subject_entity"])
        account.delete_entity_quarantine(self.const.quarantine_pending)

        self.__assign_default_user_spreads(account)
        return "OK, account %s confirmed" % account.account_name
    # end __process_new_account_request
        


    def __process_email_change_request(self, issuer_id, event):
        """Perform the necessary magic associated with confirming an e-mail
        change request.
        """
        assert event["change_type_id"] == self.const.va_email_change
        
        params = event["change_params"]
        old_address = params["old"]
        new_address = params["new"]
        account = self._get_account(event["subject_entity"])
        account.set_email_address(new_address)
        account.write_db()

        # Delete allt the e-mail change requests preceeding this one (why
        # would we want to pollute change_log?)
        for row in self.db.get_log_events(subject_entity=account.entity_id,
                                          types=self.const.va_email_change,):
            if row["tstamp"] < event["tstamp"]:
                self.db.remove_log_event(row["change_id"])
        
        return "OK, e-mail changed, %s -> %s" % (old_address, new_address)
    # end __process_email_change_request
    


    def __process_group_invitation_request(self, invitee_id, event):
        """Perform the necessary magic associated with letting an account join
        a group.
        """
        assert event["change_type_id"] == self.const.va_group_invitation

        params = event["change_params"]
        group_id = int(params["group_id"])
        inviter_id = int(params["inviter_id"])
        invitee_mail = params["invitee_mail"]

        group = self._get_group(group_id)
        assert group.entity_id == int(event["subject_entity"])
        member = self._get_account(invitee_id)
        if member.np_type not in (self.const.virtaccount_type,
                                  self.const.fedaccount_type):
            raise CerebrumError("Account %s (type %s) cannot join groups." %
                                (member.account_name, member.np_type))

        # Now, users who have been explicitly invited must be tagged as
        # such. There is a slight point of contention here, if the same VA is
        # invited multiple times, and the user accepts all invitations -- only
        # the first invitation will be records as trait_user_invited. This
        # should not be a problem, though.
        if not member.get_trait(self.const.trait_user_invited):
            member.populate_trait(self.const.trait_user_invited,
                                  numval=inviter_id,
                                  date=now())
            member.write_db()
        
        if group.has_member(member.entity_id):
            raise CerebrumError("User %s is already a member of group %s" %
                                (member.account_name, group.group_name))

        group.add_member(member.entity_id)
        return "OK, account %s joined group %s" % (member.account_name,
                                                   group.group_name)
    # end __process_group_invitation_request



    def __process_owner_swap_request(self, issuer_id, event):
        """Perform the necessary magic associated with letting another account
        take over group ownership.

        issuer_id is the new owner.

        event describes the change.

        issuer_id MUST BE an FA.
        """

        assert event["change_type_id"] == self.const.va_group_owner_swap

        params = event["change_params"]
        new_owner = self._get_account(issuer_id)
        old_owner = self._get_account(params["old"])
        group = self._get_group(params["group_id"])
        assert group.entity_id == int(event["subject_entity"])

        self.ba.can_own_group(new_owner.entity_id)
        self.ba.can_change_owners(old_owner.entity_id, group.entity_id)

        if new_owner.entity_id == old_owner.entity_id:
            return "OK, no changes necessary"

        # Let's swap them
        # ... first add a new owner
        self.__manipulate_group_permissions(group, new_owner, "group-owner",
                                            self.__grant_auth)
        # ... then remove an old one
        self.__manipulate_group_permissions(group, old_owner, "group-owner",
                                            self.__revoke_auth)
        return "OK, %s's owner changed (%s -> %s)" % (group.group_name,
                                                      old_owner.account_name,
                                                      new_owner.account_name)
    # end __process_owner_swap_request



    def __process_moderator_add_request(self, issuer_id, event):
        """Perform the necessary magic associated with letting another account
        join the moderator squad.

        issuer_id is the new moderator.

        event has data on which group this event applies to.

        issuer_id MUST BE an FA.
        """

        assert event["change_type_id"] == self.const.va_group_moderator_add

        params = event["change_params"]
        new_moderator = self._get_account(issuer_id)
        inviter = self._get_account(params["inviter_id"])
        group = self._get_group(params["group_id"])
        assert group.entity_id == int(event["subject_entity"])

        self.ba.can_moderate_group(new_moderator.entity_id)

        self.__manipulate_group_permissions(group, new_moderator, 'group-moderator',
                                            self.__grant_auth)

        return "OK, added moderator %s for group %s (at %s's request)" % (
            new_moderator.account_name,
            group.group_name,
            inviter.account_name)
    # end __process_moderator_add_request



    def __process_password_recover_request(self, issuer_id, event, *rest):
        """Perform the necessary magic to auto-issue a new password.

        webapp is the user for this request type.

        The request itself carries the 'target' for the password change.
        """

        assert event["change_type_id"] == self.const.va_password_recover
        assert len(rest) == 1
        # FIXME: have a permission trap here for issuer_id? 
        params = event["change_params"]
        assert params["account_id"] == event["subject_entity"]
        target = self._get_account(params["account_id"])
        if target.np_type != self.const.virtaccount_type:
            raise CerebrumError("Password recovery works for VA only")

        new_password = rest[0]
        self.__check_password(target, new_password)
        target.set_password(new_password)
        target.write_db()
        return "OK, password reset"
    # end __process_password_recover_request



    def __reset_expire_date(self, issuer_id, event):
        """Push the expire date ahead for the specified account.

        webapp is the issuer_id in this case. The true account target is in
        event['subject_entity'].
        """

        assert event["change_type_id"] == self.const.va_reset_expire_date
        account_id = event["subject_entity"]
        target = self._get_account(account_id)
        if target.np_type not in (self.const.virtaccount_type,
                                  self.const.fedaccount_type):
            raise CerebrumError("Expiration date setting is limited to "
                                "VA/FA only.")

        target.extend_expire_date()
        target.write_db()
        return "OK, reset expire date to %s for %s" % (
            target.expire_date.strftime("%Y-%m-%d"),
            target.account_name)
    # end __reset_expire_date
        


    def __process_request_confirmation(self, issuer_id, magic_key, *rest):
        """Perform the necessary magic when confirming a pending event.

        Also, see __setup_request.

        Naturally, processing each kind of confirmation is a function of the
        pending event. Events require no action other than deleting the
        pending event; others, however, require that we perform the actual
        state alternation.

        The important thing here is to trap *all* possible pending request
        types and be verbose about the failure, should we encounter an event
        that is unknown.

        @type request_owner: int
        @param request_owner:
          entity_id of the account issuing the confirmation request. Yes, on
          occasion this value is important.

        @param magic_key:
          request_id previously issued by vh bofhd that points to a request
          with all the necessary information.

        @param *rest:
          Whichever extra arguments a specific command requires. 
        """

        def delete_event(pcl, magic_key):
            pcl.remove_pending_log_event(magic_key)

        # A map of confirmation event types to actions.
        #
        # None means "simply delete the event"
        # FIXME: we should probably use callable as value, so that event
        # processing can be delegated in a suitable fashion.
        #
        all_events = {self.const.va_pending_create:
                          self.__process_new_account_request,
                      self.const.va_email_change:
                          self.__process_email_change_request,
                      self.const.va_group_invitation:
                          self.__process_group_invitation_request,
                      self.const.va_group_owner_swap:
                          self.__process_owner_swap_request,
                      self.const.va_group_moderator_add:
                          self.__process_moderator_add_request,
                      self.const.va_password_recover:
                          self.__process_password_recover_request,
                      self.const.va_reset_expire_date:
                          self.__reset_expire_date,
        }

        event = self.__get_request(magic_key)
        # 'event' is a dict where the keys are the column names of the
        # change_log tables.
        event_id, event_type = event["change_id"], event["change_type_id"]
        # If we don't know what to do -- leave the event alone! (and log an error)
        if event_type not in all_events:
            self.logger.warn("Confirming event %s (id=%s): unknown event type %s",
                             magic_key, event_id, self.const.ChangeType(event_type))
            raise CerebrumError("Don't know how to process event %s (id=%s)",
                                self.const.ChangeType(event_type),
                                event_id)

        # Run request-specific magic
        feedback = all_events[event_type](issuer_id, event, *rest)

        # Delete the pending marker
        # FIXME: Should this be request specific?
        delete_event(self.db, magic_key)

        return feedback
    # end __process_request_confirmation



    def __check_account_name_availability(self, account_name):
        """Check that L{account_name} is available in Cerebrum.

        (The combination if this call and account.write_db() is in no way
        atomic, but checking for availability lets us produce more meaningful
        error messages in (hopefully) most cases).

        @return:
          False if account_name is used in Cerebrum, True otherwise.
        """

        # Does not matter which one.
        account = self.virtaccount_class(self.db)
        try:
            account.find_by_name(account_name)
            return False
        except Errors.NotFoundError:
            return True

        # NOTREACHED
        assert False
    # end __check_account_name_availability



    def __create_account(self, account_type, account_name, email, expire_date,
                         human_first_name, human_last_name,
                         with_confirmation=True):
        """Create an account of the specified type.

        This is a convenience function to avoid duplicating some of the work.

        @param with_confirmation:
          Controls whether a confirmation request should be issued for this
          account. In some situations it makes no sense to confirm anything.
        """

        assert issubclass(account_type, (self.fedaccount_class,
                                         self.virtaccount_class))

        # Creation can still fail later, but hopefully this captures most
        # situations and produces a sensible account_name.
        if not self.__check_account_name_availability(account_name):
            raise CerebrumError("Account '%s' already exists" % account_name)

        account = account_type(self.db)
        account.populate(email, account_name, human_first_name,
                         human_last_name, expire_date)
        account.write_db()

        self.__assign_default_user_spreads(account)

        magic_key = ""
        if with_confirmation:
            magic_key = self.__setup_request(account.entity_id,
                                             self.const.va_pending_create)

        return account, magic_key
    # end __create_account



    def __check_password(self, account, password, uname=None):
        """Assert that the password is of proper quality.

        Throws a CerebrumError, if the password is too weak.

        This is a convenience function.

        @param account:
          Account proxy associated with the proper account or None. The latter
          means that no password history will be checked.

        @param password: Plaintext password to verify.

        @param account_name:
          Username to use for password checks. This is useful when creating a
          new account (L{account} does not exist, but we need the username for
          password checks)
        """

        try:
            pwd_checker = PasswordChecker(self.db)
            pwd_checker.goodenough(account, password, uname)
        except PasswordGoodEnoughException:
            _, m, _ = sys.exc_info()
            raise CerebrumError("Password too weak: %s" % str(m))
    # end __check_password



    all_commands["user_confirm_request"] = Command(
        ("user", "confirm_request"),
        SimpleString())
    def user_confirm_request(self, operator, confirmation_key, *rest):
        """Confirm a pending operation.

        @type confirmation_key: basestring
        @param confirmation_key:
          A confirmation key that has been issued when the operation was
          created. There is a pending_change_log event associated with that
          key. 
        """
        self.ba.can_confirm(operator.get_entity_id())
        return self.__process_request_confirmation(operator.get_entity_id(),
                                                   confirmation_key,
                                                   *rest)
    # end user_confirm_request



    all_commands["user_virtaccount_join_group"] = Command(
        ("user", "virtaccount_join_group"),
        SimpleString(),
        AccountName(),
        EmailAddress(),
        SimpleString(),
        Date(),
        PersonName(),
        PersonName(),
        fs=FormatSuggestion("%12s %36s",
                            ("entity_id", "session_key"),
                            hdr="%12s %36s" % ("Account id", "Session key")))
    def user_virtaccount_join_group(self, operator, magic_key,
                                    account_name, email, password,
                                    expire_date=None,
                                    human_first_name=None,
                                    human_last_name=None):
        """Perform the necessary magic to let a new user join a group.

        This is very much akin to user_virtaccount_create +
        user_confirm_request.

        FIMXE: What's the permission mask for this?
        """

        # If there is no request, this will throw an error back -- we need to
        # check that there actually *is* a request for joining a group behind
        # magic_key.
        request = self.__get_request(magic_key)
        if request["change_type_id"] != self.const.va_group_invitation:
            raise CerebrumError("Illegal command for request type %s",
                                str(self.const.ChangeType(request["change_type_id"])))

        # ... check that the group is still there...
        params = request["change_params"]
        self._get_group(int(params["group_id"]))

        if password:
            self.__check_password(None, password, account_name)
        else:
            raise CerebrumError("A VirtAccount must have a password")

        # Create account without confirmation
        account, junk = self.__create_account(self.virtaccount_class,
                                              account_name,
                                              email,
                                              expire_date,
                                              human_first_name,
                                              human_last_name,
                                              False)
        account.set_password(password)
        account.write_db()

        # NB! account.entity_id, NOT operator.get_entity_id() (the latter is
        # probably webapp)
        return self.__process_request_confirmation(account.entity_id, magic_key)
    # end user_virtaccount_join_group



    def __account_nuke_sequence(self, account_id):
        """Remove information associated with account_id before it's deleted
        from Cerebrum.

        This removes the junk associated with an account that the account
        logically should not be responsible for (permissions, change_log
        entries, and so forth).

        NB! This method is akin to user_virtaccount_disable.
        """

        account = self._get_account(account_id)

        # Drop permissions
        self.__remove_auth_target(self.const.auth_target_type_account,
                                  account.entity_id)
        self.__remove_auth_role(account.entity_id)

        # Drop memberships
        group = self.Group_class(self.db)
        for row in group.search(member_id=account.entity_id):
            group.clear()
            group.find(row["group_id"])
            group.remove_member(account.entity_id)

        row = account.search(name=cereconf.INITIAL_ACCOUNTNAME)
        bootstrap_id = row[0]['account_id']

        # Set change_by to bootstrap_account
        self.db.cl_init(change_by=bootstrap_id)

        # Set group's creator_id to bootstrap account
        for row in group.search(creator_id=account.entity_id):
            group.clear()
            group.find(row["group_id"])
            group.creator_id = bootstrap_id
            group.write_db()

        # Yank the spreads
        for row in account.get_spread():
            account.delete_spread(row["spread"])

        # Write all events so they can be removed
        self.db.commit()
        # wipe the changelog -- there is a foreign key there.
        for event in self.db.get_log_events(change_by=account.entity_id):
            self.db.remove_log_event(event["change_id"])

        account.delete()
    # end __account_nuke_sequence
    


    all_commands["user_fedaccount_nuke"] = Command(
        ("user", "fedaccount_nuke"),
        AccountName())
    def user_fedaccount_nuke(self, operator, uname):
        """Nuke (completely) a FEDAccount from Cerebrum.

        Completely remove a FEDAccount from Cerebrum. This includes
        memberships, traits, moderator/owner permissions, etc.
        """

        try:
            account = self.fedaccount_class(self.db)
            account.find_by_name(uname)
        except Errors.NotFoundError:
            raise CerebrumError("Did not find account %s" % uname)

        self.ba.can_nuke_fedaccount(operator.get_entity_id(),
                                    account.entity_id)
        uname = account.account_name
        operator.clear_state()
        self.__account_nuke_sequence(account.entity_id)
        return "OK, account %s has been deleted" % (uname,)
    # end user_fedaccount_nuke



    all_commands["user_virtaccount_disable"] = Command(
        ("user", "virtaccount_disable"),
        AccountName())
    def user_virtaccount_disable(self, operator, uname):
        """Mark a virtaccount as disabled.

        Essentially, this is equivalent to deletion, except that an account
        entity stays behind to keep the account name reserved.

        NB! This method is akin to __account_nuke_sequence().
        """
 
        account = self._get_account(uname)
        if account.np_type != self.const.virtaccount_type:
            raise CerebrumError("Only VA can be disabled")
        self.ba.can_nuke_virtaccount(operator.get_entity_id(), account.entity_id)

        # Drop permissions
        self.__remove_auth_target(self.const.auth_target_type_account,
                                  account.entity_id)
        self.__remove_auth_role(account.entity_id)

        # Drop memberships
        group = self.Group_class(self.db)
        for row in group.search(member_id=account.entity_id):
            group.clear()
            group.find(row["group_id"])
            group.remove_member(account.entity_id)

        # Set account as expired
        account.expire_date = now()
        account.write_db()

        # Yank the spreads
        for row in account.get_spread():
            account.delete_spread(row["spread"])

        # Slap it with a quarantine
        if not account.get_entity_quarantine(self.const.quarantine_disabled):
            account.add_entity_quarantine(self.const.quarantine_disabled,
                        self._get_account(cereconf.INITIAL_ACCOUNTNAME).entity_id,
                        "Account has been disabled",
                        now())

        return "OK, account %s (id=%s) has been disabled" % (account.account_name,
                                                             account.entity_id)
    # end user_virtaccount_disable
       


    all_commands["user_fedaccount_login"] = Command(
        ("user", "fedaccount_login"),
        AccountName(),
        EmailAddress(),
        Date(),
        PersonName(),
        PersonName())
    def user_fedaccount_login(self, operator, account_name, email,
                              expire_date=None, human_first_name=None,
                              human_last_name=None):
        """Login a (potentially new) fedaccount.

        This method performs essentially two functions: create a new federated
        user if it does not exist (user_fedaccount_create) and change session
        to that user (user_su)
        """
        self.ba.can_create_fedaccount(operator.get_entity_id())
        
        if self.__check_account_name_availability(account_name):
            self.logger.debug("New FA logging in for the 1st time: %s",
                              account_name)
            self.user_fedaccount_create(operator, account_name, email,
                                        expire_date, 
                                        human_first_name, human_last_name)
        else:

            # FIXME: If we allow None names here, should the names be updated
            # then?  We can't store NULL for None in the db schema, since it
            # does not allow it (non null constraint). What to do?
            account = self._get_account(account_name)
            if account.get_email_address() != email:
                account.set_email_address(email)
            if account.get_owner_name(self.const.human_first_name) != human_first_name:
                account.set_owner_name(self.const.human_first_name, human_first_name)
            if account.get_owner_name(self.const.human_last_name) != human_last_name:
                account.set_owner_name(self.const.human_last_name, human_last_name)

            account.extend_expire_date()
            account.write_db()

        return self.user_su(operator, account_name)
    # end user_fedaccount_login



    all_commands["user_su"] = Command(
        ("user", "su"),
        AccountName())
    def user_su(self, operator, target_account):
        """Perform a UNIX-like su, reassociating operator's session to
        target_account.
        """

        #
        # The problem here is that we must be able to re-assign session_id in
        # bofhd server from this command. self.server points to a
        # BofhdServerImplementation subclass that keeps track of sessions and
        # some such. 
        op_account = self._get_account(operator.get_entity_id())
        target_account = self._get_account(target_account)
        if not self.ba.can_su(op_account.entity_id, target_account.entity_id):
            raise CerebrumError("Cannot change identity (su %s -> %s)" %
                                (op_account.account_name,
                                 target_account.account_name))

        operator.reassign_session(target_account.entity_id)
        return "OK, user %s (id=%s) su'd to user %s (id=%s)" % (
               op_account.account_name, op_account.entity_id,
               target_account.account_name, target_account.entity_id)
    # end user_su


    
    # FIXME: Maybe this should be with the misc commands?
    all_commands["user_request_info"] = Command(
        ("user", "request_info"),
        SimpleString())
    def user_request_info(self, operator, magic_key):
        """Look up confirmation request by its id.

        It may be useful for the web interface to look up some request's
        parameters to provide a better feedback to the user.

        @return:
          A dict rescribing the request.
        """

        self.ba.can_view_requests(operator.get_entity_id())
        return self.__get_request(magic_key)
    # end user_request_info



    def __quarantine_to_string(self, eq):
        """Return a human-readable representation of eq's quarantines.

        @type eq: EntityQuarantine subclass of some sort
        @param eq:
          An entity for which we want to fetch quarantine information. This
          entity must be associated with suitable db rows (i.e. it must have
          entity_id attribute set).

        @return:
          A string describing the quaratine for the entity in question or an
          empty string.
        """

        quarantined = "<not set>"
        for q in eq.get_entity_quarantine():
            if q["start_date"] <= now():
                if q["end_date"] and q["end_date"] < now():
                    quarantined = "expired"
                elif (q["disable_until"] is not None and
                      q["disable_until"] > now()):
                    quarantined = "disabled"
                else:
                    return "active"
            else:
                quarantined = "pending"

        return quarantined
    # end __quarantine_to_string


    
    all_commands["user_info"] = Command(
        ("user", "info"), AccountName(),
        fs=FormatSuggestion("Username:      %s\n"
                            "Confirmation:  %s\n"
                            "E-mail:        %s\n"
                            "First name:    %s\n"
                            "Last name:     %s\n"
                            "Spreads:       %s\n"
                            "Traits:        %s\n"
                            "Expire:        %s\n"
                            "Entity id:     %d\n"
                            "Quarantine:    %s\n"
                            "Moderates:     %s group(s)\n"
                            "Owns:          %s group(s)\n"
                            "User EULA:     %s\n"
                            "Group EULA:    %s\n",
               ("username",
                "confirmation",
                "email_address",
                "first_name",
                "last_name",
                "spread",
                "trait",
                "expire",
                "entity_id",
                "quarantine",
                "moderator",
                "owner",
                "user_eula",
                "group_eula",
                )))
    def user_info(self, operator, user):
        """Return information about a specific VirtHome user.
        """

        account = self._get_account(user)
        self.ba.can_view_user(operator.get_entity_id(), account.entity_id)

        pending = "confirmed"
        if list(self.db.get_log_events(subject_entity=account.entity_id,
                                       types=(self.const.va_pending_create,))):
            pending = "pending confirmation"

        user_eula = account.get_trait(self.const.trait_user_eula)
        if user_eula:
            user_eula = user_eula.get("date")
        group_eula = account.get_trait(self.const.trait_group_eula)
        if group_eula:
            group_eula = group_eula.get("date")

        result = {"username": account.account_name,
                  "email_address":
                      ",".join(x["contact_value"]
                               for x in
                               account.get_contact_info(self.const.system_virthome,
                                                        self.const.virthome_contact_email))
                       or "N/A",
                  "first_name": self._get_owner_name(account,
                                                    self.const.human_first_name),
                  "last_name": self._get_owner_name(account,
                                                    self.const.human_last_name),
                  "spread":  self._get_entity_spreads(account.entity_id)
                             or "<not set>",
                  "trait": list(str(self.const.EntityTrait(x).description)
                                for x in account.get_traits()),
                  "expire": account.expire_date,
                  "entity_id": account.entity_id,
                  "quarantine": self.__quarantine_to_string(account),
                  "confirmation": pending,
                  "moderator": self._opset_group_lister(user, "group-moderator"),
                  "owner": self._opset_group_lister(user, "group-owner"),
                  "user_eula": user_eula,
                  "group_eula": group_eula,
            }
        return result
    # end user_info



    all_commands["user_accept_eula"] = Command(
        ("user", "accept_eula"),
        SimpleString())
    def user_accept_eula(self, operator, eula_type):
        """Register that operator has accepted a certain EULA.
        """

        eula = self.const.human2constant(eula_type,
                                         self.const.EntityTrait)
        if eula not in (self.const.trait_user_eula,
                        self.const.trait_group_eula):
            raise CerebrumError("Invalid EULA: %s" % str(eula_type))

        account = self._get_account(operator.get_entity_id())
        if account.get_trait(eula):
            return "OK, EULA %s has been accepted by %s" % (str(eula),
                                                         account.account_name)

        account.populate_trait(eula, date=now())
        account.write_db()
        return "OK, EULA %s has been accepted by %s" % (str(eula),
                                                        account.account_name)
    # end user_accept_eula
        


    all_commands["user_change_password"] = Command(
        ("user", "change_password"),
        SimpleString())
    def user_change_password(self, operator, old_password, new_password):
        """Set a new password for operator.

        This command is available to VirtAccounts only.

        We require both the old and the new password to perform the
        change. old_password is checked last.
        """

        account = self._get_account(operator.get_entity_id())
        if account.np_type != self.const.virtaccount_type:
            raise CerebrumError("Changing passwords is possible for "
                                "VirtAccounts only")

        self.__check_password(account, new_password, None)

        if not account.verify_auth(old_password):
            raise CerebrumError("Old password does not match")
        
        account.set_password(new_password)
        account.extend_expire_date()
        account.write_db()

        # FIXME: drop quarantines? If so, which ones?
        return "OK, password changed for user %s" % account.account_name
    # end user_virtaccount_password


    
    all_commands["user_change_email"] = Command(
        ("user", "change_email"),
        SimpleString())
    def user_change_email(self, operator, new_email):
        """Set a new e-mail address for operator.

        This command makes sense for VA and FA only. System accounts neither
        need nor want an e-mail address.
        """

        account = self._get_account(operator.get_entity_id())
        if not isinstance(account, (self.virtaccount_class,
                                    self.fedaccount_class)):
            raise CerebrumError("Changing e-mail is possible "
                                "for VirtAccounts/FEDAccounts only")

        magic_key = self.__setup_request(account.entity_id,
                                         self.const.va_email_change,
                                         params={"old": account.get_email_address(),
                                                 "new": new_email,})
        return {"entity_id": account.entity_id,
                "confirmation_key": magic_key}
    # end user_change_email



    all_commands["user_change_human_name"] = Command(
        ("user", "change_human_name"),
        SimpleString(),
        SimpleString())
    def user_change_human_name(self, operator, name_type, new_name):
        """Set a new human owner name for operator.

        This command makes sense for VA only, since FAs information comes from
        feide.
        """

        account = self._get_account(operator.get_entity_id())
        if account.np_type != self.const.virtaccount_type:
            raise CerebrumError("Only non-federated accounts may change owner's name")

        nt = self.const.human2constant(name_type, self.const.ContactInfo)
        if nt not in (self.const.human_first_name, self.const.human_last_name):
            raise CerebrumError("Unknown name type: %s" % str(name_type))

        account.set_owner_name(nt, new_name)
        account.write_db()
        return "OK, name %s changed for account %s to %s" % (str(nt),
                                                             account.account_name,
                                                             new_name)
    # end user_change_human_name



    all_commands["user_recover_password"] = Command(
        ("user", "recover_password"),
        AccountName(),
        EmailAddress())
    def user_recover_password(self, operator, uname, email):
        """Start the magic for auto-issuing a new password.

        This method creates an auto-password changing request. 
        """

        #
        # FIXME: Do we need a permission trap here?
        missing_msg = "Unable to recover password, unknown username and/or e-mail"
        try:
            account = self._get_account(uname)
        except CerebrumError:
            raise CerebrumError(missing_msg)
            
        if account.np_type != self.const.virtaccount_type:
            raise CerebrumError("Account %s (id=%s) is NOT a VA."
                                "Cannot recover password" %
                                (account.account_name, account.entity_id))

        if account.get_email_address() != email:
            raise CerebrumError(missing_msg)

        # Ok, we are good to go. Make the request.
        magic_key = self.__setup_request(account.entity_id,
                                         self.const.va_password_recover,
                                         params={"account_id": account.entity_id})
        return {"confirmation_key": magic_key}
    # end user_recover_password



    all_commands["user_recover_uname"] = Command(
        ("user", "recover_uname"),
        EmailAddress())
    def user_recover_uname(self, operator, email):
        """Return active user names associated with an e-mail.

        This command is useful is a user forgot his/her username in VH. We
        collect all active VAs associated with the e-mail and return them.
        """

        #
        # FIXME: Do we need a permission trap here?
        account = self.virtaccount_class(self.db)
        unames = set()
        for row in account.list_contact_info(
                               source_system=self.const.system_virthome,
                               contact_type=self.const.virthome_contact_email,
                               entity_type=self.const.entity_account,
                               contact_value=email):
            try:
                account.clear()
                account.find(row["entity_id"])
                # Skip non-VA
                if account.np_type != self.const.virtaccount_type:
                    continue

                # Skip expired accounts
                if account.is_expired():
                    continue

                # Skip quarantined accounts
                if list(account.get_entity_quarantine(only_active=False)):
                    continue
                    
                unames.add(account.account_name)
            except Errors.NotFoundError:
                pass

        return list(unames)
    # end user_recover_uname



    def __check_group_name_availability(self, group_name):
        """Check that L{group_name} is available in Cerebrum.

        (The combination if this call and group.write_db() is in no way
        atomic, but checking for availability lets us produce more meaningful
        error messages in (hopefully) most cases).
        """

        group = self.Group_class(self.db)
        try:
            group.find_by_name(group_name)
            return False
        except Errors.NotFoundError:
            return True

        assert False, "NOTREACHED"
    # end __check_account_name_availability



    def _get_opset(self, opset, idtype=None):
        aos = BofhdAuthOpSet(self.db)
        try:
            if idtype is None:
                if isinstance(opset, (int, long)):
                    idtype = "id"
                elif opset.find(":") != -1:
                    idtype, opset = opset.split(":", 1)
                    if len(opset) == 0:
                        raise CerebrumError("Must specify id in <%s>" % idtype)
                else:
                    idtype = "name"

            if idtype == "name":
                aos.find_by_name(opset)
            elif idtype == "id":
                aos.find(int(opset))
            else:
                raise CerebrumError("Unknown idtype: '%s'" % idtype)
        except Errors.NotFoundError:
            raise CerebrumError("Could not find auth_operation_set with %s=%s" %
                                (idtype, opset))

        return aos
    # end _get_opset



    def __grant_auth(self, account, op_set, op_target_id):
        """Grant the specified op_set to account (must be a FEDAccount) on
        target designated by op_target_id (it must 'point' to a group)

        @param account: FEDaccount proxy

        @param op_set: BofhdAuthOpSet proxy

        @param op_target_id: op_target_id for an auth_op_target (an id, NOT a
        proxy) 
        """
        
        # 
        # Ok, we have all the tidbits, grant op_set_id to holder_id on
        # whatever op_target_id points to.
        ar = BofhdAuthRole(self.db)
        aot = BofhdAuthOpTarget(self.db)
        aot.find(op_target_id)
        assert aot.target_type == self.const.auth_target_type_group
        assert account.np_type == self.const.fedaccount_type
        group_name = self._get_group(aot.entity_id).group_name
        rows = list(ar.list(account.entity_id, op_set.op_set_id,
                            aot.op_target_id))
        if len(rows) == 0:
            ar.grant_auth(account.entity_id, op_set.op_set_id,
                          aot.op_target_id)
            return "OK, granted %s to %s on group %s" % (op_set.name,
                                                         account.account_name,
                                                         group_name)
        return "OK, %s already has %s on group %s" % (op_set.name,
                                                      account.account_name,
                                                      group_name)
    # end __grant_auth


    def __revoke_auth(self, account, op_set, op_target_id):
        """__grant_auth's counterpart.
        """

        ar = BofhdAuthRole(self.db)
        aot = BofhdAuthOpTarget(self.db)
        aot.find(op_target_id)
        assert aot.target_type == self.const.auth_target_type_group
        assert account.np_type == self.const.fedaccount_type
        group_name = self._get_group(aot.entity_id).group_name

        rows = list(ar.list(account.entity_id, op_set.op_set_id,
                            aot.op_target_id))
        if len(rows) == 0:
            return "OK, %s does not have access %s to %s" % (
                account.account_name,
                op_set.name,
                group_name)

        ar.revoke_auth(account.entity_id, op_set.op_set_id, aot.op_target_id)
        # If that was the last permission for this op_target, kill op_target
        if len(list(ar.list(op_target_id=aot.op_target_id))) == 0:
            aot.delete()

        return "OK, removed %s from %s on %s" % (op_set.name,
                                                 account.account_name,
                                                 group_name)
    # end __revoke_auth


    def __manipulate_group_permissions(self, group, permission_holder, opset_id,
                                       access_function):
        """Grant/revoke a specific operation-set to/from permission_holder on
        group. 

        @param group: A VirtGroup proxy (must be associated with a group)

        @param permission_holder: A FEDAccount proxy (must be associated with
        a federated account).

        @type opset: string or int
        @param opset:
          An id for an opset that will be granted to/revoked from
          L{permission_holder} on L{group}.
        """

        opset = self._get_opset(opset_id)
        target_id = group.entity_id
        target_type = self.const.auth_target_type_group

        # First, locate or create a suitable auth_op_target
        aot = BofhdAuthOpTarget(self.db)
        op_targets = list()
        for row in aot.list(entity_id=target_id, target_type=target_type):
            op_targets.append(row)
        if not op_targets:
            aot.populate(target_id, target_type)
            aot.write_db()
            op_target_id = aot.op_target_id
        else:
            # We never need more than 1 in *VirtHome*.
            assert len(op_targets) == 1
            op_target = op_targets[0]
            assert op_target["attr"] is None
            op_target_id = int(op_targets[0]["op_target_id"])

        return access_function(permission_holder, opset, op_target_id)
    # end __manipulate_group_permissions


    def __remove_auth_target(self, target_type, entity_id):
        """Delete *all* permissions granted ON target_type/target_id.

        This is useful in conjunctiuon with entity_id's deletion (e.g. when a
        group is deleted, we want to revoke *ALL* permissions granted on that
        group. The 'leftovers' do not possess a security risk, but the data
        in the db would become inconsistent and this is something that we
        *really* need to avoid).
        """

        ar = BofhdAuthRole(self.db)
        aot = BofhdAuthOpTarget(self.db)
        for r in aot.list(entity_id=entity_id, target_type=target_type):
            aot.clear()
            aot.find(r['op_target_id'])
            # We remove all auth_role entries pointing to this entity_id
            # first.
            for role in ar.list(op_target_id = r["op_target_id"]):
                ar.revoke_auth(role['entity_id'], role['op_set_id'],
                               r['op_target_id'])
            aot.delete()
    # end __remove_auth_target


    def __remove_auth_role(self, entity_id):
        """Delete *all* permissions granted TO entity_id.

        This is useful in conjuction with entity_id's deletion. It does not
        happen often, but we *must* clean up auth_op_target, since there are
        no FKs binding entity_info and auth_op_target.entity_id (by design)
        """

        ar = BofhdAuthRole(self.db)
        aot = BofhdAuthOpTarget(self.db)
        for r in ar.list(entity_id):
            ar.revoke_auth(entity_id, r['op_set_id'], r['op_target_id'])
            # Also remove targets if this was the last reference from
            # auth_role.
            remaining = ar.list(op_target_id=r['op_target_id'])
            if len(remaining) == 0:
                aot.clear()
                aot.find(r['op_target_id'])
                aot.delete()
    # end __remove_auth_role

        

    all_commands["group_create"] = Command(
        ("group", "create"), 
        GroupName(),
        SimpleString(),
        AccountName(),
        SimpleString())
    def group_create(self, operator, group_name, description, owner, url):
        """Register a new VirtGroup in Cerebrum.

        @param group_name: Name of the group. It must have a realm suffix.

        @description: Human-friendly group description

        @owner: An account that will be assigned 'owner'-style permission.

        @url:
          A resource url associated with the group (i.e. some hint to a
          thingamabob justifying group's purpose).
        """

        self.ba.can_create_group(operator.get_entity_id())
        if not self.__check_group_name_availability(group_name):
            raise CerebrumError("Group name %s already exists" % group_name)

        # FIXME: MUST owner be the same as operator?
        account = self._get_account(owner)
        self.ba.can_own_group(account.entity_id)
        
        group = self.Group_class(self.db)
        try:
            group.populate(operator.get_entity_id(), group_name, description)
            group.write_db()
            group.set_group_resource(url)
        except ValueError:
            raise CerebrumError(str(sys.exc_info()[1]))
        for spread in getattr(cereconf, "BOFHD_NEW_GROUP_SPREADS", ()):
            group.add_spread(self.const.human2constant(spread,
                                                       self.const.Spread))

        self.__manipulate_group_permissions(group, account, 'group-owner',
                                            self.__grant_auth)
        return {"group_id": int(group.entity_id)}
    # end group_create



    all_commands["group_disable"] = Command(
        ("group", "disable"),
        GroupName())
    def group_disable(self, operator, gname):
        """Disable group in VH.

        This is an effective deletion, although the group entity actually
        remains there as a placeholder for the group name.
        """

        group = self._get_group(gname)
        self.ba.can_delete_group(operator.get_entity_id(), group.entity_id)

        # Yank all the spreads
        for row in group.get_spread():
            group.delete_spread(row["spread"])

        # Remove all members
        for membership in group.search_members(group_id=group.entity_id):
            group.remove_member(membership["member_id"])
            
        # Clean up the permissions (granted ON the group and TO the group)
        self.__remove_auth_target(self.const.auth_target_type_group,
                                  group.entity_id)
        self.__remove_auth_role(group.entity_id)

        return "OK, group %s has been disabled" % (group.group_name,)
    # end group_disable
    


    all_commands["group_remove_members"] = Command(
        ("group", "remove_members"),
        AccountName(repeat=True),
        GroupName(repeat=True))
    def group_remove_members(self, operator, uname, gname):
        """L{group_add_members}'s counterpart.
        """
        
        account = self._get_account(uname)
        group = self._get_group(gname)
        self.ba.can_remove_from_group(operator.get_entity_id(), group.entity_id,
                                      account.entity_id)
        if not group.has_member(account.entity_id):
            raise CerebrumError("User %s is not a member of group %s" %
                                (account.account_name, group.group_name))

        group.remove_member(account.entity_id)
        return "OK, removed %s from %s" % (account.account_name,
                                           group.group_name)
    # end group_remove_members



    def _member_lister(self, gname, indirect_members):
        """This is the driver function for group_list/expanded.
        """

        group = self._get_group(gname)
        result = list()
        for x in group.search_members(group_id=group.entity_id,
                                      indirect_members=indirect_members):
            tmp = {"member_id": x["member_id"],
                   "member_type": str(self.const.EntityType(x["member_type"])),
                   "member_name": self._get_entity_name(x["member_id"],
                                                        x["member_type"]),
                   "owner_name": self._get_owner_name(
                                     x["member_id"],
                                     self.const.human_full_name),
                   "email_address": self._get_email_address(x["member_id"]),}
            result.append(tmp)

        result.sort(lambda x, y: cmp(x["member_name"], y["member_name"]))
        return result
    # end _member_lister



    def _opset_account_lister(self, gname, opset_name):
        """Return account_ids holding a specific permission on gname.

        This method is meant for answering questions like 'which accounts
        moderate this group?'.

        See also L{_opset_group_lister}.
        """

        assert opset_name in ("group-owner", "group-moderator",)

        opset = self._get_opset(opset_name)
        group = self._get_group(gname)

        tmp = list(self.ba.get_permission_holders_on_groups(
            opset.op_set_id, group_id=group.entity_id))
        for entry in tmp:
            account_id = entry["account_id"]
            entry["owner_name"] = self._get_owner_name(account_id,
                                                       self.const.human_full_name)
            entry["email_address"] = self._get_email_address(account_id)
            
        return tmp
    # end _opset_account_lister



    def _opset_group_lister(self, account, opset_name):
        """Return group_ids where L{account} has a specific permission.

        This is a complement to the L{_opset_account_lister}. This method is
        meant for answering questions like 'which groups am I moderating?'
        """

        assert opset_name in ("group-owner", "group-moderator")

        opset = self._get_opset(opset_name)
        account = self._get_account(account)
        tmp = list(self.ba.get_permission_holders_on_groups(
            opset.op_set_id, account_id=account.entity_id))
        for entry in tmp:
            entry["url"] = self._get_group_resource(entry["group_id"])
        
        return tmp
    # end _opset_group_lister



    all_commands["group_list"] = Command(
        ("group", "list"),
        GroupName())
    def group_list(self, operator, gname):
        """List the content of group L{gname}.

        FIXME: Do we want a cut-off for large groups?
        FIXME: Do we want a permission hook here? (i.e. listing only the
        groups where one is a member/moderator/owner)
        """

        return self._member_lister(gname, indirect_members=False)
    # end group_list



    all_commands["user_list_memberships"] = Command(
        ("user", "list_memberships"))
    def user_list_memberships(self, operator):
        """List all groups where operator is a member.
        """

        group = self.Group_class(self.db)
        result = list()
        for row in group.search(member_id=operator.get_entity_id()):
            tmp = row.dict()
            tmp["url"] = self._get_group_resource(tmp["group_id"])
            result.append(tmp)

        return result
    # end user_list_memberships



    all_commands["group_change_owner"] = Command(
        ("group", "change_owner"),
        EmailAddress(),
        GroupName())
    def group_change_owner(self, operator, email, gname):
        """Change gname's owner to FA associated with email.
        """

        group = self._get_group(gname)
        self.ba.can_change_owners(operator.get_entity_id(), group.entity_id)
        magic_key = self.__setup_request(group.entity_id,
                                         self.const.va_group_owner_swap,
                                         params={"old": operator.get_entity_id(),
                                                 "group_id": group.entity_id,
                                                 "new": email,})
        return {"confirmation_key": magic_key}
    # end group_change_owner


    all_commands["group_change_description"] = Command(
        ("group", "change_description"),
        GroupName(),
        SimpleString())
    def group_change_description(self, operator, gname, description):
        """Change gname's description."""

        group = self._get_group(gname)
        self.ba.can_change_description(operator.get_entity_id(), group.entity_id)
        old, new = group.description, description
        group.description = description
        group.write_db()
        return "OK, changed %s (id=%s) description '%s' -> '%s'" % (
            group.group_name, group.entity_id, old, new)
    # end group_change_description
    


    all_commands["group_change_resource"] = Command(
        ("group", "change_resource"),
        GroupName(),
        SimpleString())
    def group_change_resource(self, operator, gname, url):
        """Change URL associated with group gname."""

        group = self._get_group(gname)
        self.ba.can_change_resource(operator.get_entity_id(), group.entity_id)
        try:
            group.verify_group_url(url)
        except ValueError:
            raise CerebrumError("Invalid URL for group <%s>: <%s>" %
                                (group.group_name, url))
        group.set_group_resource(url)
        return "OK, changed resource for Group %s to %s" % (group.group_name,
                                                            url)
    # end group_change_resource


    
    all_commands["group_invite_moderator"] = Command(
        ("group", "invite_moderator"),
        EmailAddress(),
        GroupName())
    def group_invite_moderator(self, operator, email, gname):
        """Invite somebody to join the moderator squad for group gname.
        """

        group = self._get_group(gname)
        self.ba.can_moderate_group(operator.get_entity_id())
        self.ba.can_change_moderators(operator.get_entity_id(), group.entity_id)

        magic_key = self.__setup_request(group.entity_id,
                                         self.const.va_group_moderator_add,
                                         params={"inviter_id": operator.get_entity_id(),
                                                 "group_id": group.entity_id,
                                                 "invitee_mail": email,})
        return {"confirmation_key": magic_key}
    # end group_invite_moderator

        

    all_commands["group_remove_moderator"] = Command(
        ("group", "remove_moderator"),
        AccountName(),
        GroupName())
    def group_remove_moderator(self, operator, moderator, gname):
        """L{group_invite_moderator}'s counterpart.
        """

        group = self._get_group(gname)
        account = self._get_account(moderator)

        # Check that operator has permission to manipulate moderator list
        self.ba.can_change_moderators(operator.get_entity_id(), group.entity_id)

        self.__manipulate_group_permissions(group, account, 'group-moderator',
                                            self.__revoke_auth)

        return "OK, removed %s as moderator of %s" % (account.account_name,
                                                      group.group_name)
    # end group_remove_moderator



    all_commands["group_invite_user"] = Command(
        ("group", "invite_user"),
        EmailAddress(),
        GroupName())
    def group_invite_user(self, operator, email, gname):
        """Invite e-mail to join gname.

        This method is intended to let users invite others to join their
        groups.

        Only FAs can invite, and only for groups that they own/moderate.

        An invitation will not be executed until the email recipient performns
        a confirm-like action.
        """

        group = self._get_group(gname)
        # If you can't add members, you can't invite...
        self.ba.can_add_to_group(operator.get_entity_id(), group.entity_id)

        magic_key = self.__setup_request(group.entity_id,
                                         self.const.va_group_invitation,
                                         {"inviter_id": operator.get_entity_id(),
                                          "group_id": group.entity_id,
                                          "invitee_mail": email,})
        return {"confirmation_key": magic_key}
    # end group_invite_user


    all_commands["group_info"] = Command(
        ("group", "info"),
        GroupName(),
        fs=FormatSuggestion("Name:         %s\n"
                            "Expire:       %s\n"
                            "Spreads:      %s\n"
                            "Description:  %s\n"
                            "Entity id:    %i\n"
                            "Creator:      %s\n"
                            "Moderator(s): %s\n"
                            "Owner:        %s\n"
                            "Member(s):    %s\n"
                            "Pending (mod) %s\n"
                            "Pending (mem) %s\n"
                            "Resource:     %s",
                            ("group_name",
                             "expire",
                             "spread",
                             "description",
                             "entity_id",
                             "creator",
                             "moderator",
                             "owner",
                             "member",
                             "pending_moderator",
                             "pending_member",
                             "url",)))
    def group_info(self, operator, gname):
        """Fetch basic info about a specific group.

        FIXME: No permission restrictions?
        """
        group = self._get_group(gname)
        answer = {"group_name": group.group_name,
                  "expire": group.expire_date,
                  "spread": self._get_entity_spreads(group.entity_id)
                            or "<not set>",
                  "description": group.description,
                  "entity_id": group.entity_id,
                  "creator": self._get_account(group.creator_id).account_name,
                  "moderator": self._opset_account_lister(gname,
                                                          "group-moderator"),
                  "owner": self._opset_account_lister(gname,
                                                      "group-owner"),
                  "url": self._get_group_resource(group),
                  "pending_moderator": self.__load_group_pending_events(
                                                  group,
                                                  self.const.va_group_moderator_add),
                  "pending_member": self.__load_group_pending_events(
                                                  group,
                                                  self.const.va_group_invitation), }
        members = dict()
        for row in group.search_members(group_id=group.entity_id,
                                        indirect_members=False):
            mt = int(row["member_type"])
            members[mt] = members.get(mt, 0) + 1

        answer["member"] = ", ".join("%s: %d member(s)" %
                                     (str(self.const.EntityType(key)),
                                      members[key])
                                     for key in members)
        return answer
    # end group_info



    def __load_group_pending_events(self, group, event_types):
        """Load inconfirmed invitations associated with group.

        This is a help function for colleting such things as unconfirmed
        moderator invitations or requests to join group.
        """

        result = list()
        for row in self.db.get_pending_events(subject_entity=group.entity_id,
                                              types=event_types):
            magic_key = row["confirmation_key"]
            request = self.__get_request(magic_key)
            params = request["change_params"]
            entry = {"invitee_mail": params["invitee_mail"],
                     "timestamp": row["tstamp"].strftime("%F %T"),}
            try:
                inviter = self._get_account(params["inviter_id"])
                inviter = inviter.account_name
            except (Errors.NotFoundError, CerebrumError, KeyError):
                inviter = None

            entry["inviter"] = inviter
            result.append(entry)

        return result
    # end __load_group_pending_events

    

    all_commands["user_virtaccount_create"] = Command(
            ("user", "virtaccount_create"),
            AccountName(),
            EmailAddress(),
            SimpleString(),
            Date(),
            PersonName(),
            PersonName(),
            fs=FormatSuggestion("%12s %36s",
                                ("entity_id",
                                 "session_key"),
                                hdr="%12s %36s"
                                % ("Account id", "Session key")))
    def user_virtaccount_create(self, operator, account_name, email, password,
                                expire_date=None,
                                human_first_name=None, human_last_name=None):
        """Create a VirtAccount in Cerebrum.
        
        Create a new virtaccount instance in Cerebrum. Tag it with
        VACCOUNT_UNCONFIRMED trait.

        @type email: basestring
        @param email:
          VirtAccount's e-mail address.

        @type account_name: basestring
        @param account_name:
          Desired VirtAccount name. It is not certain that this name is
          available.

        @type expire_date: mx.DateTime.DateTimeType instance
        @param expire_date:
          Expiration date for the VirtAccount we are about to create.

        @type human_name: basestring
        @param human_name:
          (Optional) name of VirtAccount's human owner. We have no idea
          whether this name corresponds to reality. 

        @type password: basestring
        @param password:
          (Optional) clear text password for this user to be used on login to
          VirtHome/Cerebrum. FIXME: Does it make sense to have the password
          *optional* ?
        """

        if password:
            self.__check_password(None, password, account_name)
        else:
            raise CerebrumError("A VirtAccount must have a password")

        account = self.virtaccount_class(self.db)
        account, confirmation_key = self.__create_account(self.virtaccount_class,
                                                          account_name,
                                                          email,
                                                          expire_date,
                                                          human_first_name,
                                                          human_last_name)
        account.set_password(password)
        account.write_db()

        # slap an initial quarantine, so the users are forced to confirm
        # account creation.
        account.add_entity_quarantine(self.const.quarantine_pending,
                   self._get_account(cereconf.INITIAL_ACCOUNTNAME).entity_id,
                   "Account pending confirmation upon creation",
                   now())

        return {"entity_id": account.entity_id,
                "confirmation_key": confirmation_key}
    # end user_virtaccount_create



    #######################################################################
    #
    # Commands that should not be exposed to the webapp, but which are useful
    # for testing
    #######################################################################
    all_commands["user_fedaccount_create"] = Command(
        ("user", "fedaccount_create"),
        AccountName(),
        SimpleString())
    def user_fedaccount_create(self, operator, account_name, email,
                               expire_date=None,
                               human_first_name=None, human_last_name=None):
        """Create a FEDAccount in Cerebrum.

        Create a new FEDAccount instance in Cerebrum. Tag it with
        VACCOUNT_UNCONFIRMED trait. 

        Create a new virtaccount instance in Cerebrum. Tag it with
        VACCOUNT_UNCONFIRMED trait.

        @type email: basestring
        @param email:
          VirtAccount's e-mail address.

        @type account_name: basestring
        @param account_name:
          Desired VirtAccount name. It is not certain that this name is
          available.

        @type expire_date: mx.DateTime.DateTimeType instance
        @param expire_date:
          Expiration date for the VirtAccount we are about to create.

        @type human_name: basestring
        @param human_name:
          (Optional) name of VirtAccount's human owner. We have no idea
          whether this name corresponds to reality. 

        @type password: basestring
        @param password:
          (Optional) clear text password for this user to be used on login to
          VirtHome/Cerebrum.
        """

        self.ba.can_create_fedaccount(operator.get_entity_id())
        account, confirmation_key = self.__create_account(self.fedaccount_class,
                                                          account_name,
                                                          email,
                                                          expire_date,
                                                          human_first_name,
                                                          human_last_name,
                                                          with_confirmation=False)
        return {"entity_id": account.entity_id,
                "confirmation_key": confirmation_key}
    # end user_fedaccount_create



    all_commands["user_virtaccount_nuke"] = Command(
        ("user", "virtaccount_nuke"),
        AccountName())
    def user_virtaccount_nuke(self, operator, uname):
        """Nuke (completely) a VirtAccount from Cerebrum.

        Completely remove a VirtAccount from Cerebrum. This includes
        membershipts, traits, etc.

        TBD: Coalesce into one command with user_fedaccount_nuke?
        FIXME: if operator == uname, this fails, because there is a FK from
        bofhd_session to account_info. This should be addressed.
        """
        
        try:
            account = self.virtaccount_class(self.db)
            account.find_by_name(uname)
            account_id = account.entity_id
        except Errors.NotFoundError:
            raise CerebrumError("Did not find account %s" % uname)
            
        self.ba.can_nuke_virtaccount(operator.get_entity_id(), account.entity_id)
        self.__account_nuke_sequence(account.entity_id)
        return "OK, account %s (id=%s) deleted" % (uname, account_id)
    # end user_virtaccount_nuke


    all_commands["group_delete"] = Command(
        ("group", "delete"),
        AccountName())
    def group_delete(self, operator, groupname):
        """Delete a group from the database.

        Deletion is group_disable() + group.delete(). 
        """

        group = self._get_group(groupname)
        gname, gid = group.group_name, group.entity_id
        self.ba.can_delete_group(operator.get_entity_id(), group.entity_id)
        self.group_disable(operator, groupname)
        group.delete()
        return "OK, deleted group '%s' (id=%s)" % (gname, gid)
    # end group_delete


    all_commands["group_add_members"] = Command(
        ("group", "add_members"),
        AccountName(),
        GroupName())
    def group_add_members(self, operator, uname, gname):
        """Add uname as a member of group.
        """

        group = self._get_group(gname)
        account = self._get_account(uname)
        self.ba.can_add_to_group(operator.get_entity_id(), group.entity_id)
        if account.np_type not in (self.const.virtaccount_type,
                                   self.const.fedaccount_type):
            raise CerebrumError("Account %s (type %s) cannot join groups." %
                                (account.account_name, account.np_type))
        
        if group.has_member(account.entity_id):
            raise CerebrumError("User %s is already a member of group %s" %
                                (account.account_name, group.group_name))
        group.add_member(account.entity_id)
        return "OK, added %s to %s" % (account.account_name, group.group_name)
    # end group_add_members

    ## MARK
# end BofhdVirthomeCommands



class BofhdVirthomeMiscCommands(BofhdCommandBase):
    """This class is for misc commands that are not specific for accounts or
    groups.
    """

    all_commands = dict()

    # FIXME: Anytime *SOMETHING* from no/uio/bofhd_uio_cmds.py:BofhdExtension
    # is used here, pull that something into a separate BofhdCommon class and
    # stuff that into Cerebrum/modules/bofhd. Make
    # no/uio/bofhd_uio_cmds.py:BofhdExtension inherit that common
    # class. Refactoring, hell yeah!

    

    def __init__(self, server):
        super(BofhdVirthomeMiscCommands, self).__init__(server)

        self.ba = BofhdVirtHomeAuth(self.db)
    # end __init__



    def _get_spread(self, spread):
        """Fetch the proper spread constant.

        If not found -> throw a CerebrumError.
        """

        spread = self.const.Spread(spread)
        try:
            int(spread)
        except Errors.NotFoundError:
            raise CerebrumError("No such spread %s")

        return spread
    # end _get_spread


    all_commands['spread_add'] = Command(
        ("spread", "add"),
        EntityType(default='group'),
        Id(),
        Spread())
    def spread_add(self, operator, entity_type, identification, spread):
        """Add specified spread(s) to entity_id.
        """

        entity = self._get_entity(entity_type, identification)
        spread = self._get_spread(spread)
        self.ba.can_manipulate_spread(operator.get_entity_id(),
                                      entity.entity_id)

        entity.add_spread(spread)
        return "OK, added spread %s to %s" % (str(spread),
                                              identification)
    # end spread_add


    all_commands['spread_remove'] = Command(
        ("spread", "remove"),
        EntityType(default='group'),
        Id(),
        Spread())
    def spread_remove(self, operator, entity_type, identification, spread):
        """Remove a spread from an entity.
        """
        
        entity = self._get_entity(entity_type, identification)
        spread = self._get_spread(spread)
        self.ba.can_manipulate_spread(operator.get_entity_id(),
                                      entity.entity_id)
        entity.delete_spread(spread)
        return "OK, deleted spread %s from %s" % (str(spread),
                                                  identification)
    # end spread_remove


    all_commands['spread_list'] = Command(
        ("spread", "list"),
        fs=FormatSuggestion("%-14s %s", ('name', 'desc'),
                            hdr="%-14s %s" % ('Name', 'Description')))
    def spread_list(self, operator):
        """List all spreads available in the database.
        """
        
        ret = list()
        spr = Entity.EntitySpread(self.db)
        for s in spr.list_spreads():
            ret.append({'name': s['spread'],
                        'desc': s['description'],
                        'type': s['entity_type_str'],
                        'type_id': s['entity_type']})
        return ret
    # end spread_list


    all_commands["spread_entity_list"] = Command(
        ("spread", "entity_list"),
        EntityType(default="account"),
        Id())
    def spread_entity_list(self, operator, entity_type, entity_id):
        """List all spreads FOR A SPECIFIC ENTITY

        (See also L{spread_list})
        """

        entity = self._get_entity(entity_type, entity_id)
        self.ba.can_view_spreads(operator.get_entity_id(), entity.entity_id)
        return [str(self.const.Spread(x["spread"]))
                for x in entity.get_spread()]
    # end spread_entity_list



    all_commands['quarantine_add'] = Command(
        ("quarantine", "add"),
        EntityType(default="account"),
        Id(repeat=True),
        QuarantineType(),
        SimpleString(),
        SimpleString())
    def quarantine_add(self, operator, entity_type, ident, qtype, why, date_end):
        """Set a quarantine on an entity.
        """

        # FIXME: factor out _parse*date*-methods from bofhd_uio_cmds.py
        date_end = strptime(date_end, "%Y-%m-%d")
        entity = self._get_entity(entity_type, ident)
        qconst = self.const.human2constant(qtype, self.const.Quarantine)
        self.ba.can_manipulate_quarantines(operator.get_entity_id(),
                                           entity.entity_id)
        rows = list(entity.get_entity_quarantine(type=qconst))
        if rows:
            raise CerebrumError("Entity %s %s already has %s quarantine" %
                                (entity_type, ident, str(qconst)))

        entity.add_entity_quarantine(qconst, operator.get_entity_id(),
                                     why, now(), date_end)
        return "OK, quarantined %s %s with %s" % (entity_type, ident,
                                                  str(qconst))
    # end quarantine_add



    all_commands['quarantine_remove'] = Command(
        ("quarantine", "remove"),
        EntityType(default="account"),
        Id(),
        QuarantineType())
    def quarantine_remove(self, operator, entity_type, entity_ident, qtype):
        """Remove a specific quarantine from a given entity.

        See also L{quarantine_add}.
        """

        entity = self._get_entity(entity_type, entity_ident)
        qconst = self.const.human2constant(qtype, self.const.Quarantine)
        self.ba.can_manipulate_quarantines(operator.get_entity_id(),
                                           entity.entity_id)
        entity.delete_entity_quarantine(qconst)
        return "OK, removed quarantine %s from %s" % (str(qconst), entity_ident)
    # end quarantine_remove



    all_commands['quarantine_list'] = Command(
        ("quarantine", "list"),
        fs=FormatSuggestion("%-16s  %1s  %-17s %s",
                            ('name', 'lock', 'shell', 'desc'),
                            hdr="%-15s %-4s %-17s %s" %
                            ('Name', 'Lock', 'Shell', 'Description')))
    def quarantine_list(self, operator):
        """Display all quarantines available."""

        ret = []
        for c in self.const.fetch_constants(self.const.Quarantine):
            lock = 'N'; shell = '-'
            rule = cereconf.QUARANTINE_RULES.get(str(c), {})
            if 'lock' in rule:
                lock = 'Y'
            if 'shell' in rule:
                shell = rule['shell'].split("/")[-1]
            ret.append({'name': "%s" % c,
                        'lock': lock,
                        'shell': shell,
                        'desc': c._get_description()})
        return ret
    # end quarantine list

    

    all_commands['quarantine_show'] = Command(
        ("quarantine", "show"),
        EntityType(default="account"),
        Id(),
        fs=FormatSuggestion("%-14s %-16s %-16s %-14s %-8s %s",
                            ('type', 'start', 'end',
                            'disable_until', 'who', 'why'),
                            hdr="%-14s %-16s %-16s %-14s %-8s %s" % 
                            ('Type', 'Start', 'End', 'Disable until', 'Who',
                             'Why')))
    def quarantine_show(self, operator, entity_type, entity_id):
        """Display quarantines set on the specified entity.
        """
        
        ret = []
        entity = self._get_entity(entity_type, entity_id)
        self.ba.can_show_quarantines(operator.get_entity_id(), entity.entity_id)
        for r in entity.get_entity_quarantine():
            acc = self._get_account(r['creator_id'], idtype='id')
            ret.append({'type': str(self.const.Quarantine(r['quarantine_type'])),
                        'start': r['start_date'],
                        'end': r['end_date'],
                        'disable_until': r['disable_until'],
                        'who': acc.account_name,
                        'why': r['description']})
        return ret
    # end quarantine show



    all_commands["trait_list"] = Command(
        ("trait", "list"))
    def trait_list(self, operator):
        """Display all traits available.

        This may come in handy when presenting a user with a list of choices
        for a trait, should this functionality be exposed to users at all.
        """

        # This command is available to everybody
        ret = list()
        for c in self.const.fetch_constants(self.const.EntityTrait):
            ret.append({"code": int(c),
                        "code_str": str(c),
                        "entity_type": str(self.const.EntityType(c.entity_type)),
                        "description": c.description})
        return ret
    # end trait_list



    all_commands["trait_set"] = Command(
        ("trait", "set"),
        EntityType(default="account"),
        Id(),
        SimpleString(),
        SimpleString(repeat=True))
    def trait_set(self, operator, entity_type, entity_ident, trait, *values):
        """Add or update a trait belonging to an entity.

        If the entity already has a specified trait, it will be updated to the
        values specified.

        @type values: sequence of basestring
        @param values:
          Parameters to be set for the trait. Each value is either a value (in
          which case it designates the trait attribute name with an empty
          value) or a key=value assignment (in which case it designates the
          trait attribute name and the corresponding value). The order of the
          items i L{values} is irrelevant.
        """

        valid_keys = ("target_id", "date", "numval", "strval",)
        entity = self._get_entity(entity_type, entity_ident)
        self.ba.can_manipulate_traits(operator.get_entity_id(),
                                      entity.entity_id)
        trait = self.const.human2constant(trait, self.const.EntityTrait)
        params = dict()
        for val in values:
            key, value = val, ''
            if "=" in val:
                key, value = val.split("=", 1)
            assert key in valid_keys, "Illegal key %s" % key

            if key == "target_id":
                params[key] = self._get_entity(value).entity_id
            elif key == "date":
                params[key] = strptime(value, "%Y-%m-%d")
            elif key == "numval":
                params[key] = int(value)
            elif key == "strval":
                params[key] = value

        # shove the trait into the db
        entity.populate_trait(trait, **params)
        entity.write_db()
        return "OK, set trait %s for %s" % (trait, entity_ident)
    # end trait_set


    all_commands["trait_remove"] = Command(
        ("trait", "remove"),
        EntityType(default="account"),
        Id(),
        SimpleString())
    def trait_remove(self, operator, entity_type, entity_id, trait):
        """Remove a trait from entity.
        """
        
        entity = self._get_entity(entity_type, entity_id)
        self.ba.can_manipulate_traits(operator.get_entity_id(),
                                      entity.entity_id)
        trait = self.const.human2constant(trait, self.const.EntityTrait)

        if entity.get_trait(trait) is None:
            return "%s has no %s trait" % (entity_id, trait)

        entity.delete_trait(trait)
        return "OK, deleted trait %s from %s" % (trait, entity_id)
    # end trait_remove


    all_commands["trait_show"] = Command(
        ("trait", "show"),
        EntityType(default="account"),
        Id())
    def trait_show(self, operator, entity_type, entity_id):
        """Display traits set on the specified entity.
        """

        # FIXME: We may want to process traits' strval here -- if it's a
        # pickled value, it makes no sense sending the pickled value to the
        # client (quite pointless, really).
        entity = self._get_entity(entity_type, entity_id)
        self.ba.can_show_traits(operator.get_entity_id(),
                                entity.entity_id)
        return entity.get_traits().values()
    # end trait_show
# end BofhdVirthomeMiscCommands

    


