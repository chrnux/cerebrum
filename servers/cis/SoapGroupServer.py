#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010, 2011, 2012 University of Oslo, Norway
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

import sys, socket, traceback
import getopt

from twisted.python import log

from rpclib.model.complex import ComplexModel, Iterable
from rpclib.model.primitive import String, Integer, Boolean
from rpclib.model.fault import Fault
# Note the difference between rpc and the static srpc - the former sets the
# first parameter as the current MethodContext. Very nice if you want
# environment details.
from rpclib.decorator import rpc, srpc

import cerebrum_path
from cisconf import groupservice as cisconf
from Cerebrum.Utils import Messages, dyn_import
from Cerebrum import Errors
from Cerebrum.modules.cis import SoapListener, auth

class GroupMember(ComplexModel):
    __namespace__ = 'tns'
    __tns__ = 'tns'
    uname = String
    member_type = String
    member_id = String

    # TODO more info about a member?

class GroupService(SoapListener.BasicSoapServer):

    # Require the session ID in the client's header
    __in_header__ = SoapListener.SessionHeader

    # Respond with a header with the current session ID
    __out_header__ = SoapListener.SessionHeader

    # The class where the Cerebrum-specific functionality is done. This is
    # instantiated per call, to avoid thread conflicts.
    cere_class = None

    # The hock for the site object
    site = None

    @rpc(String, _returns = Iterable(GroupMember),
            _throws=SoapListener.EndUserFault)
    def get_members(ctx, groupname):
        return ctx.udc['groupinfo'].search_members_flat(groupname)


# And then the individuation specific events:
def _on_method_call(ctx):
    """Event method for fixing the individuation functionality, like language."""
    # TODO: the language functionality may be moved into SoapListener? It is
    # probably usable by other services too.
    if ctx.udc is None:
        # TODO: change to object later, or is that necessary at all?
        log.msg("DEBUG: ctx.udc is None, initializing")
        ctx.udc = dict()
    ctx.udc['groupinfo'] = ctx.service_class.cere_class()
    log.msg('DEBUG: GroupService _on_method_call')

def _on_method_exception(ctx):
    """Event for updating raised exceptions to return a proper error message in
    the chosen language. The individuation instance could then raise errors with
    a code that corresponds to a message, and this event updates the error with
    the message in the correct language.
    """
    log.msg('DEBUG: GroupService _on_method_exception')
    if isinstance(ctx.out_error, SoapListener.EndUserFault):
        err = ctx.out_error
        #try:
        #    err.faultstring = 'Soap Fault'#ctx.udc['session']['msgs'][err.faultstring] % err.extra
        #except KeyError, e:
        #    log.msg('WARNING: Unknown error: %s - %s' % (err.faultstring, e))

# When a call is processed, it has to be closed:
def _on_method_exit(ctx):
    """Event for cleaning up the groupinfo instances, i.e. close the
    database connections. Since twisted runs all calls in a pool of threads, we
    can not trust __del__."""
    # TODO: is this necessary any more, as we now are storing it in the method
    # context? Are these deleted after each call?
    log.msg('DEBUG: GroupService  on_exit')
    if ctx.udc.has_key('groupinfo'):
        ctx.udc['groupinfo'].close()
GroupService.event_manager.add_listener('method_exception_object',
                                               _on_method_exception)
GroupService.event_manager.add_listener('method_exception_object', _on_method_exit)


# Add events to this service:
GroupService.event_manager.add_listener('method_call',
                                            SoapListener.on_method_call_session)
GroupService.event_manager.add_listener('method_call', _on_method_call)
GroupService.event_manager.add_listener('method_call',
                                            auth.on_method_authentication)
GroupService.event_manager.add_listener('method_return_object',
                                            SoapListener.on_method_exit_session)
GroupService.event_manager.add_listener('method_return_object', _on_method_exit)


## Add events to authentication service:
auth.PasswordAuthenticationService.event_manager.add_listener('method_exception_object',
                                               _on_method_exception)
auth.PasswordAuthenticationService.event_manager.add_listener('method_call',
                                            SoapListener.on_method_call_session)

def usage(exitcode=0):
    print """Usage: %s [-p <port number] [-l logfile] [--unencrypted]

Starts up the GroupService webservice on a given port. Please note that config
(cisconf) contains more settings for the service.

  -p
  --port num        Run on alternative port than defined in cisconf.PORT.

  --interface ADDR  What interface the server should listen to. Overrides
                    cisconf.INTERFACE. Default: 0.0.0.0

  -l
  --logfile:        Where to log. Overrides cisconf.LOG_FILE.

  --instance        The individuation instance which should be used. Defaults
                    to what is defined in cisconf.CEREBRUM_CLASS, e.g:
                        Cerebrum.modules.cis.GroupInfo/GroupInfo

  --unencrypted     Don't use HTTPS. All communications goes unencrypted, and
                    should only be used for testing.

  -h
  --help            Show this and quit.
    """
    sys.exit(exitcode)

if __name__=='__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:l:h',
                                   ['port=', 'unencrypted', 'logfile=',
                                    'help', 'instance=', 'interface='])
    except getopt.GetoptError, e:
        print e
        usage(1)

    use_encryption = True
    port        = getattr(cisconf, 'PORT', 0)
    logfilename = getattr(cisconf, 'LOG_FILE', None)
    instance    = getattr(cisconf, 'CEREBRUM_CLASS', None)
    interface   = getattr(cisconf, 'INTERFACE', None)
    log_prefix  = getattr(cisconf, 'LOG_PREFIX', None)

    for opt, val in opts:
        if opt in ('-l', '--logfile'):
            logfilename = val
        elif opt in ('-p', '--port'):
            port = int(val)
        elif opt in ('--unencrypted',):
            use_encryption = False
        elif opt in ('--instance',):
            instance = val
        elif opt in ('--interface',):
            interface = val
        elif opt in ('-h', '--help'):
            usage()
        else:
            print "Unknown argument: %s" % opt
            usage(1)

    # Get the service tier class and give it to the server
    module, classname = instance.split('/', 1)
    mod = dyn_import(module)
    cls = getattr(mod, classname)
    GroupService.cere_class = cls
    # TBD: Should Cerebrum tier be started once per session instead? Takes
    # more memory, but are there benefits we need, e.g. language control?

    private_key_file  = None
    certificate_file  = None
    client_ca         = None
    fingerprints      = None

    services = [auth.PasswordAuthenticationService, GroupService]
    if interface:
        SoapListener.TwistedSoapStarter.interface = interface

    if use_encryption:
        private_key_file  = cisconf.SERVER_PRIVATE_KEY_FILE
        certificate_file  = cisconf.SERVER_CERTIFICATE_FILE
        client_ca         = cisconf.CERTIFICATE_AUTHORITIES
        fingerprints      = getattr(cisconf, 'FINGERPRINTS', None)

        server = SoapListener.TLSTwistedSoapStarter(port = int(port),
                        applications = services,
                        private_key_file = private_key_file,
                        certificate_file = certificate_file,
                        client_ca = client_ca,
                        client_fingerprints = fingerprints,
                        logfile = logfilename,
                        log_prefix = log_prefix)
    else:
        server = SoapListener.TwistedSoapStarter(port = int(port),
                                    applications = services,
                                    logfile = logfilename,
                                    log_prefix = log_prefix)
    GroupService.site = server.site # to make it global and reachable by tier (wrong, I know)
    auth.PasswordAuthenticationService.site = server.site # to make it global and reachable (wrong, I know)

    # We want the sessions to be simple dicts, for now:
    server.site.sessionFactory = SoapListener.SessionCacher
    # Set the timeout to something appropriate:
    SoapListener.SessionCacher.sessionTimeout = 600 # = 10 minutes
    log.msg("DEBUG: GroupServer is using: %s" % instance)
    server.run()
