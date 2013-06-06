#!/usr/bin/env python
# -*- encoding: iso-8859-1 -*-
#
# Copyright 2013 University of Oslo, Norway
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

""" This file contains workflows and common operations related to virthome
accounts and groups. It's a generalization of some of the bofhd-commands, so
that they can be used by other applications.

NOTICE: The classes here won't check permissions, that needs to be done from
the caller!

TODO: This is the new home for all virthome-related bofh-commands. All changes
should be done here, and called from bofhd_virthome_cmds. This class should
stay genereic enough to be used outside of bofhd.
"""

import sys
import re
import cereconf
from Cerebrum.Utils import Factory
from Cerebrum.Errors import CerebrumError, NotFoundError

from mx.DateTime import DateTimeDelta
from Cerebrum.modules.bofhd.auth import BofhdAuthOpSet, BofhdAuthOpTarget, BofhdAuthRole
from Cerebrum.modules.virthome.bofhd_auth import BofhdVirtHomeAuth


# TODO: Theres should be moved to cereconf, better than to have these hardcoded here, no?
cereconf.BOFHD_OPSETS = ('group-owner', 'group-moderator', )

# TODO: Should we rather have a more restrictive, proper whitelist?
cereconf.ALLOWED_URL_REGEXP = ('^http(s)?://([a-zA-Z0-9\-]+\.)+?uio\.no', # ONLY http(s)://uio.no or http(s)://*.uio.no 
                               '^http(s)?://(?!folk)', # NOT http(s)://folk
                               '^http(s)?://(?!heim\.ifi)', # NOT http(s)://heim.ifi
                               '^http(s)?://(?![a-zA-Z0-9\-]+\.at\.ifi)', # NOT http(s)://*.at.ifi
                              ) # The URLs must pass ALL of the rules here

# TODO: Is this okay? Should we just have one class in stead? There's no real
#       reason to keep two classes... 
#       They have been split up here in order to separate between methods that
#       should be visible (imported) in other modules. All the methods in
#       VirthomeUtils should only be used here. However, they DO need to be
#       visible elsewhere until all functionality have been migrated from
#       bofhd_virthome_cmds. It'll be easy to merge the classes later. I hope.
class VirthomeBase:
    """ The outer access layer: Methods here are workflows such as creating
    accounts, creating groups, disabling groups, creating events...
    This is the only class that _should_ be imported (visible) to other
    modules.
    """

    def __init__(self, db):
        """ NOTE: This class does not commit any changes to the db. That must
        be done from the calling environment.

        @type db: Cerebrum.Database
        @param db: A database connection.
        """
        self.db = db
        self.co = Factory.get('Constants')(db)

        self.account_class = Factory.get('Account')
        self.group_class = Factory.get('Group')

        self.vhutils = VirthomeUtils(db)


    # TODO: Should owners be restricted to the FEDAccount class? How about the
    # Webapp-account, or other su accs?
    def group_create(self, group_name, description, creator, owner, url=None, forward=None):
        """ This method creates a new VirtHome group.

        @type group_name: str
        @param group_name: The name of the new group

        @type description: str
        @param description: The group description

        @type creator: self.account_class
        @param creator: The account object of the creator of this group.

        @type owner: self.account_class
        @param owner: The account object of the owner of this group.

        @type url: str
        @param url: A url resource associated with the group

        @type forward: str
        @param forward: A url resource to an external app that uses this group
        """
        gr = self.group_class(self.db)

        if self.vhutils.group_exists(group_name):
            raise CerebrumError("Group name '%s' already exists" % group_name)

        # TBD: Verify owner.np_type is FEDaccount? Must it be?

        try:
            gr.populate(creator.entity_id, group_name, description)
            gr.write_db()
            gr.set_group_resource(url)
        except ValueError:
            raise CerebrumError(str(sys.exc_info()[1]))

        #forward = self.vhutils.whitelist_url(forward)
        #if forward:
            #self.gr.populate_trait(self.co.trait_group_forward, strval=forward)

        for spread in getattr(cereconf, "BOFHD_NEW_GROUP_SPREADS", ()):
            gr.add_spread(self.co.human2constant(spread, self.co.Spread))

        self.vhutils.grant_group_auth(owner, 'group-owner', gr)
        gr.write_db()
        return gr


    def group_invite_user(self, inviter, group, email, timeout=3):
        """ This method sets up an event that will allow a user to join a
        group. 

        @type inviter: self.account_class
        @param inviter: The account that is setting up the invitation

        @type group: self.group_class
        @param group_name: The group that should be joined

        @type email: str
        @param : The email adrress of the user that is invited

        @type timeout: int
        @param timeout: The number of days until the confirmation key expires.

        @rtype: dict
        @return: A dictionary with the following keys:
                'confirmation_key': <str> The code that is used to confirm the invitation
                'match_user': <str> A username, if a user exists with that email-address
                'match_user_email': An e-mailaddress. Not sure why?
        """
        ac = self.account_class(self.db)

        assert hasattr(inviter, 'entity_id')
        assert hasattr(group, 'entity_id')

        timeout = DateTimeDelta(int(timeout))
        if timeout.day < 1:
            raise CerebrumError('Timeout too short (%d)' % timeout.day)
        if (timeout > cereconf.MAX_INVITE_PERIOD):
            raise CerebrumError("Timeout too long (%d)" % timeout.day)

        ret = {'confirmation_key': self.vhutils.setup_event_request(
                                       group.entity_id,
                                       self.co.va_group_invitation,
                                       {"inviter_id": inviter.entity_id,
                                        "group_id": group.entity_id,
                                        "invitee_mail": email,
                                        "timeout": timeout.day,})}

        # check if e-mail matches a valid username
        try:
            ac.find_by_name(email)
            ret['match_user'] = ac.account_name
            if ac.np_type in (self.co.fedaccount_type, self.co.virtaccount_type):
                ret['match_user_email'] = ac.get_email_address()
        except NotFoundError:
            pass

        return ret


    def group_disable(self, group):
        """This method removes all members and auth data related to a group,
        effectively disabling it without actually 'nuking' it.

        @type group_name: str
        @param group_name: The name of the group that should be joined

        @rtype: str
        @return: The name of the group that was disabled, nice for feedback.
        """
        assert hasattr(group, 'entity_id')

        # Yank all the spreads
        for row in group.get_spread():
            group.delete_spread(row["spread"])

        # Remove all members
        for membership in group.search_members(group_id=group.entity_id):
            group.remove_member(membership["member_id"])

        group.write_db()
            
        # Clean up the permissions (granted ON the group and TO the group)
        self.vhutils.remove_auth_targets(group.entity_id)
        self.vhutils.remove_auth_roles(group.entity_id)
        return group.group_name

    def list_members(self, group):
        members = self.vhutils.list_group_members(group)
        return set([m['member_name'] for m in members if m['member_name']])

    def list_memberships(self, account):
        groups = self.vhutils.list_group_memberships(account)
        return set([g['name'] for g in groups])



class VirthomeUtils:
    """ Helper methods related to virthome """

    def __init__(self, db):
        self.db = db
        self.co = Factory.get('Constants')(db)

        self.group_class = Factory.get('Group')
        self.account_class = Factory.get('Account')

        # Or compile on each call to 
        self.url_whitelist = [re.compile(r) for r in cereconf.ALLOWED_URL_REGEXP]



    def group_exists(self, name):
        """ This method simply tests if a group name exists in the database

        @type name: str
        @param name: Name of the group to look for

        @rtype: bool
        @return: True if the group exists, otherwise False
        """
        group = self.group_class(self.db)
        try: 
            group.find_by_name(name)
            return True
        except NotFoundError: 
            pass
        return False

    
    def list_group_members(self, group, indirect_members=False):
        """ This methid lists members of a group. It does NOT include operators
        or moderators, unless they are also members.

        @type group: Cerebrum.Group
        @param group: The group to list members of

        @type indirect: bool
        @param indirect: If we should include indirect members
        """
        ac = self.account_class(self.db)
        gr = self.group_class(self.db)

        assert hasattr(group, 'entity_id')

        result = list()
        for x in group.search_members(group_id=group.entity_id,
                                      indirect_members=indirect_members):
            owner_name = None
            member_name = None
            email_address = None
            member_type = self.co.EntityType(x['member_type'])
            if member_type == self.co.entity_account:
                ac.clear()
                ac.find(x['member_id'])
                if ac.np_type in (self.co.fedaccount_type,
                                  self.co.virtaccount_type):
                    member_name = ac.account_name
                    owner_name = ac.get_owner_name(self.co.human_full_name)
                    email_address = ac.get_email_address()
            elif member_type == self.co.entity_group:
                gr.clear()
                gr.find(x['member_id'])
                member_name = gr.group_name
            result.append({'member_id': x['member_id'],
                           'member_type': str(member_type),
                           'member_name': member_name,
                           'owner_name': owner_name,
                           'email_address': email_address,})

        #eids = set([x['member_id'] for x in result])
        #contact_raw = ac.list_contact_info(entity_ids=eids)
        #ac_email_cache = dict((x['entity_id'], x['contact_value']) for x
            #in contact_raw if x['contact_type'] == co.virthome_contact_email)
        #ac_owner_cache = dict((x['entity_id'], x['contact_value']) for x
            #in contact_raw if x['contact_type'] == co.virthome_contact_email)

        result.sort(lambda x, y: cmp(x['member_name'], y['member_name']))
        return result
        

    def list_group_memberships(self, account, indirect_members=False):
        """
        ['group_id', 'name', 'description', 'visibility', 'creator_id',
        'create_date', 'expire_date'] 
        """
        gr = self.group_class(self.db)
        assert hasattr(account, 'entity_id')

        result = list()
        for group in gr.search(member_id=account.entity_id, 
                               indirect_members=indirect_members):
            gr.clear()
            gr.find(group['group_id'])
            tmp = group.dict()
            tmp['url'] = gr.get_contact_info(self.co.virthome_group_url)
            result.append(tmp)

        return result



    def get_trait_val(self, entity, trait_const, val='strval'):
        """Get the trait value of type L{val} of L{entity} that is of type
        L{trait_const}.
        
        @type entity: Cerebrum.Entity
        @param entity: The entity which trait is being looked up

        @type trait_const: _EntityTraitCode
        @param trait_const: The type of trait to load

        @rtype: str
        @return: The L{val} of the trait, if it exists. None if the L{entity}
                 doesn't have a trait of type L{trait_const}, or the trait
                 doesn't have a value L{val}
        """
        assert hasattr(entity, 'entity_id')
        try:
            trait = entity.get_trait(trait_const)
            return trait.get(val, None)
        except AttributeError:
            pass
        return None


    # TODO: This method should only return urls that passes a whitelist check.
    #       Should we throw an error if the url fails?
    def whitelist_url(self, url):
        """ TODO

        @type url: str
        @param url: The URL to whitelist

        @rtype: str
        @return: The whitelisted url, or None if the L{url} didn't pass.
        """
        #raise NotImplementedError('TODO')
        # TODO: Prepend http, https if missing?
        
        for r in self.url_whitelist:
            if not r.match(url):
                return None

        return url
    

    # Changelog/event/invitation related methods

    def setup_event_request(self, issuer_id, event_type, params=None):
        """ Perform the necessary magic when creating a pending confirmation
        event (i.e. create a changelog entry with the event).

        @type issuer_id: int
        @param issuer_id: The C{entity_id} of the event creator/inviter

        @type event_type: Constants._ChangeTypeCode
        @param event_type: The changelog type that should be used to store this event.

        @type params: obj
        @param params: An object containing other arbitrary information that
                       relates to the L{event_type}. Will be serialized with
                       'pickle', and saved in the changelog.

        @rtype: str
        @return: The confirmation key, or ID, of the newly created event.
        """
        return self.db.log_pending_change(issuer_id, event_type, None,
                                          # This will be pickle.dumps()-ed by
                                          # the underlying API
                                          change_params=params)



    # BofhdAuth-related methods

    def find_or_create_op_target(self, entity_id, target_type):
        """ Finds an op-target of type L{target_type} that points to
        L{entity_id}. If no targets exist, one will be created.
        """
        aot = BofhdAuthOpTarget(self.db)

        op_targets = [t for t in aot.list(entity_id=entity_id,
                                          target_type=target_type)]

        # No target exists, create one
        if not op_targets:
            aot.populate(entity_id, target_type)
            aot.write_db()
            return aot
        
        assert len(op_targets) == 1 # This method will never create more than one
        assert op_targets[0]['attr'] is None # ... and never populates attr

        # Target exists, return it
        aot.find(op_targets[0]['op_target_id'])
        return aot
    
    
    def grant_group_auth(self, account, opset_name, group):
        """ Grants L{entity_id} access type L{opset_name} over group
        L{group_id}.

        This can be used to give admin and moderator access to groups.

        @type account: self.account_class
        @param account: The account that should be granted access

        @type opset_name: str
        @param opset_name: The name of the operation set (type of access)

        @type group: self.group_class
        @param group: The group that L{account} should be given access to

        @rtype: bool
        @return: True if access was granted, False if access already exists
        """
        assert opset_name in cereconf.BOFHD_OPSETS
        assert hasattr(account, 'entity_id')
        assert hasattr(group, 'entity_id')
        
        ar = BofhdAuthRole(self.db)
        aos = BofhdAuthOpSet(self.db)
        aot = self.find_or_create_op_target(group.entity_id,
                                            self.co.auth_target_type_group)
        aos.find_by_name(opset_name)

        assert account.np_type == self.co.fedaccount_type
        assert hasattr(aot, 'op_target_id') # Must be populated

        roles = list(ar.list(account.entity_id, aos.op_set_id, aot.op_target_id))

        if len(roles) == 0:
            ar.grant_auth(account.entity_id, aos.op_set_id, aot.op_target_id)
            return True # Access granted
        
        return False # Already had access
    

    def revoke_group_auth(self, account, opset_name, group):
        """ Removes L{account_id} access type L{opset_name} over group
        L{group_id}.

        This can be used to remove admin and moderator access to groups.

        @type account: self.account_class
        @param account: The account that should be granted access

        @type opset_name: str
        @param opset_name: The name of the operation set (type of access)

        @type group: self.group_class
        @param group: The group that L{account} should be given access to

        @rtype: bool
        @return: True if access was revoked, False if access didn't exist.
        """
        assert opset_name in cereconf.BOFHD_OPSETS
        assert hasattr(account, 'entity_id')
        assert hasattr(group, 'entity_id')

        ar = BofhdAuthRole(self.db)
        aos = BofhdAuthOpSet(self.db)

        aos.find_by_name(opset_name)
        aot = self.find_or_create_op_target(group.entity_id, self.co.auth_target_type_group)

        assert account.np_type == self.co.fedaccount_type
        assert aot.target_type == self.co.auth_target_type_group

        roles = list(ar.list(account.entity_id, aos.op_set_id, aot.op_target_id))

        if len(roles) == 0:
            return False # No permissions to remove
        
        ar.revoke_auth(account.entity_id, aos.op_set_id, aot.op_target_id)
        
        # If that was the last permission for this op_target, kill op_target
        if len(list(ar.list(op_target_id=aot.op_target_id))) == 0:
            aot.delete()

        return True # Permissions removed
    
    
    def remove_auth_targets(self, entity_id, target_type=None):
        """ This method will remove authorization targets of type
        L{target_type} that points to the L{entity_id}. If L{target_type} is
        None, all targets regardless of type will be removed.

        @type entity_id: int
        @param entity_id: The entity_id of an object.

        @type target_type: str
        @param target_type: The target type of the authorization target
        """
        ar = BofhdAuthRole(self.db)
        aot = BofhdAuthOpTarget(self.db)

        for target in aot.list(entity_id=entity_id, target_type=target_type):
            aot.clear()
            aot.find(target['op_target_id'])

            # Before the target is removed, we must remove all roles that
            # grants access to the target.
            for role in ar.list(op_target_id=target["op_target_id"]):
                ar.revoke_auth(role['entity_id'], role['op_set_id'],
                               target['op_target_id'])
            aot.delete()
    
    
    def remove_auth_roles(self, entity_id):
        """ This method will remove all authorization roles that has been given
        to an entity. It will also remove any remaining authorization targets
        that no longer have auth roles pointing to it as a result.

        @type entity_id: int
        @param entity_id: The entity_id of an object.
        """
        ar = BofhdAuthRole(self.db)
        aot = BofhdAuthOpTarget(self.db)

        # Remove all auth-roles the entity have over other targets
        for target in ar.list(entity_ids=entity_id):
            ar.revoke_auth(entity_id, target['op_set_id'], target['op_target_id'])

            # Remove auth-target if there aren't any more auth-roles pointing
            # to it
            remaining = ar.list(op_target_id=target['op_target_id'])
            if len(remaining) == 0:
                aot.clear()
                aot.find(target['op_target_id'])
                aot.delete()


    def list_group_owners(self, group):
        """ List owners of a group. See L{list_opset_accounts} for usage.
        """
        return self.list_opset_accounts(group, 'group-owner')


    def list_group_moderators(self, group):
        """ List moderators of a group. See L{list_opset_accounts} for usage.
        """
        return self.list_opset_accounts(group, 'group-moderator')


    def list_groups_owned(self, account):
        """ List groups owned by C{account}. See L{list_opset_groups} for
        usage.
        """
        return self.list_opset_groups(account, 'group-owner')


    def list_groups_moderated(self, account):
        """ List groups moderated by C{account}. See L{list_opset_groups} for
        usage.
        """
        return self.list_opset_groups(account, 'group-moderator')


    def list_opset_accounts(self, group, opset_name):
        """ Return accounts holding a specific permission L{opset_name} on
        L{group}.

        This method is meant for answering questions like 'which accounts
        moderate this group?'.

        @type group: Cerebrum.Group
        @param group: A populated group object to list 'moderators' for.

        @rtype: list
        @return: A list of dictionaries with keys: 
                 ['account_id', 'account_name', 'owner_name', 'email_address',
                  'group_id', 'group_name', 'description']

        See also L{list_opset_groups}.
        """
        assert opset_name in cereconf.BOFHD_OPSETS
        assert hasattr(group, 'entity_id')

        ac = self.account_class(self.db)
        ba = BofhdVirtHomeAuth(self.db)
        aos = BofhdAuthOpSet(self.db)
        aos.find_by_name(opset_name)

        tmp = list(ba.get_permission_holders_on_groups(
            aos.op_set_id, group_id=group.entity_id))
        for entry in tmp:
            ac.clear()
            ac.find(entry['account_id'])
            entry['owner_name'] = ac.get_owner_name(self.co.human_full_name)
            entry['email_address'] = ac.get_email_address()
            
        return tmp


    def list_opset_groups(self, account, opset_name):
        """ Return groups where L{account} has the specific permission
        L{opset_name}.

        This is a complement to the L{list_ownership_accounts). This method is
        meant for answering questions like 'which groups am I moderating?'

        @type group: Cerebrum.Account
        @param group: The account to list 'moderated group' for.

        @type opset_name: str
        @param opset_name: The permission to list groups for.

        @rtype: list
        @return: A list of dictionaries with keys: 
                 ['group_id', 'group_name', 'url', 'description', 
                  'account_id', 'account_name']
        """
        assert opset_name in cereconf.BOFHD_OPSETS
        assert hasattr(account, 'entity_id')

        gr = self.group_class(self.db)
        ba = BofhdVirtHomeAuth(self.db)
        aos = BofhdAuthOpSet(self.db)
        aos.find_by_name(opset_name)

        tmp = list(ba.get_permission_holders_on_groups(
            aos.op_set_id, account_id=account.entity_id))
        for entry in tmp:
            gr.clear()
            gr.find(entry['group_id'])
            entry['url'] = gr.get_contact_info(self.co.virthome_group_url)
        
        return tmp
