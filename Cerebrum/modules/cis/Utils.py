#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010 University of Oslo, Norway
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
"""Utility methods for CIS webservices.

"""

import cerebrum_path
from Cerebrum.Utils import Factory
from Cerebrum.Errors import CerebrumError

class SimpleLogger(object):
    """Simple logger that has the same API as the Cerebrum logger, but uses
    twisted's logger.
    """
    def __init__(self):
        pass

    def _log(self, *args):
        """The logger."""
        # TODO: note that this has to be changed if we won't use twisted in
        # the future
        twisted.python.log.msg(' '.join(args))

    def error(self, msg):
        self._log('ERROR:', msg)

    def warning(self, msg):
        self._log('WARNING:', msg)

    def info(self, msg):
        self._log('INFO:', msg)

    def debug(self, msg):
        self._log('DEBUG:', msg)


db = Factory.get('Database')()
co = Factory.get('Constants')(db)
pe = Factory.get('Person')(db)
ac = Factory.get('Account')(db)


def get_person_data(id_type, ext_id):    
    try:
        id_type = getattr(co, id_type)
    except AttributeError:
        raise CerebrumError("No such id type: " + id_type)
    # find person
    pe.clear()
    pe.find_by_external_id(id_type, ext_id)
    account_id = pe.get_primary_account()
    if account_id is None:
        return None, None
    ac.clear()
    ac.find(account_id)
    return ac.get_account_name(), ac.get_primary_mailaddress()
