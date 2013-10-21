#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 University of Oslo, Norway
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
"""Job for syncing Cerebrum data with TSD's Gateway (GW).

The Gateway needs information about all projects, accounts, hosts, subnets and
VLANs, to be able to let users in to the correct project. This information comes
from Cerebrum. Some of the information is sent to the Gateway e.g through bofh
commands and the import from Nettskjema, but not all information gets update
that way. An example is quarantines that gets activated or deactivated.

"""

import sys
import os
import getopt
from mx import DateTime

import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules.dns import Subnet, IPv6Subnet
from Cerebrum.modules.tsd import Gateway

logger = Factory.get_logger('cronjob')

def usage(exitcode=0):
    print """
    %(doc)s 
    
    Usage: %(file)s TODO

    TODO

    --url URL           The full URL to the Gateway.
                        Example: https://gw.tsd.uio.no:1234/RPC
                        Default: cereconf.TSD_GATEWAY_URL

    -d --dryrun         Run the sync in dryrun. Data is retrieved from the
                        Gateway and compared, but changes are not sent back to
                        the gateway. Default is to commit the changes.

    --mock              Mock the gateway by returning empty lists instead of
                        talking with the GW. Usable for testing the
                        functionality locally.

    -h --help           Show this and quit.

    """ % {'doc': __doc__,
           'file': os.path.basename(sys.argv[0])}
    sys.exit(exitcode)

class Project(object):
    """Container of a project and its data.

    This is to ease the comparement of projects with the Gateway.

    """
    def __init__(self, entity_id):
        self.entity_id = entity_id
        #self.pid = TODO # ?
        # TODO: add more data

class Processor:
    """The processor class, doing the sync with the gateway."""

    def __init__(self, gw, dryrun):
        self.gw = gw
        self.dryrun = dryrun
        self.db = Factory.get('Database')()
        self.co = Factory.get('Constants')(self.db)
        self.ou = Factory.get('OU')(self.db)
        self.pe = Factory.get('Person')(self.db)
        self.ac = Factory.get('Account')(self.db)
        self.pu = Factory.get('PosixUser')(self.db)

        # Map account_id to account_name:
        self.acid2acname = dict((row['account_id'], row['name']) for row in
                                self.ac.search(spread=self.co.spread_gateway_account))
        logger.debug2("Found %d accounts" % len(self.acid2acname))
        # Map ou_id to project id:
        self.ouid2pid = dict((row['entity_id'], row['external_id']) for row in
                self.ou.search_external_ids(entity_type=self.co.entity_ou,
                    id_type=self.co.externalid_project_id))
        logger.debug2("Found %d project IDs" % len(self.ouid2pid))

    def process(self):
        """Go through all projects in Cerebrum and compare them with the Gateway.

        If the Gateway contains mismatches, it should be updated.

        """
        gw_data = dict()
        for key, meth in (('projects', self.gw.list_projects), 
                          ('users', self.gw.list_users),
                          ('hosts', self.gw.list_hosts),
                          ('subnets', self.gw.list_subnets),
                          ('vlans', self.gw.list_vlans)):
            logger.debug("Getting %s from GW...", key)
            gw_data[key] = meth()
            logger.debug("Got %d entities in %s", len(gw_data[key]), key)

        self.process_projects(gw_data['projects'])
        self.process_users(gw_data['users'])

        # Sync all hosts:
        self.process_dns(gw_projects)

    def process_projects(self, gw_projects):
        """Go through and update the projects from the GW.

        Since we should not have that many projects, maybe up to a few hundreds,
        it loops through each OU by find() and clear(). If TSD would grow larger
        in size, this script might take too long to finish, so we then might
        have to cache it.

        """
        processed = set()
        # Update existing projects:
        for proj in gw_projects:
            pid = proj['name']
            try:
                self.process_project(pid, proj)
            except Gateway.GatewayException, e:
                logger.warn("GatewayException for %s: %s" % (pid, e))
            processed.add(pid)
        # Add new OUs:
        for row in self.ou.search(filter_quarantined=True):
            self.ou.clear()
            self.ou.find(row['ou_id'])
            pid = self.ou.get_project_id()
            if pid in processed:
                continue
            self.gw.create_project(pid)

    def process_project(self, pid, proj):
        """Process a given project retrieved from the GW.

        The information should be retrieved from the gateway, and is then
        matched against what exist in Cerebrum.

        @type pid: string
        @param pid: The project ID.

        @type proj: dict
        @param proj: Contains the information about a project and all its
            elements.

        """
        logger.debug("Processing project %s: %s", pid, proj)
        self.ou.clear()
        try:
            self.ou.find_by_tsd_projectid(pid)
        except Errors.NotFoundError:
            # TODO: check if the project is marked as 'expired', so we don't
            # send this to the gw every time.
            # if proj['expires'] and proj['expires'] < DateTime.now():
            self.gw.delete_project(pid)
            return

        quars = dict((row['quarantine_type'], row) for row in
                     self.ou.get_entity_quarantine(only_active=False))
        active_quars = dict((row['quarantine_type'], row) for row in
                            self.ou.get_entity_quarantine(only_active=True))

        # Quarantines - delete, freeze and thaw
        if (quars.has_key(self.co.quarantine_project_end) and
                quars[self.co.quarantine_project_end]['start_date'] < DateTime.now()):
            self.gw.delete_project(pid)
        if len(active_quars) > 0:
            if not proj['frozen']:
                self.gw.freeze_project(pid)
        else:
            if proj['frozen']:
                self.gw.thaw_project(pid)

    def process_users(self, gw_users):
        """Sync all users with the GW."""
        processed = set()
        # Get the mapping to each project. Each user can only be part of one
        # project.
        ac2proj = dict()
        for row in self.pu.list_accounts_by_type(
                            affiliation=self.co.affiliation_project,
                            filter_expired=True,
                            account_spread=self.co.spread_ad_account):
            if ac2proj.has_key(row['account_id']):
                logger.warn("Account %s affiliated with more than one project",
                            row['account_id'])
                continue
            ac2proj[row['account_id']] = row['ou_id']

        # Update existing projects:
        for usr in gw_users:
            username = usr['username']
            pid = usr['project']
            processed.add(username)

            self.pu.clear()
            try:
                self.pu.find_by_name(username)
            except Errors.NotFoundError:
                self.gw.delete_user(pid, username)
                continue
            # TODO: freeze and thaw...
            is_frozen = bool(tuple(self.pu.get_entity_quarantine(
                only_active=True)))


            if not ac2proj.get(self.pu.entity_id):
                self.gw.delete_user(pid, username)
                continue
            if pid != self.ouid2pid.get(ac2proj[self.pu.entity_id]):
                logger.error("Danger! Project mismatch in Cerebrum and GW for account %s" % self.pu.entity_id)
                raise Exception("Project mismatch with GW and Cerebrum")
            if is_frozen:
                if not usr['frozen']:
                    self.gw.freeze_user(pid, username)
            else:
                if usr['frozen']:
                    self.gw.thaw_user(pid, username)
        # Add new users:
        for row in self.pu.search(spread=self.co.spread_gateway_account):
            if row['name'] in processed:
                continue
            self.pu.clear()
            self.pu.find(row['account_id'])
            # Skip all quarantined accounts:
            if tuple(self.pu.get_entity_quarantine(only_active=True)):
                continue
            # Skip accounts not affiliated with a project.
            pid = self.ouid2pid.get(ac2proj.get(self.pu.entity_id))
            if not pid:
                logger.debug("Skipping unaffiliated account: %s",
                        self.pu.entity_id)
                continue
            self.gw.create_user(pid, row['name'])

    #def process_project_members(self, ou, proj):
    #    """Sync the members of a project."""
    #    pid = ou.get_project_id()
    #    ce_users = dict((self.acid2acname[row['account_id']], row) for row in
    #                    self.pu.list_accounts_by_type(ou_id=ou.entity_id,
    #                                                  filter_expired=False,
    #                            account_spread=self.co.spread_gateway_account))
    #    # Remove accounts not registered in Cerebrum:
    #    for user in proj['users']:
    #        username = user['username']
    #        if username not in ce_users:
    #            if not user['expires'] or user['expires'] > DateTime.now():
    #                logger.debug("Removing account %s: %s", username, user)
    #                self.gw.delete_user(pid, username)
    #    # Update the rest of the accounts:
    #    for username, userdata in ce_users.iteritems():
    #        self.pu.clear()
    #        self.pu.find(userdata['account_id'])
    #        # Updating realname not implemented, as it's not used.

    def process_dns(self, gw_projects):
        """Sync all hosts to the gateway.

        @type gw_projects: dict
        @param gw_projects: All info about the projects, from the GW.

        """
        # Hosts:
        #
        # TODO
        # Subnets and vlans
        gw_subnets = dict()
        #for proj in gw_projects.itervalues():
        #    gw_subnets[

        #ret = []
        ## IPv6:
        subnet6 = IPv6Subnet.IPv6Subnet(self.db)
        compress = IPv6Utils.IPv6Utils.compress
        for row in subnet6.search():
            ret.append({
                'subnet': '%s/%s' % (compress(row['subnet_ip']),
                                     row['subnet_mask']),
                'vlan_number': str(row['vlan_number']),
                'description': row['description']})
        # IPv4:
        #subnet = Subnet.Subnet(self.db)
        #for row in subnet.search():
        #    ret.append({
        #        'subnet': '%s/%s' % (row['subnet_ip'], row['subnet_mask']),
        #        'vlan_number': str(row['vlan_number']),
        #        'description': row['description']})
        #self.logger.debug("Found %d subnets", len(ret))
        ## Sort by subnet
        #return sorted(ret, key=lambda x: x['subnet'])

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd',
                                   ['help', 'url=', 'dryrun', 'mock'])
    except getopt.GetoptError, e:
        print e
        usage(1)

    dryrun = False
    mock = False
    url = None

    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-d', '--dryrun'):
            dryrun = True
        elif opt in ('--mock'):
            mock = True
            dryrun = True
        elif opt in ('--url',):
            url = val
        else:
            print "Unknown argument: %s" % opt
            usage(1)

    if url:
        gw = Gateway.GatewayClient(logger, uri=url, dryrun=dryrun)
    else:
        gw = Gateway.GatewayClient(logger, dryrun=dryrun)

    if mock:
        #gw.get_projects = lambda: dict()
        logger.debug("Mocking GW")
        for t in gw.__class__.__dict__:
            if t.startswith('list_'):
                logger.debug("Mocking: %s", t)
                setattr(gw, t, lambda: list())
            elif t.startswith('get_'):
                logger.debug("Mocking: %s", t)
                setattr(gw, t, lambda: dict())

    logger.debug("Start gw-sync against URL: %s", gw)
    p = Processor(gw, dryrun)
    p.process()
    logger.info("Finished gw-sync")

if __name__ == '__main__':
    main()
