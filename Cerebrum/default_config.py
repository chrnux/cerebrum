# -*- coding: iso-8859-1 -*-
# Copyright 2002, 2003, 2004 University of Oslo, Norway
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

"""Default Cerebrum installation settings.  Overrides go in cereconf.py."""

# Files containing the authentication data needed for database access
# are kept in this directory.
DB_AUTH_DIR = '/etc/cerebrum'

# Name of the SQL database
CEREBRUM_DATABASE_NAME = None

CEREBRUM_DATABASE_CONNECT_DATA = {'user': None,
                                  'table_owner': None}

AUTH_CRYPT_METHODS = ("auth_type_md5_crypt",)

# List of full path filenames to files containing non-allowed
# passwords.
PASSWORD_DICTIONARIES = ()


# Look for things like person name by evaluating source systems in in
# this order
SYSTEM_LOOKUP_ORDER = ("system_manual",)
#  Generate a full-name to display in this order
NAME_LOOKUP_ORDER = (("name_full",),
                     ("name_first", "name_last"))
DEFAULT_GECOS_NAME="name_full"

DEFAULT_GROUP_NAMESPACE = 'group_names'
DEFAULT_ACCOUNT_NAMESPACE = 'account_names'

DEFAULT_OU = None   # Used by bofh "account affadd" if OU is not set
POSIX_HOME_TEMPLATE_DIR = "/local/etc/newusertemplates"
POSIX_USERMOD_SCRIPTDIR = "/etc/cerebrum"

# User by run_pribileged_command.py:
CREATE_USER_SCRIPT= '/local/etc/reguser/mkhomedir'
MVUSER_SCRIPT = '/cerebrum/sbin/mvuser'
RMUSER_SCRIPT = '/cerebrum/sbin/aruser'
LEGAL_BATCH_MOVE_TIMES = '20:00-08:00'
MAILMAN_SCRIPT = None
CONVERT_MAILCONFIG_SCRIPT = None
MVMAIL_SCRIPT = None
SUBSCRIBE_SCRIPT = None
RSH_CMD = '/local/bin/ssh'

# Temporary switch until someone can figure out why mktime won't work
# with year < 1970 on some systems.  Must NOT be set on production
# systems.
ENABLE_MKTIME_WORKAROUND=0

# If m2crypto is installed, set this to 1 to use ssl
ENABLE_BOFHD_CRYPTO=0

# Makedb will create an initial Group and an Account.  These are
# needed for initial population of the database, as the database model
# requires that accounts and groups have creator_ids/owner_ids.
INITIAL_GROUPNAME = "bootstrap_group"
INITIAL_ACCOUNTNAME = "bootstrap_account"
INITIAL_ACCOUNTNAME_PASSWORD = "change_on_install"

# Specify the class this installation should use when working with
# various entities.
#

# The specification has the format [modulename/classname].  To use
# multiple constant classes, list them

CLASS_OU = ['Cerebrum.OU/OU']
CLASS_PERSON = ['Cerebrum.Person/Person']
CLASS_ACCOUNT = ['Cerebrum.Account/Account']
CLASS_GROUP = ['Cerebrum.Group/Group']
CLASS_HOST = ['Cerebrum.Disk/Host']
CLASS_DISK = ['Cerebrum.Disk/Disk']
CLASS_CONSTANTS = ['Cerebrum.Constants/Constants', 'Cerebrum.Constants/ExampleConstants']

CLASS_CL_CONSTANTS = ['Cerebrum.modules.CLConstants/CLConstants']

CLASS_DBDRIVER = ['Cerebrum.Database/PostgreSQL']
CLASS_DATABASE = ['Cerebrum.CLDatabase/CLDatabase']
# To enable logging, use this:
#CLASS_CHANGELOG = ['Cerebrum.modules.ChangeLog/ChangeLog']
CLASS_CHANGELOG = ['Cerebrum.ChangeLog/ChangeLog']

# Plain Email-backend generation.
# UiO has it's own. Enable it with
# CLASS_EMAILLDAP = ['Cerebrum.modules.no.uio.EmailLDAP/EmailLDAPUiOMixin']
CLASS_EMAILLDAP = ['Cerebrum.modules.EmailLDAP/EmailLDAP']

# Which module(s) to use as ClientAPI
# (use Cerebrum.Utils.Factory.get_module("ClientAPI")
MODULE_CLIENTAPI = ['Cerebrum.client.BofhModel']

# URL to bofh server
BOFH_URL='http://127.0.0.1:8000'

# Toggle debugging various parts of the code.
# Comparing two Entity (or subclass) instances:
DEBUG_COMPARE = False

# GroupUioMixin limits max # of groupmemberships in groups with
# these spreads
NIS_SPREADS = ()

# Spreads that are legal for entries in account_home
HOME_SPREADS = ()

# If your CLASS_ACCOUNT includes
#   Cerebrum.modules.AccountExtras/AutoPriorityAccountMixin
# you must override this value in your cereconf.py.  The purpose of
# the structure is to specify the default (affiliation, status) ->
# (pri_min, pri_max) ranges for new account_type rows.  See the mixin
# class for information on the proper structure of the value.
ACCOUNT_PRIORITY_RANGES = None

# Active directory specific settings.

AD_SERVER_HOST = 'bastard'
AD_SERVER_PORT = 1681
AD_DOMAIN = 'WinNT://WINTEST'
AD_LDAP= 'DC=wintest,DC=uio,DC=no'
AD_SOURCE_SEARCH_ORDER = ('system_ureg','system_lt','system_fs')
AD_PASSWORD = 'hallo\n'
AD_LOST_AND_FOUND = 'lost-n-found'
#A value og '0' represents cn=Users,value -1 uses OU in AD_LDAP_PATH.
AD_DEFAULT_OU = '0'
AD_CERE_ROOT_OU_ID = '682'
AD_DONT_TOUCH = ('Group Policy Creator Owners','DnsUpdateProxy','Tivoli_Admin_Privileges','Domain Guests','Domain Admins','Domain Users','Cert Publishers','Domain Controllers','Domain Computers','Administrator','Guest','tmersrvd','krbtgt','TsInternetUser')
#Necesary if groups and users have different namespaces in Cerebrum.
AD_GROUP_POSTFIX = '-gruppe'
AD_HOME_DRIVE = 'M'
AD_PASSWORD_EXPIRE = '0'
AD_CANT_CHANGE_PW = '0'

# Novell eDirectory settings.
NW_LDAPHOST = 'www.nldap.com'
NW_LDAPPORT = 389
# Every letter in NW_LDAP_ROOT is case-sensitive
NW_LDAP_ROOT= 'ou=HiST,ou=user,o=NOVELL'
NW_SOURCE_SEARCH_ORDER = ('system_fs',)
NW_CERE_ROOT_OU_ID = 6
NW_DEFAULT_OU_ID = 13
NW_ADMINUSER = 'cn=xxxxyyyyy,ou=HiST,ou=user,o=NOVELL'
NW_PASSWORD = 'pass-here'
NW_LOST_AND_FOUND = 'ou=lost-n-found'
#Necesary if groups and users have different namespaces in Cerebrum.
NW_GROUP_POSTFIX = '-gruppe'
NW_PASSWORD_EXPIRE = 'FALSE'
NW_CAN_CHANGE_PW = 'FALSE'
NW_GROUP_SPREAD = ('spread_novell_group',)


#Notes spesifikke variable.
NOTES_SERVER_HOST = 'devel01.uio.no'
NOTES_SERVER_PORT = 2000
NOTES_PASSWORD = 'test\n'
NOTES_DEFAULT_OU = 'andre'
NOTES_SOURCE_SEARCH_ORDER = ('system_ureg','system_lt','system_fs')

# You should set this variable to the location of your logging ini file
LOGGING_CONFIGFILE = None

QUARANTINE_RULES = {}
# QUARANTINE_RULES = {
#   'system': {'lock': 1, 'shell': '/local/etc/shells/nologin.system'}
# }

CEREBRUM_DDL_DIR="../share/doc/cerebrum/design"
BOFHD_SUPERUSER_GROUP=INITIAL_GROUPNAME
BOFHD_STUDADM_GROUP=BOFHD_SUPERUSER_GROUP
# Should contain mapping lang: [('template-prefix', 'tpl-type)...]
BOFHD_TEMPLATES={}
BOFHD_MOTD_FILE=None
BOFHD_NEW_USER_SPREADS = []
BOFHD_CHECK_DISK_SPREAD=None
BOFHD_CLIENTS = {'jbofh': '0.0.3'}
# Max number of seconds a client can have a socket stuck in recv/send
BOFHD_CLIENT_SOCKET_TIMEOUT=None
# Directory for templates
TEMPLATE_DIR=None

# Configure commands needed to send processed templates to printer
PRINT_LATEX_CMD=None
PRINT_DVIPS_CMD=None
PRINT_LPR_CMD=None
PRINT_PRINTER=None
PRINT_BARCODE=None

# Used for sending e-mail
SMTP_HOST='localhost'

# Logdir for AutoStud jobs
AUTOADMIN_LOG_DIR='.'     # Set to a place where only 'cerebrum' has write access
# Socket used to query the job-runner server, should not be writeable by untrusted users
JOB_RUNNER_SOCKET="/tmp/jr-socket"

JOB_RUNNER_LOG_DIR='.'   # Set to a place where only 'cerebrum' has write access
JOB_RUNNER_MAX_PARALELL_JOBS = 3

# Used by Cerebrum/no/Stedkode.py
DEFAULT_INSTITUSJONSNR=None

# INSTITUTION_DOMAIN_NAME: The DNS domain name your institution
# prefers to use for identifying itself on the internet.
#
# For FEIDE-enabled institutions, this setting specifies the domain
# name that will be used for qualifying its eduPersonPrincipalName
# attributes, as described in the "FEIDE Object Class Specification".
#
# Note that you MUST override this setting in your cereconf.py; the
# default value given here will parse as a domain name, but is
# guaranteed (by RFC 2606) to never actually appear in DNS.
#
# Example: At the University of Oslo in Norway, this setting should be
# "uio.no".
INSTITUTION_DOMAIN_NAME = "my-institution.example"

# The Email module's algorithm for determining a user's "default"
# email domain needs a default.  This should be a string, naming fully
# qualified domain name that is registered in the installation's
# 'email_domain' table.
EMAIL_DEFAULT_DOMAIN = None

# LDAP-stuff.
LDAP_BASE_DN="dc=uio,dc=no"
LDAP_MAIL_BASE = """
dn: ou=mail,%s
objectClass: top
objectClass: organizationalUnit
ou: mail
description: mail-config ved UiO.\n
""" % LDAP_BASE_DN

# Base reference for URLs on webpages
WEBROOT = "/"

# Used when pgp-encrypting passwords:
PGPPROG = '/usr/bin/gpg'
PGPID = "enter your string here"
PGP_DEC_OPTS = ['--batch', '--passphrase-fd', "0", '--decrypt', '--quiet']
# ['--recipient', id, '--default-key', id] is appended to PGP_ENC_OPTS
PGP_ENC_OPTS = ['--encrypt', '--armor', '--batch', '--quiet']


#
# LDAP stuff
#

# Generation of LDIF-file for organizational data
CLASS_ORGLDIF = ['Cerebrum.modules.OrgLDIF/OrgLDIF']

# LDAP server used for LDAP quick-sync?
#LDAP_SERVER = 'ldap.example.com'

# Default directory in which to write LDIF files
LDAP_DUMP_DIR   = '/cerebrum/dumps/LDAP/'
# Default output files in LDAP_DUMP_DIR for generate_*_ldif.py
LDAP_ORG_FILE   = 'organization.ldif'
LDAP_POSIX_FILE = 'posix.ldif'

# DNs of the LDAP trees to make.  Only trees whose DNs are set will be made.
#
# Generated by generate_org_ldif.py:
# Top level DN of LDAP tree.  Should normally have the following value:
#LDAP_BASE_DN        = ('.' + INSTITUTION_DOMAIN_NAME).replace('.', ',dc=')
# Base of tree of organizational units.  Can be == LDAP_BASE_DN.
#LDAP_ORG_DN         = 'cn=organization,' + LDAP_BASE_DN
# Base of tree with people.  If it is == LDAP_ORG_DN, people are
# placed below their primary org.units in the organization tree.
# Otherwise, they are placed in a flat structure below LDAP_PERSON_DN.
# Attributes from object class eduPerson will refer to the persons' org.units.
#LDAP_PERSON_DN      = 'cn=people,'       + LDAP_BASE_DN
#
# Generated by generate_posix_ldif.py:
# Note: LDAP_POSIX_DN should not be set if it is == LDAP_BASE_DN
# and one uses generate_org_ldif.py to make that entry.
#LDAP_POSIX_DN       = 'cn=system,'       + LDAP_BASE_DN
# Unix users, Unix filegroups and netgroups.
#LDAP_USER_DN        = 'cn=users,'        + LDAP_POSIX_DN
#LDAP_FILEGROUP_DN   = 'cn=filegroups,'   + LDAP_POSIX_DN
#LDAP_NETGROUP_DN    = 'cn=netgroups,'    + LDAP_POSIX_DN
#
# Generated by generate_mail_ldif.py:
# E-mail information, used by the mail system.
#LDAP_MAIL_DN        = 'cn=mail,'         + LDAP_BASE_DN
#
# Generated by generate_mail_dns_ldif.py:
# Host and domain names, used by the mail system.
#LDAP_MAIL_DNS_DN    = 'cn=mail-dns,'     + LDAP_BASE_DN

# Attributes for the objects named by the above DNs, in dicts of
# {'attribute type': (value, value, ...), ...}:
#LDAP_<BASE/ORG/PERSON/POSIX/...>_ATTRS = {'description': ('nice text',), ...}
#
# May be set to default attributes for all LDAP_*_DN objects except BASE.
# Each attribute is added if the object does not already have that attribute:
#LDAP_CONTAINER_ATTRS= {'objectClass': ('top', 'uioUntypedObject')}
# (uioUntypedObject is an object class which allows the 'cn' in the RDNs.)
#
# Note that LDAP_BASE_ATTRS is special:
# It must at least contain
# - 'objectClass' which allows the RDN of LDAP_BASE_DN (typically 'dcObject'),
# - 'o' (variants of the organization's name),
# - preferably 'eduOrgLegalName' (organization's legal corporate name).
# Generate_org_ldif.py adds objectClasses organization, eduOrg and norEduOrg.
# It also takes the phone, fax, postal addres and street address, if those
# are not set in LDAP_BASE_ATTRS, from the LDAP_ORG_ROOT org.unit.
# Example LDAP_BASE_ATTRS = {
#    'objectClass':       ('dcObject', 'labeledURIObject'),
#    'o':                 ('Our fine Organization', 'OfO'),
#    'eduOrgLegalName':   ('Our fine Organization A/S',),
#    'telephoneNumber':   ('+47-12345678',),
#    'labeledURI':        ('http://www.ofo.no/',)}

# Whether to give the organization tree alias entries for persons.
# Disabled by default: Aliases defeat indexing in OpenLDAP since the
# server does not index a value 'through' an alias, so a search which
# has aliasing turned on must examine all aliases that are in scope.
LDAP_ALIASES         = False

# If one org.unit in Cerebrum actually represents the organization, set
# this variable to its ou_id, or to 'base' to have Cerebrum deduce the
# root OU from the org.unit structure.  This OU is excluded from LDAP,
# instead phone numbers etc. from it are included in the LDAP_BASE_DN
# object.  Other root OUs, if any, are put below LDAP_ORG_DN as usual.
LDAP_ORG_ROOT        = None

# If set, make a fake org.unit <ou=LDAP_DUMMY_OU_NAME,LDAP_ORG_DN>.
# It becomes the parent entry of any person or alias entries that would
# otherwise end up just below LDAP_ORG_DN instead of under some org.unit.
#LDAP_DUMMY_OU_NAME  = '--'
LDAP_DUMMY_OU_ATTRS  = {'description': ('Other organizational units',)}

# Name of source system with perspective of org.unit structure.
#LDAP_OU_PERSPECTIVE = 'FOOBAR'

# Constants.py varname of source system with phone and fax for people and
# organization, plus postal and street addresses for people.
#LDAP_CONTACT_SOURCE_SYSTEM = 'system_foobar'

# Lists of Constants.py varnames for spreads to select entries to these trees.
#LDAP_USER_SPREAD      = ('spread_whatever', 'spread_something_else')
#LDAP_FILEGROUP_SPREAD = ('spread_whatever', 'spread_something_else')
#LDAP_NETGROUP_SPREAD  = ('spread_whatever', 'spread_something_else')

# Constants.py varname for spread to select persons, or None.
LDAP_PERSON_SPREAD     = None

# Constants.py varname of source system(s) of personal affiliations, or None.
LDAP_PERSON_AFFILIATION_SOURCE_SYSTEM = None

# Selectors for person-entries:
# Each selector is evaluated for a person with some (affiliation, status)es.
# A selector can be a simple-selector (below), or a dict
#   {'affiliation': {'status': simple-selector,
#                    True:     simple-selector, ...},  # True means wildcard
#    True:          {True:     simple-selector, ...},  # True means wildcard
#    # Shorthand for 'affiliation': {True: simple-selector}:
#    'affiliation': simple-selector}
# where for each (aff., status), the first existing simple-selector is used
# of selector[aff.][status], selector[aff.][True] and selector[True][True].
# For convenience, each affiliation or status can be a tuple of several values.
#
# A list selector evaluates to a list of the selected values for the
# affiliations it is applied to.  Each simple-selector is a list of values.
#
# A boolean selector evaluates to True or False.  Each simple-selector is
# a bool, a tuple ('group', 'name of group whose members will be selected'),
# or a tuple ('not', simple-selector).
#
# Example:
# LDAP_PERSON_AFFILIATION_SELECTOR = {
#     # Select all employees and affiliates:
#     ('EMPLOYEE', 'AFFILIATE'): True,
#     # Select all active students except members of group 'no-LDAP-student':
#     'STUDENT': {'active': ('not', ('group', 'no-LDAP-student'))}}
#
# Boolean selector: Persons and their affiliations to include in LDAP.
# Select the affiliations to use for generating a person's entry.
# (Even the other selectors only use these affiliations.)
# The person is excluded from LDAP if no affiliations are left.
#LDAP_PERSON_AFFILIATION_SELECTOR   = True
# Boolean selector: Persons who should be visible in LDAP.
LDAP_VISIBLE_PERSON_SELECTOR       = True
# Boolean selector: Persons to get postal address, phone, work title, etc.
#LDAP_PERSON_CONTACT_SELECTOR       = True
# List selector: eduPersonAffiliation attribute values for the person.
LDAP_EDUPERSONAFFILIATION_SELECTOR = []

# ACI (Access control information) attributes for visible persons.
# With OpenLDAP-2.1.4 or later, one can e.g. configure with --enable-aci,
# put something like this in slapd.conf:
#   access to dn.children=<cereconf.LDAP_PERSON_DN>  by self read  by aci read
# so a person without OpenLDAPaci only will be visible to that person,
# and then give this ACI to persons who should be visible:
#   LDAP_VISIBLE_PERSON_ATTRS = {
#       'OpenLDAPaci': ('1.1#entry#grant;c,r,s,x;[all],[entry]#public#',)}
LDAP_VISIBLE_PERSON_ATTRS = {}

# Mapping used to rewrite domains in e-mail addresses:
# {'domain returned from Cerebrum': 'real domain', ...}.
# This variable should be renamed.  Used in the Email module.
LDAP_REWRITE_EMAIL_DOMAIN = {}

# LDIF files to insert in the LDAP dumps from generate_<org,posix>_ldif.
LDAP_ORG_ADD_LDIF_FILE = LDAP_POSIX_ADD_LDIF_FILE = None

# generate_mail_dns_ldif.py parameters:
#
# Only consider hosts which have these hosts as lowest priority
# MX record and also are A records.
#LDAP_MAIL_DNS_MX_HOSTS = ("some-host", ...)
#
# Treat these hosts as if they have A records.
LDAP_MAIL_DNS_EXTRA_A_HOSTS = ()
#
# 'dig' command used to fetch information from DNS.
LDAP_MAIL_DNS_DIG_CMD = "/usr/bin/dig %s. @%s. axfr"
#
# Sequence of sequence of arguments to LDAP_MAIL_DNS_DIG_CMD.  The command
# is run once for each sequence of arguments.  The resulsts are combined.
#LDAP_MAIL_DNS_DIG_ARGS = ((domain, name server), (domain, name server), ...)
#
# Maximum percent change of the size of the output file since last run.
# With a larger change, an error is reported and the file if not updated.
LDAP_MAIL_DNS_MAX_CHANGE = 10

# arch-tag: 58fc16b3-e7ef-4304-b561-477ced8d6b96
