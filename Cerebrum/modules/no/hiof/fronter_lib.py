#!/usr/bin/env python
# -*- encoding: iso-8859-1 -*-

"""This module contains various Fronter-tidbits for Hi�f's Fronter
implementation.
"""
import time



def lower(obj):
    """Do a safe string lowering on object (and its subobjects).

    The idea is to force certain string values (on their own, or parts of a
    more complex data structure) to lowercase, so that we won't have to deal
    with case sensitive keys/identifiers.

    @type obj: a str, unicode, tuple, list, set, dict
    @param obj:

      The object to lowercase. str are lowercased directly, unicode objects
      are encoded to latin-1 first, then lowercased. tuple/list/set/dict are
      processed recursively with lower() called on each member. All other
      types are returned as they are.

    @rtype: type of L{obj}
    @return:
      Lowercased version of obj, if possible, or obj itself.
    """

    if isinstance(obj, (tuple, list, set)):
        return type(obj)([lower(x) for x in obj])
    elif isinstance(obj, dict):
        return dict((lower(key), lower(obj[key])) for key in obj)
    elif isinstance(obj, str):
        return obj.lower()
    elif isinstance(obj, unicode):
        return obj.encode("iso-8859-1").lower()
    else:
        return obj
# end lower



def count_back_semesters(attributes):
    """Given a bunch of attributes for an FS entity with terminnr, figure
    out the year and starting semester for that FS entity (i.e. the one
    with terminnr=1).
    
    This method assumes that there are spring and fall semesters only (it
    is not true for all FS entities), but it's the best guess we can make!
    
    BEWARE - L{attributes} is modified destructively!

    @type attributes: dict of str->str
    @param attributes:
      Dictionary with a bunch of attributes built from FS data.

    @rtype: type(attributes)
    @return:
      The initial dict, with some of the keys modified -- 'arstall',
      'terminnr' and 'terminkode'.
    """

    terminnr = int(attributes["terminnr"])
    terminkode = attributes["terminkode"]
    year = int(attributes["arstall"])
    # counting backwards
    while terminnr > 1:
        terminnr -= 1
        if terminkode == "h�st":
            terminkode = "v�r"
        else:
            year -= 1
            terminkode = "h�st"

    attributes["terminnr"] = '1'
    attributes["terminkode"] = terminkode
    attributes["arstall"] = str(year)

    return attributes
# end count_back_semesters



def timeslot_is_valid(attributes):
    """Decide whether the semester captured by attributes is valid.

    We generate fronter structures for this and next semester. Anything
    outside of this time frame (be it past or future) is considered defunct
    data and should be ignored.
    """

    #
    # If the timeframe is not specified, assume it's a valid attr set
    if ("arstall" not in attributes or
        "terminkode" not in attributes):
        return True

    # Only some attribute sets are trapped -- we care essentially about
    # undenh/undakt only. Precisely they (either role or student) have
    # 'emnekode' attribute
    if "emnekode" not in attributes:
        return True

    year, month = time.localtime()[:2]

    if 1 <= month <= 7:
        semester = "v�r"
    else:
        semester = "h�st"

    this_semester = (year, semester)

    if semester == "h�st":
        next_semester = (year+1, "v�r")
    elif semester == "v�r":
        next_semester = (year, "h�st")
    else:
        assert False, "This cannot happen"

    semester_to_check = (int(attributes["arstall"]), attributes["terminkode"])
    
    return (semester_to_check == this_semester  or
            semester_to_check == next_semester)
# end timeslot_is_valid
