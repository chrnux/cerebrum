# -*- coding: iso-8859-1 -*-
# Copyright 2003, 2004 University of Oslo, Norway
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

""""""

import os
import re
import sys
import string
import time
import mx

from Cerebrum.Utils import Factory
from Cerebrum.modules import Email
from Cerebrum.modules.EmailLDAP import EmailLDAP

class EmailLDAPUiOMixin(EmailLDAP):
    """Methods specific for UiO."""

    __write_attr__ = ('local_uio_domain',)

    def __init__(self, db):
        self.__super.__init__(db)
        self.local_uio_domain = {}

    spam_act2dig = {'noaction':   '0',
                    'spamfolder': '1',
                    'dropspam':   '2'}
    db_tt2ldif_tt = {'account': 'user',
                     'forward': 'forwardAddress'}         
    _translate_domains = {'UIO_HOST': 'ulrik.uio.no',
                          }
    maildrop = "/uio/mailspool/mail"


    def get_targettype(self, targettype):
        return self.db_tt2ldif_tt.get(str(targettype), str(targettype))


    def get_server_info(self, target, entity, home, path):
        # Find mail-server settings:
        uname = self.acc2name[entity][0]
        sinfo = ""
        if self.targ2server_id.has_key(target):
            type, name = self.serv_id2server[int(self.targ2server_id[target])]
            if type == self.const.email_server_type_nfsmbox:
                # FIXME: we really want to log this
                # self.logger.warn("%s is not on Cyrus, but %s" % (uname, name))
                False # Python needs a statement here.
            elif type == self.const.email_server_type_cyrus:
                sinfo += "IMAPserver: %s\n" % name
        return sinfo


    def _build_addr(self, local_part, domain):
        domain = self._translate_domains.get(domain, domain)
        return '@'.join((local_part, domain))

    
    def list_machines(self, spread):
        disk = Factory.get('Disk')(self._db)
        res = []
        path_pattern = re.compile(r'/(?P<department>[^/]+)/(?P<host>[^/]+)/[^/]+')
        for d in disk.list(spread=spread):
            path = d['path']
            m = path_pattern.match(path)
            if m:
                res.append([m.group('department'), m.group('host')])
        return res


    def read_spam(self):
        mail_spam = Email.EmailSpamFilter(self._db)
        for row in mail_spam.list_email_spam_filters_ext():
            self.targ2spam[int(row['target_id'])] = [
                row['level'], self.spam_act2dig.get(row['code_str'], '0')]

    
    def read_addr(self):
        mail_dom = Email.EmailDomain(self._db)
        mail_addr = Email.EmailAddress(self._db)
        # Handle "magic" domains.
        #   local_part@magic_domain
        # defines
        #   local_part@[all domains with category magic_domains],
        # overriding any entry for that local_part in any of those
        # domains.
        glob_addr = {}
        for dom_catg in (self.const.email_domain_category_uio_globals,):
            domain = str(dom_catg)
            lp_dict = {}
            glob_addr[domain] = lp_dict
            # Fill glob_addr[magic domain][local_part]
            for row in mail_addr.list_email_addresses_ext(domain):
                lp_dict[row['local_part']] = row
            for row in mail_dom.list_email_domains_with_category(dom_catg):
                # Alias glob_addr[domain name] to glob_addr[magic domain],
                # for later "was local_part@domain overridden" check.
                glob_addr[row['domain']] = lp_dict
                # Update dicts 'targ2addr' and 'aid2addr' with the
                # override addresses.
                for lp, row2 in lp_dict.items():
                    # Use 'row', and not 'row2', for domain.  Using 'dom2'
                    # would give us 'UIO_GLOBALS'.
                    addr = self._build_addr(lp, row['domain'])
                    t_id = int(row2['target_id'])
                    self.targ2addr.setdefault(t_id, []).append(addr)
                    # Note: We don't need to update aid2addr here, as
                    # addresses @UIO_GLOBALS aren't allowed to be primary
                    # addresses.
        for row in mail_addr.list_email_addresses_ext():
            lp, dom = row['local_part'], row['domain']
            # If this address is in a domain that is subject to overrides
            # from "magic" domains, and the local_part was overridden, skip
            # this row from being added to targ2addr.
            addr = self._build_addr(lp, dom)
            a_id, t_id = [int(row[x]) for x in ('address_id', 'target_id')]
            self.aid2addr[a_id] = addr
            if glob_addr.has_key(dom) and glob_addr[dom].has_key(lp):
                continue
            self.targ2addr.setdefault(t_id, []).append(addr)
                        
                
    def _validate_primary(self, dom, prim, local_uio_domain):
        if prim in ['pat', 'mons', 'goggins', 'miss', 'smtp', 'mail-mx1',
                    'mail-mx2', 'mail-mx3']:
            self.local_uio_domain[dom] = prim


# arch-tag: 7bb4c2b7-8112-4bd0-85dd-0112db222638
