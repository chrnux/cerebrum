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

group_help = {
    'access': "Access (authorisation) related commands",
    'disk': "Disk related commands",
    'email': "E-mail commands",
    'entity': "Entity commands",
    'group': "Group commands",
    'host': "Host related commands",
    'misc': 'Miscellaneous commands',
    'perm': 'Control of Privileges in Cerebrum',
    'person': 'Person related commands',
    'pquota': 'Pquota related commands',
    'quarantine': 'Quarantine related commands',
    'spread': 'Spread related commands',
    'trait': 'Trait related commands',
    'user': 'Account building and manipulation',
    }

# The texts in command_help are automatically line-wrapped, and should
# not contain \n
command_help = {
    'access': {
    'access_grant':
       "Grant authorisation to perform the operations in opset "
       "<set> on <entity> of type <type> to the members of group <group>.  "
       "The meaning of <attr> depends on <type>.",
    'access_disk':
       "List who's authorised to operate on disk <disk>",
    'access_global_group':
       "List who's authorised to operate on all groups",
    'access_global_host':
       "List who's authorised to operate on all hosts",
    'access_global_maildom':
       "List who's authorised to operate on all e-mail domains",
    'access_global_ou':
       "List who's authorised to operate on all OUs",
    'access_group':
       "List who's authorised to operate on group <gname>",
    'access_host':
       "List who's authorised to operate on host <hostname>",
    'access_list':
       "List everything an account or group can operate on.  Only direct "
       "ownership is reported: the entities an account can access "
       "due to group memberships will not be listed.",
    'access_list_opsets':
       "List all operation sets",
    'access_maildom':
       "List who's authorised to operate on e-mail domain <domain>",
    'access_ou':
       "List who's authorised to operate on OU <ou>",
    'access_revoke':
       "Revoke authorisation",
    'access_show_opset':
       "List the operations included in the operation set",
    'access_user':
       "List who's authorised to operate on account <uname>",
    },
    'disk': {
    "disk_list":
        "List the disks registered with a host.  A quota value in parenthesis "
        "means it uses to the host's default disk quota.",
    "disk_quota":
        "Enable quotas on a disk, and set the default value",
    },
    'email': {
    "email_add_address":
        "Add an alias address",
    "email_remove_address":
        "Remove an alias address",
    "email_add_filter":
        "Add a target filter",
    "email_remove_filter":
        "Remove target_filter",
    "email_reassign_address":
        "Move an address from one account to another",
    "email_update":
        "Update default address and aliases associated with account",
    "email_create_domain":
        "Create a new e-mail domain",
    "email_create_forward":
        "Create a new e-mail forward target",
    "email_domain_info":
        "View information about an e-mail domain",
    "email_add_domain_affiliation":
        "Connect a OU to an e-mail domain",
    "email_remove_domain_affiliation":
        "Remove link between OU and e-mail domain",
    "email_domain_configuration":
        "Configure settings for an e-mail domain",
    "email_failure_message":
        "Customise the failure message for a deleted account",
    "email_forward":
        "Turn e-mail forwarding for a user on/off",
    "email_add_forward":
        "Add a forward address",
    "email_remove_forward":
        "Remove a forward address",
    "email_info":
        "View e-mail information about a user or address",
    "email_create_archive":
        "Add address feeding an archive of a list",
    "email_create_list":
        "Add addresses needed for a Mailman list",
    "email_create_sympa_list":
        "Add addresses needed for a Sympa list",
    "email_create_sympa_cerebrum_list":
        "Add addresses needed for a Sympa list (Cerebrum only)",
    "email_create_list_alias":
       "Add an alias for a Mailman list.  This also adds additional "\
       "-owner and -request addresses.",
    "email_create_sympa_list_alias":
       "Add an alias for a Sympa list.  This also adds additional addresses "
       "(e.g. -owner, -request, etc.)",
    "email_remove_list_alias":
       "Remove an alias for a Mailman list. This also removes additional "
       "administrative addresses (-owner, -request, etc.)",
    "email_remove_sympa_list_alias":
       "Remove an alias for a Sympa list. This also removes additional "
       "administrative addresses (-owner, -request, etc.)",
    "email_create_multi":
        "Make an e-mail target which expands to the members of a group",
    "email_create_pipe":
        "Make an e-mail target which points to a pipe",
    "email_delete_pipe":
        "Delete an e-mail target that points to a pipe",
    "email_delete_archive":
        "Remove address for a Mailman archive",
    "email_delete_list":
        "Remove a Mailman list's addresses",
    "email_delete_sympa_list":
        "Remove a Sympa list's addresses",
    "email_delete_multi":
        "Remove a multi target and all its addresses",
    "email_edit_pipe_command":
        "Change the command the pipe target runs",
    "email_edit_pipe_user":
        "Change the account the pipe target runs as",
    "email_migrate":
        "Migrate users from old to new e-mail service",
    "email_mod_name":
        "Override name for person (to be used in e-mail address)",
    "email_move":
        "Move a user's e-mail to another server",
    "email_primary_address":
        "Changes the primary address for the e-mail target to the specified "\
        "value",
    "email_quota":
        "Change a user's storage quota for e-mail",
    "email_rt_add_address":
        "Add a valid address for RT queue",
    "email_rt_create":
        "Create an e-mail target for Request Tracker",
    "email_rt_delete":
        "Delete Request Tracker addresses",
    "email_rt_primary_address":
        "Change which address to rewrite to",
    "email_rt_remove_address":
        "Remove a valid address from the RT target",
    "email_spam_action":
        "How to handle user's spam",
    "email_spam_level":
        "Change user's tolerance for spam",
    "email_tripnote":
        "Turn vacation messages on/off",
    "email_add_tripnote":
        "Add vacation message",
    "email_list_tripnotes":
        "List user's vacation messages",
    "email_remove_tripnote":
        "Remove vacation message",
    },
    'entity': {
    'entity_accounts':
        "List information about accounts associated with given entities",
    'entity_history':
        "List the changes made to entity.",
    },
    'group': {
    'group_add': 'Let an account join a group',
    'group_create': 'Create a new Cerebrum group',
    'group_def': 'Set default filegroup for an account',
    'group_delete': 'Delete a group from Cerebrum',
    'group_demote_posix': 'Make an existing POSIX-group into a Cerebrum group',
    'group_gadd': 'Let src_group(s) join dest_group(s)',
    'group_gremove': 'Remove src_group(s) from given dest_group(s)',
    'group_info': 'View information about a spesific group',
    'group_list': 'List account members of a group',
    'group_list_expanded': 'List all members of a group, direct og indirect',
    'group_memberships': 'List all groups an entity is a member of',
    'group_padd': 'Let a person join a group',
    'group_personal': 'Create a new personal filegroup for an account',
    'group_promote_posix': 'Make an existing group into a POSIX-group',
    'group_remove': 'Remove member accounts from a given group',
    'group_request': 'Send in request for a new Cerebrum group',
    'group_search': 'Search for a group using various criteria',
    'group_set_description': 'Set description for a group',
    'group_set_expire': 'Set expire date for a group',
    'group_set_visibility': 'Set visibility for a group',
    'group_user': 'List all groups an account is a member of',
    },
    'host': {
    'host_info':
        "Show information about a host",
    'host_disk_quota':
        "Set the default disk quota for a host",
    },
    "misc": {
    "misc_affiliations":
        "List all known affiliations",
    "misc_cancel_request":
        "Cancel a pending request",
    "misc_change_request":
        "Change execution time for a pending request",
    "misc_check_password":
        "Test the quality of a given password",
    "misc_clear_passwords":
        "Forget the passwords which have been set this session",
    "misc_dadd":
        "Register a new disk",
    "misc_dls":
        "Use 'disk list' instead",
    "misc_drem":
        "Remove a disk",
    "misc_hadd":
        "Register a new host",
    "misc_hrem":
        "Remove a host",
    "misc_list_passwords":
        "View/print all the password altered this session",
    "misc_reload":
        "Re-read server config file (use with care)",
    "misc_list_requests":
        "View pending jobs",
    "misc_samba_mount":
        "Maps disk to logon-server (for use with Samba)",
    "misc_stedkode":
        "Look up OU by stedkode or name",
    "misc_verify_password":
        "Check whether an account has a given password",
    },
    'perm': {
    'perm_opset_list': 'List defined opsets',
    'perm_opset_show': 'View definition of the given opset',
    'perm_target_list': 'List auth_op_target data of the given type',
    'perm_add_target': 'Define a new auth_op_target',
    'perm_add_target_attr': 'Add attributes to an auth target',
    'perm_del_target': 'Remove an auth_op_target',
    'perm_del_target_attr': 'Removes attributes for a given target',
    'perm_list': 'List an entitys permissions',
    'perm_grant': 'Add an entry to auth_role',
    'perm_revoke': 'Remove an entry from auth_role',
    'perm_who_owns': 'Show owner of a target',
    'perm_who_has_perm': 'Show who has the given op_set permission somewhere',
    },
    'person': {
    'person_accounts':
        'View the accounts a person owns',
    'person_affiliation_add':
        'Add an affiliation to a person',
    'person_affiliation_remove':
        'Remove an affiliation from a person',
    'person_clear_name':
        'Remove the names coming from a source system from a person',
    'person_clear_id':
        'Remove specific external id type from a source system from a person',
    'person_create':
        'Register a new person in Cerebrum',
    'person_find':
        'Search for a person in Cerebrum',
    'person_info':
        'View information about a person',
    'person_list_user_priorities':
        'View a list ordered by priority of all the accounts owned by a person',
    'person_set_bdate':
        'Set a new birth date for a person',
    'person_set_id':
        'Set a new id for a person',
    'person_set_name':
        'Change the full name of a manually registered person',
    'person_student_info':
        'View student information for a person',
    'person_set_user_priority':
        'Change account priorities for a person',
    },
    'quarantine': {
    'quarantine_disable': 'Temporarily remove a quarantine',
    'quarantine_list': 'List defined quarantine types',
    'quarantine_remove': 'Remove a quarantine from a Cerebrum entity',
    'quarantine_set': 'Quarantine a given entity',
    'quarantine_show': 'View active quarantines for a given entity',
    },
    'spread': {
    'spread_add': 'Assign a new spread for an entity',
    'spread_list': 'List all defined spreads',
    'spread_remove': 'Remove a spread from an entity',
    },
    'trait': {
    'trait_info':
        "Display all traits associated with an entity",
    'trait_list':
        "List all entities which have specified trait",
    'trait_remove':
        "Remove a trait from an entity",
    'trait_set':
        "Add or update an entity's trait",
    },
    'user': {
    'user_affiliation_add': 'Add affiliation for an account',
    'user_affiliation_remove': 'Remove an affiliation for an account',
    'user_create': 'Create a POSIX user account',
    'user_delete': 'Delete an account',
    'user_demote_posix': 'Make a POSIX user account into a generic Cerebrum account',
    'user_find': 'Search for users',
    'user_gecos': 'Set gecos field for a user account',
    'user_history': "Show history of the account with uname. Limited to users subordinate to a privilege group the BOFH user is a member of",
    'user_info': 'View general information about an account',
    'user_move': 'Move a users home directory to another disk',
    'user_password': 'Set a new password for an account',
    'user_promote_posix': 'Make a Cerebrum account into a POSIX user account',
    'user_reserve': 'Reserve a user name in the database',
    'user_set_disk_quota': 'Temporary override users disk_kvota',
    'user_set_disk_status': 'Set homedir status for user',
    'user_set_expire': 'Set expire date for an account',
    'user_set_np_type': 'Set/remove np-type for an account (i.e. program, system etc)',
    'user_set_owner': 'Assign ownership for an account',
    'user_shell': 'Set login-shell for a POSIX user account',
    'user_student_create': 'Create a user for a student'
    },
    }

arg_help = {
    'account_name':
        ['uname', 'Enter account name',
         'Enter the name of the account for this operation'],
    'account_name_member':
        ['uname', 'Enter members accountname',
         "Enter the name of an account that already is a member"],
    'account_name_src':
        ['uname', 'Enter source accountname',
         'You should enter the name of the source account for this operation'],
    'account_password':
        ['password', 'Enter password'],
    'affiliation':
        ['affiliation', 'Enter affiliation',
         """A persons affiliation defines the current rolle of that person
within a defined organizational unit.  'misc affiliations' lists all
possible affiliations"""],
    'affiliation_optional':
        ['aff_opt', 'Affiliation? (optional)',
         'Enter affiliation to narrow search. Leave empty to search all affiliations.'],
    'affiliation_status':
        ['aff_status', 'Enter affiliation status',
"""Affiliation status describes a persons current status within a
defined organizational unit (e.a. whether the person is an active
student or an employee on leave).  'misc affiliations' lists
affiliation status codes"""],
    'source_system':
        ['source_system', 'Enter source system',
         'The name of the source system, i.e. FS/LT etc.'],
    'command_line':
        ['command', 'Enter command line'],
    'date':
        ['date', 'Enter date (YYYY-MM-DD)',
         "The legal date format is 2003-12-31"],
    'date_birth':
        ['date', 'Enter date of birth(YYYY-MM-DD)',
         "The legal date format is 2003-12-31"],
    'disk':
        ['/path/to/disk', 'Enter disk',
         "Enter the path to the disk without trailing slash or username.  "
         "Example:\n"
         "  /usit/sauron/u1\n\n"
         "If the disk isn't registered in Cerebrum and never should be, "
         "enter the whole path verbatim, prepended by a colon.  Example:\n"
         "  :/usr/local/oracle"],
    'disk_quota_set': ['size', 'Enter quota size',
                       "Enter quota size in MiB, or 'none' to disable quota, "
                       "or 'default' to use the host's default quota value."],
    'disk_quota_size': ['size', 'Enter quota size',
                        'Enter quota size in MiB, or -1 for unlimited quota'],
    'disk_quota_expire_date': ['end_date', 'Enter end-date for override',
                               'Format is 2003-12-31'],
    'email_address':
        ['address', 'Enter e-mail address'],
    'email_category':
        ['category', 'Enter e-mail category for domain',
         "Legal categories include:\n"+
         " - noexport     don't include domain in data exports\n"+
         " - cnaddr       primary address is firstname.lastname\n"+
         " - uidaddr      primary address is username\n"+
         " - all_uids     all usernames are valid e-mail addresses\n"+
         " - uio_globals  direct Postmaster etc. to USIT"],
    'email_domain':
        ['domain', 'Enter e-mail domain'],
    'email_failure_message':
        ['message', 'Enter failure message'],
    'email_forward_action':
        ['action', 'Enter action',
         "Legal forward actions:\n - on\n - off\n - local"],
    'email_tripnote_action':
        ['action', 'Enter action',
         "Legal tripnote actions:\n - on\n - off"],
    'entity_id':
        ['id', 'Enter entity ID',
         "Numeric ID of the entity you wish to process."],
    'external_id_type':
        ['external_id_type', 'Enter external id type',
         'The external id type, i.e. NO_BIRTHNO/NO_STUDNO etc'],
    'group_name':
        ['gname', 'Enter groupname'],
    'group_name_dest':
        ['dest_gname', 'Enter the destination group'],
    'group_name_new':
        ['gname', 'Enter the new group name'],
    'group_name_src':
        ['src_gname', 'Enter the source group'],
    'group_name_moderator':
	['gname', 'Enter the name of the moderator group'],
    'group_operation':
        ['op', 'Enter group operation',
         """Three values are legal: union, intersection and difference.
Normally only union is used."""],
    'group_visibility':
        ['vis', 'Enter visibility', "Example: A (= all)"],
    'id':
        ['id', 'Enter id',
         "Enter a group's internal id"],
    'id:entity_ext':
        ['entity_id', 'Enter entity_id, example: group:foo',
         'Enter an entity_id either as number or as group:name / account:name'],
    'id:target:account':
        ['account', 'Enter an existing entity',
         """Enter the entity as type:name, for example 'account:bob'.  If only
a name is entered, the type 'account' is assumed.  Other types include
'group', 'fnr' (f�dselsnummer), 'id' (Cerebrum's internal id) and
'host'.  The type name may be abbreviated.  (Some of the types may not
make sense for this command.)
"""],
    'id:target:group':
        ['group', 'Enter an existing entity',
         """Enter the entity as type:name, for example 'group:foo'.  If only a
name is entered, the type 'group' is assumed.  Other types include
'account', 'fnr' (f�dselsnummer), 'id' (Cerebrum's internal id) and
'host'.  The type name may be abbreviated.  (Some of the types may not
make sense for this command.)
"""],
    'id:target:person':
        ['person', 'Enter an existing entity',
         """Enter the entity as type:name, for example: 'account:bob'.  If
only a name is entered, it will be assumed to be either an account or
a fnr.  If an account is given, the person owning the account will be
used.  Other types include 'account', 'fnr' (f�dselsnummer), 'id'
(Cerebrum's internal id) and 'host'.  The type name may be
abbreviated.  (Some of the types may not make sense for this command.)
"""],
    'id:op_target':
        ['op_target_id', 'Enter op_target_id'],
    'id:request_id':
        ['request_id', 'Enter request_id',
         "'misc list_requests' returns legal values"],
    'limit_number_of_results':
        ['number', 'Number of results for query',
         "Gives upper limit for how many entries to include, counting " +
         "backwards from the most recent. Default (when left empty) is 100"],
    'mailing_admins':
        ['addresses', 'Enter comma separated list of administrators for '+
         'a mailing list'],
    'mailing_list':
        ['address', 'Enter address for a mailing list'],
    'mailing_list_alias':
        ['address', 'Enter alias for a mailing list'],
    'mailing_list_exist':
        ['address', 'Enter address of an existing mailing list'],
    'mailing_list_profile':
        ['list_profile', 'Enter mailing list profile'],
    'mailing_list_description':
        ['list_description', 'Enter mailing list description'],
    'move_type':
        ['move_type', 'Enter move type',
         """Legal move types:
 - immediate
 - batch
 - nofile
 - hard_nofile
 - student
 - student_immediate
 - give
 - request
 - confirm
 - cancel"""],
    'number_size_mib':
        ['size', 'Enter size (in MiB)',
        'Enter the size of storage, in mebibytes (1024*1024 bytes)'],
    'number_percent':
        ['percent', 'Enter percent',
        'Enter the percentage (without trailing percent sign)'],
    'on_or_off':
        ['on/off', 'Enter action',
         "Legal actions:\n - on\n - off"],
    'ou':
        ['ou', 'Enter OU',
        'Enter the 6-digit code of the organizational unit the person is '+
        'affiliated to'],
    'person_id':
        ['person_id', 'Enter person id',
        """Enter person id as idtype:id.
If idtype=fnr, the idtype does not have to be specified.
The currently defined id-types are:
  - fnr : norwegian f�dselsnummer."""],
    'person_id_other':
        ['person_id', 'Enter person id',
         """Enter person id as idtype:id.
If idtype=fnr, the idtype does not have to be specified.
You may also use entity_id:id."""],
    'person_id:current':
        ['[id_type:]current_id', 'Enter current person id',
         'Enter current person id.  Example: fnr:01020312345'],
    'person_id:new':
        ['[id_type:]new_id', 'Enter new person id',
         'Enter new person id.  Example: fnr:01020312345'],
    'person_name':
        ['name', 'Enter person name'],
    'person_name_full':
        ['fullname', 'Enter persons fullname'],
    'person_name_first':
        ['firstname', 'Enter all persons given names'],
    'person_name_last':
        ['lastname', 'Enter persons family name'],
    'person_name_type':
        ['nametype', 'Enter person name type'],
    # this is also in help.py, but without the search type "stedkode"
    'person_search_type':
        ['search_type', 'Enter person search type',
         """Possible values:
  - 'fnr'
  - 'name'
  - 'date' of birth, on format YYYY-MM-DD
  - 'stedkode'"""],
    'posix_shell':
        ['shell', 'Enter shell',
         'Enter the required shell without path.  Example: bash'],
    'print_select_range':
        ['range', 'Select range',
         """Select persons by entering a space-separated list of numbers.
Ranges can be written as "3-15" """],
    'print_select_template':
        ['template', 'Select template',
         """Choose template by entering its template.  The format of the
template name is: <language>:<template-name>.  If language ends with
-letter the letter will be sendt through snail-mail from a central
printer."""],
    'quarantine_type':
        ['qtype', 'Enter quarantine type',
          "'quarantine list' lists defined quarantines"],
    'rt_queue':
        ['queue', 'Enter name of RT queue',
         "Format is <queue>@<host>.  If <host> is the default host, it can be "
         "omitted."],
    'spam_action':
        ['spam action', 'Enter spam action',
          """Choose one of
          'dropspam'    Reject messages classified as spam
          'spamfolder'  Deliver spam to a separate IMAP folder
          'noaction'    Deliver spam just like legitimate email"""],
    'spam_level':
        ['spam level', 'Enter spam level',
          """Choose one of
          'aggressive_spam' Filter everything that resembles spam
          'most_spam'       Filter most emails that looks like spam
          'standard_spam'   Only filter email that obviously is spam
          'no_filter'       No email will be filtered as spam"""],
    'spread':
        ['spread', 'Enter spread',
         "'spread list' lists possible values"],
    'string_attribute':
        ['attr', 'Enter attribute',
         "Experts only.  See the documentation for details"],
    'string_bofh_request_target':
        ['target', 'Enter target',
         'Enter a target id corresponding to the previously specified type'],
    'string_bofh_request_search_by':
        ['search_by', 'Enter type to search by',
         """Enter the operation that you want to search for.  Legal values:
'requestee' username : the user that requested the operation
'operation' type : the type of operation (move_user, move_user_now,
    move_student, move_request, delete_user etc.)
'disk' path: a disk used as target
'account' username: the user affected by the operation"""],
    'string_description':
        ['description', 'Enter description'],
    'string_spread':
	['spread', 'Enter spread. Example: AD_group NIS_fg@uio'],
    'string_email_host':
        ['hostname', 'Enter e-mail server.  Example: cyrus02'],
    'string_exec_host':
        ['run_host', 'Enter host (fqdn) for command execution'],
    'string_email_delivery_host':
        ['delivery_host', 'Enter hostname for mail delivery. Example: sympa'],
    'string_email_move_type':
        ['email_move_type', 'Enter e-mail move type',
         """Legal move types:
            - file
            - nofile"""],
    'string_email_filter':
        ['email_filter', 'Enter e-mail filter type',
         """Legal filter types:
            - greylist"""],
    'string_email_target_name':
        ['email_target_name', 'Enter e-mail target name',
         """Target name should be a valid e-mail address"""],
    'string_filename':
        ['filename', 'Enter filename'],
    'string_group_filter':
        ['filter', 'Enter filter',
         """Enter a comma-separated list of filters.  There are four filter types:
  'name'   - Name of group
  'desc'   - Description text of group
  'expire' - Include expired groups (default "no")
  'spread' - List only groups with specified spread

A filter is entered on the format 'type:value'.  If you leave out the
type, 'name' is assumed.  The values for 'name' and 'desc' can contain
wildcards (* and ?).

Example:
  pc*,spread:AD_group  - list all AD groups whose names start with 'pc'"""],
    'string_host':
        ['hostname', 'Enter hostname.  Example: ulrik'],
    'string_new_priority':
        ['new_priority', 'Enter value new priority value',
         'Enter a positive integer (1..999), lower integers give higher priority'],
    'string_np_type':
        ['np_type', 'Enter np_type',
         """Type of non-personal account.  Valid values include:
'kursbruker'  - Course related
'programvare' - Software packages
'testbruker'  - Accounts for testing purposes"""],
    'string_op_set':
        ['op_set_name', 'Enter name of operation set',
         "Experts only.  See the documentation for details"],
    'string_old_priority':
        ['old_priority', 'Enter old priority value',
         "Select the old priority value"],
    'string_perm_target':
        ['id|type', 'Enter target id or type',
         'Legal types: host, disk, group'],
    'string_perm_target_type':
        ['type', 'Enter target type',
         'Legal types: host, disk, group'],
    'string_disk_status':
        ['disk_status', 'Enter disk status',
         'Legal values: archived create_failed not_created on_disk'],
    'string_from_to':
        ['from_to', 'Enter end date (YYYY-MM-DD) or '+
         'begin and end date (YYYY-MM-DD--YYYY-MM-DD)'],
    'string_why':
        ['why', 'Why?',
         'You should type a text indicating why you perform the operation'],
    'trait':
        ['trait', 'Name of trait'],
    'trait_val':
        ['value', 'Trait value',
         """Enter the trait value as key=value.  'key' is one of

 * target_id -- value is an entity, entered as type:name
 * date -- value is on format YYYY-MM-DD
 * numval -- value is an integer
 * strval -- value is a string

The key name may be abbreviated.  If value is left empty, the value
associated with key will be cleared.  Updating an existing trait will
blank all unnamed keys."""],
    'tripnote_text':
        ['text', 'Tripnote',
         'Enter message to be sent.  You may use \\n to separate lines of text.'],
    'user_create_person_id':
        ['owner', 'Enter account owner',
         """Identify account owner (person or group) by entering:
  Birthdate (YYYY-MM-DD)
  Norwegian f�dselsnummer (11 digits)
  Export-ID (exp:exportid)
  External ID (idtype:idvalue)
  Entity ID (entity_id:value)
  Group name (group:name)"""],
    'user_create_select_person':
        ['<not displayed>', '<not displayed>',
         """Select a person from the list by entering the corresponding
number.  If the person is not registered, you must create an instance with
"person create" """],
    'user_existing':
        ['uname', 'Enter an existing user name'],
    'user_search_type':
        ['search_type', 'Enter user search type',
         """Possible values:
  - 'stedkode'
  - 'host'
  - 'disk'"""],
    'yes_no_force':
        ['force', 'Force the operation?'],
    'yes_no_all_op':
        ['all', 'All operations?'],
    'yes_no_include_expired':
        ['include_expired', 'Include expired? (y/n)']
    }

# arch-tag: 9a914c2f-f0bd-472e-9f1b-bfb3aa757dc7
