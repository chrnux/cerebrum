#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

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

# $Id$

import unittest

import cerebrum_path
import Cerebrum.tests.Run
import Cerebrum.modules.no.tests.Run

def suite():
    """Returns a suite containing all the test cases in this module.
       It can be a good idea to put an identically named factory function
       like this in every test module. Such a naming convention allows
       automation of test discovery.
    """

    suite1 = Cerebrum.tests.Run.suite()
    suite2 = Cerebrum.modules.no.tests.Run.suite()
    return unittest.TestSuite((suite1, suite2))


if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main(defaultTest='suite')

# arch-tag: c150d47a-f927-42d0-a1c3-69f465b52cc7
