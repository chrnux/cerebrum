# -*- coding: iso-8859-1 -*-

# Copyright 2002-2005 University of Oslo, Norway
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

import time
import cereconf
from Cerebrum import Constants
from Cerebrum.Utils import Factory
from Cerebrum.modules.bofhd.errors import CerebrumError
from Cerebrum import Errors
import xmlrpclib

class _BofhdRequestOpCode(Constants._CerebrumCode):
    "Mappings stored in the auth_role_op_code table"
    _lookup_table = '[:table schema=cerebrum name=bofhd_request_code]'

class _AuthRoleOpCode(Constants._CerebrumCode):
    "Mappings stored in the auth_role_op_code table"
    _lookup_table = '[:table schema=cerebrum name=auth_op_code]'

class Constants(Constants.Constants):

    BofhdRequestOp = _BofhdRequestOpCode
    AuthRoleOp = _AuthRoleOpCode

    auth_grant_disk = _AuthRoleOpCode(
        'grant_disk', 'Grant access to operate on disk')
    auth_grant_group = _AuthRoleOpCode(
        'grant_group', 'Grant access to operate on group')
    auth_grant_host = _AuthRoleOpCode(
        'grant_host', 'Grant access to operate on host')
    auth_grant_maildomain = _AuthRoleOpCode(
        'grant_maildom', 'Grant access to operate on mail domain')
    auth_grant_ou = _AuthRoleOpCode(
        'grant_ou', 'Grant access to operate on OU')
    auth_add_disk = _AuthRoleOpCode(
        'add_disks', 'Add userdisks to hosts')
    auth_create_host = _AuthRoleOpCode(
        'create_host', 'Add hosts for userdisks')
    auth_create_group = _AuthRoleOpCode(
        'create_group', 'Create groups')
    auth_search_group = _AuthRoleOpCode(
        'search_group', 'Search for groups')
    auth_disk_def_quota_set = _AuthRoleOpCode(
        'disk_def_quota', 'Set default disk quota')
    auth_disk_quota_set = _AuthRoleOpCode(
        'disk_quota_set', 'Set disk quota')
    auth_disk_quota_forever = _AuthRoleOpCode(
        'disk_quota_forev', 'Set unlimited disk quota duration')
    auth_disk_quota_unlimited = _AuthRoleOpCode(
        'disk_quota_unlim', 'Set unlimited disk quota')
    auth_disk_quota_show = _AuthRoleOpCode(
        'disk_quota_show', 'View disk quota information')
    auth_view_studentinfo = _AuthRoleOpCode(
        'view_studinfo', 'View student information')
    auth_alter_printerquota = _AuthRoleOpCode(
        'alter_printerquo', 'Alter printer quota')
    auth_modify_spread = _AuthRoleOpCode(
        'modify_spread', 'Modify spread')
    auth_create_user = _AuthRoleOpCode(
        'create_user', 'Create user')
    auth_remove_user = _AuthRoleOpCode(
        'remove_user', 'Remove user')
    auth_view_history = _AuthRoleOpCode(
        'view_history', 'View history')
    auth_set_password = _AuthRoleOpCode(
        'set_password', 'Set password')
    auth_set_gecos = _AuthRoleOpCode(
        'set_gecos', "Set account's gecos field")
    auth_move_from_disk = _AuthRoleOpCode(
        'move_from_disk', 'Move account from disk')
    auth_move_to_disk = _AuthRoleOpCode(
        'move_to_disk', 'Move account to disk')
    auth_alter_group_membership = _AuthRoleOpCode(
        'alter_group_memb', 'Alter group memberships')
    auth_email_forward_off = _AuthRoleOpCode(
        'email_forw_off', "Disable user's forwards")
    auth_email_vacation_off = _AuthRoleOpCode(
        'email_vac_off', "Disable user's vacation message")
    auth_email_migrate = _AuthRoleOpCode(
        'email_migrate', "Move user's mailbox")
    auth_email_quota_set = _AuthRoleOpCode(
        'email_quota_set', "Set quota on user's mailbox")
    auth_email_create = _AuthRoleOpCode(
        'email_create', "Create e-mail addresses")
    auth_email_delete = _AuthRoleOpCode(
        'email_delete', "Delete e-mail addresses")
    auth_email_info_detail = _AuthRoleOpCode(
        'email_info_det', "View detailed information about e-mail account")
    auth_email_reassign = _AuthRoleOpCode(
        'email_reassign', "Reassign e-mail addresses")
    auth_quarantine_set = _AuthRoleOpCode(
        'qua_add', "Set quarantine on entity")
    auth_quarantine_disable = _AuthRoleOpCode(
        'qua_disable', "Temporarily disable quarantine on entity")
    auth_quarantine_remove = _AuthRoleOpCode(
        'qua_remove', "Remove quarantine on entity")
    # These are values used as auth_op_target.target_type.  This table
    # doesn't use a code table to map into integers, so we can't use
    # the CerebrumCode framework.  TODO: redefine the database table
    # In the meantime, we define the valid code values as constant
    # strings here.
    auth_target_type_disk = "disk"
    auth_target_type_group = "group"
    auth_target_type_host = "host"
    auth_target_type_maildomain = "maildom"
    auth_target_type_ou = "ou"
    # These are wildcards, allowing access to _all_ objects of that type
    auth_target_type_global_group = "global_group"
    auth_target_type_global_host = "global_host" # also "disk"
    auth_target_type_global_maildomain = "global_maildom"
    auth_target_type_global_ou = "global_ou"

    bofh_move_user = _BofhdRequestOpCode('br_move_user', 'Move user (batch)')
    bofh_move_user_now = _BofhdRequestOpCode('br_move_user_now', 'Move user')
    bofh_move_student = _BofhdRequestOpCode('br_move_student', 'Move student')
    bofh_move_request = _BofhdRequestOpCode('br_move_request', 'Move request')
    bofh_move_give = _BofhdRequestOpCode('br_move_give', 'Give away user')
    bofh_archive_user = _BofhdRequestOpCode('br_archive_user',
                                            'Archive home directory')
    bofh_delete_user = _BofhdRequestOpCode('br_delete_user', 'Delete user')
    bofh_quarantine_refresh = _BofhdRequestOpCode('br_quara_refresh',
                                                  'Refresh quarantine')
    bofh_homedir_restore = _BofhdRequestOpCode('br_homedir_rest',
                                               'Restore users homedir')
    
    # br_email_move stays in queue until delivery has stopped.
    # generate_mail_ldif.py will set the mailPause attribute based on
    # entries in the request queue.
    #
    # Messages will queue up on the old server while mailPause is
    # true.  When the move is done, those messages will make another
    # trip through the main hub before being delivered.
    # Unfortunately, this may mean we get another shadow copy.
    #
    # state_data is optionally a request_id: wait if that request is
    # in queue (typically a create request).  A bofh_email_convert is
    # inserted when done.
    bofh_email_move = _BofhdRequestOpCode('br_email_move',
                                          'Move user among e-mail servers')
    bofh_email_create = _BofhdRequestOpCode('br_email_create',
                                            'Create user mailboxes')
    bofh_email_delete = _BofhdRequestOpCode('br_email_delete',
                                            'Delete all user mailboxes')
    bofh_email_hquota = _BofhdRequestOpCode('br_email_hquota',
                                            'Set e-mail hard quota')
    bofh_email_convert = _BofhdRequestOpCode('br_email_convert',
                                             'Convert user mail config')
    bofh_email_restore = _BofhdRequestOpCode('br_email_restore',
                                             'Restore users mail from backup')
    # entity_id is address_id of the official name of the mailing list
    # destination_id is address_id of the admin address
    bofh_mailman_create = _BofhdRequestOpCode('br_mm_create',
                                              'Create mailman list')
    # entity_id and destination_id as above
    # state_data is optional request_id for dependency
    bofh_mailman_add_admin = _BofhdRequestOpCode('br_mm_add_admin',
                                                 'Add admin to mailman list')
    # entity_id as above
    # since this has been deleted by the time process_bofhd_requests runs,
    # the name of the list is passed as a string in state_data as well.
    bofh_mailman_remove = _BofhdRequestOpCode('br_mm_remove',
                                              'Remove mailman list')

class BofhdRequests(object):
    def __init__(self, db, const, id=None):
        self._db = db
        self.co = const
        now = time.time()
        tmp = list(time.localtime(now))
        for i in range(-6,-1):
            tmp[i] = 0
        midnight = time.mktime(tmp)
        if now - midnight > 3600 * 22:
            self.batch_time = self._db.TimestampFromTicks(midnight + 3600 * (24+22))
        else:
            self.batch_time = self._db.TimestampFromTicks(midnight + 3600 * 22)
        self.now = self._db.TimestampFromTicks(time.time())

    def get_conflicts(self, op):
        """Returns a list of conflicting operation types.  op can be
        an integer or a constant."""

        # "None" means _no_ conflicts, there can even be several of
        # that op pending.  All other ops implicitly conflict with
        # themselves, so there can only be one of each op.
        c = self.co
        conflicts = {
            int(c.bofh_move_user):       [ c.bofh_move_student,
                                           c.bofh_move_user_now,
                                           c.bofh_move_request,
                                           c.bofh_delete_user ],
            int(c.bofh_move_student):    [ c.bofh_move_user,
                                           c.bofh_move_user_now,
                                           c.bofh_move_request,
                                           c.bofh_delete_user ],
            int(c.bofh_move_user_now):   [ c.bofh_move_student,
                                           c.bofh_move_user,
                                           c.bofh_move_request,
                                           c.bofh_delete_user ],
            int(c.bofh_move_request):    [ c.bofh_move_user,
                                           c.bofh_move_user_now,
                                           c.bofh_move_student,
                                           c.bofh_delete_user ],
            int(c.bofh_move_give):       None,
            int(c.bofh_archive_user):    [c.bofh_move_user,
                                          c.bofh_move_user_now,
                                          c.bofh_move_student,
                                          c.bofh_delete_user],
            int(c.bofh_delete_user):     [ c.bofh_move_user,
                                           c.bofh_move_user_now,
                                           c.bofh_move_student,
                                           c.bofh_email_create ],
            int(c.bofh_email_move):      [ c.bofh_delete_user ],
            int(c.bofh_email_create):    [ c.bofh_email_delete,
                                           c.bofh_delete_user ],
            int(c.bofh_email_delete):    [ c.bofh_email_create,
                                           c.bofh_email_move ],
            int(c.bofh_email_hquota):    [ c.bofh_email_delete ],
            int(c.bofh_email_convert):   [ c.bofh_email_delete ],
            int(c.bofh_mailman_create):  [ c.bofh_mailman_remove ],
            int(c.bofh_mailman_add_admin):  None,
            int(c.bofh_mailman_remove):  [ c.bofh_mailman_create,
                                           c.bofh_mailman_add_admin ],
            int(c.bofh_quarantine_refresh): None,
            int(c.bofh_email_restore): [c.bofh_email_create,
                                        c.bofh_email_hquota],
            int(c.bofh_homedir_restore): [c.bofh_move_user,
                                          c.bofh_move_user_now,
                                          c.bofh_move_student,
                                          c.bofh_delete_user]
            }[int(op)]

        if conflicts is None:
            conflicts = []
        else:
            conflicts.append(op)
        # Make sure all elements in the returned list are integers
        return [int(c) for c in conflicts]

    def add_request(self, operator, when, op_code, entity_id,
                    destination_id, state_data=None):

        conflicts = self.get_conflicts(op_code)

        for r in self.get_requests(entity_id=entity_id):
            if int(r['operation']) in conflicts:
                raise CerebrumError, ("Conflicting request exists (%s)" %
                                      self.co.BofhdRequestOp(r['operation']).
                                      description)
        reqid = int(self._db.nextval('request_id_seq'))
        cols = {
            'requestee_id': operator,
            'run_at': when,
            'operation': int(op_code),
            'entity_id': entity_id,
            'destination_id': destination_id,
            'state_data': state_data,
            'request_id': reqid
            }
        
        self._db.execute("""
        INSERT INTO [:table schema=cerebrum name=bofhd_request] (%(tcols)s)
        VALUES (%(binds)s)""" % {
            'tcols': ", ".join(cols.keys()),
            'binds': ", ".join([":%s" % t for t in cols.keys()])},
                         cols)
        return reqid

    def delay_request(self, request_id, minutes=10):
        for r in self.get_requests(request_id):
            # Note: the semantics of time objects is DB driver
            # dependent, and not standardised in PEP 249.
            # PgSQL will convert to ticks when forced into int().
            t = int(r['run_at'])
            # don't use self.now, it's a DateTime object.
            now = time.time()
            if t < now:
                t = now
            when = self._db.TimestampFromTicks(t + minutes*60)
            self._db.execute("""
                UPDATE [:table schema=cerebrum name=bofhd_request]
                SET run_at=:when WHERE request_id=:id""",
                             {'when': when, 'id': request_id})
            return
        raise Errors.NotFoundError, "No such request %d" % request_id

    def delete_request(self, entity_id=None, request_id=None,
                       operator_id=None, operation=None):
        cols = {}
        if entity_id is not None:
            cols['entity_id'] = entity_id
        if request_id is not None:
            cols['request_id'] = request_id
        if operator_id is not None:
            cols['requestee_id'] = operator_id
        if operation is not None:
            cols['operation'] = int(operation)
        self._db.execute("""DELETE FROM [:table schema=cerebrum name=bofhd_request]
        WHERE %s""" % " AND ".join(["%s=:%s" % (x, x) for x in cols.keys()]), cols)

    def get_requests(self, request_id=None, operator_id=None, entity_id=None,
                     operation=None, destination_id=None, given=False):
        cols = {}
        if request_id is not None:
            cols['request_id'] = request_id
        if entity_id is not None:
            cols['entity_id'] = entity_id
        if operator_id is not None:
            cols['requestee_id'] = operator_id
        if operation is not None:
            cols['operation'] = int(operation)
        if destination_id is not None:
            cols['destination_id'] = int(destination_id)
        qry = """
        SELECT request_id, requestee_id, run_at, operation, entity_id,
               destination_id, state_data
        FROM [:table schema=cerebrum name=bofhd_request]
        WHERE """
        ret = self._db.query(qry + " AND ".join(
            ["%s=:%s" % (x, x) for x in cols.keys()]),
                             cols)
        if given:
            group = Factory.get('Group')(self._db)
            tmp = []
            # TODO: include_indirect_members=1 when Group supports it
            for r in group.list_groups_with_entity(operator_id):
                tmp.append(str(r['group_id']))
            extra_where = ""
            if len(tmp) > 0:
                extra_where = "AND destination_id IN (%s)" % ", ".join(tmp)
            ret.extend(self._db.query(qry + "operation=:op %s" % extra_where,
                                      {'op': int(self.co.bofh_move_give)}))
        return ret

class BofhdUtils(object):
    """Utility functions for bofhd."""

    def __init__(self, db):
        self.db = db
        self.co = Factory.get("Constants")(db)

    # TBD: The helper functions inside get_target() might be useful
    # outside.
    #
    # TODO: Lookup by e-mail address -- but how to do that without
    # requiring mod_email?
    def get_target(self, name, default_lookup="account", restrict_to=None):
        """The user input should be a name on the form
            [LOOKUP ':'] IDENTIFIER
        The name of the lookup type can be abbreviated by the user.
        If the user doesn't include a lookup type, default_lookup
        will be used.

        Valid lookup types are
             'account' (name of user => Account or PosixUser)
             'fnr' (external ID, Norwegian SSN => Person)
             'group' (name of group => Group or PosixGroup)
             'host' (name of host => Host)
             'id' (entity ID => any)

        If name is actually an integer, 'id' lookup is always chosen.

        If restrict_to isn't set, it will be initialised according to
        default_lookup.  It should be a list containing the names of
        acceptable classes, and a CerebrumError will be raised if the
        resulting entity isn't among them.  The class names must be
        known to Factory.  To accept all kinds of objects, pass
        restrict_to=[].

        restrict_to can lead to a cast operation.  E.g., if Person is
        acceptable, but the user specified an account, the account's
        owner will be returned.

        The return value is an instantiated object of the appropriate
        class.  If no entity is found, CerebrumError is raised.

        """

        # This mapping restricts the possible values get_target returns.
        entity_lookup_types = { "account": ("Account",),
                                "fnr": ("Person",),
                                "group": ("Group",),
                                "host": ("Host",),
                                "disk": ("Disk",),
                                "entity_id": None,
                                "id": None }

        def get_target_find_lookup(name, default_lookup):
            if isinstance(name, int):
                # We ignore default_lookup in this case, even if it
                # could conceivably have been a "fnr" on systems where
                # int is 64-bit.
                ltype = "id"
            elif name.count(":") == 0:
                if name.isdigit() and len(name) == 11:
                    ltype = "fnr"
                else:
                    ltype = default_lookup
            else:
                ltype, name = name.split(":", 1)
                ltype = self.get_abbr_type(ltype, entity_lookup_types.keys())
            return ltype, name

        def get_target_lookup(ltype, name):
            if ltype == 'id' or ltype == 'entity_id':
                return get_target_entity(name)
            elif ltype == 'account' or ltype == 'group':
                return get_target_posix_by_name(name, clstype=ltype)
            elif ltype == 'fnr':
                return get_target_person_fnr(name)
            elif ltype == 'host':
                return get_target_host(name)
            elif ltype == 'disk':
                return get_target_disk(name)
            else:
                raise CerebrumError, "Lookup type %s not implemented yet" % ltype
         
        def get_target_entity(ety_id):
            try:
                ety_id = int(ety_id)
            except ValueError:
                # TBD: This triggers if the numeric value can't fit in
                # 32 bits, too.  Should we use a regexp instead?
                raise CerebrumError, "Non-numeric id lookup (%s)" % ety_id
            en = Factory.get("Entity")(self.db)
            try:
                en = en.get_subclassed_object(ety_id)
            except Errors.NotFoundError:
                raise CerebrumError, "No such entity (%d)" % ety_id
            except ValueError, e:
                raise CerebrumError, "Can't handle entity (%s)" % e
            if en.entity_type == self.co.entity_account:
                return get_target_posix_by_object(en)
            elif en.entity_type == self.co.entity_group:
                return get_target_posix_by_object(en, clstype="group")
            return en

        def get_target_posix_by_object(obj, clstype="account"):
            """Takes an Account or Group object, and returns a
            PosixUser or PosixGroup object if the entity is also a
            POSIX object.
            
            """
            # FIXME: due to constants being defined in this file, we
            # can't import these at the top level.
            from Cerebrum.modules.PosixUser import PosixUser
            from Cerebrum.modules.PosixGroup import PosixGroup

            if clstype == "account":
                promoted = PosixUser(self.db)
            elif clstype == "group":
                promoted = PosixGroup(self.db)
            try:
                promoted.find(int(obj.entity_id))
                return promoted
            except Errors.NotFoundError:
                return obj

        def get_target_posix_by_name(name, clstype="account"):
            """Returns either a Posix or a Cerebrum core version of
            Account or Group.

            """
            # FIXME: due to constants being defined in this file, we
            # can't import these at the top level.
            from Cerebrum.modules.PosixUser import PosixUser
            from Cerebrum.modules.PosixGroup import PosixGroup

            # We could use get_target_posix_by_object, but then the
            # common case of a PosixUser would lead to a wasted
            # instantiation of a plain Account object first.
            if clstype == "account":
                plain_cls = Factory.get("Account")
                posix_cls = PosixUser
            elif clstype == "group":
                plain_cls = Factory.get("Group")
                posix_cls = PosixGroup
            try:
                obj = posix_cls(self.db)
                obj.find_by_name(name)
            except Errors.NotFoundError:
                try:
                    obj = plain_cls(self.db)
                    obj.find_by_name(name)
                except Errors.NotFoundError:
                    raise CerebrumError, "Unknown %s %s" % (clstype, name)
            return obj
         
        def get_target_person_fnr(id):
            person = Factory.get("Person")(self.db)
            found = {}
            for name in cereconf.SYSTEM_LOOKUP_ORDER:
                ss = getattr(self.co, name)
                try:
                    person.clear()
                    person.find_by_external_id(self.co.externalid_fodselsnr,
                                               id, source_system=ss)
                    found[int(person.entity_id)] = person
                except Errors.NotFoundError:
                    pass
            found = found.keys()
            if len(found) == 0:
                raise CerebrumError, "No person with fnr %s" % id
            if len(found) > 1:
                raise CerebrumError, "More than one person with fnr %s found" % id
            person.clear()
            person.find(found[0])
            return person

        def get_target_host(hostname):
            host = Factory.get("Host")(self.db)
            try:
                host.find_by_name(hostname)
            except Errors.NotFoundError:
                raise CerebrumError("No such host: %s" % hostname)
            return host

        def get_target_disk(path):
            disk = Factory.get("Disk")(self.db)
            host_id = None
            if path.count(':'):
                hostname, path = path.split(':', 1)
                host_id = get_target_host(hostname).entity_id
            try:
                disk.find_by_path(path, host_id=host_id)
            except Errors.NotFoundError:
                raise CerebrumError("No such path: %s" % path)
            except Errors.TooManyRowsError:
                # This can't happen currently, disk_info.path has a
                # UNIQUE constraint.
                raise CerebrumError("%s is not unique, use 'host:path'" % path)
            return disk

         #
         # Finally, here is the start of the function itself
         #

        if name is None or name == "":
            raise CerebrumError, "Empty value given"

        ltype, name = get_target_find_lookup(name, default_lookup)
        obj = get_target_lookup(ltype, name)

        if restrict_to is None:
            restrict_to = entity_lookup_types[ltype]
        if not restrict_to:
            # empty list means accept everything
            return obj
        if not isinstance(restrict_to, (list, tuple)):
            restrict_to = (restrict_to,)
        for clsname in restrict_to:
            if isinstance(obj, Factory.get(clsname)):
                return obj
        # The object isn't strictly acceptable according to
        # restrict_to, but let's be user-friendly and turn an account
        # into a person and a disk into a host.
        if ("Person" in restrict_to and
            isinstance(obj, Factory.get("Account")) and
            obj.owner_type == self.co.entity_person):
            return get_target_entity(obj.owner_id)
        if "Host" in restrict_to and isinstance(obj, Factory.get("Disk")):
            return get_target_entity(obj.host_id)

        raise CerebrumError, ("Wrong argument type '%s' returned by %s:%s" %
                              (self.co.EntityType(obj.entity_type),
                               ltype, name))

    def get_abbr_type(self, type_name, valid_types):
        """Looks for type_name in valid_types, and returns the full
        type name if found.  Raises CerebrumError if not found, or if
        name is ambiguous.

        """
        found = None
        for v in valid_types:
            if v.startswith(type_name):
                if found:
                    raise CerebrumError("Ambiguous value '%s' (%s or %s?)" %
                                        (type_name, found, v))
                found = v
        if found is None:
            raise CerebrumError, "Unknown value '%s'" % type_name
        return found

# arch-tag: d6650fa6-6a9b-459f-be7e-80c9e6cbba52
