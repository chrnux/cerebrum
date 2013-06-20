# -*- coding: utf-8 -*-
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
"""Default Cerebrum settings for Active Directory and the AD synchronisations.

Overrides should go in a local, instance specific file named:

    adconf.py

Each setting should be well commented in this file, to inform developers and
sysadmin about the usage and consequences of the setting.

"""

# The SYNCS dict contains settings that are specific to a given sync type. The
# key is normally the name of a spread that should be used for sync with AD, but
# it could also be just an identifier if the sync can't match against one
# spread.
#
# Note that these settings could be overriden in subclasses of the basic sync,
# and they could also be overridden in parameters when running the sync scripts.
SYNCS = dict()
# The available settings for each element of SYNCS:
#
# - sync_classes (list): 
#   Contains all the classes that should be used as the sync class. Works like
#   cereconf.CLASS_CONSTANTS, as the classes gets merged through `type`.
#   Example:
#       ('Cerebrum.modules.ad2.ADSync/UserSync',
#        'Cerebrum.modules.instance/ADSyncmixin',)
#
# - target_spread (str or list):
#   What spread(s) to use to retrieve entities from Cerebrum. If not set, and
#   the key of the sync matches a spread, that is used instead.
#   Example:
#       'AD_account'
#
# - target_type (str):
#   The entity_type in Cerebrum. The sync converts the entity_type into the
#   proper object type for AD. This is required when the sync type is not a
#   spread, otherwise the spread's target_type is used.
#   Example:
#       'host'
#
# - domain (str):
#   The AD-domain the sync should update.
#   Example:
#       'kaos.local'
#
# - dryrun (bool):
#   If the sync should actually do something, or just be in read-only mode. Note
#   that you are still required to have a connection to the AD server, as
#   information is read from it, but just not written back.
#   Default:
#       False
#   Example:
#       False
#
# - ad_admin_messages (list):
#   What to do with errors and warnings that are for the AD-administrators and
#   not useful for Cerebrum's sysadmins. Must be a tuple/list with a list of
#   settings. The list could contain more elements to give the messages in
#   different ways, e.g. both logging it and sending it by mail. For the inner
#   list: the first element decides what to do, the second gives the log level
#   to send (info, warn, debug), and all following elements are options for the
#   decision. Possible values of first element:
#   - None or 'log': Log the messages just as normal log messages. Will
#                    not be sent in any other way.
#   - mail: Send the messages to given e-mail addresses.
#   - file: Put the message in a new file in the given directory. File
#           name is random to avoid overwriting existing files.
#
#   TODO: We only need to send e-mails. Remove everything else, as it only
#   complicates matters.
#
#   Example:
#   (('mail', 'warning', 'drift@example.no', 'sysadmins@example.org'),
#    ('log', 'info'),
#    ('file', 'debug', '/cerebrum/dumps/AD/log/'))
#
# - server (str):
#   The hostname of the Member server we should connect to:
#   Examples:
#       '128.39.253.98'
#       'winrmserver.example.com'
#
# - port (int):
#   If we should use a different port than the default.
#   Default:
#       5986 (for encrypted communication)
#       5985 (for unencrypted communication)
#
# - encrypted (bool):
#   If the communication should go encrypted through a TLS tunnel or not.
#   Production environments should NOT go unencrypted!
#   Default:
#       True
#
# - auth_user (str):
#   The user we should authenticate to the Windows member server with. It is
#   recommended that this user has no privileges in the AD domain, and is only
#   used for connecting to the server.
#   Example:
#       'cereauth'
#
# - domain_admin (str):
#   The user that we use to administrate the AD domain with. It is recommended
#   that this is not the same user as 'auth_user'.
#
# - target_ou (str):
#   The default OU in AD that the objects should be put in when created, or if
#   they should be moved.
#   Example:
#       OU=Users,OU=Cerebrum,DC=kaos,DC=local
#
# - search_ou (str):
#   The OU in AD that is used for searching for all objects that we should
#   update. If set too wide, we would find to many objects that we care about,
#   thus slowing down the sync. If set too narrow, we would not find all objects
#   that we should be updating, which would make the sync go and search for each
#   such object separately, thus slowing the sync down even further.
#   Example:
#       OU=Cerebrum,DC=kaos,DC=local
#
# - ignore_ou (list):
#   A list of OUs in AD that the sync should ignore. Objects put in these OUs
#   should not be updated.
#
#   Note that objects outside of the 'search_ou' are not touched unless they are
#   named the same as a Cerebrum entity that is set to be synced with AD. The
#   'ignore_ou' could contain both OUs inside and outside of 'search_ou'.
#
#   It is responsibility of the sysadmin's of the AD domain to not create
#   objects in AD that matches Cerebrum entities, as this creates conflicts that
#   could get complicated.
#
#   TODO: Not decided if passwords should be set for ignored accounts. Update
#   this doc when the decision is made.
#
#   Example:
#       ['OU=cant_touch_this,OU=cerebrum,DC=kaos,DC=local',
#        'OU=Sysadmins,OU=cerebrum,DC=kaos,DC=local',],
#
# - handle_unknown_objects (list):
#   What to do with objects unknown in Cerebrum, including those without
#   AD-spread. Possible options:
#   - ignore: do nothing. The OUs will not be cleaned up in.
#   - disable: Mark the object as disabled. Note that this only works for
#              accounts.
#   - move: deactivate and move the object to a given OU
#   - delete: delete the object. Note that this might not be undone!
#   TODO: Only move, without disabling?
#   Examples:
#       ('disable', None)
#       ('move', 'OU=Deleted,OU=Cerebrum,DC=kaos,DC=local')
#
# - handle_deactivated_objects (list):
#   What to do with entities not active in Cerebrum, e.g. if they're
#   quarantined. Possible options:
#   - ignore: do nothing. The OUs will not be cleaned up in.
#   - disable: Mark the object as disabled. Note that this only works for
#              accounts.
#   - move: deactivate and move the object to a given OU
#   - delete: delete the object. Note that this might not be undone!
#   TODO: Only move, without disabling?
#   Examples:
#       ('disable', None)
#       ('ignore', None)
#       ('move', 'OU=Deleted,OU=Cerebrum,DC=kaos,DC=local')
#
# - language (list):
#   The different languages to use, ordered by priority. Used for instance for
#   the Title attribute.
#   Examples:
#       ('nb', 'nn', 'en')
#
# - store_sid (bool):
#   If SIDs should be retrieved from AD and stored in Cerebrum as external_id.
#   SIDs can not be set in AD, so we can not write these back to AD. If a
#   deleted account gets recreated, it gets a new SID.
#   Default: 
#       False
#
# - move_objects (bool):
#   If objects that are not in the correct OU should be moved to the correct OU.
#   Note that objects that are put in a sub-OU of their target_ou will not be
#   moved upwards in the base sync.
#   Default:
#       False
#
# - change_types (list):
#   The list of change_type that the quicksync could handle. Note that you
#   should not change this list without testing the sync, because when a new
#   change type is added to the list, _all_ such changes will be retrieved from
#   the change_log, which could be quite a long list. You must then first mark
#   all those as completed before running the sync - ninja-sql? ;)
#   
#   TODO: are there shorter constants names to use instead?
#
#   Example:
#       (('e_account', 'password'), # password changes
#        ('e_account', 'create'),   # new accounts
#        ('person', 'name_mod'),    # a person's name is changed
#        ('ad_attr', 'add'),        # an AD-attribute is set
#        ('ad_attr', 'del')),       # an AD-attribute is removed
#        )
#
# - attributes (dict):
#   What AD attributes the sync should update in AD. Attributes not in this list
#   will not be modified by the sync, except of attributes indirectly modified
#   by other commands, like moving an object that makes DN change. Some
#   attributes will be generated by the sync while others could be retrieved
#   from the AD-attribute table.
#
#   Note that the case does sometimes matter in powershell, unfortunately, but
#   not always. This is confusing, unfortunately.
#
#   Note that the sync might not have access to all attributes, and some
#   attributes, like the SID, is read-only. Also, since we use SamAccountName as
#   an identifier, we would not handle a change of this.
#
#   Each element in the list must be a list with various configuration settings
#   for the given attribute.
#
#   Examples:
#       {'SamAccountName': None,
#        'Title': ('PERSONALTITLE', 'WORKTITLE'), # What person titles to use,
#                                                 # in priority.
#        'Mail': None,
#        'UserPrincipalName': None,
#        }
#
# - useraccountcontrol (dict):
#
#   TODO: Not sure how this should behave, yet!
#
#   The UserAccountControl controls what user control settings we should update.
#   Those not defined here gets ignored by us. If the variable is empty, all
#   control settings gets ignored, except enabling and disabling accounts which
#   is handled in other ways. The keys must be valid UAC settings, and the
#   values are the boolean settings we require to set.
#
#   Examples:
#       {'PasswordNotRequired': False,
#        },
#
# - scripts (dict):
#   If scripts should be executed when certain events occur. This should be a
#   dict where the keys are event identifiers in the sync. Do not confuse this
#   with change_log events. The value is the absolute path to the script to
#   execute, that is located on the Windows server we connect to, named in the
#   setting "server". The scripts must be executable by powershell, and it's the
#   AD sysadmin's responsibility that the scripts work as they should.
#
#   - new_object: When an object has been created in AD.
#   - TODO
#