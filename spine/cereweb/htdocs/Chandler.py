#!/usr/bin/env python

import os
import sys
import cgi
import Cookie
import traceback
import cereweb_path

from Cereweb.Session import Session
from Cereweb.utils import url, redirect
import forgetHTML as html

class Req(object):
    def __init__(self):
        self.headers_out = {}
        self.status = 200

dirname = os.path.dirname(__file__)

def cgi_main():
    args = {}
    for key, value in cgi.parse().items():
        args[key] = type(value) == list and len(value) == 1 and value[0] or value

    req = Req()
    req.session = None
    req.headers_out['Content-Type'] = 'text/html'
    req.headers_out['Pragma'] = 'no-cache'
    req.headers_out['Cache-Control'] = 'max-age=0'

    c = Cookie.SimpleCookie()
    c.load(os.environ.get('HTTP_COOKIE', ''))
    id = c.get('cereweb_id')

    if id:
        try:
            req.session = Session(id.value)
        except IOError, e:
            id = None

    path = os.environ.get('PATH_INFO', '')[1:]

    if not path == 'login':
        if id is None or req.session is None:
            redirect(req, url("/login"))
            path = 'redirected'

    try:
        doc = '<html><body>not found: %s</body></html>' % path
        if '/' in path:
            module, method = path.split('/', 1)
        else:
            module, method = path, 'index'


        if os.path.exists(os.path.join(dirname, '%s.py' % module)):
            module = __import__(module)

            if method[:1].isalpha() and method.isalnum():
                doc = getattr(module, method)(req, **args)

        if req.session:
            req.session.save()
        if id is None and req.session is not None:
            cookie = Cookie.SimpleCookie()
            cookie['cereweb_id'] = req.session.id
            print cookie.output()

        for key, value in req.headers_out.items():
            print '%s: %s' % (key, value)
        if req.status is not None:
            print 'Status:', req.status
        print
        print doc
    except Exception, e:
        for key, value in req.headers_out.items():
            print '%s: %s' % (key, value)
        print
        doc = html.SimpleDocument("unexcepted error")
        doc.body.append(html.Paragraph(str(e), style="color: red;"))
        doc.body.append(html.Paragraph("Path: %s; Args: %s;" % (path, args), style="color: red;"))
        print doc
        print '<pre>'
        traceback.print_exc(file=sys.stdout)
        print os.environ
        print '</pre>'

if __name__ == '__main__': # for cgi
    cgi_main()

# arch-tag: 203bd6c2-22de-4bf2-9d6f-f7c658e1fc55
