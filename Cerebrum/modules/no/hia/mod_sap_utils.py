# -*- coding: iso-8859-1 -*-
#
# Copyright 2003 University of Oslo, Norway
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

"""This module contains a collection of utilities for dealing with
SAP-specific data.
"""

import re





def sap_row_to_tuple(sap_row):
    """Split a line into fields delimited by ';'.

    NB! ';' may be escaped. The escape character is backslash. When
    such an escaped ';' occurs, it is replaced by a regular ';' in the
    value returned to called.
    """

    result = list()

    # (?<!...) is negative lookbehind assertion. It matches, if the
    # current position is not preceded by ...
    #
    # In our case we split by ";", unless it is escaped. The absurd
    # number of backslashes is because backslashes have a special
    # meaning in python strings and in regexes. 
    for field in re.split('(?<!\\\);', sap_row.strip()):
        # Also, we have to perform the actual replacement of \; by ;
        # (clients are not interested in seeing the escaped values).
        result.append(field.replace("\\;", ";"))

    return tuple(result)
# end sap_row_to_tuple


def tuple_to_sap_row(tuple):
    tmp = list()
    for field in tuple:
        # escaping, as in the sister function.
        field = str(field).replace(";", "\\;")
        tmp.append(field)
    
    return ";".join(tmp)
# end tuple_to_sap_row


def check_field_consistency(filename, field_count):
    """Check whether all lines in a file have the same number of fields.

    We want to make sure that *all* entries in a SS� SAP data file have
    exactly the same number of fields. We do NOT want to trust a file where
    some of the entries have a non-sanctioned field count.

    @type filename: basestring
    @param filename:
      File to check for consistency

    @type field_count: int
    @param field_count:
      specifies the required number of fields per line in L{filename}.

    @rtype: bool
    @return:
      True if all lines in filename have the same number of fields; False
      otherwise.
    """

    return reduce(lambda acc, x: acc and
		                 (not x.strip() or 
				  len(sap_row_to_tuple(x)) == field_count),
		  file(filename, "r"),
		  True)
# end check_field_consistency
