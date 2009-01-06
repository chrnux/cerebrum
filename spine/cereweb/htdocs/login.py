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

import urllib
import cherrypy
from omniORB import CORBA

import cgi
from lib import utils
from lib import Messages
from lib.Options import Options
from lib.templates.Login import Login
import config

import SpineClient

class Client(object):
    def __init__(self):
        self.__connect()

    def __call__(self):
        if self.spine:
            return self.spine
        else:
            return self.__connect()

    def __connect(self):
        try:
            self.spine = SpineClient.SpineClient(config=config.conf)
        except CORBA.TRANSIENT, e:
            self.spine = None
        return self.spine

    def disconnect(self):
        self.spine = None

Client = Client()

def login(**vargs):
    # Merge our session with the supplied info.  This way, we can remember
    # what client the user used last time he logged in, etc.
    username = vargs.get('username')
    password = vargs.get('password')
    client = utils.clean_url(vargs.get('client'))
    vargs.update(cherrypy.session)

    redirect = utils.clean_url(vargs.get('redirect'))

    # Make sure the user has chosen a valid client.
    # if not client in ['/user_client', '/index']:
    #     client = '/user_client'

    # IF the user is already logged in, send him to his client.
    if utils.has_valid_session():
        session = cherrypy.session['session']
        # i am not sure if this especially smart... tk.
        utils.redirect(client)

    if vargs.get('msg'):
        Messages.queue_message(
            title='No Title',
            message=vargs.get('msg'),
            is_error=True,
        )

    if username and password:
        cherrypy.session['username'] = username
        cherrypy.session['client'] = client
        Spine = Client()
        
        try:
            if not Spine:
                raise CORBA.TRANSIENT('Could not connect.')

            spine = Spine.connect()
            session = spine.login(username, password)
            #########################################################
            #  this is supposed to be set by cereconf.py
            #session.set_encoding('iso-8859-1')
            #if not session.is_admin():
            #    client = '/user_client'
        except CORBA.TRANSIENT, e:
            Messages.queue_message(
                title="Connection Failed",
                message="Could not connect to the Spine server.  Please contact Orakel.",
                is_error=True,
            )
        except Exception, e:
            Messages.queue_message(
                title="Login Failed",
                message="Incorrect username/password combination.  Please try again.",
                is_error=True,
            )
        else:
            cherrypy.session['session'] = session
            cherrypy.session['timeout'] = session.get_timeout()
            cherrypy.session['spine_encoding'] = session.get_encoding()
            cherrypy.session['options'] = Options(session, username)


            ## Try to find Accept-Charset from web-browser
            default_charset = 'utf-8'
            selected_charset = None
            allowed_charsets = cherrypy.request.headerMap.get('Accept-Charset', '')
            if allowed_charsets:
                charsets = allowed_charsets.split(',')
                for charset in charsets:
                    if charset.strip().lower() == default_charset:
                        selected_charset = default_charset
                ## just pick one...
                if not selected_charset and charsets:
                    selected_charset = charsets[0].strip()
            if not selected_charset:
                selected_charset = default_charset
            cherrypy.session['client_encoding'] = selected_charset
            
            try:
                next = cherrypy.session.pop('next')
                redirect = utils.clean_url(next)
            except KeyError, e:
                pass

            if not redirect or redirect == '/index':
                redirect = client

            utils.redirect(redirect)

    namespace = {
        'username': username,
        'messages': utils.get_messages(),
        'client': client,
    }
    template = Login(searchList=[namespace])
    return template.respond()
login.exposed = True

def logout():
    session = cherrypy.session.get('session')
    if session:
        del cherrypy.session['session']
        session.logout()
    utils.redirect("/login")
logout.exposed = True


# arch-tag: c1c42d44-1800-4608-b215-8a669cf10821
