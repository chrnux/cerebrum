#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010, 2011 University of Oslo, Norway
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
"""
Interface to Cerebrum for the Individuation service.
"""

import random, hashlib
import string, pickle
from mx.DateTime import RelativeDateTime, now
import cereconf
from Cerebrum import Errors
from Cerebrum.Utils import Factory, SMSSender, sendmail
from Cerebrum.modules import PasswordChecker

class SimpleLogger(object):
    """
    Very simple logger that just writes to stdout. Main reason for a
    class is to have the same api as Cerebrum logger.
    """
    def __init__(self):
        pass

    # Logging functions use print since twisted logger logs everything
    # written to stdout
    def error(self, msg):
        print "ERROR: " + msg
        
    def warning(self, msg):
        print "WARNING: " + msg    

    def info(self, msg):
        print "INFO: " + msg    
            
    def debug(self, msg):
        print "DEBUG: " + msg    

## Globals

db = Factory.get('Database')()
db.cl_init(change_program='individuation_service')
co = Factory.get('Constants')(db)
log = SimpleLogger()

class Individuation:
    """
    The general functionality for the Individuation project that is talking
    with Cerebrum.

    Note that this main class should be independent of what server we use.

    TBD: Create a core class with methods that is relevant to both bofhd and
    CIS? For examples: _check_password, get_person, get_account.
    """

    # The subject of the warning e-mails
    email_subject = 'Failed password recovery attempt'

    # The signature of the warning e-mails
    email_signature = 'University of Oslo'

    # The from address
    email_from = 'noreply@uio.no'

    def __init__(self):
        log.debug('Cerebrum database: %s' % cereconf.CEREBRUM_DATABASE_NAME)

    def get_person_accounts(self, id_type, ext_id):
        """
        Find Person given by id_type and external id and return a list of
        dicts with username, status and priority. 

        @param id_type: type of external id
        @type  id_type: string 
        @param ext_id: external id
        @type  ext_id: string
        @return: list of dicts with username, status and priority, sorted
        by priority
        @rtype: list of dicts
        """
        # Check if person exists
        account = Factory.get('Account')(db)
        person = self.get_person(id_type, ext_id)

        # Check reservation
        if self.is_reserved_publication(person):
            log.info("Person id=%s is reserved from publication" % person.entity_id)
            # Returns same error message as for non existing persons, to avoid
            # leaking information that a person actually exists in our systems.
            raise Errors.CerebrumRPCException('person_notfound')
        accounts = dict((a['account_id'], 9999999) for a in
                         account.list_accounts_by_owner_id(owner_id=person.entity_id,
                                                      filter_expired=False))
        for row in account.get_account_types(all_persons_types=True,
                                        owner_id=person.entity_id,
                                        filter_expired=False):
            if accounts[row['account_id']] > int(row['priority']):
                accounts[row['account_id']] = int(row['priority'])
        ret = list()
        for (ac_id, pri) in accounts.iteritems():
            account.clear()
            try:
                account.find(ac_id)
            except Errors.NotFoundError:
                log.error("Couldn't find account with id %s" % ac_id)
                continue
            status = 'status_inactive'
            if not (account.is_expired() or account.is_deleted()):
                status = 'status_active'
                accepted_quars = [int(getattr(co, q)) for q in
                                  cereconf.INDIVIDUATION_ACCEPTED_QUARANTINES]
                if any(q['quarantine_type'] not in accepted_quars
                       for q in account.get_entity_quarantine(only_active=True)):
                    status = 'status_inactive'
            ret.append({'uname': account.account_name,
                        'priority': pri,
                        'status': status})
        # Sort by priority
        ret.sort(key=lambda x: x['priority'])
        return ret

    def generate_token(self, id_type, ext_id, uname, phone_no, browser_token=''):
        """
        Generate a token that functions as a short time password for the
        user and send it by SMS.
        
        @param id_type: type of external id
        @type  id_type: string 
        @param ext_id: external id
        @type  ext_id: string
        @param uname: username 
        @type  uname: string
        @param phone_no: phone number
        @type  phone_no: string
        @param browser_token: browser id
        @type  browser_token: string
        @return: True if success, False otherwise
        @rtype: bool
        """

        # Check if account exists
        account = self.get_account(uname)
        # Check if account has been checked too many times
        self.check_too_many_attempts(account)
        # Check if person exists
        person = self.get_person(id_type, ext_id)
        if not account.owner_id == person.entity_id:
            log.info("Account %s doesn't belong to person %d" % (uname,
                                                                  person.entity_id))
            raise Errors.CerebrumRPCException('person_notfound')
        # Check if account is blocked
        if not self.check_account(account):
            log.info("Account %s is blocked" % (account.account_name))
            raise Errors.CerebrumRPCException('account_blocked')
        # Check if person/account is reserved
        if self.is_reserved(account=account, person=person):
            log.info("Account %s (or person) is reserved" % (account.account_name))
            raise Errors.CerebrumRPCException('account_reserved')
        # Check if person/account is self reserved
        if self.is_self_reserved(account=account, person=person):
            log.info("Account %s (or person) is self reserved" % (account.account_name))
            raise Errors.CerebrumRPCException('account_self_reserved')
        # Check phone_no
        phone_nos = self.get_phone_numbers(person)
        if not phone_nos:
            log.info("No affiliation or phone registered for %s" % account.account_name)
            raise Errors.CerebrumRPCException('person_miss_info')
        if not self.check_phone(phone_no, numbers=phone_nos, person=person,
                                account=account):
            log.info("phone_no %s not found for %s" % (phone_no, account.account_name))
            raise Errors.CerebrumRPCException('person_notfound')
        # Create and send token
        token = self.create_token()
        log.debug("Generated token %s for %s" % (token, uname))
        if not self.send_token(phone_no, token):
            log.error("Couldn't send token to %s for %s" % (phone_no, uname))
            raise Errors.CerebrumRPCException('token_notsent')
        db.log_change(subject_entity=account.entity_id,
                      change_type_id=co.account_password_token,
                      destination_entity=None,
                      change_params={'phone_to': phone_no})
        # store password token as a trait
        account.populate_trait(co.trait_password_token, date=now(), numval=0,
                          strval=self.hash_token(token, uname))
        # store browser token as a trait
        if type(browser_token) is not str:
            log.err("Invalid browser_token, type='%s', value='%s'" % (type(browser_token), 
                                                                      browser_token))
            browser_token = ''
        account.populate_trait(co.trait_browser_token, date=now(),
                          strval=self.hash_token(browser_token, uname))
        account.write_db()
        db.commit()
        return True

    def create_token(self):
        """Return random sample of alphanumeric characters"""
        #return "phFmZquz" # TODO: remove when done testing
        alphanum = string.digits + string.ascii_letters
        return ''.join(random.sample(alphanum, cereconf.INDIVIDUATION_TOKEN_LENGTH))

    def send_token(self, phone_no, token):
        """Send token as a SMS message to phone_no"""
        return True # TODO: remove when done testing
        sms = SMSSender(logger=log)
        msg = getattr(cereconf, 'INDIVIDUATION_SMS_MESSAGE', 
                                'Your one time password: %s')
        return sms(phone_no, msg % token)

    def hash_token(self, token, uname):
        """Generates a hash of a given token, to avoid storing tokens in plaintext."""
        return hashlib.md5(uname + token).hexdigest()

    def check_token(self, uname, token, browser_token):
        """Check if token and other data from user is correct."""
        try:
            account = self.get_account(uname)
        except Errors.CerebrumRPCException:
            # shouldn't tell what went wrong
            return False

        # Check browser_token. The given browser_token may be "" but if so
        # the stored browser_token must be "" as well for the test to pass.
        
        bt = account.get_trait(co.trait_browser_token)
        if not bt or bt['strval'] != self.hash_token(browser_token, uname):
            log.info("Incorrect browser_token %s for user %s" % (browser_token, uname))
            return False

        # Check password token. Keep track of how many times a token is
        # checked to protect against brute force attack (defaults to 20).
        pt = account.get_trait(co.trait_password_token)
        no_checks = int(pt['numval'])
        if no_checks > getattr(cereconf, 'INDIVIDUATION_TOKEN_ATTEMPTS', 20):
            log.info("No. of token checks exceeded for user %s" % uname)
            raise Errors.CerebrumRPCException('toomanyattempts_check')
        # Check if we're within time limit
        time_limit = now() - RelativeDateTime(minutes=cereconf.INDIVIDUATION_TOKEN_LIFETIME)
        if pt['date'] < time_limit:
            log.debug("Password token's timelimit for user %s exceeded" % uname)
            raise Errors.CerebrumRPCException('timeout_check')

        if pt and pt['strval'] == self.hash_token(token, uname):
            # All is fine
            return True
        log.debug("Token %s incorrect for user %s" % (token, uname))
        account.populate_trait(co.trait_password_token, strval=pt['strval'],
                          date=pt['date'], numval=no_checks+1)
        account.write_db()
        db.commit()
        return False

    def delete_token(self, uname):
        """
        Delete password token for a given user
        """
        try:
            account = self.get_account(uname)
            account.delete_trait(co.trait_password_token)
            account.write_db()
            db.commit()
        except Errors.CerebrumRPCException:
            pass
        except Errors.NotFoundError, m:
            log.error("Couldn't delete password token trait for %s. %s" % (uname, m))
        return True

    def validate_password(self, password):
        return self._check_password(str(password))

    def _check_password(self, password, account=None):
        pc = PasswordChecker.PasswordChecker(db)
        try:
            pc.goodenough(account, password, uname="foobar")
        except PasswordChecker.PasswordGoodEnoughException, m:
            raise Errors.CerebrumRPCException('password_invalid', m)
        else:
            return True

    def set_password(self, uname, new_password, token, browser_token):
        if not self.check_token(uname, token, browser_token):
            return False
        account = self.get_account(uname)
        if not self._check_password(new_password, account):
            return False
        # All data is good. Set password
        account.set_password(new_password)
        try:
            account.write_db()
            db.commit()
            log.info("Password for %s altered." % uname)
        except db.DatabaseError, m:
            log.error("Error when setting password for %s: %s" % (uname, m))
            raise Errors.CerebrumRPCException('error_unknown')
        # Remove "weak password" quarantine
        for r in account.get_entity_quarantine():
            for qua in (co.quarantine_autopassord, co.quarantine_svakt_passord):
                if int(r['quarantine_type']) == qua:
                    account.delete_entity_quarantine(qua)
                    account.write_db()
                    db.commit()
        # TODO: move these checks up and raise exceptions? Wouldn't happen,
        # since generate_token() checks this already, but might get other
        # authentication methods later.
        if account.is_deleted():
            log.warning("user %s is deleted" % uname)
        elif account.is_expired():
            log.warning("user %s is expired" % uname)
        elif account.get_entity_quarantine(only_active=True):
            log.info("user %s has an active quarantine" % uname)
        return True

    def get_person(self, id_type, ext_id):
        person = Factory.get('Person')(db)
        person.clear()
        try:
            person.find_by_external_id(getattr(co, id_type), ext_id)
        except AttributeError, e:
            log.error("Wrong id_type: '%s'" % id_type)
            raise Errors.CerebrumRPCException('person_notfound')
        except Errors.NotFoundError:
            log.debug("Couldn't find person with %s='%s'" % (id_type, ext_id))
            raise Errors.CerebrumRPCException('person_notfound')
        else:
            return person

    def get_account(self, uname):
        account = Factory.get('Account')(db)
        try:
            account.find_by_name(uname)
        except Errors.NotFoundError:
            log.info("Couldn't find account %s" % uname)
            raise Errors.CerebrumRPCException('person_notfound')
        else:
            return account

    def _get_priorities(self):
        """Return a double list with the source systems in the prioritized order
        as defined in the config."""
        if not hasattr(self, '_priorities_cache'):
            priorities = {}
            for sys, values in cereconf.INDIVIDUATION_PHONE_TYPES.iteritems():
                if not values.has_key('priority'):
                    log.error('config missing priority for system %s' % sys)
                    continue
                pri = priorities.setdefault(values['priority'], {})
                pri[sys] = values
            self._priorities_cache = (priorities[x] for x in sorted(priorities))
        return self._priorities_cache

    def get_phone_numbers(self, person):
        """
        Return a list of the registered phone numbers for a given person. Only
        the defined source systems and contact types are searched for, and the
        person must have an active affiliation from a system before a number
        could be retrieved from that same system.

        Note that the priority set for the source systems matters here. Only the
        first priority level where the person has an affiliation is checked for
        numbers, the lower priority levels are ignored.
        """
        old_limit = now() - RelativeDateTime(days=cereconf.INDIVIDUATION_AFF_GRACE_PERIOD)
        pe_systems = [int(af['source_system']) for af in
                      person.list_affiliations(person_id=person.entity_id, include_deleted=True)
                      if (af['deleted_date'] is None or af['deleted_date'] > old_limit)]
        for systems in self._get_priorities():
            sys_codes = [getattr(co, s) for s in systems]
            if not any(s in sys_codes for s in pe_systems):
                # person has no affiliation at this priority go to next priority
                continue
            phones = []
            for system, values in systems.iteritems():
                types = [getattr(co, t) for t in values['types']]
                sys = getattr(co, system)
                for row in person.list_contact_info(entity_id=person.entity_id,
                                   contact_type=types,
                                   source_system=sys):
                    phones.append({'number': row['contact_value'],
                                   'system': sys,
                                   'system_name': system,
                                   'type':   co.ContactInfo(row['contact_type']),})
            return phones
        return []

    def check_phone(self, phone_no, numbers, person, account):
        """
        Check if given phone_no belongs to person. The phone number is only searched
        for in source systems that the person has active affiliations from and
        contact types as defined in INDIVIDUATION_PHONE_TYPES. Other numbers are
        ignored.
        """
        for num in numbers:
            if not self.number_match(stored=num['number'], given=phone_no):
                continue
            delay = self.get_delay(num['system_name'], num['type'])
            block = False
            # TODO: move the following loop to its own method
            for row in db.get_log_events(types=(co.entity_cinfo_add, co.person_create),
                                         any_entity=person.entity_id,
                                         sdate=delay):
                if row['change_type_id'] == co.person_create:
                    block = False
                    log.debug("Person %s is fresh" % person.entity_id)
                    break
                else:
                    data = pickle.loads(row['change_params'])
                    if num['number'] == data['value']:
                        log.info('person_id=%s recently changed phoneno' % person.entity_id)
                        block = True
            if block:
                self.mail_warning(person=person, account=account,
                        reason=("Your phone number has recently been"
                            + " changed. Due to security reasons, it"
                            + " can not be used by the password service"
                            + " for a few days."))
                raise Errors.CerebrumRPCException('fresh_phonenumber')
            return True
        return False

    def number_match(self, stored, given):
        """Checks if a given number matches a stored number. Checks, e.g.
        removing spaces, could be put here, if necessary, but note that the best
        place to fix such mismatches is in the source system."""
        if given.strip() == stored.strip():
            return True
        # TODO: more checks here?
        return False

    def get_delay(self, system, type):
        """Return a DateTime set to the correct delay time for numbers of the
        given type and from the given source system. Numbers must be older than
        this DateTime to be accepted.
        
        If no delay is set for the number, it returns now(), which will be true
        unless you change your number in the exact same time."""
        delay = 0
        try:
            types = cereconf.INDIVIDUATION_PHONE_TYPES[system]['types']
        except KeyError:
            log.error('get_delay: Unknown system defined: %s' % system)
            delay = 0
        else:
            for t in types:
                if int(getattr(co, t, 0)) == int(type):
                    delay = int(types[t].get('delay', 0))
                    break
        return now() - RelativeDateTime(days=delay)

    def mail_warning(self, person, account, reason):
        """Warn a person by sending an e-mail to all its accounts."""
        #return # TODO: remove when done testing
        msg  = "Someone has tried to recover the password for your account: %s.\n" % account.account_name
        msg += "This has failed, due to the following reason:\n\n  %s\n\n" % reason
        msg += "If this was not you, please contact your local IT-department as soon as possible."
        msg += "\n\n-- \n%s\n" % self.email_signature
        account2 = Factory.get('Account')(self.db)
        for row in person.get_accounts():
            account2.clear()
            account2.find(row['account_id'])
            try:
                log.debug("Emailing user %s (%d)" % (account2.account_name, account2.entity_id))
                sendmail(account2.get_primary_mailaddress(), self.email_from, self.email_subject, msg)
            except Errors.NotFoundError, e:
                log.error("Couldn't warn user %s. Has no primary e-mail address? %s" % (account.account_name, e))

    def check_too_many_attempts(self, account):
        """
        Checks if a user has tried to use the service too many times. Creates the
        trait if it doesn't exist, and increments the numval. Raises an exception
        when too many attempts occur in the block period.
        """
        attempts = 0
        trait = account.get_trait(co.trait_password_failed_attempts)
        block_period = now() - RelativeDateTime(seconds=cereconf.INDIVIDUATION_ATTEMPTS_BLOCK_PERIOD)
        if trait and trait['date'] > block_period:
            attempts = int(trait['numval'])
        log.debug('User %s has tried %d times' % (account.account_name,
                                                  attempts))
        if attempts > cereconf.INDIVIDUATION_ATTEMPTS:
            log.info("User %s too many attempts, temporarily blocked" %
                     account.account_name)
            raise Errors.CerebrumRPCException('toomanyattempts')
        account.populate_trait(code=co.trait_password_failed_attempts,
                target_id=account.entity_id, date=now(), numval=attempts + 1)
        account.write_db()
        db.commit()

    def check_account(self, account):
        """
        Check if the account is not blocked from changing password.
        """
        if account.is_deleted() or account.is_expired():
            return False
        # Check quarantines
        quars = [int(getattr(co, q)) for q in
                 getattr(cereconf, 'INDIVIDUATION_ACCEPTED_QUARANTINES', ())]
        for q in account.get_entity_quarantine(only_active=True):
            if q['quarantine_type'] not in quars:
                return False
        # TODO: more to check?
        return True
        
    def is_reserved(self, account, person):
        """Check that the person/account isn't reserved from using the service."""
        # Check if superuser or in any reserved group
        group = Factory.get('Group')(db)
        for gname in (getattr(cereconf, 'INDIVIDUATION_PASW_RESERVED', ()) +
                      (cereconf.BOFHD_SUPERUSER_GROUP,)):
            group.clear()
            group.find_by_name(gname) # TODO: if groups doesn't exist it should fail!
            if account.entity_id in (int(row["member_id"]) for row in
                                     group.search_members(group_id=group.entity_id,
                                                          indirect_members=True,
                                                          member_type=co.entity_account)):
                return True
            # TODO: these two loops should be merged!
            if person.entity_id in (int(row["member_id"]) for row in
                                     group.search_members(group_id=group.entity_id,
                                                          indirect_members=True,
                                                          member_type=co.entity_account)):
                return True
        return False

    def is_self_reserved(self, account, person):
        """Check if the user has reserved himself from using the service."""
        # Check if person is reserved
        for reservation in person.list_traits(code=co.trait_reservation_sms_password,
                                              target_id=person.entity_id):
            if reservation['numval'] > 0:
                return True
        # Check if account is reserved
        for reservation in account.list_traits(code=co.trait_reservation_sms_password,
                                               target_id=account.entity_id):
            if reservation['numval'] > 0:
                return True
        return False

    def is_reserved_publication(self, person):
        """Check if a person is reserved from being published on the
        instance's web pages. Most institutions doesn't have this regime."""
        return False

