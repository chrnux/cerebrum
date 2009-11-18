# -*- coding: iso-8859-1 -*-

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

"""
Site specific auth.py for NTNU

"""

from Cerebrum.modules.bofhd import auth
from Cerebrum.modules.bofhd.errors import PermissionDenied

from Cerebrum.Utils import Factory
Person_class = Factory.get("Person")
Account_class = Factory.get("Account")
Group_class = Factory.get("Group")
OU_class = Factory.get("OU")


class BofhdAuth(auth.BofhdAuth):
    """Defines methods that are used by bofhd to determine wheter
    an operator is allowed to perform a given action.

    This class only contains special cases for NTNU.
    """
    def _has_person_access(self, operator, target, operation, operation_attr=None):
        if not isinstance(target, Person_class):
            raise TypeError(
                "Can't handle target, expected type %s but got %s" % (Person_class, type(target)))

        return self._has_access(
            operator, target, self.const.auth_target_type_global_person,
            operation, operation_attr)

    def _has_account_access(self, operator, target, operation, operation_attr=None):
        if not isinstance(target, Account_class):
            raise TypeError(
                "Can't handle target, expected type %s but got %s" % (Account_class, type(target)))

        return self._has_access(
            operator, target, self.const.auth_target_type_global_account,
            operation, operation_attr)

    def _has_group_access(self, operator, target, operation, operation_attr=None):
        if not isinstance(target, Group_class):
            raise TypeError(
                "Can't handle target, expected type %s but got %s" % (Group_class, type(target)))

        return self._has_access(
            operator, target, self.const.auth_target_type_global_group,
            operation, operation_attr)

    def _has_ou_access(self, operator, target, operation, operation_attr=None):
        if not isinstance(target, OU_class):
            raise TypeError(
                "Can't handle target, expected type %s but got %s" % (OU_class, type(target)))

        if self._has_global_access(operator,
                                   operation,
                                   self.const.auth_target_type_global_ou,
                                   target.entity_id,
                                   operation_attr):
            return True

        return self._query_target_permissions(
            operator, operation, self.const.auth_target_type_ou, target.entity_id, None,
            operation_attr)


    def _has_host_access(self, operator, host_id, operation):
        if self.is_superuser(operator):
            return True
        
        if self._has_global_access(operator,
                                   operation,
                                   self.const.auth_target_type_global_host,
                                   host_id):
            return True

        return self._query_target_permissions(
            operator, operation, self.const.auth_target_type_host,
            host_id, None)

    def _has_email_domain_access(self, operator, domain_id, operation):
        if self.is_superuser(operator):
            return True
        
        if self._has_global_access(operator,
                                   operation,
                                   self.const.auth_target_type_global_email_domain,
                                   domain_id):
            return True

        return self._query_target_permissions(
            operator, operation, self.const.auth_target_type_email_domain,
            domain_id, None)


    def _has_spread_access(self, operator, spread_id, operation, victim_id=None):
        if self.is_superuser(operator):
            return True

        if self._has_global_access(operator, operation,
                                   self.const.auth_target_type_global_spread, victim_id):
            return True

        return self._query_target_permissions(
            operator, operation, self.const.auth_target_type_spread,
            spread_id, None)
    
    def _has_access(self, operator, target, target_type, operation, operation_attr=None):
        if self.is_superuser(operator):
            return True

        if self._has_global_access(operator, operation, target_type,
                                   target.entity_id, operation_attr=operation_attr):
            return True

        return self._has_access_to_entity_via_ou(operator, operation,
                                                 target, operation_attr=operation_attr)

    def _has_entity_access(self, operator, target, operation, operation_attr=None):
        if isinstance(target, Person_class):
            return self._has_person_access(
                operator, target, operation, operation_attr=operation_attr)
        elif isinstance(target, Account_class):
            return self._has_account_access(
                operator, target, operation, operation_attr=operation_attr)
        elif isinstance(target, OU_class):
            return self._has_ou_access(
                operator, target, operation, operation_attr=operation_attr)
        elif isinstance(target, Group_class):
            return self._has_group_access(
                operator, target, operation, operation_attr=operation_attr)
        else:
            raise TypeError(
                "Can't handle target of type %s" % type(target))

    def _has_global_access(self, operator, operation, global_type, victim_id,
                           operation_attr=None):
        if self.is_superuser(operator):
            return True

        return super(BofhdAuth, self)._has_global_access(
            operator, operation, global_type, victim_id, operation_attr)

    def can_login_to_cereweb(self, operator):
        if self.is_superuser(operator):
            return True

        return self._query_target_permissions(
                        operator, self.const.auth_login,
                        self.const.auth_target_type_cereweb, None, None)

    def can_set_password(self, operator, target):
        operation = self.const.auth_set_password
        return self._has_account_access(operator, target, operation)

    def can_read_account(self, operator, target):
        operation = self.const.auth_account_read
        return self._has_account_access(operator, target, operation)

    def can_create_account(self, operator, target):
        operation = self.const.auth_account_create

        if isinstance(target, Person_class):
            return self._has_person_access(operator, target, operation)
        elif isinstance(target, Group_class):
            return self._has_group_access(operator, target, operation)
        else:
            raise TypeError(
                "Can't handle target of type %s" % type(target))

    def can_edit_account(self, operator, target):
        operation = self.const.auth_account_edit
        return self._has_account_access(operator, target, operation)

    def can_delete_account(self, operator, target):
        operation = self.const.auth_account_delete
        return self._has_account_access(operator, target, operation)

    def can_create_disk(self, operator, host_id):
        operation = self.const.auth_disk_create
        return self._has_host_access(operator, host_id, operation)

    def can_edit_disk(self, operator, target):
        operation = self.const.auth_disk_edit
        return self._has_host_access(operator, target.host_id, operation)

    def can_delete_disk(self, operator, target):
        operation = self.const.auth_disk_delete
        return self._has_host_access(operator, target.host_id, operation)

    def can_create_host(self, operator):
        if self.is_superuser(operator):
            return True

        return self._has_global_access(
            operator, self.const.auth_host_create,
            self.const.auth_target_type_global_host, victim_id=None)

    def can_edit_host(self, operator, target):
        operation = self.const.auth_host_edit
        return self._has_host_access(operator, target.entity_id, operation)

    def can_delete_host(self, operator, target):
        operation = self.const.auth_host_delete
        return self._has_host_access(operator, target.entity_id, operation)

    def can_edit_motd(self, operator):
        """
        FIXME: Not implemented since the business logic is unclear.
        """
        return self.is_superuser(operator)

    def can_create_email_target(self, operator, entity_id, target_type, host_id):
        # XXX perhaps this should also check if operator is allowed to
        # work on entity_id
        operation = self.const.auth_email_target_create
        return self._has_host_access(operator, host_id, operation)

    def can_edit_email_target(self, operator, target):
        operation = self.const.auth_email_target_edit
        return self._has_host_access(operator, target.email_server_id, operation)

    def can_delete_email_target(self, operator, target):
        operation = self.const.auth_email_target_delete
        return self._has_host_access(operator, target.email_server_id, operation)

    def can_create_email_address(self, operator, target, domain):
        operation = self.const.auth_email_address_create
        return self._has_email_domain_access(operator, domain.entity_id,
                                             operation)

    def can_delete_email_address(self, operator, target):
        operation = self.const.auth_email_address_delete
        return self._has_email_domain_access(operator, target.email_addr_domain_id,
                                             operation)

    def can_create_email_domain(self, operator):
        if self.is_superuser(operator):
            return True

        return self._has_global_access(
            operator, self.const.auth_email_domain_create,
            self.const.auth_target_type_global_email_domain, victim_id=None)

    def can_edit_email_domain(self, operator, target):
        operation = self.const.auth_email_domain_edit
        return self._has_email_domain_access(operator, target.entity_id,
                                             operation)

    def can_delete_email_domain(self, operator, target):
        operation = self.const.auth_email_domain_delete
        return self._has_email_domain_access(operator, target.entity_id,
                                             operation)

    def can_create_ou(self, operator):
        if self.is_superuser(operator):
            return True

        return self._has_global_access(
            operator, self.const.auth_ou_create,
            self.const.auth_target_type_global_ou, victim_id=None)

    def can_edit_ou(self, operator, target):
        operation = self.const.auth_ou_edit
        return self._has_ou_access(operator, target, operation)

    def can_delete_ou(self, operator, target):
        operation = self.const.auth_ou_delete
        return self._has_ou_access(operator, target, operation)

    def can_edit_spread(self, operator, entity, spread_id):
        # FIXME finn bedre navn
        operation = self.const.auth_spread_edit
        return self._has_spread_access(operator, spread_id, operation)

    def can_edit_quarantine(self, operator, entity, quarantine_str):
        # FIXME finn bedre navn
        operation = self.const.auth_quarantine_edit
        return self._has_entity_access(operator, entity, operation,
                                       quarantine_str)

    def can_disable_quarantine(self, operator, entity, quarantine_str):
        # FIXME finn bedre navn
        operation = self.const.auth_quarantine_disable
        return self._has_entity_access(operator, entity, operation,
                                       quarantine_str)

    def can_add_note(self, operator, entity):
        operation = self.const.auth_note_edit
        if self.is_superuser(operator):
            return True

        return self._has_access(
            operator, entity, self.const.auth_target_type_global_person,
            operation)

    def can_delete_note(self, operator, entity):
        operation = self.const.auth_note_edit
        if self.is_superuser(operator):
            return True

        return self._has_access(
            operator, entity, self.const.auth_target_type_global_person,
            operation)

    def _get_ou(self, ou_id):
        ou = ou_id
        if isinstance(ou_id, str):
            ou_id = int(ou_id)

        if isinstance(ou_id, (int,long)):
            ou = OU_class(self._db)
            ou.find(ou_id)
        return ou

    def can_edit_affiliation(self, operator, target, ou_id, affiliation_id):
        operation = self.const.auth_affiliation_edit

        ou = self._get_ou(ou_id)
        affiliation = self.const.PersonAffiliation(affiliation_id)

        if not self._has_ou_access(operator, ou, operation, operation_attr=str(affiliation)):
            return False

        if isinstance(target, Person_class):
            if not target.get_affiliations():
                return True

            return self._has_person_access(operator, target, operation)
        elif isinstance(target, Account_class):
            return self._has_account_access(operator, target, operation)
        else:
            raise TypeError(
                "Can't handle target of unknown type (%s)" % type(target))

    def can_edit_external_id(self, operator, target, external_id_type):
        operation = self.const.auth_external_id_edit

        return self._has_entity_access(
                operator, target, operation, operation_attr=str(external_id_type))

    def can_read_external_id(self, operator, target, external_id_type):
        operation = self.const.auth_external_id_read

        return self._has_entity_access(
                operator, target, operation, operation_attr=str(external_id_type))

    def can_edit_homedir(self, operator, target, spread_id):
        operation = self.const.auth_homedir_edit
        return self._has_spread_access(operator, spread_id, operation, target.entity_id)

    def can_read_person(self, operator, target):
        operation = self.const.auth_person_read
        return self._has_person_access(operator, target, operation)

    def can_edit_person(self, operator, target):
        operation = self.const.auth_person_edit
        return self._has_person_access(operator, target, operation)

    def can_create_person(self, operator):
        if self.is_superuser(operator):
            return True

        return self._has_global_access(
            operator, self.const.auth_person_create,
            self.const.auth_target_type_global_person, victim_id=None)

    def can_delete_person(self, operator, target):
        operation = self.const.auth_person_delete
        return self._has_person_access(operator, target, operation)

    def can_syncread_account(self, operator, spread, auth_method):
        if self.is_superuser(operator):
            return True
        if self._query_target_permissions(
            operator, self.const.auth_account_syncread,
            self.const.auth_target_type_spread, int(spread), None,
            operation_attr=str(auth_method)):
            return True
        raise PermissionDenied("Can't bulk read accounts")

    def can_syncread_group(self, operator, spread):
        if self.is_superuser(operator):
            return True
        if self._query_target_permissions(
            operator, self.const.auth_group_syncread,
            self.const.auth_target_type_spread, int(spread), None):
            return True
        if self._has_global_access(
            operator, self.const.auth_group_syncread,
            self.const.auth_target_type_global_group, victim_id=None):
            return True
        raise PermissionDenied("Can't bulk read groups")

    def can_syncread_ou(self, operator, spread=None):
        if self.is_superuser(operator):
            return True
        if spread is not None:
            if self._query_target_permissions(
                operator, self.const.auth_ou_syncread,
                self.const.auth_target_type_spread, int(spread), None):
                return True
        if self._has_global_access(
            operator, self.const.auth_ou_syncread,
            self.const.auth_target_type_global_ou, victim_id=None):
            return True
        raise PermissionDenied("Can't bulk read OUs")

    def can_syncread_alias(self, operator):
        if self.is_superuser(operator):
            return True
        if self._has_global_access(
            operator, self.const.auth_alias_syncread,
            self.const.auth_target_type_global_account, victim_id=None):
            return True
        raise PermissionDenied("Can't bulk read Aliases")

    def can_syncread_person(self, operator, spread=None):
        if self.is_superuser(operator):
            return True
        if spread is not None:
            if self._query_target_permissions(
                operator, self.const.auth_person_syncread,
                self.const.auth_target_type_spread, int(spread), None):
                return True
        if self._has_global_access(
            operator, self.const.auth_person_syncread,
            self.const.auth_target_type_global_person, victim_id=None):
            return True
        raise PermissionDenied("Can't bulk read Persons")

    def can_syncread_homedir(self, operator, host_id):
        if self.is_superuser(operator):
            return True
        if self._query_target_permissions(
            operator, self.const.auth_homedir_syncread,
            self.const.auth_target_type_host, host_id, None):
            return True
        if self._has_global_access(
            operator, self.const.auth_homedir_syncread,
            self.const.auth_target_type_global_host, victim_id=None):
            return True
        raise PermissionDenied("Can't bulk read home directories")

    def can_set_homedir_status(self, operator, host_id, status):
        if self._query_target_permissions(
            operator, self.const.auth_homedir_set_status,
            self.const.auth_target_type_host, host_id, None,
            operation_attr=str(status)):
            return True
        if self._has_global_access(
            operator, self.const.auth_homedir_set_status,
            self.const.auth_target_type_global_host, victim_id=None,
            operation_attr=str(status)):
            return True
        raise PermissionDenied("Can't set homedir status")
