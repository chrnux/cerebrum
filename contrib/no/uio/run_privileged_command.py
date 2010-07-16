#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2003 University of Oslo, Norway
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

import getopt
import sys
import os

import cerebrum_path
import cereconf

# Simple definition of legal commands.  In the future this should be
# read from a configuration file.
# Format: 'key': ['path', 'number-of-args']
# future versions could provide more restrictions on the legal arguments
commands = {
    # uname, home, uid, gid, gecos
    # 'mkhome': [cereconf.CREATE_USER_SCRIPT, 5],
    # uname, uid, gid, old_disk, new_disk, spread, mailto, receipt
    # 'mvuser': [cereconf.MVUSER_SCRIPT, 8],
    # uname, operator, old_home, mail_server
    #'aruser': [cereconf.RMUSER_SCRIPT, 5],
    # server, uname
    # 'archivemail': [cereconf.ARCHIVE_MAIL_SCRIPT, 3],
    # action, server, uname
    'subscribeimap': [cereconf.SUBSCRIBE_SCRIPT, 3],
    # uname, home, mailto, hquota, from_host, from_type, to_host, to_type
    'mvmail': [cereconf.MVMAIL_SCRIPT, 8],
    # uname, home, uid, dfg
    'convertmail': [cereconf.CONVERT_MAILCONFIG_SCRIPT, 4],
    # host, mode, listname, admin, profile, description
    # 'sympa': [cereconf.SYMPA_SCRIPT, 6],
    # operation
    'clean_rmuser': [cereconf.CLEAN_RMUSER_SCRIPT, 1],
    # dist Notes ID files
    'dist_NotesID': [cereconf.DIST_NOTESID_SCRIPT, 4],
    # move IMAP users
    # 'imap_move': ["/local/bin/ssh", 21],
    # sync src from external servers
    'sync_files': ["/local/bin/rsync", 3],
    # need to chown synced files
    'chown': ["/bin/chown", 3],
    }

def usage(exitcode=0):
    print """Usage: run_privileged_command.py [-c cmd | -h] args
    -c | --command cmd: run the command with specified args
    -h | --help: this message

    This script works as a small wrapper to other scripts.  A
    configuration file defines what commands a user may run, and to
    some extent what arguments may be provided.  It is not designed to
    be bulletproof, but rather as a method to avoid shooting oneself
    in the foot, as well as avoiding multiple complex lines in
    /etc/sudoers.

    Add something like this to /etc/sudoers:
    cerebrum  localhost=NOPASSWD: /path/to/run_privileged_command.py
    """
    
    sys.exit(exitcode)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:',
                                   ['help', 'command='])
    except getopt.GetoptError:
        usage(1)
    if not opts:
        usage(1)
    command = None
    for opt, val in opts:
        if opt in ('-c', '--command'):
            command = val
        elif opt in ('-h', '--help'):
            usage(0)
    if command is not None:
        if not commands.has_key(command):
            print "Bad command: %s" % command
            sys.exit(1)
        if len(args) != commands[command][1]:
            print "Bad # args for %s (%i/%i)" % (
                command, len(args), commands[command][1])
            sys.exit(1)
        args.insert(0, commands[command][0])
        os.execv(commands[command][0], args)

if __name__ == '__main__':
    main()
