#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2002, 2003 University of Oslo, Norway
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
from time import time as now

import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum import Utils
from Cerebrum import Account
from Cerebrum import Metainfo
from Cerebrum.Constants import _SpreadCode

# run migrate_* in this order
targets = {
    'core': ('rel_0_9_2', 'rel_0_9_3', 'rel_0_9_4', 'rel_0_9_5',
             'rel_0_9_6', 'rel_0_9_7', 'rel_0_9_8', 'rel_0_9_9',
             'rel_0_9_10', 'rel_0_9_11', 'rel_0_9_12'),
    'bofhd': ('bofhd_1_1', ),
    'changelog': ('changelog_1_2', ),
    'email': ('email_1_0', 'email_1_1', 'email_1_2', 'email_1_3'),
    'ephorte': ('ephorte_1_1', ),
    }

# Global variables
makedb_path = design_path = db = co = None

def time_spent(start):
    spent = now() - start
    hours = spent // 3600
    minutes = (spent - hours*3600) // 60
    seconds = spent % 60
    txt = ""
    if hours:
        txt = "h:%d, " % hours
    if minutes:
        txt += "m:%d, " % minutes
    txt += "s:%d" % seconds
    return txt

def makedb(release, stage, insert_codes=True):
    print "Running Makedb(%s, %s)..." % (release, stage)
    cmd = ['%s/makedb.py' % makedb_path, '-d', '--stage', stage,
           '%s/migrate_to_%s.sql' % (design_path, release)]
    r = os.system(" ".join(cmd))
    if r:
        continue_prompt("Exit value was %i, continue? (y/n)[y]" % r)
    if stage == 'pre' and insert_codes:
        cmd = ['%s/makedb.py' % makedb_path, '--only-insert-codes']
        r = os.system(" ".join(cmd))
        if r:
            continue_prompt("Exit value was %i, continue? (y/n)[y]" % r)

def continue_prompt(message):
    print message
    r = sys.stdin.readline()
    if len(r) > 1 and r[0] != 'y':
        print "aborting"
        sys.exit(1)


def get_db_version(component='core'):
    meta = Metainfo.Metainfo(db)
    version = "pre-0.9.2"
    try:
        if component == 'core':
            version = "%d.%d.%d" % \
                      meta.get_metainfo(Metainfo.SCHEMA_VERSION_KEY)
        else:
            version = meta.get_metainfo("sqlmodule_%s" % component)
    except Errors.NotFoundError:
        pass
    except Exception, e:
        # Not sure how to trap the PgSQL OperationalError
        if str(e.__class__).find("OperationalError") == -1:
            raise
    return version


def assert_db_version(wanted, component="core"):
    version = get_db_version(component=component)
    if wanted <> version:
        print "Your database is %s, not %s, aborting" % (version, wanted)
        sys.exit(1)


def migrate_to_rel_0_9_2():
    """Migrate a pre 0.9.2 (the first version) database to the 0.9.2
    database schema."""

    assert_db_version("pre-0.9.2")

    str2const = {}
    num2const = {}
    for c in dir(co):
        tmp = getattr(co, c)
        if isinstance(tmp, _SpreadCode):
            str2const[str(tmp)] = tmp
            num2const[int(tmp)] = tmp
    
    # TODO: Assert that the new classes has been installed
    makedb('0_9_2', 'pre')

    spreads = []
    for s in cereconf.HOME_SPREADS:
        spreads.append(str(getattr(co, s)))
    assert spreads

    # fill the account_home table for the relevant spreads

    # Normally, it is a no-no to use SQL outside the API.  However,
    # when migrating some data may not be available because the
    # installed API and the database are out of sync.
    ac = Account.Account(db)
    count = 0
    print "Populating account_home"
    processed = {}

    # Add an entry in account_home for each spread in HOME_SPREADS
    # that the account currently has a spread to
    for row in db.query(
        """SELECT account_id, home, disk_id, spread
        FROM [:table schema=cerebrum name=entity_spread] es,
             [:table schema=cerebrum name=account_info] ai
        WHERE es.entity_id=ai.account_id
        """, fetchall=False):
        spread = num2const[ int(row['spread']) ]
        if str(spread) in spreads:
            ac.clear()
            ac.find(row['account_id'])
            processed[int(row['account_id'])] = 1
            status = co.home_status_on_disk
            if ac.is_deleted():
                status = co.home_status_archived
            ac.set_home(spread, disk_id=row['disk_id'], home=row['home'],
                        status=status)
            ac.write_db()
            count += 1
            if (count % 100) == 1:
                sys.stdout.write('.')
                sys.stdout.flush()

    # Now include accounts not in HOME_SPREADS.  Their homedir is
    # bound to the first spread in HOME_SPREADS
    spread = str2const[spreads[0]]
    for row in db.query(
        """SELECT account_id, home, disk_id
        FROM [:table schema=cerebrum name=account_info]""", fetchall=False):
        if processed.has_key(int(row['account_id'])):
            continue
        if not row['disk_id'] and not row['home']:
            continue
        ac.clear()
        ac.find(row['account_id'])
        status = co.home_status_on_disk
        if ac.is_deleted():
            status = co.home_status_archived
        ac.set_home(spread, disk_id=row['disk_id'], home=row['home'],
                    status=status)
        ac.write_db()
        count += 1
        if (count % 100) == 1:
            sys.stdout.write('.')
            sys.stdout.flush()
    print """
    NOTE: all entries added to account_home has status=on_disk unless
    account.is_deleted() returns True, which sets status to None"""

    db.commit()
    makedb('0_9_2', 'post')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,2))
    print "Migration to 0.9.2 completed successfully"
    db.commit()

def migrate_to_rel_0_9_3():
    """Migrate from 0.9.2 database to the 0.9.3 database schema."""

    assert_db_version("0.9.2")

    # TODO: Assert that the new classes has been installed
    makedb('0_9_3', 'pre')

    # Convert all rows in auth_op_target with has_attr true.  If
    # auth_op_target_attrs contains multiple rows, we need to add
    # additional rows.

    rows = db.query(
        """SELECT op_target_id, entity_id, target_type
        FROM [:table schema=cerebrum name=auth_op_target]
        WHERE has_attr=1""")
    print "%d rows to convert..." % len(rows)
    rows_per_dot = int(len(rows) / 79 + 1)
    count = 0
    for row in rows:
        if count % rows_per_dot == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        count += 1
        attr_rows = db.query(
            """SELECT attr
            FROM [:table schema=cerebrum name=auth_op_target_attrs]
            WHERE op_target_id=:id""", {'id': int(row['op_target_id'])})
        assert attr_rows
        db.execute(
            """UPDATE [:table schema=cerebrum name=auth_op_target]
            SET attr=:attr WHERE op_target_id=:id""",
            {'id': int(row['op_target_id']), 'attr': attr_rows[0]['attr']})
        for attr_row in attr_rows[1:]:
            values = {'op_target_id': int(db.nextval('entity_id_seq')),
                      'entity_id': int(row['entity_id']),
                      'target_type': row['target_type'],
                      'attr': attr_row['attr']}
            db.execute(
                """INSERT INTO [:table schema=cerebrum name=auth_op_target]
                (%(tcols)s)
                VALUES (%(tvalues)s)""",
                {'tcols': ", ".join([x[0] for x in values]),
                 'tvalues': ", ".join([x[1] for x in values])})
            # We need to duplicate the rows in auth_role which refer
            # to this op_target_id as well, but since our database
            # doesn't have multiple attr values, I won't bother to
            # implement it.  Let me know if you need it!
            raise NotImplementedError
    
    db.commit()
    print "\ndone."
    makedb('0_9_3', 'post')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,3))
    print "Migration to 0.9.3 completed successfully"
    db.commit()


def migrate_to_rel_0_9_4():
    """Migrate from 0.9.3 database to the 0.9.4 database schema."""

    assert_db_version("0.9.3")
    makedb('0_9_4', 'pre')

    # Move all "home, disk_id, status" (t1) settings in account_home
    # to homedir.  If an account has the same values for t1 for two
    # different spreads, the same homedir_id should be used for both.

    rows = db.query("""SELECT account_id, spread, home, disk_id, status
    FROM  [:table schema=cerebrum name=account_home]""")
    print "%d rows to convert..." % len(rows)
    rows_per_dot = int(len(rows) / 79 + 1)
    count = 0
    account_id2home = {}
    for row in rows:
        if count % rows_per_dot == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        count += 1
        homedir_id = None
        for home, disk_id, status, tmp_hid in account_id2home.get(
            long(row['account_id']), []):
            if home == row['home'] and disk_id == row['disk_id']:
                if status != row['status']:
                    print >>sys.stderr, "WARNING, check status on", tmp_hid 
                homedir_id = tmp_hid
                break
        if homedir_id is None:
            # Cannot use AccountHome as the new class is not yet installed
            homedir_id = long(db.nextval('homedir_id_seq'))
            db.execute("""
            INSERT INTO [:table schema=cerebrum name=homedir]
              (homedir_id, account_id, home, disk_id, status)
            VALUES (:h_id, :account_id, :home, :disk_id, :status)""", {
                'h_id': homedir_id,
                'account_id': row['account_id'],
                'home': row['home'],
                'disk_id': row['disk_id'],
                'status': row['status']})
            account_id2home.setdefault(long(row['account_id']), []).append(
                (row['home'], row['disk_id'], row['status'], homedir_id))

        db.execute("""UPDATE [:table schema=cerebrum name=account_home]
        SET homedir_id=:h_id
        WHERE account_id=:ac_id AND spread=:spread""", {
            'h_id': homedir_id,
            'ac_id': row['account_id'],
            'spread': row['spread']})

    db.commit()
    print "\ndone."
    makedb('0_9_4', 'post')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,4))
    print "Migration to 0.9.4 completed successfully"
    db.commit()


def migrate_to_rel_0_9_5():
    """Migrate from 0.9.4 database to the 0.9.5 database schema."""

    assert_db_version("0.9.4")
    # Inserting codes is bad at this stage. We have working codes, and
    # we know they are used by person_external_id ATM and they are all
    # entity_person. Therefore, omit code-insertion.
    makedb('0_9_5', 'pre', False)
    db.commit()
    print "\ndone."
    # Copy person_ext_id_code into entity_ext_code. Insert
    # co.entity_person as well. person_ext_id_code contains only
    # people-codes ATM.
    db.execute("""
    INSERT INTO [:table schema=cerebrum name=entity_external_id_code]
      (code, code_str, entity_type, description)
    SELECT DISTINCT peic.code, peic.code_str, ei.entity_type, peic.description
    FROM person_external_id_code peic, person_external_id pei, entity_info ei
    WHERE peic.code=pei.id_type AND pei.person_id=ei.entity_id""")
    
    db.execute("""
    INSERT INTO entity_external_id
    SELECT pei.person_id, ei.entity_type, pei.id_type, pei.source_system, 
           pei.external_id
    FROM person_external_id pei, entity_info ei
    WHERE pei.person_id=ei.entity_id""")

    # CLConstants got person_ext_id_del etc. Rename to entity...
    db.execute("""
    UPDATE [:table schema=cerebrum name=change_type]
    SET category='entity'
    WHERE type IN ('ext_id_add', 'ext_id_del', 'ext_id_mod')""")
    
    db.commit()
    makedb('0_9_5', 'post')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,5))
    print "Migration to 0.9.5 completed successfully"
    db.commit()

def migrate_to_rel_0_9_6():
    """Migrate from 0.9.5 database to the 0.9.6 database schema."""
    assert_db_version("0.9.5")
    makedb('0_9_6', 'pre')
    db.commit()
    # This database change doesn't require any smarts.
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,6))
    print "Migration to 0.9.6 completed successfully"
    db.commit()

def migrate_to_rel_0_9_7():
    """Migrate from 0.9.6 database to the 0.9.7 database schema."""
    assert_db_version("0.9.6")
    makedb('0_9_7', 'pre')
    
    # deceased-field in person_info is being made into a date-field 
    # replace any deceased = 'T' with now() 
    db.execute("""
    UPDATE [:table schema=cerebrum name=person_info]
    SET deceased_date= [:now]
    WHERE deceased = 'T'""")

    db.commit()
    makedb('0_9_7', 'post')
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,7))
    print "Migration to 0.9.7 completed successfully"
    db.commit()


def migrate_to_rel_0_9_8():
    """Migrate from 0.9.7 database to the 0.9.8 database schema."""
    assert_db_version("0.9.7")
    # insert new code
    makedb('0_9_8', 'pre')
    # move data
    makedb('0_9_8', 'post')
    db.commit()
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,8))
    print "Migration to 0.9.8 completed successfully"
    db.commit()


def migrate_to_rel_0_9_9():
    """Migrate from 0.9.8 database to the 0.9.9 database schema."""
    assert_db_version("0.9.8")
    makedb('0_9_9', 'pre')
    # Find and remove all account_home entries that does not have a
    # corresponding entity_spread entry
    rows = db.query("""
    SELECT account_id, spread FROM account_home ah
    WHERE NOT EXISTS (SELECT 'foo'
                      FROM entity_spread es
                      WHERE ah.spread=es.spread AND ah.account_id=es.entity_id)""")
    print "%d rows to convert..." % len(rows)
    ac = Utils.Factory.get('Account')(db)
    rows_per_dot = int(len(rows) / 79 + 1)
    count = 0

    for r in rows:
        if count % rows_per_dot == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        count += 1
        # PK is "account_id, spread", thus clear_home will remove the correct entry
        ac.clear()
        ac.find(r['account_id'])
        ac.clear_home(r['spread'])
    for r in db.query("""
    SELECT homedir_id, account_id FROM homedir hd
    WHERE NOT EXISTS (SELECT 'foo'
                      FROM account_home ah
                      WHERE ah.homedir_id=hd.homedir_id)"""):
        ac.clear()
        ac.find(r['account_id'])
        ac._clear_homedir(r['homedir_id'])
    db.commit()
    makedb('0_9_9', 'post')
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,9))
    print "Migration to 0.9.9 completed successfully"
    db.commit()

def migrate_to_rel_0_9_10():
    """Migrate from 0.9.9 database to the 0.9.10 database schema."""
    assert_db_version("0.9.9")
    # drop old constraint
    makedb('0_9_10', 'pre')
    # add new constraint
    makedb('0_9_10', 'post')
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,10))
    print "Migration to 0.9.10 completed successfully"
    db.commit()

def migrate_to_rel_0_9_11():
    """Migrate from 0.9.10 database to the 0.9.11 database schema."""
    assert_db_version("0.9.10")
    # drop description column
    makedb('0_9_11', 'pre')
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,11))
    print "Migration to 0.9.11 completed successfully"
    db.commit()

def migrate_to_rel_0_9_12():
    """Migrate from 0.9.11 database to the 0.9.12 database schema."""
    assert_db_version("0.9.11")
    # drop description column
    makedb('0_9_12', 'pre')
    print "\ndone."
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo(Metainfo.SCHEMA_VERSION_KEY, (0,9,12))
    print "Migration to 0.9.12 completed successfully"
    db.commit()

def migrate_to_bofhd_1_1():
    print "\ndone."
    assert_db_version("1.0", component='bofhd')
    makedb('bofhd_1_1', 'pre')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo("sqlmodule_bofhd", "1.1")
    print "Migration to bofhd 1.1 completed successfully"
    db.commit()


def migrate_to_changelog_1_2():
    print "\ndone."
    assert_db_version("1.1", component='changelog')
    makedb('changelog_1_2', 'pre')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo("sqlmodule_changelog", "1.2")
    print "Migration to changelog 1.2 completed successfully"
    db.commit()


def migrate_to_email_1_1():
    print "\ndone."
    assert_db_version("1.0", component='email')
    makedb('email_1_1', 'pre')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo("sqlmodule_email", "1.1")
    print "Migration to email 1.1 completed successfully"
    db.commit()

def migrate_to_email_1_2():
    print "\ndone."
    assert_db_version("1.1", component='email')
    makedb('email_1_2', 'pre')
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo("sqlmodule_email", "1.2")
    print "Migration to email 1.2 completed successfully"
    db.commit()

def migrate_to_email_1_3():
    print "\ndone."
    assert_db_version("1.2", component='email')
    # Check for new entity_types
    entity_types = []
    for e in ('entity_email_domain', 'entity_email_address',
              'entity_email_target'):
        entity_types.append(getattr(co, e))
    try:
        [int(c) for c in entity_types]
    except Errors.NotFoundError:
        print "*** New email entity-types not added to database. Run makedb.py --update-codes first."
        sys.exit(0)
    # Remove constraints and add tmp-columns
    start = now()
    print "pre"
    curr = now()
    makedb('email_1_3', 'pre')
    print "...done %s" % time_spent(curr)
    ent = Utils.Factory.get('Entity')(db)
    # Create new entities for these tables
    t_id2e_id = {}
    d_id2e_id = {}
    a_id2e_id = {}
    print "making entities"
    # email_target
    curr = now()
    print "  email_target"
    rows = db.query("""SELECT target_id, target_type, entity_type, entity_id,
                       alias_value, using_uid, server_id
                       FROM [:table schema=cerebrum name=email_target]""")
    for row in rows:
        ent.clear()
        ent.populate(co.entity_email_target)
        ent.write_db()
        t_id2e_id[int(row['target_id'])] = ent.entity_id
        db.execute("""INSERT INTO [:table schema=cerebrum name=tmp_email_target]
                      VALUES (:e_t, :t_id, :t_t, :t_e_t, :t_e_id, :a_v, :u_u,
                              :s_id)""", {'e_t': int(co.entity_email_target),
                                          't_id': ent.entity_id,
                                          't_t': row['target_type'],
                                          't_e_t': row['entity_type'],
                                          't_e_id': row['entity_id'],
                                          'a_v': row['alias_value'],
                                          'u_u': row['using_uid'],
                                          's_id': row['server_id']})
    # email_domain
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_domain"
    rows = db.query("""SELECT domain_id, domain, description 
                       FROM [:table schema=cerebrum name=email_domain]""")
    for row in rows:
        ent.clear()
        ent.populate(co.entity_email_domain)
        ent.write_db()
        d_id2e_id[int(row['domain_id'])] = ent.entity_id
        db.execute("""INSERT INTO [:table schema=cerebrum name=tmp_email_domain]
                      VALUES (:e_t, :d_id, :d,
                              :desc)""", {'e_t': int(co.entity_email_domain),
                                          'd_id': ent.entity_id,
                                          'd': row['domain'],
                                          'desc': row['description']})
    # email_address
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_address"
    rows = db.query("""SELECT address_id, local_part, domain_id,
                       target_id, create_date, change_date, expire_date
                       FROM [:table schema=cerebrum name=email_address]""")
    counter = 0
    total = len(rows)
    for row in rows:
        ent.clear()
        ent.populate(co.entity_email_address)
        ent.write_db()
        counter += 1
        if counter % 100000 == 0:
            print "      counter at %d/%d" % (counter, total)
        a_id2e_id[int(row['address_id'])] = ent.entity_id
        db.execute("""INSERT INTO [:table schema=cerebrum name=tmp_email_address]
                      VALUES (:e_t, :a_id, :l_p, :d_id, :t_id, :cr_d, :ch_d,
                              :e_d)""", {'e_t': int(co.entity_email_address),
                                         'a_id': ent.entity_id,
                                         'l_p': row['local_part'],
                                         'd_id': d_id2e_id[int(row['domain_id'])],
                                         't_id': t_id2e_id[int(row['target_id'])],
                                         'cr_d': row['create_date'],
                                         'ch_d': row['change_date'],
                                         'e_d': row['expire_date']})
    print "...done %s" % time_spent(curr)
    print "filling in misc tables"
    # email_entity_domain
    curr = now()
    print "  email_entity_domain"
    rows = db.query("""SELECT DISTINCT domain_id
                       FROM [:table schema=cerebrum name=email_entity_domain]""")
    for row in rows:
        d_id = int(row['domain_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_entity_domain]
                      SET tmp_domain_id=:e_id
                      WHERE domain_id=:d_id""", {'d_id': d_id,
                                                 'e_id': d_id2e_id[d_id]})
    # email_quota
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_quota"
    rows = db.query("""SELECT DISTINCT target_id
                       FROM [:table schema=cerebrum name=email_quota]""")
    for row in rows:
        t_id = int(row['target_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_quota]
                      SET tmp_target_id=:e_id
                      WHERE target_id=:t_id""", {'t_id': t_id,
                                                 'e_id': t_id2e_id[t_id]})
    # email_spam_filter
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_filter"
    rows = db.query("""SELECT DISTINCT target_id
                       FROM [:table schema=cerebrum name=email_spam_filter]""")
    for row in rows:
        t_id = int(row['target_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_spam_filter]
                      SET tmp_target_id=:e_id
                      WHERE target_id=:t_id""", {'t_id': t_id,
                                                 'e_id': t_id2e_id[t_id]})
    # email_virus_scan
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_virus_scan"
    rows = db.query("""SELECT DISTINCT target_id
                       FROM [:table schema=cerebrum name=email_virus_scan]""")
    for row in rows:
        t_id = int(row['target_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_virus_scan]
                      SET tmp_target_id=:e_id
                      WHERE target_id=:t_id""", {'t_id': t_id,
                                                 'e_id': t_id2e_id[t_id]})
    # email_forward
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_forward"
    rows = db.query("""SELECT DISTINCT target_id
                       FROM [:table schema=cerebrum name=email_forward]""")
    for row in rows:
        t_id = int(row['target_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_forward]
                      SET tmp_target_id=:e_id
                      WHERE target_id=:t_id""", {'t_id': t_id,
                                                 'e_id': t_id2e_id[t_id]})
    # email_vacation
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_vacation"
    rows = db.query("""SELECT DISTINCT target_id
                       FROM [:table schema=cerebrum name=email_vacation]""")
    for row in rows:
        t_id = int(row['target_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_vacation]
                      SET tmp_target_id=:e_id
                      WHERE target_id=:t_id""", {'t_id': t_id,
                                                 'e_id': t_id2e_id[t_id]})
    # email_primary_address
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_primary_address"
    rows = db.query("""SELECT target_id, address_id
                       FROM [:table schema=cerebrum name=email_primary_address]""")
    for row in rows:
        t_id = int(row['target_id'])
        a_id = int(row['address_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_primary_address]
                      SET tmp_target_id=:tt_id, tmp_address_id=:ta_id
                      WHERE target_id=:t_id AND
                            address_id=:a_id""", {'t_id': t_id,
                                                  'tt_id': t_id2e_id[t_id],
                                                  'a_id': a_id,
                                                  'ta_id': a_id2e_id[a_id]})

    # email_domain_category
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_domain_category"
    rows = db.query("""SELECT DISTINCT domain_id
                       FROM [:table schema=cerebrum name=email_domain_category]""")
    for row in rows:
        d_id = int(row['domain_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_domain_category]
                      SET tmp_domain_id=:e_id
                      WHERE domain_id=:d_id""", {'d_id': d_id,
                                                 'e_id': d_id2e_id[d_id]})

    # email_target_filter
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "  email_target_filter"
    rows = db.query("""SELECT DISTINCT target_id
                       FROM [:table schema=cerebrum name=email_target_filter]""")
    for row in rows:
        t_id = int(row['target_id'])
        db.execute("""UPDATE [:table schema=cerebrum name=email_target_filter]
                      SET tmp_target_id=:e_id
                      WHERE target_id=:t_id""", {'t_id': t_id,
                                                 'e_id': t_id2e_id[t_id]})
 

    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "pre commit()"
    db.commit()
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "post"
    makedb('email_1_3', 'post')
    print "  ...done %s" % time_spent(curr)
    curr = now()
    print "post2"
    makedb('email_1_3', 'post2')
    print "  ...done %s" % time_spent(curr)
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo("sqlmodule_email", "1.3")
    db.commit()
    print "Migration to email 1.3 completed successfully %s" % time_spent(start)

def migrate_to_ephorte_1_1():
    print "\ndone."
    assert_db_version("1.0", component='ephorte')
    # Remove "equal" roles that occur more than once
    from Cerebrum.modules.no.uio.Ephorte import EphorteRole
    ephorte_role = EphorteRole(db)
    for row in db.query("""
    SELECT * FROM (SELECT person_id, role_type, adm_enhet, arkivdel,
                   journalenhet, COUNT(*) FROM ephorte_role GROUP BY
                   person_id, role_type, adm_enhet, arkivdel, journalenhet)
                   AS blatti WHERE count > 1"""):
        ephorte_role.remove_role(row['person_id'], row['role_type'],
                                 row['adm_enhet'], row['arkivdel'],
                                 row['journalenhet'])
        print "Removing role (%s, %s, %s, %s) for person %s" % (
            row['role_type'], row['adm_enhet'], row['arkivdel'],
            row['journalenhet'], row['person_id'])
    db.commit()
    makedb('ephorte_1_1', 'pre')
    # update manually given roles
    db.query("""
    UPDATE ephorte_role SET auto_role = 'F' where role_type !=
    (SELECT code from ephorte_role_type_code where code_str = 'SB')""")
    # update SB roles
    db.query("""
    UPDATE ephorte_role SET auto_role = 'F' where role_type =
    (SELECT code from ephorte_role_type_code where code_str = 'SB')""")
    db.commit()
    meta = Metainfo.Metainfo(db)
    meta.set_metainfo("sqlmodule_ephorte", "1.1")
    print "Migration to ephorte 1.1 completed successfully"
    db.commit()


def init():
    global db, co

    Factory = Utils.Factory
    db = Factory.get('Database')()
    db.cl_init(change_program="migrate")
    co = Factory.get('Constants')(db)


def show_migration_info():
    init()
    print "Your current db-version is:", get_db_version()
    
    meta = Metainfo.Metainfo(db)
    print "Additional modules with metainfo:"
    mod_prefix = "sqlmodule_"
    for name, value in meta.list():
        if name.startswith(mod_prefix):
            print "  %-20s %s" % (name[len(mod_prefix):], value)
    print "Migration targets:"
    fmt = "  %30s    %30s"
    print fmt % ("Component", "Version")
    print fmt % ("---------", "-------")
    for component, versions in targets.items():
        for v in versions:
            print fmt % (component, v)


def main():
    global makedb_path, design_path
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'r',
                                   ['help', 'releases', 'from=', 'to=',
                                    'makedb-path=', 'design-path=',
                                    'component=',
                                    'no-changelog', 'info'])
    except getopt.GetoptError, e:
        print e
        usage()

    from_rel = to_rel = None
    makedb_path = design_path = None
    component = 'core'
    for opt, val in opts:
        if opt in ('--help',):
            usage(exitcode=0)
        elif opt in ('--component',):
            if val in targets:
                component = val
            else:
                print "Invalid component '%s'.  Valid components are:" % val
                print "\n".join(targets.keys())
        elif opt in ('-r', '--releases',):
            print "\n".join(targets.get(component, []))
            sys.exit()
        elif opt in ('--makedb-path',):
            makedb_path = val
        elif opt in ('--design-path',):
            design_path = val
        elif opt in ('--no-changelog',):
            cereconf.CLASS_CHANGELOG = ('Cerebrum.ChangeLog/ChangeLog',)
        elif opt in ('--from',):
            from_rel = val
        elif opt in ('--to',):
            to_rel = val
        elif opt in ('--info',):
            show_migration_info()
            sys.exit(0)
        else:
            print "Unknown option:", opt
            usage()
    if not (from_rel or to_rel):
        print "You must specify --from and/or --to"
        usage()
    if not (makedb_path and design_path):
        print "You must specify --makedb-path and --design-path"
        usage()

    continue_prompt("Do you have a backup of your '%s' database? (y/n)[y]" % \
                    cereconf.CEREBRUM_DATABASE_NAME)
    init()    
    started = False
    if not from_rel:
        started = True
    for v in targets[component]:
        print v, from_rel, started
        if not started:
            if from_rel == v:   # from is not inclusive
                started = True
        elif started:
            print "Running migrate_to_%s" % v
            globals()["migrate_to_%s" % v]()
            if to_rel == v:
                started = False

def usage(exitcode=64):
    # TBD: --from could be fetched from Metainfo, but do we want that?
    print """Usage: [options]
    Migrates database from one database-schema to another.
    --component: which component to upgrade (default 'core')
    --releases:  list available release names
    --from release_name: migrate from this release
    --to release_name: migrate to this release
    --help: this text
    --makedb-path: directory where makedb.py is
    --design-path: directory where the sql files are
    --no-changelog: don't log the changes to the changelog
    --info: show info about installation, and available migration targets
    
    If --from is omitted, all migrations up to --to is performed.  If
    --to is omitted, all migrations from --from is performed.

    --makedb-path and --design-path are mandatory

    Example:
      migrate_cerebrum_database.py --from rel_0_9_4 --makedb-path \\
        ~/src/cerebrum --design-path ~/src/cerebrum/design
    """
    sys.exit(exitcode)

if __name__ == '__main__':
    main()

# arch-tag: aead5a70-52cf-468b-a9ef-7bb55f6d365c
