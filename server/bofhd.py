#!/usr/bin/env python2.2

# Copyright 2002 University of Oslo, Norway
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

# $Id$

#
# Server used by clients that wants to access the cerebrum database.
#
# Work in progress, current implementation, expect big changes
#

import cerebrum_path

from SimpleXMLRPCServer import SimpleXMLRPCServer
import re
import socket
# import xmlrpclib
import cereconf
from Cerebrum import Database,Person,Utils,Account,Errors
from Cerebrum.modules import PosixUser
import sys
import traceback
# import dumputil
import pprint

pp = pprint.PrettyPrinter(indent=4)

class ExportedFuncs(object):

    """

    These functions can be called by anyone with access to the port
    that the server is running on.  Care must be taken to validate
    input.

    """

    def __init__(self, Cerebrum, fname):
        self.defaultSessionId = 'secret'
        self.modules = {}           # Maps modulenames to a module reference
        self.command2module = {}    # Maps a command to a modulename
        self.module_order = []
        self.Cerebrum = Cerebrum
        self.person = Person.Person(self.Cerebrum)
        self.const = self.person.const
            
        f = file(fname)
        while 1:
            line = f.readline()
            if not line: break
            if line[0] == '#':
                continue

            # Import module, create an instance of it, and update
            # mapping between command and the module implementing it.
            # Sub-modules may override functions.
            modfile = line.strip()
            mod = Utils.dyn_import(modfile)
            modref = mod.BofhdExtension(self.Cerebrum)
            self.modules[modfile] = modref
            self.module_order.append(modfile)
            for k in modref.all_commands.keys():
                self.command2module[k] = modfile
        t = self.command2module.keys()
        t.sort()
        for k in t:
            if getattr(self.modules[self.command2module[k]], k, None) is None:
                print "Warning, function '%s' is not implemented" % k
        
    def login(self, uname, password):
        if(uname != 'runefro'):
            raise "CerebrumError", "Invalid user"
        return self.defaultSessionId

    def get_commands(self, sessionid):
        # Build a tuple of tuples describing the commands available to
        # the client

        if(sessionid != self.defaultSessionId):
            raise "CerebrumError", "Authentication failure"
        else:
            # TODO: This may potentially return a different command
            # than self.command2module
            commands = {}
            for mn in self.module_order:
                newcmd = self.modules[mn].get_commands("uname")
                for k in newcmd.keys():
                    commands[k] = newcmd[k]
            return commands

    def get_format_suggestion(self, cmd):
        modfile = self.command2module[cmd]
        suggestion = self.modules[modfile].get_format_suggestion(cmd)
        if suggestion is not None:
            suggestion['str'] = unicode(suggestion['str'], 'iso8859-1')
        else:
            return ''    # TODO:  Would be better to allow xmlrpc-wrapper to handle none
        return suggestion

    def validate(self, argtype, arg):
        """Check if arg is a legal value for the given argtype"""
        pass
    
    def help(self, *group):
        # TBD: Re-think this
        # Show help by parsing the help file.  This is only partially implemented
        f = file("help.txt")
        ret = ''
        while 1:
            line = f.readline()
            if not line: break
            if line[0] == '#':
                continue
            ret = ret + line
        ret = ret + "End of help text"
        return unicode(ret.strip(), 'iso8859-1')

    def run_command(self, sessionid, *args):
        """Execute the callable function (in the correct module) with
        the given name after mapping sessionid to username"""

        user = self.get_user_from_session(sessionid)

        print "Run command: %s (%s)" % (args[0], args)
        modfile = self.command2module[args[0]]
        func = getattr(self.modules[modfile], args[0])
        try:
            new_args = ()
            for n in range(1, len(args)):
                if args[n] == 'XNone':     # TBD: Don't do this this way
                    new_args += (None,)
                else:
                    new_args += (args[n],)
                # TBD: Hvis vi f�r lister/tupler som input, skal func
                # kalles flere ganger
                if isinstance(args[n], list) or isinstance(args[n], tuple):
                    raise NotImplemetedError, "tuple argumenter ikke implemetert enda"
            ret = func(user, *new_args)
            print "process ret: "
            pp.pprint(ret)
            self.Cerebrum.commit()
            return self.process_returndata(self.Cerebrum.pythonify_data(ret))
        except Exception:
            # ret = "Feil: %s" % sys.exc_info()[0]
            # print "Error: %s: %s " % (sys.exc_info()[0], sys.exc_info()[1])
            # traceback.print_tb(sys.exc_info()[2])
            self.Cerebrum.rollback()
            raise

    ## Prompting and tab-completion works pretty much the same way.
    ## First we check if the function 'name' has a function named
    ## 'name_prompt' (or 'name_tab'), and uses this.  If no such
    ## function is defined, we check the Parameter object to find out
    ## what to do.

    def tab_complete(self, sessionid, *args):
        "Atempt to tab-complete the command."
        
        user = self.get_user_from_session(sessionid)
        func, modref, param = self._lookupParamInfo(args[0], "_tab", len(args)-1)
        if func is not None:
            ret = func(user, *args[1:])
        else:
            if param._tab_func is None:
                ret = ()
            else:
                ret = getattr(modref, param._tab_func)(user, *args[1:])
        return self.process_returndata(ret)

    def prompt_next_param(self, sessionid, *args):
        "Prompt for next parameter."

        user = self.get_user_from_session(sessionid)
        func, modref, param = self._lookupParamInfo(args[0], "_prompt", len(args)-1)
        if func is not None:
            ret = func(user, *args[1:])
            return self.process_returndata(ret)
        else:
            if param._prompt_func is None:
                return param.getPrompt()
            else:
                return getattr(modref, param._prompt_func)(user, *args[1:])

    def _lookupParamInfo(self, cmd, fext, nargs):
        modref = self.modules[ self.command2module[cmd] ]
        try:
            func = getattr(modref, cmd+fext)
            return (func, None, None, None)
        except AttributeError:
            pass
        cmdspec = modref.all_commands[cmd]
        assert(nargs < len(cmdspec._params)) # prompt skal ikke kalles hvis for mange argumenter(?)
        return (None, modref, cmdspec._params[nargs])

    def process_returndata(self, ret):
        """Encode the returndata so that it is a legal XML-RPC structure."""
        # Todo: process recursive structures
        if isinstance(ret, list) or isinstance(ret, tuple):
            for x in range(len(ret)):
                if isinstance(ret[x], str):
                    ret[x] = unicode(ret[x], 'iso8859-1')
                elif ret[x] is None:
                    ret[x] = ''
            return ret
        elif isinstance(ret, dict):
            for x in ret.keys():
                if isinstance(ret[x], str):
                    ret[x] = unicode(ret[x], 'iso8859-1')
                elif ret[x] is None:
                    ret[x] = ''
            return ret
        else:
            if isinstance(ret, str):
                ret = unicode(ret, 'iso8859-1')
            return ret

    def get_user_from_session(self, sessionid):
        """Map sessionid to an existing authenticated user"""
        if(1 == 0):
            raise "CerebrumError", "Authentication failure"
        return 'runefro'

def find_config_dat():
    # XXX This should get the path from configure
    for filename in "config.dat", "/etc/cerebrum/config.dat", \
            "/tmp/cerebrum/etc/cerebrum/config.dat":
        try:
            print "Testing filename ",filename
            f = file(filename)
            if (f):
                return filename
        except:
            continue
    return "config.dat"

if __name__ == '__main__':
    conffile = find_config_dat()
    # Loop for an available port while testing to avoid already bound error
    for port in range(8000,8005):
        try:
            print "Server starting at port: %d" % port
            if not cereconf.ENABLE_BOFHD_CRYPTO:
                server = SimpleXMLRPCServer(("0.0.0.0", port))
            else:
                from server import MySimpleXMLRPCServer
                from M2Crypto import SSL

                ctx = MySimpleXMLRPCServer.init_context('sslv23', 'server.pem',
                                                        'ca.pem',
                                                        SSL.verify_none)
                ctx.set_tmp_dh('dh1024.pem')
                server = MySimpleXMLRPCServer.SimpleXMLRPCServer(('',port),ctx)

            server.register_instance(ExportedFuncs(Database.connect(),
                                                   conffile))
            server.serve_forever()
        except socket.error:
            print "Failed, trying another port"
            pass
