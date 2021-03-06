#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2003, 2005, 2016 University of Oslo, Norway
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

"""This is a python port of the PRISS pq daemon.

This daemon is the backend for the PRISS Quota system. It listens
to port 'prissquota' (8106) on the ureg2000 machine and resolves
incoming requests. The requests are resolved against the UREG2000
Oracle database running on this host."""

# TODO:  If the database is down, return ok for all commands

import SocketServer
import socket
import signal
import os
from time import strftime, time, localtime
import getopt
import sys
import traceback
import cStringIO

import cereconf

from Cerebrum import Errors
from Cerebrum.modules.no.uio.printer_quota import PaidPrinterQuotas
from Cerebrum.modules.no.uio import printer_quota
from Cerebrum.Utils import Factory

rev = '$Revision$'
rev = rev[rev.find(" ")+1:]
rev = rev[:rev.find(" ")]
# 2NN answers, meaning last command was a success.
helo = "220 PRISS Quota Daemon V%s ready" % rev
firstok = "250 Nice to meet you,"
ok = "250 OK"
no = "251 NO"
no_insuficcient = "252 NO, Insufficient quota"
no_blocked = "253 NO, Quota blocked"
bye = "280 Bye"
#
# 5NN answers, meaning last command caused problems
edbdown = "511 Database down"
ebadpage = "512 Invalid pagecount"
enouser = "513 No such user"
ecmd = "514 Unknown command"
eerror = "515 Unknown error"
unknownkey = "516 Unknown key"
eperm = "517 Permission denied"

pqdlog = "/cerebrum/var/log/cerebrum/prissquotad"
my_pid = os.getpid()

# To perform accounting for jobs by unknown accounts
log_unknown_accounts = True
last_refresh = 0

ok_has_quota = {}


def _assert_has_quota(person_id, db, ppq):
    # Assert that person has a paid_quota_status entry so that we can
    # track total_pages
    if person_id in ok_has_quota:
        return
    ok_has_quota[person_id] = True
    if person_id is not None:
        try:
            ppq.find(person_id)
        except Errors.NotFoundError:
            ppq.new_quota(person_id)
            db.commit()


def refresh_has_quota_hash(db):
    global last_refresh
    last_refresh = time()
    ppq = PaidPrinterQuotas.PaidPrinterQuotas(db)
    for row in ppq.list():
        ok_has_quota[long(row['person_id'])] = True


class MyServer(SocketServer.ForkingTCPServer):
    # We use a forking server to attemt to work-around client-timeouts
    # during periods with up to 10k connections/hour.  This means that
    # we must initialize our db-connectors in the child.
    # Unfortunately, this means that children can no longer update a
    # cash of known quota victims.  This hash must now be regularly
    # re-created in the parent.

    # Following line seems to make sense in testing environment
    SocketServer.TCPServer.allow_reuse_address = 1

    def close_request(self, request):
        SocketServer.ForkingTCPServer.close_request(self, request)
        if last_refresh < time() - 3600:
            refresh_has_quota_hash(Factory.get('Database')())


class RequestHandler(SocketServer.StreamRequestHandler):
    def set_vars(self):
        assert os.getpid() != my_pid  # Should only be done in child
        self.db = Factory.get('Database')()
        self.co = Factory.get('Constants')(self.db)
        self.ppq = PaidPrinterQuotas.PaidPrinterQuotas(self.db)

    def process_commands(self):
        self.set_vars()
        if not self.client_address[0].startswith(
                cereconf.PQ_IP_CONNECT_PREFIX):
            self.send(eperm)
            return

        self.send(helo)
        cmd = self.get()

        # Our first input line must be of the type
        #    HELO username hostname
        #
        if not (len(cmd) == 3 and cmd[0] == "HELO"):
            self.log('ERROR', "HELO expected %s received" % cmd)
            self.send("%s %s" % (ecmd, str(cmd)))
            return
        else:
            self.log('INFO', "HELO %s %s from %s" % (
                cmd[1], cmd[2], self.client_address))
            self._helo = (cmd[1], cmd[2])
            # Get information based on username
            self.username = cmd[1]
            try:
                account = Factory.get('Account')(self.db)
                account.clear()
                account.find_by_name(self.username)
            except Errors.NotFoundError:
                self.log('ERROR', "Invalid username %s from %s" % (
                    self.username, self.client_address))
                self.send(enouser)
                if not log_unknown_accounts:
                    return
                account = None
            self.pq_data = None
            self.person_id = None
            self.account_id = None
            if account is not None:
                self.account_id = account.entity_id
                try:
                    if account.owner_type == self.co.entity_person:
                        self.person_id = account.owner_id
                        self.pq_data = self.ppq.find(account.owner_id)
                except Errors.NotFoundError:
                    self.log('TRACE', "%s / %i / %i has no quota" %
                             (cmd[1], account.entity_id, self.person_id))
                    pass
                self.send("%s %s." % (firstok, cmd[1]))

            done = 0
            job_data = {}
            while not done:
                cmd = self.get()

                if len(cmd) == 0 or (not cmd[0]):
                    self.log('ERROR', "Connection down? !")
                    self.send(eerror)
                    done = 1
                elif cmd[0] == 'QUIT':
                    self.send(bye)
                    done = 1
                elif cmd[0] == 'SET' and len(cmd) >= 3:
                    # We loose whitspace, but that is probably OK
                    if cmd[1] not in (
                            'STEDKODE', 'JOBNAME', 'SPOOL_TRACE',
                            'PRISS_QUEUE_ID', 'PAPERTYPE', 'PAGES'):
                        self.send(unknownkey)
                    else:
                        job_data[cmd[1]] = " ".join(cmd[2:])
                        self.send(ok)
                elif cmd[0] == 'HISTORY' and len(cmd) == 1:
                    self.send_history(self.person_id)
                elif cmd[0] == 'CANP' and len(cmd) == 3:
                    self.send(self.check_quota(cmd[1], cmd[2]))
                elif cmd[0] == 'SUBP' and len(cmd) == 3:
                    self.send(self.subtract_quota(cmd[1], cmd[2], job_data))
                    job_data = {}
                else:
                    self.log('ERROR', "Unknown command %s" % str(cmd))
                    self.send(ecmd)
                    done = 1

    def alarm_handler(self, signum, frame):
        raise IOError("Timout")

    def handle(self):
        signal.alarm(30)
        signal.signal(signal.SIGALRM, self.alarm_handler)
        start = time()
        try:
            self.process_commands()
        except IOError, msg:
            self.log('ERROR', "IOError: %s" % msg)
        except ValueError, msg:
            self.log('ERROR', "ValueError: %s" % msg)
            self.send(ebadpage)
        except:
            self.log('CRITICAL', 'Unexpected exception: %s' %
                     self.formatException(sys.exc_info()))
        self.log('DEBUG', 'Total execution time: %s' % (time() - start))
        signal.alarm(0)
        self.db.close()

    def check_quota(self, printer, pageunits):
        # check_quota() - Given a username (username from HELO), and a positive
        #                 number of pageunits, it will use SQL to check that
        #                 the user has enough pages on his quota to cover at
        #                 one page at this pageunit. The printername is purely
        #                 for logging purposes.
        #
        # Possible &send() feedback: ok, no, edbdown, badpage

        self.log('TRACE', 'check_quota: %s@%s %s / %i' % (
            pageunits, printer, self.username, self.person_id or 0))
        if (self.pq_data is None or
                self.pq_data['has_quota'] == 'F'):
            return ok
        if self.pq_data['has_blocked_quota'] == 'T':
            self.log('INFO', 'check_quota: %s is blocked' % self.username)
            return no_blocked
        pageunits = float(pageunits)
        if pageunits <= 0:
            return ebadpage
        quota = (self.pq_data['free_quota'] + self.pq_data['accum_quota'] +
                 (1/printer_quota.PAGE_COST)*self.pq_data['kroner'])
        if quota >= pageunits:
            return ok+", quota=%f" % (quota)
        self.log('INFO', 'check_quota: %s insufficient quota: %d' %
                 (self.username, quota))
        return no_insuficcient

    def subtract_quota(self, printer, pageunits, job_data):
        if not self.client_address[0] in authorized_hosts:
            return eperm

        self.log('TRACE', "subtract_quota: %s for %s / %i, data=%s" % (
            pageunits, self.username, self.person_id or 0, repr(job_data)))
        pageunits = float(pageunits)
        if pageunits < 0:
            self.log('TRACE', "subtract_quota: BAD_PAGE")
            return ebadpage

        update_quota = self.pq_data and self.pq_data['has_quota'] == 'T'

        _assert_has_quota(self.person_id, self.db, self.ppq)
        job_id = self.ppq.add_printjob(
            self.person_id, self.account_id, printer,
            pageunits, 'pq',
            stedkode=job_data.get('STEDKODE', None),
            job_name=job_data.get('JOBNAME', None),
            spool_trace=job_data.get('SPOOL_TRACE', None),
            priss_queue_id=job_data.get('PRISS_QUEUE_ID', None),
            paper_type=job_data.get('PAPERTYPE', None),
            pages=job_data.get('PAGES', None),
            update_quota=update_quota)
        if self.person_id is None and self.account_id is None:
            self.log("INFO", "Job %i by unknown account: %s" %
                     (job_id, str(self._helo)))
        self.db.commit()
        return ok

    def send_history(self, person_id):
        """Returns up to 7 days of history, but max 7 entries"""
        if not self.client_address[0] in authorized_hosts:
            return self.send(eperm)
        if not person_id:
            self.send(enouser)
            return
        when = self.db.Date(*(localtime(time()-3600*24*7)[:3]))
        rows = self.ppq.get_history(person_id=person_id, tstamp=when)
        ok_data = ok[:3] + '-'
        for r in rows[-7:]:
            if r['transaction_type'] == int(self.co.pqtt_printout):
                self.send(ok_data+":".join(["%s" % x for x in (
                    r['job_id'], r['tstamp'].ticks(), r['printer_queue'],
                    r['pageunits_total'])]))
        self.send(ok)

    # send(line) - send a line (terminated by CR NL)
    def send(self, msg):
        self.wfile.write("%s^M\n" % msg)

    # @foo = &get; - Returns a list of tokens
    def get(self):
        return self.rfile.readline().rstrip().split()

    def log(self, lvl, msg):
        f = file(pqdlog, "a")
        f.write("%s [%s] %s %s\n" % (
            strftime("%Y-%m-%d %H:%M:%S", localtime()), os.getpid(), lvl, msg))
        f.close()

    def formatException(self, ei):  # from logging.py
        """
        Format the specified exception information as a string. This
        default implementation just uses traceback.print_exception()
        """
        sio = cStringIO.StringIO()
        traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1] == "\n":
            s = s[:-1]
        return s


def get_authorized_hosts(machine_list):
    db = Factory.get('Database')()
    gr = Factory.get('Group')(db)
    co = Factory.get('Constants')(db)

    def lookup_gids(groups):
        l = []
        for group in groups:
            gr.clear()
            try:
                gr.find_by_name(group[1:])
            except Errors.NotFoundError:
                continue
            l.append(gr.entity_id)
        return l

    groups = filter(lambda x: x.startswith('@'), machine_list)
    machines = set(machine_list) - set(groups)

    machines.update(map(lambda x: x['member_name'],
                        gr.search_members(group_id=lookup_gids(groups),
                                          indirect_members=True,
                                          member_type=co.entity_dns_owner,
                                          include_member_entity_name=True)))

    return map(lambda x: socket.gethostbyname(x), machines)


def usage(exitcode=0):
    print """Usage: pq.py [options]
    --port port : run on alternative port
    --bind adr  : run on alternative interface

Sample session:
HELO chrisege hermes.uio.no
SET STEDKODE 123456
SET JOBNAME en fin jobb
SET SPOOL_TRACE noe data her
SET PRISS_QUEUE_ID aq12345
SET PAPERTYPE a4
SET PAGES 27
SUBP foo 12
    """
    sys.exit(exitcode)

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   '',
                                   ['help', 'port=', 'bind='])
    except getopt.GetoptError:
        usage(1)

    port = None
    bind = ''
    for opt, val in opts:
        if opt in ('--help',):
            usage()
        elif opt in ('--port',):
            port = int(val)
        elif opt in ('--bind',):
            bind = val
    if not port:
        port = socket.getservbyname("prissquota", "tcp")

    authorized_hosts = get_authorized_hosts(cereconf.PQ_IP_SUBP)
    server = MyServer((bind, port), RequestHandler)
    server.serve_forever()
