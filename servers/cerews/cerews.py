#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2009 University of Oslo, Norway
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

import os, sys, socket, time, md5

import cerebrum_path

import cereconf

import Cerebrum.lib
from Cerebrum.lib.cerews.cerews_services import *
from Cerebrum.lib.cerews.SignatureHandler import SignatureHandler
from Cerebrum import Errors
from Cerebrum.modules.bofhd.errors import PermissionDenied
from Cerebrum.modules import Email

from SocketServer import ForkingMixIn

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from ZSI.wstools import logging
from ZSI.ServiceContainer import AsServer
from ZSI.ServiceContainer import ServiceSOAPBinding
from ZSI.ServiceContainer import ServiceContainer
from ZSI.ServiceContainer import SOAPRequestHandler
from ZSI import ParsedSoap, SoapWriter
from ZSI import _get_element_nsuri_name
from ZSI.wstools.Namespaces import OASIS, DSIG

from M2Crypto import SSL
from M2Crypto import X509
from Cerebrum.modules.no.ntnu import bofhd_auth

import time
import cerebrum_path
from Cerebrum.Utils import Factory

from Cerebrum.Entity import EntityQuarantine

from Cerebrum.lib.cerews.dom import DomletteElementProxy
def elementproxy_patch():
    """
    Monkeypatches ZSI to use 4Suite instead of PyXML to write XML
    """
    import ZSI.ServiceContainer as SC
    from ZSI.writer import SoapWriter
    def SoapWriterFactory(*args, **kwargs):
        kwargs['outputclass'] = DomletteElementProxy
        return SoapWriter(*args, **kwargs)
    SC.SoapWriter = SoapWriterFactory
elementproxy_patch()

def int_or_none(i):
    if i is None:
        return None
    else:
        return int(i)

def bool_default(i, default=False):
    if i is None:
        return default
    else:
        return bool(i)

class AuthenticationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class IncrementalError(Errors.CerebrumError):
    """Too large incremental range"""

class QueryError(Exception):
    pass

class BaseQuery(object):
    def __init__(self, db, co):
        self.select = []
        self.tables = []
        self.where = []
        self.order_by = []
        self.binds = {}
        self.distinct = False
        
        self.db = db
        self.co = co
        self._is_used = False
        

    def _execute(self):
        if self._is_used:
            raise QueryError("Query already spent.")
        self._is_used = True
        sql = "SELECT "
        if self.distinct:
            sql += "DISTINCT "
        sql += ",\n".join(self.select)
        sql += " FROM " + "\n".join(self.tables)
        if self.where:
            sql += " WHERE " + " AND ".join(self.where)
        if self.order_by:
            sql += " ORDER BY " + ", ".join(self.order_by)

        return self.db.query(sql, self.binds)
        
class PersonQuery(BaseQuery):
    def __init__(self, db, co, personspread=None, accountspread=None, changelog_id=None):
        BaseQuery.__init__(self, db, co)
        self.tables = ["person_info"]
        self.select = ["person_info.person_id AS id"]
        self.where = ["(person_info.deceased_date IS NULL)"]
        self._changelog_id = changelog_id

        if personspread:
            self._set_spread(personspread)
        if accountspread:
            self._set_accountspread(accountspread)

        if changelog_id:
            self._set_changelogid(changelog_id)

    def search_data(self, include_keycard=False):
        self._include_data()
        if include_keycard:
            self._include_keycard()

        return self._execute()

    def search_affiliations(self):
        self._include_account_priority()
        
        return self._execute()
    
    def _set_changelogid(self, changelog_id):
        self.tables.append("""JOIN change_log
                   ON (change_log.subject_entity = person_info.person_id
                     AND change_log.change_id > :changelog_id)""")
        self.order_by.append("change_log.change_id ASC")
        self.binds["changelog_id"] = changelog_id

    def _set_spread(self, spread):
        self.tables.append("""JOIN entity_spread person_spread
        ON (person_spread.spread = :person_spread
          AND person_spread.entity_id = person_info.person_id)""")
        self.binds["person_spread"] = spread
        
    def _set_accountspread(self, spread):
        self.select.append("accounts.account_id AS spread_account_id")
        self.tables.append("""JOIN account_info accounts
          ON (accounts.owner_id = person_info.person_id)
        JOIN entity_spread account_spread
          ON (account_spread.spread = :account_spread
            AND account_spread.entity_id = accounts.account_id)""")
        self.where.append("""accounts.expire_date > [:now]
          OR accounts.expire_date IS NULL""")
        self.binds["account_spread"] = spread
    
    def _include_data(self):
        self.select += [
            "person_info.export_id AS export_id",
            "person_full_name.name AS full_name",
            "person_first_name.name AS first_name",
            "person_last_name.name AS last_name",
            "person_work_title.name AS work_title",
            "contact_email.contact_value AS email",
            "contact_url.contact_value AS url",
            "contact_phone.contact_value AS phone",
            "person_info.birth_date AS birth_date",
            "person_nin.external_id AS nin",
            "entity_address.address_text AS address_text",
            "entity_address.postal_number AS postal_number",
            "entity_address.city AS city"
            ]

        self.tables.append("""
    LEFT JOIN entity_external_id person_nin
    ON (person_nin.entity_id = person_info.person_id
      AND person_nin.id_type = :externalid_nin
      AND person_nin.source_system = :nin_source )
    LEFT JOIN person_name person_first_name
      ON ((person_first_name.person_id = person_info.person_id)
        AND (person_first_name.source_system = :system_cached)
        AND (person_first_name.name_variant = :name_first))
    LEFT JOIN person_name person_last_name
    ON ((person_last_name.person_id = person_info.person_id)
      AND (person_last_name.source_system = :system_cached)
      AND (person_last_name.name_variant = :name_last))
    LEFT JOIN person_name person_full_name
    ON ((person_full_name.person_id = person_info.person_id)
      AND (person_full_name.source_system = :system_cached)
      AND (person_full_name.name_variant = :name_full))
    LEFT JOIN person_name person_display_name
    ON ((person_display_name.person_id = person_info.person_id)
      AND (person_display_name.source_system = :system_cached)
      AND (person_display_name.name_variant = :name_display))
    LEFT JOIN person_name person_personal_title
    ON ((person_personal_title.person_id = person_info.person_id)
      AND (person_personal_title.source_system = :system_cached)
      AND (person_personal_title.name_variant = :name_personal_title))
    LEFT JOIN person_name person_work_title
    ON ((person_work_title.person_id = person_info.person_id)
      AND (person_work_title.source_system = :system_cached)
      AND (person_work_title.name_variant = :name_work_title))
    LEFT JOIN entity_contact_info contact_email
    ON (contact_email.entity_id = person_info.person_id
      AND contact_email.contact_type = :contact_email
      AND contact_email.source_system = :system_bdb)
    LEFT JOIN entity_contact_info contact_url
    ON (contact_url.entity_id = person_info.person_id
      AND contact_url.contact_type = :contact_url
      AND contact_url.source_system = :system_cached) 
    LEFT JOIN entity_contact_info contact_phone
    ON (contact_phone.entity_id = person_info.person_id
      AND contact_phone.contact_type = :contact_phone
      AND contact_phone.source_system = :system_cached) 
    LEFT JOIN entity_address entity_address
    ON (entity_address.entity_id = person_info.person_id
      AND entity_address.source_system = :address_source
      AND entity_address.address_type = :contact_post_address)""")

        self.binds["externalid_nin"] = self.co.externalid_fodselsnr
        self.binds["nin_source"] = self.co.system_bdb
        self.binds["system_cached"] = self.co.system_cached
        self.binds["system_bdb"] = self.co.system_bdb
        self.binds["address_source"] = self.co.system_fs
        self.binds["name_first"] = self.co.name_first
        self.binds["name_last"] = self.co.name_last
        self.binds["name_full"] = self.co.name_full
        self.binds["name_display"] = self.co.name_display
        self.binds["name_personal_title"] = self.co.name_personal_title
        self.binds["name_work_title"] = self.co.name_work_title
        self.binds["contact_email"] = self.co.contact_email
        self.binds["contact_url"] = self.co.contact_url
        self.binds["contact_phone"] = self.co.contact_phone
        self.binds["contact_email"] = self.co.contact_email
        self.binds["contact_post_address"] = self.co.address_post

    def _include_keycard(self):
        self.select.append("keycard_employee.external_id AS keycardid0")
        self.select.append("keycard_student.external_id AS keycardid1")
        self.tables.append("""LEFT JOIN entity_external_id keycard_employee
            ON (keycard_employee.entity_id = person_info.person_id
              AND keycard_employee.id_type = :keycard_employee
              AND keycard_employee.source_system = :keycard_source)
            LEFT JOIN entity_external_id keycard_student
            ON (keycard_student.entity_id = person_info.person_id
              AND keycard_student.id_type = :keycard_student
              AND keycard_student.source_system = :keycard_source)""")
        self.binds["keycard_source"] = self.co.system_kjernen
        self.binds["keycard_employee"] = self.co.externalid_keycardid_employee
        self.binds["keycard_student"] = self.co.externalid_keycardid_student

    def _include_account_priority(self):
        self.binds["account_namespace"] = self.co.account_namespace
        self.binds["authentication_method"] = self.co.auth_type_ssha
        self.select.append("account_type.ou_id AS ou_id")
        self.select.append("account_type.affiliation AS affiliation")
        self.select.append("account_type.account_id AS account_id")
        self.select.append("affiliation.status AS status")
        self.select.append("account_name.entity_name AS account_name")
        self.select.append("account_type.priority AS priority")
        self.select.append("account_authentication.auth_data AS account_passwd")
        self.tables.append("""JOIN account_type account_type
          ON (account_type.person_id = person_info.person_id)""")
        self.tables.append("""JOIN person_affiliation_source affiliation
          ON (affiliation.person_id = account_type.person_id
              AND affiliation.ou_id = account_type.ou_id
              AND affiliation.affiliation = account_type.affiliation)""")
        self.tables.append("""JOIN account_info account_info
          ON (account_info.account_id = account_type.account_id)""")
        self.tables.append("""JOIN entity_name account_name
          ON (account_name.entity_id = account_info.account_id
             AND account_name.value_domain = :account_namespace)""")
        self.tables.append("""LEFT JOIN account_authentication
          ON (account_authentication.method = :authentication_method
             AND account_authentication.account_id = account_info.account_id)""")
        self.where.append("affiliation.deleted_date IS NULL")
        self.where.append("""account_info.expire_date > [:now]
          OR account_info.expire_date IS NULL""")

    def _include_account_data(self):
        self.binds["account_namespace"] = self.co.account_namespace
        self.binds["authentication_method"] = self.co.auth_type_ssha
        self.select.append("account_info.account_id AS account_id")
        self.select.append("account_name.entity_name AS account_name")
        self.select.append("account_authentication.auth_data AS account_passwd")
        self.tables.append("""JOIN entity_name account_name
          ON (account_name.entity_id = account_info.account_id
             AND account_name.value_domain = :account_namespace)""")
        self.tables.append("""LEFT JOIN account_authentication
          ON (account_authentication.method = :authentication_method
             AND account_authentication.account_id = account_info.account_id)""")

# Merge this with Account.search()....

class AccountQuery(BaseQuery):
    def __init__(self, db, co, spread=None, changelog_id=None):
        BaseQuery.__init__(self, db, co)
        self.tables = ["account_info"]
        self.select = ["account_info.account_id AS id"]
        self.where=["""(account_info.expire_date > now()
              OR account_info.expire_date IS NULL)"""]
        if changelog_id:
            self._set_changelogid(changelog_id)
            
        self.tables.append("""
            JOIN entity_spread account_spread
            ON (account_spread.spread = :account_spread
                AND account_spread.entity_id = account_info.account_id)""")
        self.binds['account_spread'] = spread
        
    def search_data(self, auth_type=None, include_affiliations=False,
                    include_posix=True, include_owner=True,
                    include_home=True):
        if auth_type is None:
            auth_type = self.co.auth_type_md5_crypt

        self._include_data()
        self._set_auth_type(auth_type)
        if include_posix:
            self._include_posix()
        if include_owner:
            self._include_owner()
        if include_home:
            self._include_home()
        return self._execute()

    def search_affiliations(self):
        self._include_account_priority()

        return self._execute()

    def _set_changelogid(self, changelog_id):
        self.tables.append("""JOIN change_log
         ON (change_log.subject_entity = account_info.account_id
            AND change_log.change_id > :changelog_id)""")
        #self.order_by.append("change_log.change_id ASC")
        self.distinct = True
        self.binds['changelog_id'] = changelog_id

    def _include_home(self):
        self.select.append("homedir.home AS home")
        self.select.append("disk_info.path AS disk_path")
        self.select.append("disk_host_name.entity_name AS disk_host")
        self.tables.append("""
        LEFT JOIN account_home
          ON (account_home.spread = :account_spread
            AND account_home.account_id = account_info.account_id)
        LEFT JOIN homedir
          ON (homedir.homedir_id = account_home.homedir_id)
        LEFT JOIN disk_info
          ON (disk_info.disk_id = homedir.disk_id)
        LEFT JOIN entity_name disk_host_name
          ON (disk_host_name.entity_id = disk_info.host_id
            AND disk_host_name.value_domain = :host_namespace)
        """)
        self.binds['host_namespace'] = int(self.co.host_namespace)


    def _include_posix(self):
        self.select.append("""
        posix_user.gecos AS gecos,
        posix_user.posix_uid AS posix_uid,
        posix_shell.shell AS shell,
        posix_shell.code_str AS shell_name,
        posix_group.posix_gid AS posix_gid,
        group_name.entity_name AS primary_group
        """)
        self.tables.append("""
        LEFT JOIN posix_user
          ON (account_info.account_id = posix_user.account_id)
        LEFT JOIN posix_shell_code posix_shell
          ON (posix_shell.code = posix_user.shell)
        LEFT JOIN group_info
          ON (group_info.group_id = posix_user.gid)
        LEFT JOIN posix_group
          ON (group_info.group_id = posix_group.group_id)
        LEFT JOIN entity_name group_name
          ON (group_info.group_id = group_name.entity_id
            AND group_name.value_domain = :group_namespace)
        """)
        self.binds['group_namespace'] = int(self.co.group_namespace)
        
    def _include_owner(self):
        self.select.append("""
        owner_group_name.entity_name AS owner_group_name,
        person_name.name AS full_name
        """)
        self.tables.append("""
        LEFT JOIN group_info owner_group_info
          ON (owner_group_info.group_id = account_info.owner_id)
        LEFT JOIN person_info
          ON (person_info.person_id = account_info.owner_id)
        LEFT JOIN entity_name owner_group_name
          ON (owner_group_name.entity_id = owner_group_info.group_id
            AND owner_group_name.value_domain = :group_namespace)
        LEFT JOIN person_name
          ON (person_name.person_id = person_info.person_id
            AND person_name.name_variant = :name_display
            AND person_name.source_system = :system_cached)
        """)
        self.binds['group_namespace'] = int(self.co.group_namespace)
        self.binds['name_display'] = int(self.co.name_display)
        self.binds['system_cached'] = int(self.co.system_cached)

    def _set_auth_type(self, auth_type):
        self.select.append("account_authentication.auth_data AS passwd")
        self.tables.append("""
        LEFT JOIN account_authentication
          ON (account_authentication.method = :authentication_method
            AND account_authentication.account_id = account_info.account_id)""")
        self.binds['authentication_method'] = auth_type

    def _include_data(self):
        self.select.append("account_info.owner_id AS owner_id")
        self.select.append("account_name.entity_name AS name")
        self.tables.append("""
        JOIN entity_name account_name
        ON (account_info.account_id = account_name.entity_id
            AND account_name.value_domain = :account_namespace)""")
        self.binds['account_namespace'] = int(self.co.account_namespace)
        
    def _include_account_priority(self):
        self.select.append("account_type.ou_id AS ou_id")
        self.select.append("account_type.affiliation AS affiliation")
        self.select.append("account_type.priority AS priority")
        self.tables.append("""JOIN account_type account_type
          ON (account_type.account_id = account_info.account_id)""")

# Groups -- merge into Group.search()
def search_groups(group, group_spread, changelog_id=None):
    co=group.const
    db=group._db
    
    posix=True

    select=["group_info.group_id AS id",
            "group_name.entity_name AS name"]
    tables=["group_info"]
    where = ["((group_info.expire_date > now() OR group_info.expire_date IS NULL)",
             "(group_info.visibility = :group_visibility_all))"]

    binds={'group_visibility_all': co.group_visibility_all}
    binds['group_spread'] = group_spread
    order_by=""
    
    if changelog_id is not None:
        tables.append("""JOIN change_log
          ON (change_log.subject_entity = group_info.group_id
            AND change_log.change_id > :changelog_id)""")
        order_by=" ORDER BY change_log.change_id"
        binds['changelog_id'] = changelog_id

    tables.append("""
      JOIN entity_spread group_spread
      ON (group_spread.spread = :group_spread
        AND group_spread.entity_id = group_info.group_id)
      JOIN entity_name group_name
        ON (group_name.entity_id = group_info.group_id)""")
      
    if posix:
        select += ["posix_group.posix_gid AS posix_gid"]
        tables.append("""LEFT JOIN posix_group
          ON (posix_group.group_id = group_info.group_id)""")
        
    sql = "SELECT " + ",\n".join(select)
    sql += " FROM " + "\n".join(tables)
    sql += " WHERE " + " AND ".join(where)
    sql += order_by
    
    return db.query(sql, binds)



def search_ous(db, co, changelog_id=None):
    stedkode=True
    contactinfo=True
    select=["ou_info.ou_id AS id",
            "ou_info.name AS name",
            "ou_info.acronym AS acronym",
            "ou_info.short_name AS short_name",
            "ou_info.display_name AS display_name",
            "ou_info.sort_name AS sort_name",
            "ou_structure.parent_id AS parent_id",
            ]
    tables = ["ou_info"]
    order_by=""
    binds={"perspective": co.perspective_kjernen}

    if changelog_id is not None:
        tables.append("""JOIN change_log
         ON (change_log.subject_entity = ou_info.ou_id
           AND change_log.change_id > :changelog_id)""")
        order_by=" ORDER BY change_log.change_id"
        binds["changelog_id"]=changelog_id

    tables.append("""JOIN ou_structure
      ON (ou_structure.ou_id = ou_info.ou_id
        AND ou_structure.perspective = :perspective)""")
                  

    if stedkode:
        tables.append("""LEFT JOIN stedkode
          ON (stedkode.ou_id = ou_info.ou_id)
        LEFT JOIN stedkode stedkode_parent
          ON (stedkode_parent.ou_id = ou_structure.parent_id)""")

        select.append("""to_char(stedkode.landkode,'FM000')||
             to_char(stedkode.institusjon,'FM00000')||
             to_char(stedkode.fakultet,'FM00')||
             to_char(stedkode.institutt,'FM00')||
             to_char(stedkode.avdeling,'FM00') AS stedkode""")
        select.append("""to_char(stedkode_parent.landkode,'FM000')||
             to_char(stedkode_parent.institusjon,'FM00000')||
             to_char(stedkode_parent.fakultet,'FM00')||
             to_char(stedkode_parent.institutt,'FM00')||
             to_char(stedkode_parent.avdeling,'FM00') AS parent_stedkode""")
             
    if contactinfo:
        select+=["contact_email.contact_value AS email",
                 "contact_url.contact_value AS url",
                 "contact_phone.contact_value AS phone",
                 "contact_fax.contact_value AS fax",
                 "contact_address.contact_value AS post_address",
                 ]
        tables.append("""LEFT JOIN entity_contact_info contact_email
          ON (contact_email.entity_id = ou_info.ou_id
            AND contact_email.source_system = :system_kjernen
            AND contact_email.contact_type = :contact_email)
        LEFT JOIN entity_contact_info contact_url
          ON (contact_url.entity_id = ou_info.ou_id
            AND contact_url.source_system = :system_kjernen
            AND contact_url.contact_type = :contact_url)
        LEFT JOIN entity_contact_info contact_phone
          ON (contact_phone.entity_id = ou_info.ou_id
            AND contact_phone.source_system = :system_kjernen 
            AND contact_phone.contact_type = :contact_phone)
        LEFT JOIN entity_contact_info contact_fax
          ON (contact_fax.entity_id = ou_info.ou_id
            AND contact_fax.source_system = :system_kjernen
            AND contact_fax.contact_type = :contact_fax)
        LEFT JOIN entity_contact_info contact_address
          ON (contact_address.entity_id = ou_info.ou_id
            AND contact_address.source_system = :system_kjernen
            AND contact_address.contact_type = :contact_post_address)""")
        binds["contact_url"]=co.contact_url
        binds["contact_email"]=co.contact_email
        binds["contact_phone"]=co.contact_phone
        binds["contact_fax"]=co.contact_fax
        binds["contact_post_address"]=co.address_post
        binds["system_cached"]=co.system_cached
        binds["system_kjernen"]=co.system_kjernen

    sql = "SELECT " + ",\n".join(select)
    sql += " FROM " + "\n".join(tables)
    sql += order_by
    
    return db.query(sql, binds)




class group_members:
    def __init__(self, group, types=None):
        self.co=group.const
        self.db=group._db
        
        if types is not None:
            self.types=types
        else:
            self.types=[int(self.co.entity_account)]
        
        memberships=self.db.query("""
        SELECT gm.group_id AS group_id,
        gm.member_type AS member_type,
        gm.member_id AS member_id,
        en.entity_name AS member_name
        FROM group_member gm
        LEFT OUTER JOIN entity_name en
           ON (en.entity_id = gm.member_id)
        WHERE
        en.value_domain = CASE
        WHEN gm.member_type=:entity_account THEN :account_namespace
        WHEN gm.member_type=:entity_group   THEN :group_namespace
        WHEN gm.member_type=:entity_host    THEN :host_namespace
        END
        """, { 'entity_account': int(self.co.entity_account),
               'entity_group': int(self.co.entity_group),
               'entity_host': int(self.co.entity_host),
               'account_namespace': int(self.co.account_namespace),
               'group_namespace': int(self.co.group_namespace),
               'host_namespace': int(self.co.host_namespace),
               })
        
        self.group_members={}
        self.member_names={}
        for m in memberships:
            if not m['group_id'] in self.group_members:
                self.group_members[m['group_id']]=[]
            self.group_members[m['group_id']].append((m['member_type'],
                                                      m['member_id']))
            self.member_names[m['member_id']]=m['member_name']

    def _get_members(self, id, groups, members, type, types):
        if type==None or type==self.co.entity_group:
            if not id in self.group_members:
                return 
            for t, i in self.group_members[id]:
                if not i in groups:
                    groups.add(i)
                    self._get_members(i, groups, members, t, types)
        elif type in types:
            members.append(id)
    
    def get_members(self, id, type=None, types=None):
        members=[]
        groups=set()
        if types==None: types=self.types
        self._get_members(id, groups, members, type, types)
        return members
    
    def get_members_name(self, id):
        return [self.member_names[i] for i in self.get_members(id)]
    def addto_group(self, d):
        d['members']=self.get_members_name(d['id'])
        return d


def search_aliases(db, co, emailserver, changelog_id=None):
    select=["email_address.local_part AS local_part",
            "email_domain.domain AS domain",
            "email_target.target_id AS target_id",
            "email_target.target_type AS target_type",
            "email_address.address_id AS address_id",
            "email_primary_address.address_id AS primary_address_id",
            "primary_address.local_part AS primary_address_local_part",
            "primary_address_domain.domain AS primary_address_domain",
            "host_name.entity_name AS server_name",
            "account_info.account_id AS account_id",
            "account_name.entity_name AS account_name",
            ]
    tables=["email_address"]
    order_by=""
    where=[]
    
    if changelog_id is not None:
        tables.append("""JOIN change_log
        ON (change_log.subject_entity = email_address.address_id
            AND change_log.change_id > :changelog_id)""")
        order_by=" ORDER BY change_log.change_id"
        binds["changelog_id"]=changelog_id
        
    tables.append("""JOIN email_domain
  ON (email_domain.domain_id = email_address.domain_id)
JOIN email_target
  ON (email_address.target_id = email_target.target_id)
LEFT JOIN email_primary_address
  ON (email_primary_address.target_id = email_target.target_id)
LEFT JOIN entity_name host_name
  ON (host_name.entity_id = email_target.server_id
      AND host_name.value_domain = :host_namespace)
LEFT JOIN account_info
  ON (account_info.account_id = email_target.target_entity_id)
LEFT JOIN entity_name account_name
  ON (account_name.entity_id = account_info.account_id
      AND account_name.value_domain = :account_namespace)
LEFT JOIN email_address primary_address
  ON (primary_address.address_id = email_primary_address.address_id)
LEFT JOIN email_domain primary_address_domain
  ON (primary_address_domain.domain_id = primary_address.domain_id)
""")
    binds={
        'account_namespace': co.account_namespace,
        'host_namespace': co.host_namespace,
        }

    if emailserver is not None:
        where.append("email_target.server_id = :emailserver_id")
        binds["emailserver_id"] = emailserver.entity_id
        
        
    
    sql = "SELECT " + ",\n".join(select)
    sql += " FROM " + "\n".join(tables)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += order_by

    return db.query(sql, binds)


def search_homedirs(host, status):
    include_posix=True
    co=host.const
    db=host._db

    binds={'account_namespace': co.account_namespace}
    binds['status']=int(co.AccountHomeStatus(status))

    binds['host_id']=host.entity_id

    select =["homedir.homedir_id AS homedir_id",
             "homedir.home AS home",
             "disk.path AS disk_path",
             "account_name.entity_name AS account_name"]
    tables=["""disk_info disk
      JOIN homedir homedir ON (homedir.disk_id = disk.disk_id)
      LEFT JOIN entity_name account_name
        ON (account_name.entity_id = homedir.account_id
          AND account_name.value_domain = :account_namespace)
    """]
    where=["homedir.status = :status", "disk.host_id = :host_id"]

    if include_posix:
        select+=["posix_user.posix_uid AS posix_uid",
                 "posix_group.posix_gid AS posix_gid"]
        tables.append("""
          LEFT JOIN posix_user posix_user
            ON (posix_user.account_id = homedir.account_id)
          LEFT JOIN posix_group posix_group
            ON (posix_group.group_id = posix_user.gid)
        """)

    sql = "SELECT " + ",\n".join(select)
    sql += " FROM " + "\n".join(tables)
    sql += " WHERE " + " AND ".join(where)
    return db.query(sql, binds)

class quarantines:    
    def __init__(self, db, co):
        quarantines = {}
        quarantines_has = quarantines.has_key
        eq = EntityQuarantine(db)
        for quarantine in eq.list_entity_quarantines(only_active=True):
            id = quarantine["entity_id"]
            qtype = str(co.Quarantine(quarantine["quarantine_type"]))
            
            if quarantines_has(id):
                quarantines[id].append(qtype)
            else:
                quarantines[id] = [qtype]
        self.quarantines = quarantines

    def get_quarantines(self, id):
        return self.quarantines.get(id, [])


class DTO(object):
    def __init__(self, row, atypes):
        self._attrs = {}
        for key, value in row.dict().items():
            if key in atypes:
                atype = atypes[key]
                if value is not None:
                    self._attrs[key] = value

class GroupDTO(DTO):
    def __init__(self, row, atypes):
        super(GroupDTO, self).__init__(row, atypes)

class AccountDTO(DTO):
    def __init__(self, row, atypes, account):
        super(AccountDTO, self).__init__(row, atypes)
        homedir = account.resolve_homedir(
            account_name=row['name'],
            disk_path=row['disk_path'],
            home=row['home'])

        # None gets encoded as the string None which causes problems for the
        # clients.  Fix this by replacing None with the empty string instead.
        self._attrs["homedir"] = homedir or ''
        # TDB: extend get_gecos() to do this job.
        if not row["gecos"]:
            if row["full_name"]:
                self._attrs["gecos"] = row["full_name"]
            elif row["owner_group_name"]:
                self._attrs["gecos"] = "%s user (%s)" % (
                    row["name"], row["owner_group_name"])
            else:
                self._attrs["gecos"] = "%s user" % row["name"]

class PersonDTO(DTO):
    def __init__(self, row, atypes):
        super(PersonDTO, self).__init__(row, atypes)

class OUDTO(DTO):
    def __init__(self, row, atypes):
        super(OUDTO, self).__init__(row, atypes)

class AliasDTO(DTO):
    def __init__(self, row, atypes):
        super(AliasDTO, self).__init__(row, atypes)

class HomedirDTO(DTO):
    def __init__(self, row, atypes, account):
        super(HomedirDTO, self).__init__(row, atypes)
        self._attrs["homedir"] = account.resolve_homedir(
            account_name=row['account_name'],
            disk_path=row['disk_path'],
            home=row['home'])

class AffiliationDTO(DTO):
    def __init__(self, row, co):
        self._attrs = {}
        self._attrs['affiliation'] = str(co.PersonAffiliation(row['affiliation']))
        self._attrs['ou_id'] = row['ou_id']
        if row.has_key('status'):
            self._attrs['status'] = co.PersonAffStatus(row['status']).str

def get_node_value(node):
    if not node:
        return None
    value = None
    valueNode = node._get_firstChild()
    if valueNode:
        value = valueNode._get_nodeValue()
    if value:
        value.strip()
    return value
 
def get_element(elements, namespace, localname):
    for elt in elements:
        ns, name = _get_element_nsuri_name(elt)
        if ns == namespace and name == localname:
            return elt
    return None

def get_auth_values(ps):

    headerElements = ps.GetMyHeaderElements()
    securityElement = get_element(headerElements, OASIS.WSSE, 'Security')
    if not securityElement:
        raise RuntimeError('Unauthorized, missing Security-element in header')

    secChildren = securityElement._get_childNodes()
    if len(secChildren) == 0:
        raise RuntimeError('Unauthorized, Security-element has no children')
    
    usernameToken = get_element(secChildren, OASIS.WSSE, 'UsernameToken')
    if not usernameToken:
        raise RuntimeError('Unauthorized, UsernameToken not present')

    tokenChildren = usernameToken._get_childNodes()
    if len(tokenChildren) == 0:
        raise RuntimeError('Unauthorized, UsernameToken has no children')

    username = get_node_value(get_element(tokenChildren, OASIS.WSSE,
                                'Username'))
    if not username:
        raise RuntimeError('Unauthorized, Username not present')

    password = get_node_value(get_element(tokenChildren, OASIS.WSSE,
                                'Password'))
    if not password:
        raise RuntimeError('Unauthorized, Password not present')

    created = get_node_value(get_element(tokenChildren, OASIS.UTILITY,
                                'Created'))
    if not created:
        raise RuntimeError('Unauthorized, Created not present')
    return username, password, created

def check_created(created):
    gmCreated= time.strptime(created, '%Y-%m-%dT%H:%M:%SZ')
    ## allow timeout up to 10 secs.
    auth_timeout = getattr(cereconf, "CEREWS_AUTH_TIMEOUT", 600)
    gmNow = time.gmtime((time.time() - auth_timeout))
    if gmCreated < gmNow:
        raise RuntimeError('Unauthorized, UsernameToken is expired')
    
def check_username_password(db, username, password):
    account=Factory.get("Account")(db)
    try:
        account.find_by_name(str(username))
    except Errors.NotFoundError:
        raise AuthenticationError('Unauthorized, wrong username or password')
    if not account.verify_auth(password):
        raise AuthenticationError('Unauthorized, wrong username or password')
    return account.entity_id


def authenticate(db, ps):
    debug = False
    username, password, created = get_auth_values(ps)
    check_created(created)
    try:
        operator_id = check_username_password(db, username, password)
        logger.info("Login succeeded for user=%s" % username)
    except AuthenticationError, e:
        logger.warning("Login failed for user=%s" % username)
        raise
    return operator_id, username


def format_args(request):
    args={}
    for attr in dir(request):
        if attr[0] == "_" and attr[1] != "_":
            args[attr[1:]] = getattr(request, attr)
    return ", ".join(["%s=%s" % (k, repr(v)) for k,v in args.items()])

def logmethod(requesttype):
    def reallogmethod(fn):
        def wrapper(self, ps):
            db = Factory.get("Database")(client_encoding='UTF-8')
            request = ps.Parse(requesttype.typecode)
            operator_id, user_name = authenticate(db, ps)
            args = format_args(request)
            logger.info("Running %s(%s) user=%s" % (
                    fn.__name__, args, user_name))
            try:
                result=fn(self, db, operator_id, request)
            except PermissionDenied, e:
                logger.warning("Authentication failed %s(%s) user=%s" % (
                        fn.__name__, args, user_name))
                raise
            except Exception, e:
                logger.warning("Operation failed %s(%s) user=%s: %s" % (
                        fn.__name__, args, user_name, repr(e)))
                raise
            return result
        wrapper.__name__ = fn.__name__
        return wrapper
    return reallogmethod


class cerews(ServiceSOAPBinding):
    #_wsdl = "".join(open("cerews.wsdl").readlines())
    soapAction = {}
    root = {}

    def check_incremental(self, db, incremental_from):
        if incremental_from is not None:
            last=db.get_last_changelog_id()
            db.rollback()
            incr_max = getattr(cereconf, "CEREWS_INCREMENTAL_MAX", 1000)
            if last - incremental_from > incr_max:
                raise IncrementalError()
            return last
        return None

    def __init__(self, post='/', **kw):
        ServiceSOAPBinding.__init__(self, post)

    @logmethod(getChangelogidRequest)
    def get_changelogid(self, db, operator_id, request):
        id = db.get_last_changelog_id()
        db.rollback()
        return getChangelogidResponse(id)

    @logmethod(setHomedirStatusRequest)
    def set_homedir_status(self, db, operator_id, request):
        db.cl_init(change_program="cerews")
        co=Factory.get("Constants")()
        account=Factory.get("Account")(db)
        disk=Factory.get("Disk")(db)
        auth=bofhd_auth.BofhdAuth(db)

        status_str = str(request._status)
        homedir_id = int(request._homedir_id)

        response = setHomedirStatusResponse()

        status=int(co.AccountHomeStatus(status_str))
        account.clear()
        r=account.get_homedir(homedir_id)
        
        if r["disk_id"] is None:
            host_id = None
        else:
            disk.clear()
            disk.find(r["disk_id"])
            host_id = disk.host_id

        auth.can_set_homedir_status(operator_id, host_id, status_str)

        account.find(r['account_id'])
        account.set_homedir(current_id=homedir_id, status=status)
        db.commit()

        return response

    @logmethod(getHomedirsRequest)
    def get_homedirs(self, db, operator_id, request):
        co=Factory.get("Constants")()
        host=Factory.get("Host")(db)
        account=Factory.get("Account")(db)
        auth=bofhd_auth.BofhdAuth(db)
        
        status = str(request._status)
        hostname = str(request._hostname)

        host.clear()
        host.find_by_name(hostname)
        auth.can_syncread_homedir(operator_id, host.entity_id)

        response = getHomedirsResponse()

        atypes = response.typecode.ofwhat[0].attribute_typecode_dict
        
        response._homedir = []
        for row in search_homedirs(host, status):
            h=HomedirDTO(row, atypes, account)
            response._homedir.append(h)
        db.rollback()
        
        return response

    @logmethod(getAliasesRequest)
    def get_aliases(self, db, operator_id, request):
        co = Factory.get("Constants")()
        auth = bofhd_auth.BofhdAuth(db)

        incremental_from = int_or_none(request._incremental_from)

        if request._emailserver is None:
            emailserver = None
        else:
            emailserver = Email.EmailServer(db)
            emailserver.clear()
            emailserver.find_by_name(str(request._emailserver))
        
        auth.can_syncread_alias(operator_id, emailserver)

        self.check_incremental(db, incremental_from)

        response = getAliasesResponse()
        atypes = response.typecode.ofwhat[0].attribute_typecode_dict

        response._alias = []
        for row in search_aliases(db, co, emailserver, incremental_from):
            a=AliasDTO(row, atypes)
            response._alias.append(a)
        db.rollback()

        return response

    @logmethod(getOUsRequest)
    def get_ous(self, db, operator_id, request):
        co=Factory.get("Constants")()
        auth=bofhd_auth.BofhdAuth(db)

        auth.can_syncread_ou(operator_id)
        incremental_from = int_or_none(request._incremental_from)
        self.check_incremental(db, incremental_from)

        response = getOUsResponse()
        atypes = response.typecode.ofwhat[0].attribute_typecode_dict

        response._ou=[]
        q=quarantines(db, co)
        for row in search_ous(db, co, incremental_from):
            o=OUDTO(row, atypes)
            o._quarantine = q.get_quarantines(row['id'])
            response._ou.append(o)
        db.rollback()

        return response
        

    @logmethod(getGroupsRequest)
    def get_groups(self,  db, operator_id, request):
        co=Factory.get("Constants")()
        group=Factory.get("Group")(db)
        auth=bofhd_auth.BofhdAuth(db)

        groupspread = co.Spread(str(request._groupspread))
        accountspread = co.Spread(str(request._accountspread))
        incremental_from = int_or_none(request._incremental_from)
        self.check_incremental(db, incremental_from)

        auth.can_syncread_group(operator_id, groupspread)

        response = getGroupsResponse()
        atypes = response.typecode.ofwhat[0].attribute_typecode_dict
        
        response._group=[]
        members=group_members(group)
        q=quarantines(db, co)
        for row in search_groups(group, groupspread, incremental_from):
            g=GroupDTO(row, atypes)
            g._member = members.get_members_name(row['id'])
            g._quarantine = q.get_quarantines(row['id'])
            response._group.append(g)
        db.rollback()

        return response

    @logmethod(getAccountsRequest)
    def get_accounts(self, db, operator_id, request):
        co=Factory.get("Constants")()
        account=Factory.get("Account")(db)
        auth=bofhd_auth.BofhdAuth(db)

        accountspread = co.Spread(str(request._accountspread))
        auth_type = co.Authentication(str(request._auth_type))
        include_affiliations = bool_default(request._include_affiliations,
                                            False)

        incremental_from = int_or_none(request._incremental_from)
        self.check_incremental(db, incremental_from)
        
        

        auth.can_syncread_account(operator_id,
                                  accountspread,
                                  auth_type)

        response = getAccountsResponse()
        atypes = response.typecode.ofwhat[0].attribute_typecode_dict

        account_priorities = {}
        if include_affiliations:
            for row in AccountQuery(db, co, accountspread,
                                    incremental_from).search_affiliations():
                account_priorities.setdefault(row['id'], {})[row['priority']]=row
        
        response._account = []
        q = quarantines(db, co)
        for row in AccountQuery(db, co, accountspread,
                                incremental_from).search_data(
                auth_type,
                include_affiliations=include_affiliations):
            a = AccountDTO(row, atypes, account)
            a._quarantine = (q.get_quarantines(row['id']) +
                             q.get_quarantines(row['owner_id']))
            response._account.append(a)
            my_account_priorities = account_priorities.get(row['id'])
            if my_account_priorities is not None:
                primary_prio = min(my_account_priorities.keys())
                primary = my_account_priorities[primary_prio]
                a._attrs['primary_affiliation'] = str(co.PersonAffiliation(primary['affiliation']))
                a._attrs['primary_ou_id'] = primary['ou_id']
                a._affiliation = [
                    AffiliationDTO(ap, co) for ap in my_account_priorities.values()]
                
        db.rollback()

        return response

    @logmethod(getPersonsRequest)
    def get_persons(self, db, operator_id, request):
        co=Factory.get("Constants")()
        auth=bofhd_auth.BofhdAuth(db)

        personspread = None
        if request._personspread is not None:
            personspread = int(co.Spread(str(request._personspread)))
        accountspread = None
        if request._accountspread is not None:
            accountspread = int(co.Spread(str(request._accountspread)))
            
        if personspread and accountspread:
            raise Error("Huh?")

        incremental_from = int_or_none(request._incremental_from)
        self.check_incremental(db, incremental_from)

        auth.can_syncread_person(operator_id, personspread)

        response = getPersonsResponse()
        atypes = response.typecode.ofwhat[0].attribute_typecode_dict
        response._person = []
        
        account_priorities={}
        for row in PersonQuery(
               db, co, personspread, accountspread, incremental_from).search_affiliations():
            account_priorities.setdefault(row['id'], {})[row['priority']]=row
            
        q=quarantines(db, co)
        for row in PersonQuery(
               db, co, personspread, accountspread,
               incremental_from).search_data(include_keycard=True):
            
            p=PersonDTO(row, atypes)
            p._quarantine = q.get_quarantines(row['id'])
            my_account_priorities = account_priorities.get(row['id'])
            if accountspread and my_account_priorities:
                my_account_priorities = dict([(pri,ap) for pri,ap in my_account_priorities.items()
                                              if row['spread_account_id'] == ap['account_id']]) or None
            if my_account_priorities is not None:
                primary_prio = min(my_account_priorities.keys())
                primary = my_account_priorities[primary_prio]
                p._attrs['primary_account'] = primary['account_id']
                p._attrs['primary_account_name'] = primary['account_name']
                p._attrs['primary_account_password'] = primary['account_passwd']
                p._attrs['primary_affiliation'] = str(co.PersonAffiliation(primary['affiliation']))
                p._attrs['primary_affiliation_status'] = co.PersonAffStatus(primary['status']).str
                p._attrs['primary_ou_id'] = primary['ou_id']
                p._affiliation = [
                    AffiliationDTO(ap, co) for ap in my_account_priorities.values()]
                response._person.append(p)
        db.rollback()

        return response

    root[(getGroupsRequest.typecode.nspname,
          getGroupsRequest.typecode.pname)] = 'get_groups'
    root[(getPersonsRequest.typecode.nspname,
          getPersonsRequest.typecode.pname)] = 'get_persons'
    root[(getAccountsRequest.typecode.nspname,
          getAccountsRequest.typecode.pname)] = 'get_accounts'
    root[(getOUsRequest.typecode.nspname,
          getOUsRequest.typecode.pname)] = 'get_ous'
    root[(getAliasesRequest.typecode.nspname,
          getAliasesRequest.typecode.pname)] = 'get_aliases'
    root[(getHomedirsRequest.typecode.nspname,
          getHomedirsRequest.typecode.pname)] = 'get_homedirs'
    root[(setHomedirStatusRequest.typecode.nspname,
          setHomedirStatusRequest.typecode.pname)] = 'set_homedir_status'
    root[(getChangelogidRequest.typecode.nspname,
          getChangelogidRequest.typecode.pname)] = 'get_changelogid'

        
def test_soap(fun, cl, **kw):
    #fun=root[(cl.typecode.nspname, cl.typecode.pname)]
    o=cl()
    for k,w in kw.items():
        setattr(o,"_"+k,w)
    t=time.time()
    sw=SoapWriter()
    sig=SignatureHandler(cereconf.TEST_USERNAME, cereconf.TEST_PASSWORD)
    sw.serialize(o)
    sig.sign(sw)
    s=str(sw)
    ps=ParsedSoap(s)
    rps=fun(ps)
    t1=time.time()-t
    rs=str(SoapWriter(outputclass=DomletteElementProxy).serialize(rps))
    open("/tmp/log.%s.ny" % fun.__name__, 'w').write(rs)
    #rps=ParsedSoap(rs)
    t2=time.time()-t
    return fun.__name__, t1, t2

def test():
    global logger
    logger = Factory.get_logger("console")
    sp=cerews()
    db = Factory.get("Database")(client_encoding='UTF-8')
    fromid = db.get_last_changelog_id() - 40000

    print test_soap(sp.get_persons, getPersonsRequest,
                    accountspread="user@kalender")
    print test_soap(sp.get_aliases, getAliasesRequest,
                    emailserver="emanuel.itea.ntnu.no")
    print test_soap(sp.get_aliases, getAliasesRequest)
    print test_soap(sp.get_accounts, getAccountsRequest,
                    accountspread="user@stud", auth_type="MD5-crypt",
                    incremental_from=fromid)
    print test_soap(sp.get_accounts, getAccountsRequest,
                    accountspread="user@stud", auth_type="MD5-crypt",
                    include_affiliations=True)
    print test_soap(sp.get_persons, getPersonsRequest)
    print test_soap(sp.set_homedir_status, setHomedirStatusRequest,
                    homedir_id=85752, status="not_created")
    print test_soap(sp.get_ous, getOUsRequest)
    print test_soap(sp.get_groups, getGroupsRequest, 
                    accountspread="user@stud", groupspread="group@ntnu")
    print test_soap(sp.get_homedirs, getHomedirsRequest,
                    hostname="jak.itea.ntnu.no", status="not_created")
    print test_soap(sp.get_persons, getPersonsRequest,
                    person_spread="group@ntnu")
    print test_soap(sp.get_changelogid, getChangelogidRequest)
    print test_soap(sp.get_ous, getOUsRequest)

class SSLForkingMixIn(ForkingMixIn):
    from time import sleep
    def process_request(self, request, client_address):
        """
        Override ForkingMixIn.process_request to replace close_request with
        request.clear.  This is needed to handle SSL-connections.
        """

        self.collect_children()
        pid = os.fork()
        if pid:
            # Parent process
            if self.active_children is None:
                self.active_children = []
            self.active_children.append(pid)
            request.clear()
            return
        else:
            # Child process.
            # This must never return, hence sys.exit()!
            try:
                self.finish_request(request, client_address)
                request.close()
            except:
                try:
                    self.handle_error(request, client_address)
                finally:
                    sys.exit(1)
            sys.exit(0)

class SecureServiceContainer(SSLForkingMixIn, SSL.SSLServer, ServiceContainer):

    def __init__(self, server_address, ssl_context, services=[], RequestHandlerClass=SOAPRequestHandler):
        self.max_children = getattr(cereconf, "CEREWS_MAX_CHILDREN", 5)
        ServiceContainer.__init__(self, server_address, services, RequestHandlerClass)
        SSL.SSLServer.__init__(self, server_address, RequestHandlerClass, ssl_context)
        self.server_name, self.server_port = server_address

def RunAsServer(port=80, services=(), fork=False):
    address = ('', port)
    ctx = init_ssl()
    sc = SecureServiceContainer(address, ssl_context=ctx, services=services)
    sc.serve_forever()

def passphrase_callback(v):
    return cereconf.CEREWS_KEY_FILE_PASSWORD

def init_ssl(debug=None):
    ctx = SSL.Context('sslv23')
    ## certificate and private-key in the same file
    ctx.load_cert(cereconf.CEREWS_KEY_FILE, callback=passphrase_callback)
    ## do not use sslv2
    ctx.set_options(SSL.op_no_sslv2)
    ctx.set_session_id_ctx('ceresync_srv')
    return ctx

def daemonize():
    import os
    import sys
    import resource

    try:
        pid=os.fork()
        if pid > 0:
            sys.exit(0)
        os.chdir("/")
        os.setsid()
        os.umask(022)
        pid=os.fork()
        if pid > 0:
            sys.exit(0)

        os.close(0)
        os.close(1)
        os.close(2)
        infd=os.open("/dev/null", os.O_RDONLY)
        outfd=os.open("/dev/null", os.O_WRONLY)
        ## redirect stdin to /dev/null
        os.dup2(infd, 0)
        ## redirect stdout and stderr to logfile.
        os.dup2(outfd, 1)
        os.dup2(outfd, 2)
    except OSError, e:
        global logger
        logger.error("Demonize failed: %s" % e.strerror)

def main(daemon=False):
    global logger
    if daemon:
        logger = Factory.get_logger("cerews")
        daemonize()
        if hasattr(cereconf, "CEREWS_PIDFILE"):
            open(cereconf.CEREWS_PIDFILE, "w").write(str(os.getpid())+"\n")
    else:
        logger = Factory.get_logger("console")
        logger.setLevel(logging.DEBUG)
    logger.info("starting...")
    RunAsServer(port=int(cereconf.CEREWS_PORT), services=[cerews(),])

if __name__ == '__main__':
    help = False
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start' or sys.argv[1] == 'debug':
            main()
        elif sys.argv[1] == 'daemon':
            main(daemon=True)
        elif sys.argv[1] == 'test':
            test()
        else:
            help = True
    else:
        help = True

    if help:
        print >> sys.stderr, """
cerews!

Hello. Try one of these:

%(prog)s daemon   start the server
%(prog)s debug    start the server in the foreground
%(prog)s start    start the server in the foreground
%(prog)s test     run internal tests
""" % {'prog': sys.argv[:1]}