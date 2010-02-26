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
#

import unittest
from mx.DateTime import DateTime
import cerebrum_path
from Cerebrum import Utils
from lib.data.ConstantsDAO import ConstantsDAO
Constants = Utils.Factory.get("Constants")
from CerebrumTestCase import CerebrumTestCase

class ConstantsDAOTest(CerebrumTestCase):
    """We test against the test-database and we use the fabricated person Test Testesen to verify that we get the expected data."""

    def setUp(self):
        super(ConstantsDAOTest, self).setUp()
        self.dao = ConstantsDAO(self.db)

    def test_get_group_visibilities(self):
        visibilities = self.dao.get_group_visibilities()
        
        self.assert_(visibilities)
        for v in visibilities:
            self.assert_(v.name)
            self.assert_(v.description)

    def test_get_group_spreads(self):
        spreads = self.dao.get_group_spreads()
        self.assert_(spreads)

    def test_get_email_target_types(self):
        types = self.dao.get_email_target_types()
        self.assert_(types)

    def test_that_we_can_get_shells(self):
        for shell in self.dao.get_shells():
            self.assert_(shell.id is not None)

    def test_that_we_can_get_account_types(self):
        types = self.dao.get_account_types()
        self.assertEqual(3,len(types))

    def test_that_we_can_get_name_types(self):
        types = self.dao.get_name_types()
        self.assertEqual(6, len(types))

    def test_that_we_can_get_affiliation_types(self):
        types = self.dao.get_affiliation_types()
        self.assertEqual(4, len(types))

    def test_that_we_can_get_affiliation_statuses(self):
        statuses = self.dao.get_affiliation_statuses()
        self.assertEqual(14, len(statuses))

    def test_that_we_can_get_ou_perspective_types(self):
        types = self.dao.get_ou_perspective_types()
        self.assertEqual(5, len(types))

    def test_that_we_can_get_ou_perspective_by_name(self):
        kjernen = self.dao.get_ou_perspective_type("Kjernen")
        self.assertEqual(150, kjernen.id)

    def test_that_we_can_get_id_types(self):
        id_types = self.dao.get_id_types()
        self.assertEqual(13, len(id_types))

if __name__ == '__main__':
    unittest.main()