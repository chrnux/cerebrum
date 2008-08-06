#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2004-2008 University of Oslo, Norway
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

import time, mx.DateTime as dt

import cerebrum_path
import cereconf
from Cerebrum import Errors
from Cerebrum import Utils
from Cerebrum import Constants as _c
from Cerebrum.modules.EntityTrait import _EntityTraitCode
import pickle

class Constants(_c.Constants):
    """
    Constants used by PasswordNotifier
    """
    trait_passwordnotifier_excepted = _EntityTraitCode(
        'autopass_except',
        _c.Constants.entity_account,
        "Trait marking accounts whose password's change is not enforced by PasswordNotifier.")

    trait_passwordnotifier_notifications = _EntityTraitCode(
        'pw_notifications',
        _c.Constants.entity_account,
        "Trait marking accounts whose password's change is not enforced by PasswordNotifier.")

class PasswordNotifier(object):
    """
    Sends password notifications to users with old passwords, and
    can query information about passwords notifications.
    """

    class default_config(object):
        change_log_program = 'notify_ch_passwd'
        change_log_account = None
        template = []
        max_password_age = dt.DateTimeDelta(365)
        grace_period = dt.DateTimeDelta(5*7)
        reminder_delay = []
        class_notifier = ['Cerebrum.modules.PasswordNotifier/PasswordNotifier']
        trait = Constants.trait_passwordnotifier_notifications
        except_trait = Constants.trait_passwordnotifier_excepted
        summary_from = None
        summary_to = None
        summary_cc = None
        summary_bcc = []

    def __init__(self, db=None, logger=None, dryrun=None, *rest, **kw):
        """
        Constructs a PasswordNotifier.

        @type db: Cerebrum.Database or NoneType
        @keyword db: Database object (default use Factory)

        @type logger: logging.logger
        @keyword logger: logger object (default Factory.get_logger('crontab'))

        @type dryrun: boolean
        @keyword dryrun: Refrain from side effects?
        """

        from Cerebrum.Utils import Factory
        if logger:
            self.logger = logger
        else:
            self.logger = Factory.get_logger('console')
        # fi logger

        if db:
            self.db = db
        else:
            self.db = Factory.get("Database")()
        # fi db

        self.now = self.db.Date(*(time.localtime()[:3]))
        
        if dryrun:
            self.dryrun = True
        else:
            self.dryrun = False
        # fi

        account = Utils.Factory.get("Account")(self.db)
        account.find_by_name(cereconf.INITIAL_ACCOUNTNAME)
        self.splattee_id = account.entity_id
        self.constants = Utils.Factory.get('Constants')(db)
        self.splatted_users = []

        import email, email.Header
        self.mail_info = []
        for fn in self.config.template:
            fp = open(fn, 'rb')
            msg = email.message_from_file(fp)
            fp.close()
            self.mail_info.append({
                'Subject': email.Header.decode_header(msg['Subject'])[0][0],
                'From': msg['From'],
                'Cc': msg['Cc'],
                'Reply-To': msg['Reply-To'],
                'Body': msg.get_payload(decode=1)
                })
    # end __init__
                
    def get_old_account_ids(self):
        """
        Returns a set of account_id's for candidates.
        """
        from Cerebrum.modules import PasswordHistory
        ph = PasswordHistory.PasswordHistory(self.db)
        old_ids = set((int(x['account_id']) for x in ph.find_old_password_accounts((dt.now()
            - self.config.max_password_age).strftime("%Y-%m-%d"))))
        old_ids.update(set((int(x['account_id']) for x in ph.find_no_history_accounts())))
        return old_ids
    # end get_old_account_ids

    def get_notified_ids(self):
        """
        Returns a set of account_id's which have a password trait
        """
        account = Utils.Factory.get("Account")(self.db)
        return set((x['entity_id'] for x in account.list_traits(code=self.config.trait)))
    # end get_notified_ids

    def remove_trait(self, account):
        """
        Removes pw trait, if any, and logs it.
        """
        try:
            account.delete_trait(self.config.trait)
            account.write_db()
            self.logger.info("Deleting passwd trait for %s", account.account_name)
        except Errors.NotFoundError, e:
            # raised if account does not have trait
            pass
        # end try
    # end remove_trait

    def get_num_notifications(self, account):
        """
        Returns the number of previous notifications
        """
        try:
            traits = account.get_trait(self.config.trait)
            return int(traits['numval'])
        except (Errors.NotFoundError, TypeError), e:
            return 0
    # end get_num_notifications

    def inc_num_notifications(self, account):
        """
        Increases the number for trait by one
        """
        traits = account.get_trait(self.config.trait)
        if traits is not None:
            traits = dict(((x, traits[x]) for x in ('code', 'target_id', 'date', 'numval', 'strval')))
            traits['numval'] = int(traits['numval']) + 1
            self.logger.info("Increasing trait for %s: %d", account.account_name,
                    traits['numval'])
            if traits['strval']:
                strval = pickle.loads(str(traits['strval']))
                if not isinstance(strval, dict):
                    self.logger.error("strval not a dict for %s: %r", account.account_name, strval)
                    strval = {}
            else:
                strval = {}
            strval[traits['numval']] = str(self.now)
            traits['strval'] = pickle.dumps(strval)
        else:
            self.logger.info("Adding passwd trait for %s", account.account_name)
            traits = {
                'code': self.config.trait,
                'target_id': None,
                'date': self.now,
                'numval': 1,
                'strval': pickle.dumps({1: str(self.now)})
                }
        account.populate_trait(**traits)
        account.write_db()
    # end inc_num_notifications

    def get_notification_time(self, account):
        """
        Retrieves the date field of the trait
        """
        traits = account.get_trait(self.config.trait)
        if traits is None:
            return None
        else:
            return traits['date']
    # end get_notification_time

    def get_deadline(self, account):
        """
        Calculates the time for splatting
        """
        d = self.get_notification_time(account)
        if d is None:
            d = dt.now()
        return d + self.config.grace_period
    # end get_deadline

    def remind_ok(self, account):
        """Returns true if it is time to remind"""
        n = self.get_num_notifications(account)
        if 0 < n <= len(self.config.reminder_delay):
            delay = self.config.reminder_delay[n-1]
            if self.get_notification_time(account) < dt.now() - delay:
                return True
        return False
    # end remind_ok

    def splat_user(self, account):
        """Sets a quarantine_autopassord for account"""
        self.splatted_users.append(account.account_name)
        self.logger.debug("Splatting %s" % account.account_name)
        account.add_entity_quarantine(
            self.constants.quarantine_autopassord, self.splattee_id,
            "password not changed", self.now, None)
    # end splat_user

    def process_accounts(self):
        self.logger.info("process_accounts started")
        if self.dryrun:
            self.logger.info("Running dry")

        old_ids = self.get_old_account_ids()
        all_ids = self.get_notified_ids().union(old_ids)
        self.logger.debug("Found %d users with old passwords", len(old_ids))

        # variables for statistics
        num_mailed = num_splatted = num_previously_warned = num_reminded = lifted = skipped = 0

        account = Utils.Factory.get("Account")(self.db)
        if self.config.change_log_account:
            account.find_by_name(self.config.change_log_account)
            cl_acc = account.entity_id
        else:
            cl_acc = None
        self.db.cl_init(cl_acc, self.config.change_log_program)
        for account_id in all_ids:
            account.clear()
            account.find(account_id)
            reason = self.except_user(account)
            if reason:
                skipped += 1
                self.logger.info("Skipping %s -- %s", account.account_name, reason)
                continue
            if not account_id in old_ids:
                # Has new password, but may have notify trait
                lifted += 1
                if not self.dryrun:
                    self.remove_trait(account)
                else:
                    self.logger.info("Removing trait for %s", account.account_name)
                continue

            # now, I know the password should be old,

            if self.get_num_notifications(account) == 0:
                # No previously notification/warning sent. Send first-mail
                if self.notify(account):
                    if not self.dryrun:
                        self.inc_num_notifications(account)
                    else:
                        self.logger.info("First notify %s", account.account_name)
                num_mailed += 1
            elif self.get_deadline(account) < dt.now():
                # Deadline given in notification is passed, splat.
                if not self.dryrun:
                    self.splat_user(account)
                else:
                    self.logger.info("Splat user %s", account.account_name)
                num_splatted += 1
            else:
                num_previously_warned += 1
                if self.remind_ok(account):
                    if self.notify(account):
                        if not self.dryrun:
                            self.inc_num_notifications(account)
                        else:
                            self.logger.info("Remind %d for %s", 
                                    self.get_num_notifications(account),
                                    account.account_name)
                    num_reminded += 1
        # end for
        if self.dryrun:
            print ("Users with old password: %i\nWould splat: %i\n"
                   "Would mail: %i\nPreviously warned: %i\nNum reminded: %i"%(
                len(old_ids), num_splatted, num_mailed,
                num_previously_warned, num_reminded))
            self.db.rollback()
        elif self.config.summary_to and self.config.summary_from:
            body = """Users with old passwords: %d
Excepted users: %d
Splatted users: %d
Warned users: %d
Reminded users: %d
Users warned earlier: %d
Users with new passwords: %d
""" % (len(old_ids), skipped, num_splatted, num_mailed, 
        num_reminded, num_previously_warned, lifted)
            print body
            _send_mail(self.config.summary_to, self.config.summary_from,
                    "Statistics from password notifier", body, self.logger,
                    self.config.summary_cc)
            
            self.db.commit()
        # fi self.dryrun
    # end process_accounts

    def except_user(self, account):
        """
        Returns a false value, or a reason for skipping this user.
        This could be overridden in a subclass to match different
        criteria.
        """
        trait = account.get_trait(self.config.except_trait)
        if trait:
            return "User is excepted by trait"
        return False
    # end except_user

    def notify(self, account):
        def mail_user(account, mail_type, deadline='', first_time=''):
            mail_type = min(mail_type, len(self.mail_info)-1)
            if mail_type == -1:
                self.logger.debug("No template defined")
                return False
            try:
                prim_email = account.get_primary_mailaddress()
            except Errors.NotFoundError:
                self.logger.warn("No email-address for %i" % account_id)
                return
            subject = self.mail_info[mail_type]['Subject']
            subject = subject.replace('${USERNAME}', account.account_name)
            body = self.mail_info[mail_type]['Body']
            body = body.replace('${USERNAME}', account.account_name)
            body = body.replace('${DEADLINE}', deadline)
            body = body.replace('${FIRST_TIME}', first_time)

            return _send_mail(prim_email, self.mail_info[mail_type]['From'], subject, 
                    body, self.logger, debug_enabled=self.dryrun)

        format = '%Y-%m-%d'
        deadline = self.get_deadline(account).strftime(format)
        self.logger.info("Notifying %s, number=%d, deadline=%s", account.account_name, 
            self.get_num_notifications(account) + 1, deadline)
        if self.get_num_notifications(account) == 0:
            return mail_user(account, 0, 
                deadline=deadline)
        else:
            return mail_user(account, self.get_num_notifications(account), deadline=deadline,
                    first_time=self.get_notification_time(account).strftime(format))

    @staticmethod
    def get_notifier(config=None):
        """
        Factories a notifier class object. Secondary calls to get_notifier will always return
        the same class, regardless of the argument.

        @type config: NoneType or any object for which access to the needed variables can be read
        @param config: None means import changepassconf and use it.

        @rtype: A notifier class.
        """
        try:
            # If called previously, the class has been cached in PasswordNotifier
            return PasswordNotifier._notifier
        except AttributeError:
            pass
        if config is None:
            import changepassconf as config

        # Assert all values exist in notifier's config.
        for key, value in PasswordNotifier.default_config.__dict__.items():
            if not hasattr(config, key):
                setattr(config, key, value)

        # See also Cerebrum.Utils.Factory.get()
        classes = config.class_notifier
        bases = []
        for c in classes:
            mod, name = c.split('/')
            mod = Utils.dyn_import(mod)
            cls = getattr(mod, name)
            for i in bases:
                if issubclass(cls, i):
                    raise RuntimeError, "%r is a subclass of %r" % (cls, i)
            bases.append(cls)
        if len(bases) == 1:
            PasswordNotifier._notifier = bases[0]
            PasswordNotifier.config = config
            return bases[0]
        comp_class = type('_dynamic_notifier', tuple(bases), {})
        comp_class.config = config
        PasswordNotifier._notifier = comp_class
        return comp_class

def _send_mail(mail_to, mail_from, subject, body, logger, mail_cc=None, debug_enabled=False):
    if debug_enabled:
        logger.info("Sending mail to %s", mail_to)
        return True
    try:
        ret = Utils.sendmail(mail_to, mail_from, subject, body,
                             cc=mail_cc, debug=debug_enabled)
    except smtplib.SMTPRecipientsRefused, e:
        failed_recipients = e.recipients
        logger.info("Failed to notify <%d> users", len(failed_recipients))
        for email, condition in failed_recipients.iteritems():
            logger.info("Failed to notify: %s", condition)
    except smtplib.SMTPException, msg:
        logger.warn("Error sending to %s: %s" % (mail_to, msg))
        return False
    return True

