# -*- coding: iso-8859-1 -*-

# Copyright 2004, 2005 University of Oslo, Norway
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

from gettext import gettext as _
import cgi
import cherrypy
from lib.utils import legal_date, html_quote, spine_to_web, object_link
from lib.utils import randpasswd, get_lastname_firstname, entity_link

from lib.data.AccountDAO import AccountDAO
from lib.data.ConstantsDAO import ConstantsDAO
from lib.data.EntityDAO import EntityDAO

"""
Helper-module for search-pages and search-result-pages in cereweb.
"""

class Form(object):
    def __init__(self, transaction, **values):
        self.ajax = cherrypy.request.headerMap.get('X-Requested-With', "") == "XMLHttpRequest"
        self.values = values
        self.transaction = transaction

        self.init_form()

        ## print '**************** Form:: init:  init called......'

        for key, field in self.fields.items():
            value = self.values.get(key) or field.get('value')
            name = field.get('name', '')
            if not name:
               field['name'] = key
            field['value'] = value

    def init_form(self):
        self.order = []
        self.fields = {}

    def get_fields(self):
        ## print '================== Form:: get_fields:   called...'
        res = []
        for key in self.order:
            field = self.fields[key]
            if field['type'] == 'select':
                func = getattr(self, 'get_%s_options' % key)
                field['options'] = func()
            res.append(field)
        return res

    def get_values(self):
        values = {} 
        for key, field in self.fields.items():
            values[key] = field['value']
        return values

    def quote_all(self):
        for field in self.fields.values():
            if field['value']:
                if 'reject' == field.get('quote'):
                    if field['value'] != cgi.escape(field['value']):
                        self.error_message = _("Field '%s' is unsafe.") % field ['label']
                        return False
        for key, field in self.fields.items():
            if field['value']:
                if 'escape' == field.get('quote'):
                    self.fields[key]['value'] = cgi.escape(field['value'])
        return True

    def has_required(self):
        res = True
        for field in self.fields.values():
            if field['required'] and not field['value']:
                res = False
                self.error_message = _("Required field '%s' is empty.") % field['label']
                break
        return res

    def is_correct(self):
        correct = self.has_required()
        if correct:
            correct = self.quote_all()

        if correct:
            for field in self.fields.values():
                if field['value']:
                    func = getattr(self, 'check_%s' % field['name'], None)
                    if func and not func(field['value']):
                        correct = False
                        message = "Field '%s' " % field['label']
                        self.error_message = message + self.error_message
                        break
        return correct

    def get_error_message(self):
        message = getattr(self, 'error_message', False)
        return message and (message, True) or ''

    def _check_short_string(self, name):
        is_correct = True
        if len(name) > 256:
            is_correct = False
            self.error_message = 'too long (max. 256 characters).'
        return is_correct

    def check_expire_date(self, date):
        is_correct = True
        if not legal_date(date):
            self.error_message = 'not a legal date.'
            is_correct = False
        return is_correct

    def get_action(self):
        return getattr(self, 'action', '/index')

    def get_title(self):
        return getattr(self, 'title', 'No Title')

    def get_help(self):
        return getattr(self, 'help', [])
            
class PersonCreateForm(Form):
    def init_form(self):
        self.order = [
            'ou',
            'affiliation',
            'firstname',
            'lastname',
            'externalid',
            'gender',
            'birthdate',
            'description',
        ]
        self.fields = {
            'ou': {
                'label': _('OU'),
                'required': True,
                'type': 'select',
                'quote': 'reject',
            },
            'affiliation': {
                'label': _('Affiliation Type'),
                'required': True,
                'type': 'select',
                'quote': 'reject',
            },
            'firstname': {
                'label': _('First name'),
                'required': True,
                'type': 'text',
                'quote': 'reject',
            },
            'lastname': {
                'label': _('Last name'),
                'required': True,
                'type': 'text',
                'quote': 'reject',
            },
            'gender': {
                'label': _('Gender'),
                'required': True,
                'type': 'select',
            },
            'birthdate': {
                'label': _('Birth date'),
                'required': True,
                'type': 'text',
                'help': _('Date must be in YYYY-MM-DD format.'),
            },
            'externalid': {
                'label': '<abbr title="%s">%s</abbr>' % (_('National Identity Number'), _('NIN')),
                'required': False,
                'type': 'text',
                'help': _('Norwegian "F�dselsnummer", 11 digits'),
            },
            'description': {
                'label': _('Description'),
                'required': False,
                'type': 'text',
                'quote': 'escape',
            }
        }

    def get_affiliation_options(self):
        options = [('%s:%s' % (t.get_affiliation().get_id(), t.get_id()), '%s: %s' % (t.get_affiliation().get_name(), t.get_name())) for t in
            self.transaction.get_person_affiliation_status_searcher().search()]
        options.sort()
        return options

    def get_ou_options(self):
        searcher = self.transaction.get_ou_searcher()
        return [(t.get_id(), t.get_name()) for t in searcher.search()]

    def get_gender_options(self):
        return [(g.get_name(), g.get_description()) for g in 
                   self.transaction.get_gender_type_searcher().search()]

    def check_firstname(self, name):
        return self._check_short_string(name)

    def check_lastname(self, name):
        return self._check_short_string(name)


    def check_birthdate(self, date):
        is_correct = True
        if not legal_date(date):
            self.error_message = 'not a legal date.'
            is_correct = False
        return is_correct

    def check_externalid(self, ssn):
        is_correct = True
        if len(ssn) <> 11 or not ssn.isdigit():
            self.error_message = 'SSN should be an 11 digit Norwegian Social Security Number'
            is_correct = False
        return is_correct

class PersonEditForm(PersonCreateForm):
    def init_form(self):
        self.order = [
            'id', 'gender', 'birthdate', 'description', 'deceased'
        ]
        self.fields = {
            'id': {
                'label': 'id',
                'required': True,
                'type': 'hidden',
            },
            'gender': {
                'label': _('Gender'),
                'required': True,
                'type': 'select',
            },
            'birthdate': {
                'label': _('Birth date'),
                'required': True,
                'type': 'text',
                'help': 'YYYY-MM-DD',
            },
            'description': {
                'label': _('Description'),
                'required': False,
                'type': 'text',
                'quote': 'escape',
            },
            'deceased': {
                'label': _('Deceased date'),
                'required': False,
                'type': 'text',
                'help': 'YYYY-MM-DD',
            },
        }

    def check_deceased(self, date):
        is_correct = True
        if not legal_date(date):
            self.error_message = 'not a legal date.'
            is_correct = False
        return is_correct

    def get_title(self):
        return 'Edit ' + getattr(self, 'title', 'person')

class AccountCreateForm(Form):
    def init_form(self):
        self.action = '/account/create'

        self.order = [
            'owner_id', 'name', '_other', 'group', 'expire_date', 'password0', 'password1', 'randpasswd',
        ]
        self.fields = {
            'owner_id': {
                'required': True,
                'type': 'hidden',
                'label': _('Owner id'),
            },
            'name': {
                'label': _('Select username'),
                'required': True,
                'type': 'select',
            },
            '_other': {
                'label': _('Enter username'),
                'required': False,
                'type': 'text',
                'quote': 'reject',
            },
            'expire_date': {
                'label': _('Expire date'),
                'required': False,
                'type': 'text',
                'help': _('Date must be in YYYY-MM-DD format.'),
            },
            'group': {
                'label': _('Primary group'),
                'required': False,
                'cls': 'ac_group',
                'type': 'text',
                'quote': 'reject',
            },
            'password0': {
                'label': _('Enter password'),
                'required': False,
                'type': 'password',
            },
            'password1': {
                'label': _('Re-type password'),
                'required': False,
                'type': 'password',
            },
            'randpasswd': {
                'label': _('Random password'),
                'required': False,
                'type': 'radio',
                'name': 'randpwd',
                'value': [randpasswd() for i in range(10)],
            },
        }

        self.owner = self.values.get("owner_entity")
        self.type = self.owner.type_name
        self.name = self.owner.name

        if self.type != 'person':
            self.fields['np_type'] = {
                'label': _('Account type'),
                'required': True,
                'type': 'select',
            }
            self.fields['join'] = {
                'label': _('Join %s') % self.name,
                'type': 'checkbox',
                'required': False,
            }
            self.order.append('np_type')
            self.order.append('join')

    def get_name_options(self):
        usernames = AccountDAO().suggest_usernames(self.owner)
        return [(username, username) for username in usernames]

    def get_np_type_options(self):
        account_types = ConstantsDAO().get_account_types()
        return [(t.id, t.description) for t in account_types]

    def get_title(self):
        return "%s %s" % (_('Owner is'), entity_link(self.owner))

    def is_correct(self):
        correct = self.has_required()
        if correct:
            correct = self.quote_all()

        if correct:
            for field in self.fields.values():
                if field['value'] and field['name'] != 'password0' and field['name'] != 'password1':
                    func = getattr(self, 'check_%s' % field['name'], None)
                    if func and not func(field['value']):
                        correct = False
                        message = "Field '%s' " % field['label']
                        self.error_message = message + self.error_message
                        break
        if correct:
            pwd0 = self.fields['password0'].get('value', '')
            pwd1 = self.fields['password1'].get('value', '')
            
            msg = 'The two passwords differ.'
            if (pwd0 and pwd1) and (pwd0 != pwd1):
                self.error_message = msg
                correct = False
            if correct:
                if (pwd0 and pwd1) and (pwd0 == pwd1) and (len(pwd0) < 8):
                    self.error_message = 'The password must be 8 chars long.'
                    correct = False
            if correct:
                if (pwd0 and not pwd1) or (not pwd0 and pwd1):
                    self.error_message = msg
                    correct = False
        return correct

class AccountEditForm(AccountCreateForm):
    def init_form(self):
        self.action = '/account/edit'
        self.error_message = ''
        self.order = [
            'id', 'expire_date', 
        ]
        self.fields = {
            'id': {
                'label': 'id',
                'required': True,
                'type': 'hidden',
            },
            'expire_date': {
                'label': _('Expire date'),
                'required': False,
                'type': 'text',
                'help': _('Date must be in YYYY-MM-DD format.'),
            },
        }

        self.account = account = self.transaction.get_account(int(self.values.get('id')))
        self.title = object_link(self.account, text=spine_to_web(self.account.get_name()))
        if account.is_posix():
            self.order.extend(['group', 'gecos', 'shell'])
            self.fields['group'] = {
                'label': _('Primary group'),
                'type': 'select',
                'required': True,
            }
            self.fields['shell'] = {
                'label': _('Shell'),
                'type': 'select',
                'required': True,
            }
            self.fields['gecos'] = {
                'label': _('Gecos'),
                'type': 'text',
                'required': False,
            }
            self.values['uid'] = html_quote(account.get_posix_uid())
            self.values['group'] = html_quote(account.get_primary_group().get_id())
            self.values['gecos'] = spine_to_web(account.get_gecos())
            self.values['shell'] = spine_to_web(account.get_shell().get_name())
        print 'init_form finished'

    def get_group_options(self):
        # groups which the user can have as primary group
        return [(i.get_id(), i.get_name())
                    for i in self.account.get_groups() if i.is_posix()]

    def get_shell_options(self):
        # shells which the user can change on the account
        shell_searcher = self.transaction.get_posix_shell_searcher()
        return [(i.get_name(), i.get_name())
                        for i in shell_searcher.search()]
    def get_action(self):
        print 'get_action'
        return self.action

    def has_required(self):
        correct = True
        if self.account.is_posix():
            if not self.values['uid']:
                self.error_message = 'uid is missing'
                correct = False
            if correct and not self.values['group']:
                self.error_message = 'grouo is missing'
                correct = False
            if correct and not self.values['gecos']:
                self.error_message = 'gecos is missing'
                correct = False
            if correct and not self.values['shell']:
                self.error_message = 'shell is missing'
                correct = False
        if correct and not self.values['id']:
            self.error_message = 'id is missing'
            correct = False
        print 'has_required = ', correct
        return correct

    def is_correct(self):
        correct = True
        if self.error_message:
            correct = False
        print 'is_correct = ', correct
        return correct

    def get_title(self):
        print 'get_title'
        return self.title

    def get_error_message(self):
        print 'get_errot_message'
        return self.error_message
        
class RoleCreateForm(Form):
    def init_form(self):
        self.order = [
            'group', 'op_set', 'target_type', 'target',
        ]
        self.fields = {
            'group': {
                'label': _('Select group'),
                'required': True,
                'type': 'select',
            },
            'op_set': {
                'label': _('Select op_set'),
                'required': True,
                'type': 'select',
            },
            'target_type': {
                'label': _('Select target type'),
                'required': True,
                'value': 'entity',
                'type': 'select',
            },
            'target': {
                'label': _('Select target'),
                'required': True,
                'type': 'select',
            },
        }

    def get_group_options(self):
        searcher = self.transaction.get_group_searcher()
        searcher.set_name_like('cereweb_*')
        return [(t.get_id(), t.get_name()) for t in searcher.search()]

    def get_op_set_options(self):
        searcher = self.transaction.get_auth_operation_set_searcher()
        return [(t.get_id(), t.get_name()) for t in searcher.search() if not t.get_name().endswith('client')]

    def get_target_options(self):
        searcher = self.transaction.get_ou_searcher()
        return [(t.get_id(), t.get_name()) for t in searcher.search()]

    def get_target_type_options(self):
        return [
            ('global', 'global'),
            ('entity', 'entity'),
            ('self', 'self'),
        ]
