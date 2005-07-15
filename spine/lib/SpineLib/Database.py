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

from threading import RLock
from Cerebrum.Utils import Factory
Database = Factory.get('Database')

__all__ = ['get_database']

class SpineDatabase(Database):
    """This class extends the commit() method of the Cerebrum database
    to include locking. Using this scheme, only one transaction can
    commit at a time.
    """
    
    def __init__(self, entity_id=None):
        self._lock = RLock()
        Database.__init__(self)
        if entity_id is None:
            self.cl_init(change_program='Spine')
        else:
            self.cl_init(change_by=entity_id)

        # i hope this is the correct way to do it
        self.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')

    def lock(self):
        self._lock.acquire()

    def release(self):
        self.rollback_log() # just in case
        self.rollback() # will this break the database?
        self._lock.release()

# arch-tag: 3a36a882-0fd8-4a9c-9889-9540095f93e3
