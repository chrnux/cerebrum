#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Author: Petter Reinholdtsen <pere@hungry.com>
# Date:   2002-11-06
#
# Test the f�dselsnummer class

# Copyright 2002, 2003 University of Oslo, Norway
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

import unittest

from Cerebrum.modules.no import fodselsnr

class fodselsnrTestCase(unittest.TestCase):
    def setUp(self):
        self.invalidnumbers = [
            "01013338728",
            "19055433813",
            ]

        # All valid fnrs are randomly generated. We don't link numbers to real
        # people, and we don't know if the fnrs are in use. The numbers are
        # valid, so they _could_ be in use.
        self.validnumbers = [
            # (number, sex, birth date)
            ("01013608578", 0, (1936, 01, 01)),
            ("71057141373", 0, (1971, 05, 31)),
            ("20067642148", 0, (1976, 06, 20)),
            ("30535848935", 0, (1958, 03, 30)),
            ("01015449841", 1, (1954, 01, 01)),
            ("20035324063", 1, (1953, 03, 20)),
            ("19055431011", 1, (1954, 05, 19))
            ]

        self.invalidinfo = [
            ("01013602979", 1, (1867, 01, 01)),
            ("19055430651", 0, (1954, 05, 12))
            ]

    def testIsNumberOK(self):
        "Check if able to separate valid f�delsnummers from invalid"
        for number in self.validnumbers:
            assert( fodselsnr.personnr_ok(number[0]) )
        for number in self.invalidnumbers:
            try:
                nr = fodselsnr.personnr_ok(number)
                raise AssertionError("Invalid f�delsnr accepted")
            except:
                pass

    def testDate(self):
        "Check if the Date is correctly extracted from f�delsnummers"
        for number in self.validnumbers:
            year, month, day = fodselsnr.fodt_dato(number[0])
            assert( (year, month, day) == number[2] )

        for number in self.invalidinfo:
            year, month, day = fodselsnr.fodt_dato(number[0])
            assert( (year, month, day) != number[2] )

    def testSex(self):
        "Check if the sex is correctly extracted from f�delsnummers"
        for number in self.validnumbers:
            assert( fodselsnr.er_kvinne(number[0]) == number[1] )

        for number in self.invalidinfo:
            assert( fodselsnr.er_kvinne(number[0]) != number[1] )

    def suite():
        suite = unittest.TestSuite()
        suite.addTest(fodselsnrTestCase("testIsNumberOK"))
        suite.addTest(fodselsnrTestCase("testDate"))
        suite.addTest(fodselsnrTestCase("testSex"))
        return suite
    suite=staticmethod(suite)

def suite():
    return fodselsnrTestCase.suite()

if __name__ == "__main__":
    unittest.main()

