# -*- coding: iso-8859-1 -*-

import time

from Cerebrum import Account
from Cerebrum import Constants
from Cerebrum import Errors
from Cerebrum import Person
from Cerebrum.Utils import Factory
from Cerebrum.modules.bofhd.cmd_param import Command, PersonId, SimpleString, FormatSuggestion, Integer
from Cerebrum.modules.bofhd.errors import CerebrumError
from Cerebrum.modules.no.uio.printer_quota import PPQUtil
from Cerebrum.modules.no.uio.printer_quota import PaidPrinterQuotas
from Cerebrum.modules.no.uio.printer_quota import bofhd_pq_utils

def format_time(field):
    fmt = "yyyy-MM-dd HH:mm"            # 16 characters wide
    return ':'.join((field, "date", fmt))

class BofhdExtension(object):
    all_commands = {}

    def __init__(self, server):
        self.server = server
        self.logger = server.logger
        self.db = server.db
        self.const = Factory.get('Constants')(self.db)
        self.tt_mapping = {}
        for c in self.const.fetch_constants(
            self.const.PaidQuotaTransactionTypeCode):
            self.tt_mapping[int(c)] = "%s" % c
        self.bu = bofhd_pq_utils.BofhdUtils(server)
        
    def get_help_strings(self):
        group_help = {
            'pquota': "Commands for administrating printer quotas",
            }

        # The texts in command_help are automatically line-wrapped, and should
        # not contain \n
        command_help = {
            'pquota': {
            'pquota_status': 'Returnerer status for skriverkvoten',
            'jbofh_pquota_history': 'Returnerer 7 dagers historikk for utskrifter',
            'pquota_off': 'Turns off quota for a person',
            'pquota_update': 'Updates a persons free quota',
            'pquota_undo': 'Undo a whole, or part of a job',
            },
            }
        
        arg_help = {
            'person_id':
            ['person_id', 'Enter person id',
             """Enter person id as idtype:id.
If idtype=fnr, the idtype does not have to be specified.
The currently defined id-types are:
  - fnr : norwegian fødselsnummer."""],
            'quota_date': ['from_date', 'Enter from date'],
            'int_new_quota': ['new_quota', 'Enter new value for free_pages.'],
            'job_id': ['job_id', 'Enter job_id of job to undo'],
            'subtr_pages': ['num_pages', 'Number of pages to undo',
                            'To undo the entire job, leave blank'],
            'undo_why': ['why', 'Why', 'Why do you want to undo this job?']
            
            }
        return (group_help, command_help,
                arg_help)

    def get_format_suggestion(self, cmd):
        return self.all_commands[cmd].get_fs()
    
    def get_commands(self, uname):
        # TODO: Do some filtering on uname to remove commands
        commands = {}
        for k in self.all_commands.keys():
            tmp = self.all_commands[k]
            if tmp is not None:
                commands[k] = tmp.get_struct(self)
        return commands

    # pquota status
    all_commands['pquota_status'] = Command(
        ("pquota", "status"), PersonId(),
        fs=FormatSuggestion("Has quota Blocked   Paid   Free\n"+
                            "%-9s %-9s %-6i %i",
                            ('has_quota', 'has_blocked_quota',
                            'paid_quota', 'free_quota')))
    def pquota_status(self, operator, person_id):
        # Everyone can access quota-status for anyone
        ppq_info = self.bu.get_pquota_status(
            self.bu.find_person(person_id))
        return {
            'has_quota': ppq_info['has_quota'],
            'has_blocked_quota': ppq_info['has_blocked_quota'],
            'paid_quota': ppq_info['paid_quota'],
            'free_quota': ppq_info['free_quota']
            }

    # We provide two methods for history data, one for jbofh, and one
    # for scripts
    def _pquota_history(self, person_id, when):
        # when is number of days in the past
        ppq_info = self.bu.get_pquota_status(person_id)
        if when:
            when = self.db.Date(*( time.localtime(time.time()-3600*24*when)[:3]))

        ret = []
        ppq = PaidPrinterQuotas.PaidPrinterQuotas(self.db)
        for row in ppq.get_history(person_id=person_id, tstamp=when):
            t = dict([(k, row[k]) for k in row._keys()])
            t['transaction_type'] = self.tt_mapping[int(t['transaction_type'])]
            if t['update_by']:
                t['update_by'] = self.bu.get_uname(int(t['update_by']))
            ret.append(t)
        
        return ret
        
    all_commands['pquota_history'] = None
    def pquota_history(self, operator, person, when=None):
        # TODO: Permission sjekking
        return self._pquota_history(
            self.bu.find_pq_person(person), when)

    all_commands['jbofh_pquota_history'] = Command(
        ("pquota", "history"), PersonId(),
        #SimpleString(help_ref='quota_date', optional=True),
        fs=FormatSuggestion("%8i %-7s %16s %-10s %-20s %5i %5i",
                            ('job_id', 'transaction_type',
                             format_time('tstamp'), 'update_by',
                             'data', 'pageunits_free',
                             'pageunits_paid'),
                            hdr="%-8s %-7s %-16s %-10s %-20s %-5s %-5s" %
                            ("JobId", "Type", "When", "By", "Data", "#Free",
                             "#Paid")))
    def jbofh_pquota_history(self, operator, person_id):
        # TODO: Permission sjekking
        #when = 14              # Max days for cmd-client
        when = None
        ret = []
        for r in self._pquota_history(self.bu.find_person(person_id), when):
            tmp = {
                'job_id': r['job_id'],
                'transaction_type': r['transaction_type'],
                'tstamp': r['tstamp'],
                'pageunits_free': r['pageunits_free'],
                'pageunits_paid': r['pageunits_paid']}
            if not r['update_by']:
                r['update_by'] = r['update_program']
            tmp['update_by'] = r['update_by'][:10]
            if r['transaction_type'] == str(self.const.pqtt_printout):
                tmp['data'] = (
                    "%s:%s" % (r['printer_queue'][:10], r['job_name']))[:20]
            elif r['transaction_type'] == str(self.const.pqtt_quota_fill_pay):
                tmp['data'] = "%s:%s kr" % (r['description'][:10], r['kroner'])
            elif r['transaction_type'] == str(self.const.pqtt_quota_fill_free):
                tmp['data'] = r['description']
            elif r['transaction_type'] == str(self.const.pqtt_undo):
                tmp['data'] = "undo %s: %s" % (r['target_job_id'], r['description'])
            elif r['transaction_type'] == str(self.const.pqtt_quota_balance):
                tmp['data'] = "balance"
            ret.append(tmp)
        return ret

    all_commands['pquota_off'] = Command(
        ("pquota", "off"), PersonId())
    def pquota_off(self, operator, person_id):
        person_id = self.bu.find_person(person_id)
        self.bu.get_pquota_status(person_id)
        ppq = PaidPrinterQuotas.PaidPrinterQuotas(self.db)
        ppq.set_has_quota(person_id, has_quota=False)
        return "OK, turned off quota for person_id=%i" % person_id

    all_commands['pquota_update'] = Command(
        ("pquota", "update"), PersonId(), Integer(help_ref='int_new_quota'),
        SimpleString(help_ref='undo_why'))
    def pquota_update(self, operator, person_id, new_value, why):
        person_id = self.bu.find_person(person_id)
        self.bu.get_pquota_status(person_id)
        pu = PPQUtil.PPQUtil(self.db)
        try:
            pu.set_free_pages(person_id, int(new_value), why,
                              update_by=operator.get_entity_id())
        except ValueError, msg:
            raise bofhd_pq_utils.BadQuotaValue(msg)
        return "OK, set free quota for %i to %s" % (person_id, new_value)

    all_commands['pquota_undo'] = Command(
        ("pquota", "undo"), PersonId(), Integer(help_ref='job_id'),
        Integer(help_ref='subtr_pages'), SimpleString(help_ref='undo_why'))
    def pquota_undo(self, operator, person_id, job_id, num_pages, why):
        person_id = self.bu.find_person(person_id)
        pu = PPQUtil.PPQUtil(self.db)
        try:
            pu.undo_transaction(person_id, job_id, int(num_pages),
                                why, update_by=operator.get_entity_id())
        except ValueError, msg:
            raise bofhd_pq_utils.BadQuotaValue(msg)
        return "OK"


if __name__ == '__main__':  # For testing
    import xmlrpclib
    svr = xmlrpclib.Server("http://127.0.0.1:8000", encoding='iso8859-1')
    secret = svr.login("bootstrap_account", "test")
    print svr.run_command(secret, 'pquota_status', '05107747682')
    print svr.run_command(secret, 'pquota_history', '05107747682')
    print svr.run_command(secret, 'pquota_status', '15035846422')
