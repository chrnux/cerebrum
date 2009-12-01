#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2004, 2005 University of Oslo, Norway
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

from ceresync import errors
from ceresync import syncws as sync
from ceresync import config

import os
import sys
import socket

log = config.logger

changelog_file = config.get("sync","last_change", "/var/lib/cerebrum/sync.last_change")

def load_changelog_id():
    local_id = 0
    if os.path.isfile(changelog_file):
        local_id = long(open(changelog_file).read())
        log.debug("Loaded changelog-id %ld", local_id)
    else:
        log.debug("Default changelog-id %ld", local_id)
    return local_id

def save_changelog_id(server_id):
    log.debug("Storing changelog-id %ld", server_id)
    open(changelog_file, 'w').write(str(server_id))

def set_incremental_options(options, incr, server_id):
    if not incr:
        return

    local_id = load_changelog_id()
    log.debug("Local id: %ld, server_id: %ld", local_id, server_id)
    if local_id > server_id:
        log.warning("local changelogid is larger than the server's!")
    elif incr and local_id == server_id:
        log.debug("No changes to apply. Quiting.")
        sys.exit(0)

    options['incr_from'] = local_id

def set_encoding_options(options, config):
    options['encode_to'] = 'utf-8'

def main():
    options = config.make_bulk_options() + config.make_testing_options()
    config.parse_args(options)

    incr = config.getboolean('args','incremental', allow_none=True)
    add = config.getboolean('args','add')
    update = config.getboolean('args','update')
    delete = config.getboolean('args','delete')
    using_test_backend = config.getboolean('args', 'use_test_backend')

    if incr is None:
        log.error("Invalid arguments. You must provide either the --bulk or the --incremental option")
        sys.exit(1)

    log.debug("Setting up CereWS connection")
    try:
        s = sync.Sync(locking=not using_test_backend)
        server_id = s.get_changelogid()
    except sync.AlreadyRunningWarning, e:
        log.warning(str(e))
        sys.exit(1)
    except sync.AlreadyRunning, e:
        log.error(str(e))
        sys.exit(1)
    except socket.error, e:
        log.error("Unable to connect to web service: %s", e)
        sys.exit(1)

    sync_options = {}
    set_incremental_options(sync_options, incr, server_id)
    config.set_testing_options(sync_options)
    set_encoding_options(sync_options, config)

    systems = config.get('ldap', 'sync', default='').split()
    for system in systems:
        log.debug("Syncing system %s", system)
        if using_test_backend:
            backend = get_testbackend(system)
        else:
            backend = get_ldapbackend(system)

        backend.begin(
            incr=incr,
            bulk_add=add,
            bulk_update=update,
            bulk_delete=delete)

        for entity in get_entities(s, system, sync_options):
            backend.add(entity)
        backend.close()

    if incr or (add and update and delete):
        save_changelog_id(server_id)

def get_conf(system, name, default=None):
    conf_section = 'ldap_%s' % system
    if default is not None:
        return config.get(conf_section, name, default=default)
    return config.get(conf_section, name)

def get_testbackend(system):
    import ceresync.backend.test as ldapbackend
    entity = get_conf(system, "entity")

    if (entity == "account"):
        return ldapbackend.Account()
    elif (entity == "group"):
        return ldapbackend.Group()
    elif (entity == "person"):
        return ldapbackend.Person()
    elif (entity == "ou"):
        return ldapbackend.OU()
    else:
        raise NotImplementedError("Haven't faked %s, and didn't plan on it." % entity)

def get_ldapbackend(system):
    from ceresync.backend import ldapbackend

    backend_class = get_conf(system, "backend")
    base = get_conf(system, "base")
    filter = get_conf(system, "filter", default="(objectClass='*')")

    log.debug("Initializing %s backend with base %s", backend_class, base)
    backend = getattr(ldapbackend, backend_class)(base=base, filter=filter)
    return backend

cache = {}
def get_entities(s, system, sync_options):
    entity = get_conf(system, "entity")
    if entity in cache:
        return cache[entity]

    my_options = sync_options.copy()

    if entity == 'account':
        my_options['spread'] = get_conf(system, "spread")

    cache[entity] = entities = getattr(s, "get_%ss" % entity)(**my_options)
    return entities

if __name__ == "__main__":
    main()
