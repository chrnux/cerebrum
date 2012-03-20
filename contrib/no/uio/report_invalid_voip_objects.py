#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Copyright 2002, 2003, 2004,2012 University of Oslo, Norway
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
Report voipAddress owned by persons without an account. The purpose is to
identify objects that get the same LDAP destinguished name leading to a
collision.
"""

import getopt
import sys

import cerebrum_path
import cereconf
from Cerebrum.Utils import Factory, sendmail
from Cerebrum.modules.LDIFutils import ldapconf
from Cerebrum.modules.no.uio.voip.voipAddress import VoipAddress


def report_invalid_voip_addresses(logger, report):
    """Find voipAddress-objects owned by persons without an account.

    @param logger

    @type list
    @param report is a list of dicts.
    """
    logger.debug('-'*8 + 'voipAddresses' + '-'*8)
    db = Factory.get("Database")()
    va = VoipAddress(db)

    for entry in va.list_voip_attributes():
        if entry['voipOwnerType'] != 'person':
            continue # skip objects owned by services
        entry['objectClass'] = ['top','voipAddress']
        if 'voipOwnerId' in entry:
            dn = "voipOwnerId=%s,%s" %(entry['voipOwnerId'],
                            ldapconf('VOIP_ADDRESS', 'dn', None))
        else:
            dn = "uid=%s,%s" %(entry['uid'],
                            ldapconf('VOIP_ADDRESS', 'dn', None))
        entry['dn'] = dn
        del entry["entity_id"]
        if not entry.get("cn"):
            entry["cn"] = ()
        if entry["uid"] is None:
            logger.debug('uid is None')
            entry['reason'] = 'uid is None.'
            report.append(entry)
    logger.debug('-'*8+'end voipAddresses'+'-'*8)


def dump_entry(entry, sink):
    """Dump an entry dict to stream.

    Filters out uneeded data from the dict.
    Output format:
            key: value

    @type dict
    @param entry

    @type file-like object.
    @param sink
    """
    assert isinstance(entry, dict)

    # filter out
    # passwords and pincodes
    if 'a1Password' in entry:
        del entry['a1Password']
    if 'voipPinCode' in entry:
        del entry['voipPinCode']

    for k,v in sorted(entry.iteritems()):
        if isinstance(v, (list,tuple)):
            for elm in v:
                sink.write("%s: %s\n" %(k,elm))
        else:
            sink.write("%s: %s\n" %(k,v))
    sink.write("\n")


def create_report_message(report):
    """ Return email message text created from list of entries.

    @type list
    @param report is a list of dicts. A dict represents voipAddress in a format
    based on ldif.
    @return text of email message as string
    """

    from cStringIO import StringIO
    string_stream = StringIO()
    string_stream.write('Found %d voipAddresses owned by persons '
                        'without primary account.\n\n' %len(report))
    for elm in report:
        dump_entry(elm, string_stream)

    from mx.DateTime import now
    string_stream.write('\nReport finished %s.\n' %now().strftime('%Y-%m-%d at %H:%M'))
    res = string_stream.getvalue()
    string_stream.close()
    return res


def main():
    logger = Factory.get_logger("cronjob")
    outfile = None
    outstream = sys.stdout
    mail_to = None
    mail_from = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                "hdo:",("help","outfile=","mail_to=","mail_from="))
    except getopt.GetoptError, e:
        usage(str(e))

    if args:
        usage("Invalid arguments: " + " ".join(args))
    for opt, val in opts:
        if opt in ("-o", "--outfile"):
            outfile = val
            outstream = open(outfile, 'w')
        elif opt in ("--mail_to"):
            mail_to = val
        elif opt in ("--mail_from"):
            mail_from = val
        else:
            usage()

    report = []

    logger.info("### Searching invalid VOIP objects...")
    report_invalid_voip_addresses(logger, report)
    logger.info("### Search  finished, found %d" %len(report))

    if len(report):
        message = create_report_message(report)
        if mail_to and mail_from:
            subject = 'Report of invalid voipAddresses.'
            sendmail(mail_to, mail_from, subject, message)
            logger.info("Sent report by mail to %s." %mail_to)
        else:
            outstream.write(message)
            logger.info("Wrote report to file %s" %outfile)

    if not outstream is sys.stdout:
        outstream.close()


def usage(err=0):
    if err:
        print >>sys.stderr, err
    prog = sys.argv[0]
    print >>sys.stderr, """Usage: %s [options]
    Report voip addresses owned by persons without accounts.

    -o, --output    File to save the report to. Defaults to stdout.
                    Report is saved if no source and destination email address
                    was given.
    --mail_to       Email destination address. Mandatory for sending report by email.
    --mail_from     Email source address. Mandatory for sending report by email.
    -h, --help      Show this help message and exit.

    Examples:
        %s
            report is dumped to stdout.
        %s --output filename --mail_to dest@example.com --mail_from source@example.com
            report is sent to mail_to address. File filename is not written to.

        %s --output filename --mail_to dest@example.com
            report is written to file.
    """ % (prog, prog, prog, prog)
    sys.exit(bool(err))


if __name__ == '__main__':
    main()