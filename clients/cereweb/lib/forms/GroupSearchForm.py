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
from lib.forms.FormBase import SearchForm

class GroupSearchForm(SearchForm):
    title = _("Search for Groups")
    action = '/group/search/'

    Order = [
        'name',
    ]

    Fields = {
        'name': {
            'label': _('Group name'),
            'required': True,
            'type': 'text',
        },
    }

    check_name = SearchForm._check_short_string

    help = [
        _('Use wildcards * and ? to extend the search.'),
    ]