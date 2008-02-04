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

import pickle

class ChangeLog(object):
    # Don't want to override the Database constructor
    def cl_init(self, change_by=None, change_program=None):
        self.change_by = change_by
        self.change_program = change_program
        self.messages = []

    def update_log_event(self, change_id, change_params):
        """This method is typically used to remove informtion from the
        changelog"""
        if change_params is not None:
            change_params = pickle.dumps(change_params)
        self.execute("""
        UPDATE [:table schema=cerebrum name=change_log]
        SET change_params=:change_params
        WHERE change_id=:change_id""", {
            'change_id': int(change_id),
            'change_params': change_params})
        
    def remove_log_event(self, change_id):
        self.execute("""
        DELETE FROM [:table schema=cerebrum name=change_log]
        WHERE change_id=:change_id""", {
            'change_id': int(change_id)})

    def log_change(self, subject_entity, change_type_id,
                   destination_entity, change_params=None,
                   change_by=None, change_program=None):
        if change_by is None and self.change_by is not None:
            change_by = self.change_by
        elif change_program is None and self.change_program is not None:
            change_program = self.change_program
        if change_by is None and change_program is None:
            raise self.ProgrammingError, "must set change_by or change_program"
        change_type_id = int(change_type_id)
        if change_params is not None:
            change_params = pickle.dumps(change_params)
        self.messages.append( locals() )

    def rollback_log(self):
        """See commit_log"""
        self.messages = []

    def commit_log(self):
        """This method should be called by Database.commit to prevent
        ELInterface from returning data that are not commited (and are
        thus invisible to other processes, and may be rolled back),"""

        for m in self.messages:
            m['id'] = int(self.nextval('change_log_seq'))
            self.execute("""
            INSERT INTO [:table schema=cerebrum name=change_log]
               (change_id, subject_entity, change_type_id, dest_entity,
                change_params, change_by, change_program)
            VALUES (:id, :subject_entity, :change_type_id,
                    :destination_entity, :change_params, :change_by,
                    :change_program)""", m)
        self.messages = []

    def get_log_events(self, start_id=0, max_id=None, types=None,
                       subject_entity=None, dest_entity=None,
                       any_entity=None, change_by=None, sdate=None):
        if any_entity and (dest_entity or subject_entity):
            raise self.ProgrammingError, "any_entity is mutually exclusive with dest_entity or subject_entity"
        where = ["change_id >= :start_id"]
        bind = {'start_id': int(start_id)}
        if subject_entity is not None:
            where.append("subject_entity=:subject_entity")
            bind['subject_entity'] = int(subject_entity)
        if dest_entity is not None:
            where.append("dest_entity=:dest_entity")
            bind['dest_entity'] = int(dest_entity)
        if any_entity is not None:
            where.append("subject_entity=:any_entity OR "
                         "dest_entity=:any_entity")
            bind['any_entity'] = int(any_entity)
        if change_by is not None:
            where.append("change_by=:change_by")
            bind['change_by'] = int(change_by)
        if max_id is not None:
            where.append("change_id <= :max_id")
            bind['max_id'] = int(max_id)
        if types is not None:
            where.append("change_type_id IN("+", ".join(
                ["%i" % x for x in types])+")")
        if sdate is not None:
            where.append("tstamp > :sdate")
            bind['sdate'] = sdate
        where = "WHERE (" + ") AND (".join(where) + ")"
        return self.query("""
        SELECT tstamp, change_id, subject_entity, change_type_id, dest_entity,
               change_params, change_by, change_program
        FROM [:table schema=cerebrum name=change_log] %s
        ORDER BY change_id""" % where, bind, fetchall=False)

    def get_log_events_date(self, type=None, sdate=None, edate=None):
        where = []
        if type is not None:
            where.append("change_type_id = %s" % type)
        if sdate is not None:
            if edate is not None:
                where.append("""tstamp BETWEEN TO_DATE('%s', 'YYYY-MM-DD') 
                                AND TO_DATE('%s', 'YYYY-MM-DD')""" % (sdate,edate))
            else:
                where.append("tstamp >= TO_DATE('%s', 'YYYY-MM-DD')" % sdate)
        else:
            if edate is not None:
                where.append("tstamp <= TO_DATE('%s', 'YYYY-MM-DD')" % edate)
        if (type, sdate, edate) is not None:
            where = "WHERE "+" AND ".join(where)
        ret = []
        for r in self.query("""
        SELECT tstamp, change_id, subject_entity, change_type_id,
               dest_entity, change_params, change_by, change_program
        FROM [:table schema=cerebrum name=change_log] %s
        ORDER BY change_id""" % where):
            ret.append(r)
        return ret

    def get_changetypes(self):
        return self.query("""
        SELECT change_type_id, category, type, msg_string
        FROM [:table schema=cerebrum name=change_type]""")

    def get_last_changelog_id(self):
        return self.query_1("""
        SELECT change_id
        FROM [:table schema=cerebrum name=change_log]
        ORDER BY change_id DESC LIMIT 1""")


##     def rollback(self):
##         self.rollback_log()
##         self.orig_rollback()

##     def commit(self):
##         self.commit_log()
##         self.orig_commit()

# arch-tag: 199ad3d8-a467-462e-bb6e-b34d20bda841
