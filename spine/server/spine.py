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

import cerebrum_path
import cereconf

import sys
import thread
import traceback

def main():
    print 'Importing all classes...'
    from Cerebrum.spine.server import Communication
    from Cerebrum.spine.server import LockHandler
    from Cerebrum.spine.server import SessionHandler
    from Cerebrum.spine.server import Spine

    com = Communication.get_communication()
    session_handler = SessionHandler.get_handler()
    lock_handler = LockHandler.get_handler()

    # creating server
    print 'Creating server object...'
    server = com.servant_to_reference(Spine.SpineImpl())

    print 'Starting session handler...'
    session_handler.start()

    print 'Starting lock handler...'
    lock_handler.start()

    # Write server object IOR to file
    print 'IOR written to:', cereconf.SPINE_IOR_FILE
    ior = com.orb.object_to_string(server)
    fd = open(cereconf.SPINE_IOR_FILE, 'w')
    fd.write(ior)
    fd.close()

    # Starting communication
    print 'Running server...'
    try:
        com.start()
    except KeyboardInterrupt:
        print 'Interrupt caught! Shutting down...'
        pass
    except AssertionError, e:
        raise e # Asserts should make us die
    except:
        traceback.print_exc()
    print 'Stopping lock handler...'
    lock_handler.stop()
    print 'Stopping session handler...'
    session_handler.stop()
    print 'Spine is going down.'

def check():
    from Cerebrum.spine.SpineLib import Builder, DatabaseClass
    from Cerebrum.Utils import Factory

    db = Factory.get('Database')()

    for cls in Builder.get_builder_classes(DatabaseClass.DatabaseClass):
        for table in cls._get_sql_tables():
            if DatabaseClass._table_exists(db, table):
                print '+ exists:', table
            else:
                print '- WARNING does not exists:', table

def build():
    from Cerebrum.spine.SpineLib import Builder, DatabaseClass
    from Cerebrum.Utils import Factory

    db = Factory.get('Database')()

    for cls in Builder.get_builder_classes(DatabaseClass.DatabaseClass):
        if cls.slots:
            DatabaseClass.create_tables(db, cls)

if __name__ == '__main__':        
    help = False
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            main()
        elif sys.argv[1] == 'check':
            check()
        elif sys.argv[1] == 'build':
            build()
        else:
            help = True
    else:
        help = True
    
    if help:
        print """Spine!

Hello. Try one of these:

%s start    start the spine server
%s check    check all tables
%s build    build all missing tables
""" % tuple(sys.argv[:1] * 3)

# arch-tag: c5bbf2ca-6dee-49e3-9774-a3f7487b9594
