# -*- coding: iso-8859-1 -*-
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
"""Help text for bofhd in the TSD project."""

group_help = {
    'access': "Access (authorisation) related commands",
    'entity': "Entity commands",
    'group': "Group commands",
    'misc': 'Miscellaneous commands',
    'ou': 'Organizational unit related commands',
    'person': 'Person related commands',
    'project': "Project related commands",
    'quarantine': 'Quarantine related commands',
    'spread': 'Spread related commands',
    'user': 'Account building and manipulation',
    'trait': 'Trait related commands',
    'perm': 'Control of Privileges in Cerebrum'
    }

# The texts in command_help are automatically line-wrapped, and should
# not contain \n
command_help = {
    'access': {
    'access_grant':
       "Grant authorisation to perform the operations in opset "
       "<set> on <entity> of type <type> to the members of group <group>.  "
       "The meaning of <attr> depends on <type>.",
    'access_group':
       "List who's authorised to operate on group <gname>",
    'access_host':
       "List who's authorised to operate on host <hostname>",
    'access_revoke':
       "Revoke authorisation",
    },
    'group': {
    'group_add_member': 'Add a member to a group',
    'group_remove_member': 'Remove a member from a group',
    'group_create': 'Create a new Cerebrum group',
    'group_delete': 'Delete a group from Cerebrum',
    'group_info': 'View information about a spesific group',
    'group_list': 'List account members of a group',
    'group_list_all': 'List all existing groups',
    'group_list_expanded': 'List all members of a group, direct and indirect',
    'group_memberships': 'List all groups an entity is a member of',
    'group_search': 'Search for a group using various criteria',
    'group_set_expire': 'Set expire date for a group',
    'group_set_description': 'Set description for a group',
    'group_set_visibility': 'Set visibility for a group',
    },
    'misc': {
    'misc_affiliations': 'List all the affiliations defined in the database',
    'misc_change_request': 'Change execution time for a pending request',
    'misc_clear_passwords': 'clear password(s) from the altered-passwords list in the current sessions',
    'misc_dadd': 'Register a disk in Cerebrum database',
    'misc_dls': 'List all registered disk for a given host',
    'misc_drem': 'Remove a disk entry from Cerebrum',
    'misc_hadd': 'Register a new host in the Cerebrum database',
    'misc_hrem': 'Remove a host entry from Cerebrum',
    'misc_list_passwords': 'View/print all the password altered during a session',
    'misc_reload': 'Re-read server config file (use with care)',
    'misc_list_requests': 'View pending jobs the current BOFH user has requested/may confirm',
    'misc_user_passwd': 'Check whether an account has a given password',
    "misc_verify_password":
        "Check whether an account has a given password",
    },
    'ou': {
    'ou_search': 'Search for OUs by name or a partial stedkode',
    'ou_info': 'View information about an OU',
    'ou_tree': 'Show parents/children of an OU',
    },
    'entity': {
    'entity_accounts':
        "List information about accounts associated with given entities",
    'entity_history':
        "List the changes made to entity.",
    'entity_contactinfo_add':
        "Add contact information to entity.",
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
    },
    'person': {
    'person_accounts': 'View account a person is owner of',
    'person_affiliation_add': 'Add an affiliation to a person',
    'person_affiliation_remove': 'Remove an affiliation from a person',
    'person_create': 'Register a new person in Cerebrum',
    'person_find': 'Search for a person in Cerebrum',
    'person_info': 'View information about a person',
    'person_set_id': 'Set a new id for a person',
    'person_set_bdate':
        'Set a new birth date for a person',
    'person_set_name':
        'Change the full name of a manually registered person',
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
    'user_find': 'Search for users',
    'user_delete': 'Delete an account',
    'user_demote_posix': 'Make a POSIX user account into a generic Cerebrum account',
    'user_history': "Show history of the account with uname. Limited to users subordinate to a privilege group the BOFH user is a member of",
    'user_info': 'View general information about an account',
    'user_move': 'Move a users home directory to another disk',
    'user_set_password': 'Set a new password for an account',
    'user_promote_posix': 'Make a Cerebrum account into a POSIX user account',
    'user_reserve': 'Reserve a user name in the database',
    'user_set_expire': 'Set expire date for an account',
    'user_set_np_type': 'Set/remove np-type for an account (i.e. program, system etc)',
    'user_set_otpkey': 'Regenerate a One Time Password (OTP) key for an account',
    'user_set_owner': 'Assign ownership for an account',
    'user_shell': 'Set login-shell for a POSIX user account',
    },
    'project': {
        'project_approve':
            'Approve a project with the given name',
        'project_freeze_request':
            'Add a BofhdRequest for freezing a project',
        'project_terminate':
            'Terminate a project by removing all data',
        'project_list':
            'List all projects according to given filter',
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
    'source_system':
        ['source_system', 'Enter source system',
         'The name of the source system, i.e. system_fs/system_lt etc.'],
    'account_password':
        ['password', 'Enter password'],
    'affiliation':
        ['affiliation', 'Enter affiliaton',
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
    'date':
        ['date', 'Enter date (YYYY-MM-DD)',
         "The legal date format is 2003-12-31"],
    'date_birth':
        ['date', 'Enter date of birth(YYYY-MM-DD)',
         "The legal date format is 2003-12-31"],
    'disk':
        ['disk', 'Enter disk',
         """Enter the path to the disc without trailing slash or username.
 Example: /usit/sauron/u1
 For non-cerebrum disks, prepend the path with a :"""],
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
    'email_forward_action':
        ['action', 'Enter action',
         "Legal forward actions:\n - on\n - off\n - local"],
    'email_tripnote_action':
        ['action', 'Enter action',
         "Legal tripnote actions:\n - on\n - off"],
    'group_name':
        ['gname', 'Enter groupname'],
    'group_name_dest':
        ['gname', 'Enter the destination group'],
    'group_name_new':
        ['gname', 'Enter the new group name'],
    'group_name_src':
        ['gname', 'Enter the source group'],
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
    'id:target:account':
        ['account', 'Enter an existing entity',
         """Enter the entity as type:name, for example 'account:bob'.  If only
a name is entered, the type 'account' is assumed.  Other types include
'group', 'fnr' (fødselsnummer), 'id' (Cerebrum's internal id) and
'host'.  The type name may be abbreviated.  (Some of the types may not
make sense for this command.)
"""],
    'id:target:group':
        ['group', 'Enter an existing entity',
         """Enter the entity as type:name, for example 'group:foo'.  If only a
name is entered, the type 'group' is assumed.  Other types include
'account', 'fnr' (fødselsnummer), 'id' (Cerebrum's internal id) and
'host'.  The type name may be abbreviated.  (Some of the types may not
make sense for this command.)
"""],
    'id:target:person':
        ['person', 'Enter an existing entity',
         """Enter the entity as type:name, for example: 'account:bob'. If only
a name is entered, it will be assumed to be either an account or a fnr.
If an account is given, the person owning the account will be used.
Other types:
    - account
    - fnr (fødselsnummer)
    - id (Cerebrum's internal id)
    - external_id (e.g. student numbers and SAP ids)
    - host

The type name may be abbreviated. 

Some of the types may not make sense for this command.
"""],
    'id:entity_ext':
        ['entity_id', 'Enter entity_id, example: group:foo',
         'Enter an entity_id either as number or as group:name / account:name'],
    'id:gid:name':
        ['group', 'Enter an existing entity',
         """Enter the entity as type:name, for example 'name:foo'.  If only a
name is entered, the type 'name' is assumed.  Other types are 'gid'
(only Posix groups), and 'id' (Cerebrum's internal id).
"""],
    'id:op_target':
        ['op_target_id', 'Enter op_target_id'],
    'mailman_admins':
        ['addresses', 'Enter comma separated list of administrators for '+
         'the Mailman list'],
    'mailman_list':
        ['address', 'Enter address for Mailman list'],
    'mailman_list_exist':
        ['address', 'Enter address of existing Mailman list'],
    'member_type':
        ['member_type', 'Enter type of member',
         'account, person or group'],
    'member_name_src':
        ['member_name_src', 'Enter name of source member'],
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
    'ou_stedkode_or_id':
        ['ou', 'Enter OU stedkode/id',
        'Enter a 6-digit stedkode of an organizational unit, or id:? to ' +
        'look up by entity ID.'],
    'ou_perspective':
        ['perspective', 'Enter a perspective (usually SAP or FS)',
        'Enter a perspective used for getting the organizational structure.'],
    'ou_search_pattern':
        ['pattern', 'Enter search pattern',
        'Enter a string (% works as a wildcard) or a partial stedkode to' +
        'search for.'],
    'ou_search_language':
        ['language', 'Enter a language code (nb/en)',
        'Enter a language code (nb/en) to be used for searching and ' +
        'displaying OU names and acronyms.'],
    'person_id':
        ['person_id', 'Enter person id',
        """Enter person id as idtype:id.
If idtype=fnr, the idtype does not have to be specified.
The currently defined id-types are:
  - fnr : norwegian fødselsnummer."""],
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
  - 'name'
  - 'date' of birth, on format YYYY-MM-DD
  - 'person_id'
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
    'spam_action':
        ['spam action', 'Enter spam action',
          """Choose one of
          'dropspam'    Messages classified as spam won't be delivered at all
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
    'spread_filter':
        ['spread_filter', 'Enter spread to filter by (leave empty for no filtering)',
         """Results should only include groups having the given spread.
If no value is given, no filtering will occur.
The bofh-command 'spread list' lists possible values"""],
    'string_attribute':
        ['attr', 'Enter attribute',
         "Experts only.  See the documentation for details"],
    'string_description':
        ['description', 'Enter description'],
    'string_spread':
        ['spread', 'Enter spread. Example: AD_group NIS_fg@uio'],
    'string_email_host':
        ['hostname', 'Enter e-mail server.  Example: mail-sg2'],
    'string_mdb':
        ['mdb', 'Enter mdb. Example: MailboxDatabase01'],
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
  Norwegian fødselsnummer (11 digits)
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
        ['include_expired', 'Include expired? (y/n)'],
    'yes_no_with_request':
        ['yes_no_with_request', 'Issue bofhd request? (y/n)'],
    'yes_no_extrainfo':
        ['yes_no_extrainfo', 'Show extra information? (y/n)'],
    'limit_number_of_results':
        ['number', 'Number of results for query',
         "Gives upper limit for how many entries to include, counting " +
         "backwards from the most recent. Default (when left empty) is 100"],
    }






# arch-tag: e438828e-958d-4d94-a579-51395dddf5fa