
#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
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

import socket
import re
import time
import string

import cerebrum_path
import cereconf
from Cerebrum.Utils import Factory
from Cerebrum import Errors
from Cerebrum import Entity
from Cerebrum import QuarantineHandler


db = Factory.get('Database')()
co = Factory.get('Constants')(db)
account = Factory.get('Account')(db)
person = Factory.get('Person')(db)
quarantine = Entity.EntityQuarantine(db)
ou = Factory.get('OU')(db)
logger = Factory.get_logger("cronjob")

class SocketCom(object):
    """Class for Basic socket communication to connect to the ADserver"""

    p = re.compile('210 OK')

    def __init__(self):
        self._buffer = ""
        self.connect()


    def connect(self):
        try:
            self.sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sockobj.connect((cereconf.NOTES_SERVER_HOST, cereconf.NOTES_SERVER_PORT))
            logger.info("Connecting, starting session %s", now())
            logger.info(">> %s", self.sockobj.recv(8192))
            logger.info("<< Authenticating")
            self.sockobj.send(cereconf.NOTES_PASSWORD)
            self.readline()
        except:
            logger.critical("failed connecting to: %s:%s",
                            cereconf.NOTES_SERVER_HOST, cereconf.NOTES_SERVER_PORT)
            raise


    def send(self, message):
        if(string.find(message,"&pass&")>=0):
           tmp=string.split(message,"&")
           tmp.pop()
           tmp.append("XXXXXXXX")
           tmp=string.join(tmp,"&")
           logger.debug("<< %s", tmp)
        if self.sockobj.send(message) == len(message):
            return True
        return False

    def readline(self, out=True):
        while True:
            eol = self._buffer.find("\n")
            if eol == -1:
                new_data = self.sockobj.recv(8192)
                if not new_data:
                    # End of file.
                    ret = self._buffer
                    self._buffer = ""
                    break
                self._buffer += new_data
            else:
                ret = self._buffer[:eol]
                self._buffer = self._buffer[eol+1:]
                break
        ret=ret.lstrip()
        return ret


    def read(self,out=1):
        received = []
        rec = []
        while 1:
            data = self.sockobj.recv(8196)
            if data[3] != '-': break
            m=self.p.search(data)
            if m: break
            received.append(data)
        received.append(data)
        #process data
        for i in received:
            rec.append(i.strip())
        if out:     
            for elem in rec:
                logger.debug(">> %s", elem)
        return rec    


    def close(self):
        logger.info("Finished, ending session %s", now()) 
        self.sockobj.send("QUIT\n")
        self.sockobj.close()


def get_cerebrum_ou_path(ou_id):
    try:
        ou.clear()
        ou.find(ou_id)
        path = ou.structure_path(co.perspective_sap)
        # Notes can only take 4 OU levels, if there are more, we chop
        # off the more specific levels.  We also don't include the
        # root OU name since it is implicit.
        # "A/B/C/D/E/F" -> ["B", "C", "D", E"]
        return path.split('/')[-5:-1]
    except Errors.NotFoundError:
        logger.warn("Could not find OU with id %s", ou_id)


def chk_quarantine(account_id):
    # Check against quarantine.
    account_disable = 0
    quarantine.clear()
    quarantine.find(account_id)
    quarantines = quarantine.get_entity_quarantine(only_active=True)
    qua = []
    for row in quarantines:
        qua.append(row['quarantine_type'])
    qh = QuarantineHandler.QuarantineHandler(db, qua)
    try:
        if qh.is_locked():
            account_disable += 1
    except KeyError:
        logger.warn("missing QUARANTINE_RULE")
    if account_disable:
        return True


def get_primary_ou(account_id):
    account.clear()
    account.find(account_id)
    acc_types = account.get_account_types()
    if acc_types:
        return acc_types[0]['ou_id']
    return None


def now():
    return time.ctime(time.time())




if __name__ == '__main__':
    pass

# arch-tag: 4ca613c2-1ae7-40cd-b6f6-6eb29724da39
