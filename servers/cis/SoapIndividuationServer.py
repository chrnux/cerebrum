#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010 University of Oslo, Norway
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

import sys
import getopt
import SoapListener

import cerebrum_path
import cereconf
from Cerebrum.modules.cis import Individuation

from soaplib.service import soapmethod
from soaplib.serializers.primitive import String, Integer, Array, Boolean

from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.python.log import err, startLogging

try:
    from twisted.internet import ssl
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

"""
This file provides a SOAP server for the Indivudiation service at UiO.

TODO: Describe ...

TODO: The skeleton of a running server. All the SOAP actions must be
written for this server to do something useful.
"""



class IndividuationServer(SoapListener.BasicSoapServer):
    """
    This class defines the SOAP actions that should be available to
    clients. All those actions are decorated as a soapmethod, defining
    what parameters the methods accept, types and what is returned.
    """

    @soapmethod(String, String, _returns=Array(Array(String)))
    def get_usernames(self, id_type, ext_id):
        """
        Based on id-type and the id, identify a person in Cerebrum and
        return a list of the persons account and their status.

        If person exist but doesn't have any accounts return an empty
        list. I no person match id_type, my_id, throw a ...Exception.
        """
        # TBD: check parameters here?
        accounts = Individuation.get_person_accounts(id_type, ext_id)
        # TBD: decide what data structure to return
        # TBD: which exception do we throw if person doesn't exists
        return accounts
        

    @soapmethod(String, String, String, String, String, _returns=Boolean)
    def generate_token(self, id_type, my_id, username, phone_no, browser_token):
        """
        Send a token by SMS to the persons phone and store the token
        in Cerebrum.

        Return True if the person can be identified and phone_no is
        correct according to Cerebrum. Else return False
        """
        return Individuation.generate_token(id_type, ext_id, username,
                                            phone_no, browser_token)


    @soapmethod(String, String, String, String, String, String, _returns=Boolean)
    def check_token(self, id_type, my_id, username, phone_no, browser_token, token):
        """
        Check the validity of a given token.
        """
        return True


    @soapmethod(String, _returns=Boolean)
    def abort_token(self, token):
        """
        Remove token in from Cerebrum
        """
        return True


    @soapmethod(String, String, String, String, String, String, String, _returns=Boolean)
    def set_password(self, id_type, my_id, username, phone_no, browser_token,
                     token, new_password):
        """
        Set new password for a user if all information is verified and
        the token is still valid.
        """
        return True


    @soapmethod(String, _returns=Boolean)
    def validate_password(self, password):
        """
        Check if a given password is good enough.
        """
        return True

    ##
    ## Hooks for soaplib, used for logging and debugging 
    ##
    def onCall(self, environ):
        '''This is the first method called when this WSGI app is invoked'''
        print "Calling SOAP server from address %s" % environ['REMOTE_ADDR']
        print 'environ:', environ
    

    def onWsdl(self, environ, wsdl):
        '''This is called when a wsdl is requested'''
        print "wsdl requested from address %s" % (environ['REMOTE_ADDR'])
    

    def onMethodExec(self, environ, body, py_params, soap_params):
        '''Called BEFORE the service implementing the functionality is called'''
        print "Calling SOAP action %s from address %s" % (environ['HTTP_SOAPACTION'],
                                                          environ['REMOTE_ADDR'])
        print 'body:', body
        print 'py_params:', py_params
        print 'soap_params:', soap_params
        
    
    def onResults(self, environ, py_results, soap_results):
        '''Called AFTER the service implementing the functionality is called'''
        print 'onResults: '
        print 'py_results:', py_results
        print 'soap_results:', soap_results
    
    
    def onReturn(self, environ, returnString):
        '''Called before the application returns'''
        print 'returnString:', returnString



def usage(exitcode=0):
    print """Usage: %s [-p <port number] [-l logfile] [--unencrypted]
  -p | --port num: run on alternative port (default: ?)
  -l | --logfile: where to log
  --unencrypted: don't use https
  """
    sys.exit(exitcode)

if __name__=='__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:l:',
                                   ['port=', 'unencrypted', 'logfile='])
    except getopt.GetoptError:
        usage(1)

    use_encryption = CRYPTO_AVAILABLE
    port = cereconf.INDIVIDUATION_SERVICE_PORT
    logfile = cereconf.INDIVIDUATION_SERVICE_LOGFILE

    for opt, val in opts:
        if opt in ('-l', '--logfile'):
            logfile = val
        elif opt in ('-p', '--port'):
            port = int(val)
        elif opt in ('--unencrypted',):
            use_encryption = False

    ## TBD: Use Cerebrum logger instead? 
    # Init twisted logger
    log_observer = startLogging(file(logfile, 'w'))
    # Run service
    service = IndividuationServer()
    resource = WSGIResource(reactor, reactor.getThreadPool(), service)
    root = Resource()
    root.putChild('SOAP', resource)
    if use_encryption:
        # TODO: we need to set up SSL properly
        sslcontext = ssl.DefaultOpenSSLContextFactory(
            'privkey.pem',
            'cacert.pem')
        reactor.listenSSL(int(port), Site(root), contextFactory=sslcontext)
    else:
        reactor.listenTCP(int(port), Site(root))
    reactor.run()