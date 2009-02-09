#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2003, 2007 University of Oslo, Norway
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

import cerebrum_path
import cereconf

import re
from Cerebrum.modules import PasswordChecker as DefaultPasswordChecker
from Cerebrum.modules.PasswordChecker import PasswordGoodEnoughException


# The error messages are in Norwegian, since they end-users are likely to
# prefer it.
msgs = DefaultPasswordChecker.msgs
msgs.update({
    'invalid_char':
    """Vennligst ikke bruk andre tegn enn bokstaver og blank.""",
    'atleast14':
    """Passord m� ha minst 14 tegn.""",
    'atleast8':
    """Passord m� ha minst 8 tegn.""",
    'sequence_keys':
    """Ikke bruk de samme tegn om igjen etter hverandre.""",
    'was_like_old':
    """Det nye passordet var for likt det gamle. Velg et nytt ett.""",
    'repetitive_sequence':
    """Ikke bruk gjentagende grupper av tegn (eksempel: ikke 'abcabcabc').""",
    'sequence_alphabet':
    """Ikke bruk tegn i alfabetisk rekkef�lge (eksempel: ikke 'abcdef').""",
    'uname_in_password':
    """Ikke la brukernavnet v�re en del av passordet.""",
    'bad_password':
    """Passordkombinasjonen er ikke bra nok, vennligst pr�v igjen.""",
})


class OfkPasswordChecker(DefaultPasswordChecker.PasswordChecker):

    def goodenough(self, account, fullpasswd, uname=None):
        """Perform a number of checks on a password to see if it is good
        enough.

        �fk has the following rules:

        - Passwords must have minimum 8 character
        - 2 of the characters are digits
        - 6 of the characters are letters (upper/lower case mix)
        """

        num_digits = 0
        num_chars_lower = 0
        num_chars_upper = 0
        
        for char in fullpasswd:
            if not (char.isalpha() or char.isdigit()):
                raise PasswordGoodEnoughException(msgs['invalid_char'])

        # Check that the password is long enough.
        if len(fullpasswd) < 8:
            raise PasswordGoodEnoughException(msgs['atleast8'])

        # Repeating pattern: ababab, abcabcabc, abcdabcd
        if (re.search(r'^(..)\1\1', fullpasswd) or
            re.search(r'^(...)\1', fullpasswd) or
            re.search(r'^(....)\1', fullpasswd)):
            raise PasswordGoodEnoughException(msgs['repetitive_sequence'])

        # Reversed patterns: abccba abcddcba
        if (re.search(r'^(.)(.)(.)\3\2\1', fullpasswd) or
            re.search(r'^(.)(.)(.)(.)\4\3\2\1', fullpasswd)):
            raise PasswordGoodEnoughException(msgs['repetitive_sequence'])

        # Do not allow unames/reverse unames to be in passwords
        if uname is None and account is not None:
            uname = account.account_name
        if ((uname is not None) and
            (uname in fullpasswd or uname[::-1] in fullpasswd)):
            raise PasswordGoodEnoughException(msgs['uname_in_password'])
        
        # Check that the characters in the password are not a predefined sequence
        self._check_sequence(fullpasswd)

        # Check matches to previous passwords
        if account is not None:
            self.check_password_history(account, fullpasswd)
            
        # Check organisation-specific rules
        for c in fullpasswd:
            if c.isdigit():
                num_digits = num_digits + 1
            elif c.islower():
                num_chars_lower = num_chars_lower + 1
            else:
                num_chars_upper = num_chars_upper + 1

        if not (num_digits >= 2 and num_chars_lower > 0 and num_chars_upper > 0):
            raise PasswordGoodEnoughException(msgs['uname_in_password'])

        # Password good enough
        return True


class GiskePasswordChecker(DefaultPasswordChecker.PasswordChecker):

    def goodenough(self, account, fullpasswd, uname=None):
        """Perform a number of checks on a password to see if it is good
        enough.

        Giske has the following rules:

        - Characters in the passphrase are either letters or whitespace.
        - The automatically generated password has a minimum of 14
          characters and 2 words; and a maximum of 20 characters.
        - The automatically generated passwords are generated out of a
          'child-friendly' dictionary (both nynorsk and bokm�l). 
        - The user supplied passwords have a minimum of 14
          characters. There is no maximum (well, there is in the db
          schema, but this is irrelevant in the passwordchecker).
        """

        # IVR 2007-03-28: It is uncertain whether this check is meaningful. It
        # has been disabled for now.
        # # Check that the characters are legal.
        # for char in fullpasswd:
        #     if not (char.isalpha() or char in '������ '):
        #         raise PasswordGoodEnoughException(msgs['invalid_char'])

        # Check that the password is long enough.
        if len(fullpasswd) < 14:
            raise PasswordGoodEnoughException(msgs['atleast14'])

        # at least 3 words, each word at least 2 characters
        if len([x for x in fullpasswd.split(" ") if len(x) >= 2]) < 3:
            raise PasswordGoodEnoughException("For f� ord i passordet")

        # IVR 2009-01-23: At Giske the passphrases are autogenerated from a
        # dictionary. It makes no sense for us to try to match some parts of
        # such phrases against some criteria designed for passwords.
        return True
    # end goodenough
# end GiskePasswordChecker





if __name__ == "__main__":
    from Cerebrum.Account import Account
    from Cerebrum.Utils import Factory
    db = Factory.get("Database")()
    pc = OfkPasswordChecker(db)
    account = Factory.get("Account")(db)

    for candidate in ("���lllkkk34", # invalid chars (disabled 2007-03-28)
                      "hYt87",              # too short
                      "ooooooooo",    # all alike
                      "abcabcabcabcabc",     # repeating pattern
                      "abccba9fo",      # repeating pattern
                      "jashod78",      # username (fake)
                      "abcdefghijklmnopqr",  # sequence
                      "asdfghjklzxcvbnm",    # allowed 
                      "qwertyuiopasdfghj",   # allowed
                      "qwerty asdfghj zxcv", # keyboard sequence
                      "aaaaaaaaaacccccccc",  # repeating chars
                      "43HIaHeD"): # valid
        try:
            pc.goodenough(None, candidate, "this is a user")
            print "candidate: <%s>: ok!" % (candidate,)
        except PasswordGoodEnoughException, val:
            print "candidate: <%s>: failed: %s" % (candidate, val)
# fi
