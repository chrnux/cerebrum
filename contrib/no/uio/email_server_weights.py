#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2005 University of Oslo, Norway
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
Updates the weight traits associated with the e-mail servers.  The
argument to --except is a regular expression, servers matching it will
not receive a weight trait, and an existing trait will be removed.
Several --except arguments may be given.

The weight algorithm is simple: Each server gets a value which is the
difference between its assigned quota and the maximum assigned quota.
In other words, we want to make sure every server has an equal amount
of assigned quota, even when we're a long way away from filling up
capacity.

To avoid problems with weird skew when just starting out an
installation or when the server assignement rates are _very_ similar,
we add 10% to the max value.  This ensures that every server has a
chance of getting new users, even the server with the most quota
assigned to it.  If a server has 10% less assigned quota than the
fullest server, the chance of being assigned more users will be twice
that of the fullest server.
"""

def usage(exitcode=64):
    print "Usage: email_server_weights.py [--server-type TYPE] [--except]"
    print __doc__
    sys.exit(exitcode)

import sys
import getopt
import re
import cerebrum_path
from Cerebrum.Utils import Factory
from Cerebrum import Errors
from Cerebrum.modules.Email import EmailQuota, EmailServer

db = Factory.get('Database')()
co = Factory.get('Constants')(db)
logger = Factory.get_logger("cronjob")
db.cl_init(change_program="e_srv_weights")


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], '?h',
                                   ['help', 'dryrun',
                                    'server-type=', 'except='])
    except getopt.GetoptError:
        usage()

    server_type = except_re = dryrun = None
    patterns = []
    for opt, val in opts:
        if opt in ('--help', '-h', '-?'):
            usage(0)
        elif opt in ('--except',):
            try:
                except_re = re.compile(val)
            except re.error, e:
                print "Invalid regular expression '%s': %s" % (val, e)
                sys.exit(1)
            patterns.append(val)
        elif opt in ('--server-type',):
            server_type = co.EmailServerType(val)
            try:
                int(server_type)
            except Errors.NotFoundError:
                print "Unknown server type:", val
                sys.exit(1)
        elif opt in ('--dryrun',):
            dryrun = True
    if patterns:
        except_re = re.compile("(?:" + ")|(?:".join(patterns) + ")")

    process_servers(server_type, except_re)
    if not dryrun:
        db.commit()


def process_servers(server_type, except_re):
    es = EmailServer(db)
    eq = EmailQuota(db)

    existing_servers = {}

    # This lists all hosts, so we need to filter on server_type later.
    for row in es.list_traits(co.trait_email_server_weight):
        existing_servers[int(row['entity_id'])] = True

    assigned = {}
    for row in es.list_email_server_ext(server_type=server_type):
        # logger.debug("Processing %r" % row.dict())
        if except_re and except_re.match(row['name']):
            logger.debug("Skipping server named '%s'" % row['name'])
            continue
        srv = int(row['server_id'])
        assigned[srv] = eq.get_quota_stats_by_server(srv)['total_quota'] or 0
        logger.debug("%s has assigned quota %d" % (row['name'], assigned[srv]))
    max_weight = max(assigned.values()) * 110 / 100

    for srv in assigned:
        es.clear()
        es.find(srv)
        # We add 1 to handle the case with only one server
        weight = max_weight - assigned[srv] + 1
        logger.debug("Assigning weight %d to server ID %d" % (weight, srv))
        es.populate_trait(co.trait_email_server_weight, numval=weight)
        es.write_db()
        if srv in existing_servers:
            del existing_servers[srv]

    for obsolete in existing_servers:
        es.clear()
        es.find(obsolete)
        if server_type and es.email_server_type != server_type:
            continue
        logger.info("Deleting old weight trait for %s" % es.name)
        es.delete_trait(co.trait_email_server_weight)


if __name__ == '__main__':
    main()

