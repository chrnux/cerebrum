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

from lib.Searchers import CoreSearcher
from lib.DiskSearchForm import DiskSearchForm
from lib.data.DiskDAO import DiskDAO
from gettext import gettext as _

class DiskSearcher(CoreSearcher):
    url = ''
    DAO = DiskDAO
    SearchForm = DiskSearchForm

    headers = (
        (_('Path'), 'path'),
        (_('Host'), ''),
        (_('Description'), 'description'),
    )

    columns = (
        'path',
        'host.name',
        'description',
    )

    orderby_default = 'path'

    def format_path(self, column, row):
        return self._create_link(column, row)

    def format_host_name(self, column, row):
        return self._create_link(column, row.host)
