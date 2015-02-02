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

import unittest
import mx
import mx.DateTime

import cereconf
from Cerebrum.Utils import Factory

class SQLDriverTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Factory.get('Database')(
            user=cereconf.CEREBRUM_DATABASE_CONNECT_DATA['table_owner'])
        # The Python unittest framework won't call a test's tearDown()
        # method if setUp() throws exception.  We attempt a naive
        # workaround for this restriction: call tearDown() ourselves,
        # and then re-raise the exception.
        #
        # This workaround won't work particularly well if tearDown()
        # also happens to raise an exception.
        try:
            self.db.execute("""
            CREATE TABLE [:table schema=cerebrum name=test_db_dict] (
              value   NUMERIC(6,0))""")
            self.db.execute("""
            INSERT INTO [:table schema=cerebrum name=test_db_dict]
            (value) VALUES (1)""")
            self.db.execute("""
            CREATE TABLE [:table schema=cerebrum name=test_db_utf8] (
              key     NUMERIC(1,0) PRIMARY KEY,
              value   CHAR VARYING(128))""")
            self.db.execute("""
            CREATE TABLE [:table schema=cerebrum name=test_db_date] (
                tdate DATE,
                ttime TIMESTAMP)""")
            self.db.execute("""
            INSERT INTO [:table schema=cerebrum name=test_db_date]
            VALUES ([:now], [:now])""")
            self.db.execute("""
            CREATE TABLE [:table schema=cerebrum name=test_db_num] (
                int_num NUMERIC(6,0),
                float_num NUMERIC(6,2) )""")
            self.db.execute("""
            INSERT INTO [:table schema=cerebrum name=test_db_num]
            VALUES (42, 12.34)""")
        except:
            self.tearDown()
            raise
        # Calling commit() to make sure it is possible to continue
        # testing even if the SQL call fails.
        self.db.commit()

    def testDateReturnTypes(self):
        """Check that return-type of SQL-dates is using mx"""
        r = self.db.query_1("""SELECT tdate, ttime
        FROM  [:table schema=cerebrum name=test_db_date]""")
        self.failIf(not isinstance(r['tdate'], mx.DateTime.DateTimeType),
                    "tdate is type '%s'" % type(r['tdate']))
        self.failIf(not isinstance(r['ttime'], mx.DateTime.DateTimeType),
                    "ttime is type '%s'" % type(r['ttime']))

    def testSQLIntHashable(self):
        "Check if SQL NUMERIC is hashable"
        # This test fails with Debian package python2.2-pgsql version
        # 2.2-1, but works with version 2.0-3.1
        value = self.db.query_1("""SELECT max(value)
        FROM [:table schema=cerebrum name=test_db_dict]""")
        hash = {}
        try:
            hash[value] = 1 # This one fails
        except KeyError:
            self.fail("SQL integer can't be used as hash key.")
        self.assertEquals(1, hash[value],
                          'Unable to compare Integer to SQL NUMERIC')

    def testUTF8TextParam(self):
        "Check if CHAR VARYING() can store Unicode/UTF8 text"
        self.db.execute("""
        INSERT INTO [:table schema=cerebrum name=test_db_utf8] (key, value)
        VALUES (1, :text)""", {'text': u"unicodeTest������"})
        self.db.commit()

    def testUTF8TextStatement(self):
        "Check if SQL driver accept Unicode/UTF8 statements"
        self.db.execute(u"""
        INSERT INTO [:table schema=cerebrum name=test_db_utf8] (key, value)
        VALUES (2, 'foobar')""")
        self.db.commit()

    def testIsolatinTextParam(self):
        "Check that CHAR VARYING() can store Latin-1 characters"
        teststring = "������"
        self.db.execute("""
        INSERT INTO [:table schema=cerebrum name=test_db_utf8] (key, value)
        VALUES (3, :text)""", {'text': teststring})
        text = self.db.query_1("""
        SELECT value FROM [:table schema=cerebrum name=test_db_utf8]
        WHERE key=3""")
        self.failIf(text <> teststring)
        self.db.commit()

    def testBrokenDateBefore1901(self):
        "Check if the Date class handle dates before 1901 (1900-01-01)"
        date = self.db.Date(1900, 1, 1)
        date = None

    def testBrokenDateBefore1970(self):
        "Check if the Date class handle dates before 1970 (1969-01-01)"
        date = self.db.Date(1969, 1, 1)
        date = None

    def testRepeatedParam(self):
        "Check driver support for repeated bind params"
        try:
            self.db.query("""
            SELECT value
            FROM [:table schema=cerebrum name=test_db_dict]
            WHERE value = :key1 AND
                  value = :key1 AND
                  value = :key2""", {'key1': 100, 'key2': 200})
        except self.db.DatabaseError, e:
            self.fail()

    def testNumericRetval(self):
        row = self.db.query_1("""
        SELECT int_num, float_num
        FROM [:table schema=cerebrum name=test_db_num""")
        self.failIf(row['int_num'] != 42 or (not isinstance(row['int_num'], (int, long))))
        self.failIf(row['float_num'] != 12.34)

    def tearDown(self):
        self.db.commit()  # Prevents RelationForgetRelation
        self.db.execute("""
        DROP TABLE [:table schema=cerebrum name=test_db_utf8]""")
        self.db.execute("""
        DROP TABLE [:table schema=cerebrum name=test_db_dict]""")
        self.db.execute("""
        DROP TABLE [:table schema=cerebrum name=test_db_date]""")
        self.db.execute("""
        DROP TABLE [:table schema=cerebrum name=test_db_num]""")
        self.db.commit()
        self.db.close()

if __name__ == "__main__":
    unittest.main()

