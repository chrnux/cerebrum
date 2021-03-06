#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 University of Oslo, Norway
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

""" AD2 "FroupSync", or "Fake GroupSync".

This modules utilizes ad2.ADSync.GroupSync to create and maintain groups in AD
based on non-group data in Cerebrum.

This module has the following sync functionality:

1. Update AD-group memberships from person affiliations
2. Update AD-group memberships from person consents


Configuration
-------------

The following adconf settings must be set for the *sync type* used with this
sync:

search_ou
    Search OU for AD-only groups.

target_ou
    Target OU for AD-only groups.

target_spread
    Spread that makes accounts eligible for existing in AD. Accounts without
    this spread won't be given membership in the AD-only groups, and won't be
    touched by the QuickSync.

sync_classes
    To enable "FroupSync", you need to set up a separate sync config. The
    config must contain one or more FroupSync subclasses in the 'sync_classes'
    setting.

    NOTE: FroupSync sync classes are not compatible with non-FroupSync
    classes. They should not be mixed.

attributes
    AD-only group attributes. The Member attribute is mandatory, and must be a
    ConfigUtils.CallbackAttr.

    The callback must take the 'members' attribute of the input, which is a
    list of Cerebrum accounts, and return a list of AD DNs for the accounts.
    This is where the OU for accounts are set up.

affiliation_groups
    Configures population of AD-only groups where membership is decided by
    person affiliation.

    The value is a dict that maps a group name to a list of affiliations that
    should cause membership in the AD-group.

consent_groups
    Configures population of AD-only groups where membership is decided by
    person consent.

    The value is a dict that maps a group name to a list of consents that
    should cause membership in the AD-group.


Caveats
-------

1. The FroupSync fullsync should run *AFTER* account sync, so that the AD
   accounts are up to date when this sync runs.
2. All groups that are maintained by FroupSyncs *MUST* be ignored by the
   regular groupsync.


Example configuration
---------------------

    SYNCS['froups'] = {
        'sync_classes': (
            'Cerebrum.modules.ad2.froupsync/ConsentGroupSync',
            'Cerebrum.modules.ad2.froupsync/AffGroupSync',
        ),
        'object_classes': (
            'Cerebrum.modules.ad2.CerebrumData/CerebrumGroup',
        ),
        'affiliation_groups': {
            'cerebrum-ansatt': [('SAP', 'ANSATT'), ('MANUELL', 'ANSATT'), ],
            'cerebrum-student': [('FS', 'STUDENT'), ('MANUELL', 'STUDENT'), ],
        },
        'consent_groups': {
            'consent-office365': ['office365'],
        },
        'target_ou': 'OU=Groups,..',
        'search_ou': 'OU=Groups,..',
        'create_ous': True,
        'move_objects': False,

        # TODO:
        'target_type': 'account',
        'target_spread': 'AD_account',

        'attributes': {
            'SamAccountName': ConfigUtils.AttrConfig(default='%(ad_id)s'),
            'DisplayName': ConfigUtils.AttrConfig(default='%(ad_id)s'),
            'DisplayNamePrintable': ConfigUtils.AttrConfig(default='%(ad_id)s'),
            'Description': ConfigUtils.CallbackAttr(
                lambda e: getattr(e, 'description', 'N/A').strip()),
            'Member': ConfigUtils.CallbackAttr(
                default=[],
                callback=lambda g: ['CN=%s,OU=Users,..' % m
                                    for m in getattr(g, 'members', [])]), },
        'script': {},
        'change_types': (
            ('consent', 'approve'),
            ('consent', 'decline'),
            ('consent', 'delete'),
            ('person', 'aff_add'),
            ('person', 'aff_mod'),
            ('person', 'aff_del'),
        ),
        'handle_unknown_objects': ('delete', None),
        'handle_deactivated_objects': ('disable', None),
        'quicksync_retry_seconds': 7*24*60*60,
    }

"""
from collections import defaultdict
from Cerebrum.utils.funcwrap import memoize
from .ADSync import GroupSync
from .CerebrumData import CerebrumGroup


class _FroupSync(GroupSync):

    """ Fake group sync.

    This class contains common functionality to sync 'fake' groups to AD. Fake
    groups are groups that only exist in AD, but are based on a non-group data
    set in Cerebrum (e.g. an account trait or a person affiliation).

    """

    # default_ad_object_class = 'group'

    @memoize
    def pe2affs(self, person_id):
        """ Get affiliations for a person.

        :param int person_id: The entity ID of an *existing* person entity.

        :return list:
            Tuples of (source system, affiliation type) for a given person.

        """
        self.pe.clear()
        self.pe.find(person_id)
        return [(r['source_system'], r['affiliation'])
                for r in self.pe.get_affiliations()]

    @memoize
    def pe2accs(self, person_id):
        """ Fetch AD accounts for a person.

        :param int person_id: The entity ID of an *existing* person entity.

        :return list:
            TODO: Tuples of (account_name, has_ad_spread),

        """
        accs = []

        for acc in self.ac.search(owner_id=person_id,
                                  expire_start=None,
                                  expire_stop=None):
            self.ac.clear()
            self.ac.find(acc['account_id'])
            accs.append(
                (self.ac.account_name,
                 self.is_ad_account(self.ac)))
        return accs

    @property
    def ad_group_names(self):
        """ A list of groups that needs to be fetched from AD.

        :return list: A list of group names.

        """
        return []

    def is_ad_account(self, account):
        """ Check if account _should_ exist in AD.

        :param Cerebrum.Account account: The account to check

        :return bool: True if the account should exist in AD.
        """
        if self.config['target_spread'] not in (s['spread'] for s in
                                                account.get_spread()):
            return False

        if account.is_expired() or account.is_deleted():
            return False

        return True

    def start_fetch_ad_data(self, object_class=None, attributes=dict()):
        """ Run AD-command to fetch groups from AD.

        Note that the result of L{all_groups} restricts which groups we'll get
        from AD.

        :param TODO object_class:
            TODO

        :param dict attributes:
            Attributes to get in addition to the 'attributes' config setting.
            This variable has the same structure as the 'attributes' config
            setting (mapping from attribute name to ConfigUtils.ConfigAttr).

        :return int:
            Returns command id, to later fetch the result.

        """
        attrs = self.config['attributes'].copy()
        if attributes:
            attrs.update(attributes)
        self.logger.debug2("Try to fetch %d attributes: %s",
                           len(attrs),
                           ', '.join(sorted(attrs)))

        if self.config['store_sid'] and 'SID' not in attrs:
            attrs['SID'] = None
        return self.server.start_list_objects(
            self.config['search_ou'],
            attrs,
            object_class or self.ad_object_class,
            names=self.ad_group_names)

    def fetch_cerebrum_data(self):
        """ Prevents superclass' fetch method to be called. """
        entities = getattr(self, 'entities', dict())
        self.logger.debug("Found %d groups in Cerebrum", len(entities))
        for group in entities.itervalues():
            self.logger.debug2("Cerebrum group %r with %d members",
                               group.entity_name,
                               len(getattr(group, 'members', set())))

    def add_group_member(self, group_name, account_name):
        """ Add member to group.

        Creates group-maps if they don't exist (entities, adid2entity,
        name2entity - which are used by ADSync.GroupSync), and creates group
        (CerebrumData.CerebrumGroup) if it doesn't exist.

        :param str group_name: The Cerebrum-esque name of the group
        :param str account_name: The account name, in Cerebrum

        """
        for attr in ('entities', 'name2entity', 'adid2entity'):
            if not hasattr(self, attr):
                setattr(self, attr, dict())

        if group_name not in self.name2entity:
            group = CerebrumGroup(self.logger,
                                  self.config,
                                  # non-existing entity_id:
                                  -1,
                                  group_name,
                                  # TODO: Generate a more useful description?
                                  description=group_name)
            # 'entities' should probably map entity_id (which we don't have) to
            # CerberumGroup - but it looks like the GroupSync only ever looks
            # at the dict values, so the key values don't really matter as long
            # as they are unique.
            self.entities[group.entity_name] = group
            self.name2entity[group.entity_name] = group
            self.adid2entity[group.ad_id.lower()] = group

        group = self.name2entity[group_name]
        if not hasattr(group, 'members'):
            setattr(group, 'members', set())
        group.members.add(account_name)

    # def pre_process(self):
    #     return super(ConsentGroupSync, self).pre_process()

    # def calculate_ad_values(self):
    #     return super(ConsentGroupSync, self).calculate_ad_values(cmd)

    # def process_ad_data(self, cmd):
    #     return super(ConsentGroupSync, self).process_ad_data(cmd)

    # def process_entities_not_in_ad(self):
    #     return super(ConsentGroupSync, self).process_entities_not_in_ad()

    # def post_process(self):
    #     return super(ConsentGroupSync, self).post_process()

    def process_ad_object(self, ad_object):
        self.logger.debug2("Processing AD group %r, with %d members",
                           ad_object.get('Name'),
                           len(ad_object.get('Member', [])))
        return super(_FroupSync, self).process_ad_object(ad_object)

    def _update_group(self, group_name, adds, removes):
        """ Update group memberships

        :param str group_name: The group to update
        :param list adds: A list of account names to add to the group
        :param list removes: A list of accounts to remove from the group

        """
        group_id = self.group2dn(group_name)
        result = True

        if adds:
            result &= self.server.add_group_members(
                group_id, self.accounts2dns(adds))
        if removes:
            result &= self.server.remove_group_members(
                group_id, self.accounts2dns(removes))
        return result

    def group2dn(self, group_name):
        """ Gets DN for a group name. """
        group = CerebrumGroup(
            self.logger, self.config, -1, group_name, description=None)
        return group.dn

    def accounts2dns(self, accounts):
        """ Use the rules of the Member attribute to convert the member names.

        :param str,list acocunts: One or more account names

        :return list: A list with the AD account DNs
        """
        if type(accounts) != list:
            accounts = [accounts, ]
        d = type('dummy', (object, ), {'members': accounts})
        member_attr = self.config['attributes']['Member']
        return member_attr.callback(d)


class AffGroupSync(_FroupSync):

    def configure(self, config_args):
        super(AffGroupSync, self).configure(config_args)

        self.config['affiliation_groups'] = dict()
        template = config_args.get('affiliation_groups', dict())
        for group, affs in template.iteritems():
            self.config['affiliation_groups'][group] = [
                (self.co.AuthoritativeSystem(sys),
                 self.co.PersonAffiliation(aff)) for sys, aff in affs]
        self.logger.debug("config[affiliation_groups]: %r",
                          self.config['affiliation_groups'])

    @property
    def ad_group_names(self):
        """ Groups to sync with AD. """
        groups = super(AffGroupSync, self).ad_group_names
        groups.extend(self.config['affiliation_groups'].keys())
        return groups

    @memoize
    def _update_aff_group(self, person_id):
        self.logger.debug("Updating aff groups for pid=%s", person_id)
        try:
            self.pe.clear()
            self.pe.find(person_id)
        except:
            return False

        # Decide which affiliations this user has
        memberships = defaultdict(lambda: False)
        for group, criterias in self.config['affiliation_groups'].iteritems():
            for aff in criterias:
                if aff in self.pe2affs(person_id):
                    memberships[group] = True
                    break  # Next group

        # Maintain membership for all accounts of that person
        result = True
        for gname in self.config['affiliation_groups']:
            adds = [uname for uname, enable in self.pe2accs(person_id)
                    if enable and memberships[gname]]
            removes = [uname for uname, enable in self.pe2accs(person_id)
                       if enable and not memberships[group]]
            result &= self._update_group(gname, adds, removes)
        return result

    def process_cl_event(self, row):
        """ Process person affiliation changes fast. """
        if row['change_type_id'] in (self.co.person_aff_add,
                                     self.co.person_aff_del,
                                     self.co.person_aff_mod):
            return self._update_aff_group(row['subject_entity'])

        return super(AffGroupSync, self).process_cl_event(row)

    def fetch_cerebrum_data(self):
        """ Prepare groups that should be synced to AD.

        Looks through person affiliations and build groups according to the
        'affiliation_groups' config setting.

        """
        for group, affs in self.config['affiliation_groups'].iteritems():
            for sys, aff in affs:
                for row in self.pe.list_affiliations(source_system=int(sys),
                                                     affiliation=int(aff),
                                                     include_deleted=False,
                                                     fetchall=False):
                    for name, enabled in self.pe2accs(row['person_id']):
                        if enabled:
                            self.add_group_member(group, name)
        super(AffGroupSync, self).fetch_cerebrum_data()


class ConsentGroupSync(_FroupSync):

    """ Sync consents and affiliations to AD groups. """

    def configure(self, config_args):
        super(ConsentGroupSync, self).configure(config_args)

        self.config['consent_groups'] = dict()
        template = config_args.get('consent_groups', dict())
        for group, consents in template.iteritems():
            self.config['consent_groups'][group] = [
                self.co.EntityConsent(c) for c in consents]
        self.logger.debug("config[consent_groups]: %r",
                          self.config['consent_groups'])

    @property
    def ad_group_names(self):
        """ Groups to sync with AD. """
        groups = super(ConsentGroupSync, self).ad_group_names
        groups.extend(self.config['consent_groups'].keys())
        return groups

    @memoize
    def _update_consent_group(self, person_id):
        """ Update consent groups for a given person.

        The result is memoized, so that we don't process the same person twice.

        :param int person_id: The entity_id of the person.

        :return bool: True if we could process this person.

        """

        self.logger.debug("Updating consent groups for pid=%s", person_id)
        try:
            self.pe.clear()
            self.pe.find(person_id)
        except:
            return False

        # Decide which consents this person has
        memberships = defaultdict(lambda: False)
        for group, consents in self.config['consent_groups'].iteritems():
            for consent in consents:
                if self.pe.get_consent_status(consent):
                    memberships[group] = True
                    break  # Next group

        # Maintain membership for all acocunts of that person
        result = True
        for gname in self.config['consent_groups']:
            adds = [uname for uname, enable in self.pe2accs(person_id)
                    if enable and memberships[gname]]
            removes = [uname for uname, enable in self.pe2accs(person_id)
                       if enable and not memberships[group]]
            result &= self._update_group(gname, adds, removes)
        return result

    def process_cl_event(self, row):
        """ Process consent changes fast. """
        if row['change_type_id'] in (self.co.consent_approve,
                                     self.co.consent_decline,
                                     self.co.consent_remove):
            return self._update_consent_group(row['subject_entity'])
        return super(ConsentGroupSync, self).process_cl_event(row)

    def fetch_cerebrum_data(self):
        """ Prepare groups that should be synced to AD.

        Looks through person consents and build groups according to the
        'consent_groups' config setting.

        """
        for group, consents in self.config['consent_groups'].iteritems():
            for row in self.pe.list_consents(
                    consent_code=consents,
                    entity_type=self.co.entity_person):
                for name, enabled in self.pe2accs(row['entity_id']):
                    if enabled:
                        self.add_group_member(group, name)
        super(ConsentGroupSync, self).fetch_cerebrum_data()
