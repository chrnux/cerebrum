#! /usr/bin/env python
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

"""
This file performs group membership synchronization between several external
databases and cerebrum.

The updates are performed for the following sources/groups:

External db	table/source				Cerebrum group
----------------------------------------------------------------------
OFPROD		select user_name FROM applsys.fnd_user	ofprod
FSPROD		select username FROM all_users		fsprod
FSSBKURS	select username FROM all_users		fssbkurs
AJPROD		select username FROM all_users		ajprod
OAPRD		select user_name FROM applsys.fnd_user	oaprd
OEPATST		[1], [2], [3], [4], [5]
OEPAPRD         [6], [7]

[1]   basware-users-test:
      select USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'BasWareBrukere' AND upper(DOMAIN) = 'UIO'
[2]   basware-masters-test:
      SELECT USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'Masterbrukere' AND upper(DOMAIN) = 'UIO'
[3]   basware-monitor-test:
      SELECT USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'Monitorbrukere' AND upper(DOMAIN) = 'UIO'
[4]   basware-readsoft-test:
      SELECT USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'Readsoftbrukere' AND upper(DOMAIN) = 'UIO'
[5]   basware-useradmin-test:
      SELECT USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'UserAdminbrukere' AND upper(DOMAIN) = 'UIO'
[6]   basware-users:
      select USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'BasWareBrukere' AND upper(DOMAIN) = 'UIO'
[7]   basware-masters:
      SELECT USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'Masterbrukere' AND upper(DOMAIN) = 'UIO'      

After the update, each group in cerebrum contains only the members listed in
the corresponding external database. That is, if

A -- usernames in the external db but not in cerebrum
B -- usernames in the external db AND cerebrum
C -- usernames NOT in the external db but IN cerebrum

... then only A+B shall be in cerebrum (that is, in the corresponding
cerebrum group from the table above) after the update.

This script produces no output (apart from debug/error messages). All update
information is written back to cerebrum:

<external dbs> -+---> dbfg_update.py ---+
                ^                       |
                |                       |
<cerebrum db> --+                       |
      ^---------------------------------+

Each of the updates can be turned on/off from the command line.
"""

import sys
import string
import getopt
import time

import cerebrum_path
import cereconf
import traceback

import Cerebrum
from Cerebrum import Database
from Cerebrum.Utils import Factory
from Cerebrum.Utils import AtomicFileWriter
from Cerebrum.modules.no.uio.access_FS import FS
from Cerebrum.modules.no.uio.access_OF import OF
from Cerebrum.modules.no.uio.access_AJ import AJ
from Cerebrum.modules.no.uio.access_OA import OA
from Cerebrum.modules.no.uio.access_OEP import OEP





def sanitize_group(cerebrum_group, constants):
    """This helper function removes 'unwanted' members of CEREBRUM_GROUP.

    The groups handled by this script are flat and should contain only
    non-group members. I.e. all group members (of CEREBRUM_GROUP) are deleted.
    """

    removed_count = 0
    for row in cerebrum_group.search_members(group_id=cerebrum_group.entity_id,
                                             member_type=
                                             constants.entity_group):
        member_id = int(row["member_id"])
        logger.error("Aiee! Group id=%s is a member of group %s",
                     member_id, cerebrum_group.group_name)
        cerebrum_group.remove_member(member_id)
        removed_count += 1
        
    logger.info("%d entity(ies) was(were) sanitized from %s",
                removed_count, cerebrum_group.group_name)
# end sanitize_group



def synchronize_group(external_group, cerebrum_group_name):
    """
    This is where all the work is done.

    This function implements direct/immediate (rather then transitive)
    membership only.

    The synchronization is carried out in the following fashion:

    * Construct a set G_c of all members of CEREBRUM_GROUP_NAME
    * for each m in <external_group>:
          if <m does not exist in cerebrum>:
              # Here, an account exists in the external source, but not in
              # Cerebrum. We simply ignore these cases.
              <complain>
          elif <m does not exist in G_c>:
              # Here, the account exists in Cerebrum, but it is not a member
              # of the required group. Therefore we add it.
              <add m to the group>
          # fi

          # This marks m as processed
          <remove m from G_c>
      # od

    * At this step, everything still in G_c exists in Cerebrum, but not in
      the external source. Such entries must be removed from Cerebrum.
      for each n in G_c:
          <remove n from group>
      # od

    Adding an account to a group means:
      1. adding it as a direct 'union'-member.
      2. removing it as a direct 'difference'-member.

    Removing an account from a group means:
      1. removing it as a direct 'union'-member.
      2. removing it as a direct 'intersection'-member.

    NB! All the groups 'touched' by this script are flat. That is, only user
    accounts are members of these groups (not other groups). Furthermore,
    only union-membership is permitted.

    All group-, intersect- and difference members are removed
    automatically. This is intentional.
    """

    try:
        cerebrum_db = Factory.get("Database")()
        cerebrum_db.cl_init(change_program="dbfg_update")
        cerebrum_group = Factory.get("Group")(cerebrum_db)
        cerebrum_account = Factory.get("Account")(cerebrum_db)
        constants = Factory.get("Constants")

        cerebrum_group.find_by_name(cerebrum_group_name)
    except Cerebrum.Errors.NotFoundError:
        logger.error("Aiee! Group %s not found in cerebrum. " +
                     "We will not be able to synchronize it")
        return
    # yrt

    try:
        rows = list(external_group())
    except:
        logger.exception("Failed synchronizing group=%s", cerebrum_group_name)
        return 

    sanitize_group(cerebrum_group, constants)

    new_count = 0
    external_count = 0

    current = construct_group(cerebrum_group)
    for row in external_group():
        external_count += 1

        # FIXME: Ugh! Username cases are different here and there. This
        # assumes that there are no two different accounts whose name
        # differs only in the case. However, there are also accounts with
        # mixed cased in cerebrum. Basically, this means that such accounts
        # would be left out of group synchronization.
        #
        # External sources hand us usernames in uppercase.
        account_name = string.lower(row['username'])

        # Find it in cerebrum
        try:
            cerebrum_account.clear()
            # NB! This one searches among expired and non-expired users
            cerebrum_account.find_by_name(account_name)
        except Cerebrum.Errors.NotFoundError:
            logger.info("%s exists in the external source, but not in Cerebrum",
                        account_name)
        else:
            # Here we now that the account exists in Cerebrum.
            # Is it a member of CEREBRUM_GROUP_NAME already?
            if ((account_name not in current) and
                (not cerebrum_account.get_account_expired())):
                # New member for the group! Add it to Cerebrum
                add_to_cerebrum_group(cerebrum_account, cerebrum_group,
                                      constants)
                new_count += 1
            else:
                # Mark this account as processed
                if account_name in current:
                    del current[account_name]
                # fi
            # fi
        # yrt
    # od

    # Now, all that is left in CURRENT does NOT exist in EXTERNAL_GROUP.
    logger.info("Added %d new account(s) to %s",
                new_count, cerebrum_group.group_name)
    logger.info("%d account(s) from %s need to be removed",
                len(current), cerebrum_group.group_name)
    logger.info("%d account(s) in the external source", external_count)
    for account_name, account_id in current.items():
        try:
            cerebrum_account.clear()
            cerebrum_account.find_by_name(account_name)
        except Cerebrum.Errors.NotFoundError:
            logger.error("Aiee! account (%s, %s) spontaneously disappeared " + 
                         "from (%s, %s)?",
                         account_name, account_id,
                         cerebrum_group.group_name, cerebrum_group.entity_id)
        else:
            remove_from_cerebrum_group(cerebrum_account, cerebrum_group, constants)
        # yrt
    # od

    if dryrun:
        cerebrum_db.rollback()
        logger.info("All changes rolled back")
    else:
        cerebrum_db.commit()
        logger.info("Commited all changes")
    # fi
# end synchronize_group



def remove_from_cerebrum_group(account, group, constants):
    """
    Removes ACCOUNT.ENTITY_ID as a union/intersection member of
    GROUP.ENTITY_ID
    """

    try:
        group.remove_member(int(account.entity_id))
    except:
        # FIXME: How safe is it to do any updates if this happens?
        type, value, tb = sys.exc_info()
        logger.error("Aiee! Removing %s from %s failed: %s, %s, %s",
                     account.account_name,
                     group.group_name,
                     str(type), str(value),
                     string.join(traceback.format_tb(tb)))
    # yrt
# end remove_from_cerebrum_group
        


def add_to_cerebrum_group(account, group, constants):
    """
    Adds the ACCOUNT.ENTITY_ID as a (union) member of GROUP.ENTITY_ID.

    Also, removes difference member ACCOUNT from GROUP, should such a member
    exist (it should not, really, but this is just a precaution).
    """

    logger.debug("Adding 'union' account member %s (%s) to group %s (%s)",
                 account.entity_id, account.account_name,
                 group.entity_id, group.group_name)

    try:
        if not group.has_member(account.entity_id):
            group.add_member(account.entity_id)
    except:
        # FIXME: How safe is it to do any updates if this happens?
        type, value, tb = sys.exc_info()
        logger.error("Aiee! Adding %s to %s failed: %s, %s, %s",
                     account.account_name,
                     group.group_name,
                     str(type), str(value),
                     string.join(traceback.format_tb(tb)))
        
    # yrt
# end 



def construct_group(group):
    """
    This is a helper function that produces a suitable data structure for
    group synchronization.

    Specifically, it returns a dictionary mapping account names to account
    ids
    """

    result = {}
    const = Factory.get("Constants")()
    # IVR 2008-06-25 TBD: Should this be indirect_members=True?
    for row in group.search_members(group_id=group.entity_id,
                                    indirect_members=True,
                                    member_type=const.entity_account):
        account_id = int(row["member_id"])
        # If an account has no name, we are screwed anyway.
        if account_id not in account2name:
            continue
        uname = account2name[account_id]
        result[uname] = account_id

    logger.info("Fetched %d entries for group %s",
                len(result), group.group_name)
    
    return result
# end
    


def perform_synchronization(services):
    """
    Synchronize cerebrum groups with all external SERVICES.
    """

    for item in services:
        service = item["dbname"]
        klass = item["class"]
        accessor_name = item["sync_accessor"]
        cerebrum_group = item["ceregroup"]
        user = item["dbuser"]
        db_charset = item.get("db_charset")

        logger.debug("Synchronizing against source %s (user: %s)",
                     service, user)

        try:
            db = Database.connect(user = user, service = service,
                                  DB_driver = cereconf.DB_DRIVER_ORACLE)
            if db_charset:
                obj = klass(db, db_charset)
            else:
                obj = klass(db)
            accessor = getattr(obj, accessor_name)
        except:
            type, value, tb = sys.exc_info()
            logger.error("Aiee! Failed to connect to %s: %s, %s, %s",
                         service,
                         type, value,
                         string.join(traceback.format_tb(tb)))
            
        else:
            synchronize_group(accessor, cerebrum_group)
# end perform_synchronization



def check_owner_status(person, constants, owner_id, username):
    """
    A help function for report_expired_users.
    """

    try:
        person.clear()
        person.find(owner_id)
    except Cerebrum.Errors.NotFoundError:
        return "Username %s has no owner\n" % username

    # We need to know if person is tilsatt/bilag/gjest.
    # tilsatt => ANSATT-affiliation
    # bilag => ANSATT-affiliation
    # gjest => TILKNYTTET-affiliation
    # As long as there is at least one such affiliation, we are good to go.
    if not person.list_affiliations(person_id=owner_id,
                                    affiliation=(constants.affiliation_ansatt,
                                                 constants.affiliation_tilknyttet),
                                    include_deleted=False):
        return (("Owner of account %s has no tilsetting/bilag/gjest " +
                 "records in POLS\n") % username)

    return ""
# end check_owner_status



def check_expired(account):
    """
    Check if the given account has expired.
    """

    if account.get_account_expired():
        return "Account expired: %s\n" % account.account_name
    # fi

    return ""
# end check_expired



def check_spread(account, sprd):
    """
    Check if the given account has (UiO) NIS spread.
    """

    is_nis = False
    for spread in account.get_spread():
        if int(spread["spread"]) == int(sprd):
            is_nis = True
            break
        # fi
    # od

    if not is_nis:
        return "No spread NIS_user@uio for %s\n" % account.account_name
    # fi

    return ""
# end check_nis_spread

    

def report_users(stream_name, external_dbs):
    """
    Prepare status report about users in various databases.
    """
    
    def report_no_exc(user, report_missing, item, acc_name, *func_list):
        """We don't want to bother with ignore/'"""
        
        try:
            return make_report(user, report_missing, item, acc_name, *func_list)
        except:
            logger.exception("Failed accessing db=%s (accessor=%s):",
                             item["dbname"], acc_name)
            
    db_cerebrum = Factory.get("Database")()
    person = Factory.get("Person")(db_cerebrum)
    constants = Factory.get("Constants")(db_cerebrum)
    user = "ureg2000"

    report_stream = AtomicFileWriter(stream_name, "w")

    #
    # Report expired users for all databases
    for dbname in ("ajprod",):
        item = external_dbs[dbname]
        message = report_no_exc(user, False, item, item["sync_accessor"],
                                     check_expired)
        if message:
            report_stream.write("%s contains these expired accounts:\n" %
                                item["dbname"])
            report_stream.write(message)
            report_stream.write("\n")
        # fi
    # od
        
    #
    # Report NIS spread / owner's work record
    for dbname in ("ofprod", "oaprd", "fsprod", "fssbkurs",
                   "basware-users", "basware-masters"):
        logger.debug("Accessing db %s", dbname)
        item = external_dbs[dbname]
        message = report_no_exc(user, True, item, item["report_accessor"],
                      check_expired,
                      lambda acc: check_spread(acc,
                                               constants.spread_uio_nis_user),
                      lambda acc: check_owner_status(person,
                                                     constants,
                                                     acc.owner_id,
                                                     acc.account_name))
        if message:
            report_stream.write("%s contains these strange accounts:\n" %
                                item["dbname"])
            report_stream.write(message)
            report_stream.write("\n")
        # fi
    # od

    report_stream.close()
# end report_users



import StringIO
def make_report(user, report_missing, item, acc_name, *func_list):
    """
    Help function to generate report stats.
    """

    db_cerebrum = Factory.get("Database")()
    account = Factory.get("Account")(db_cerebrum)
    service = item["dbname"]
    db = Database.connect(user = user, service = service,
                          DB_driver =  cereconf.DB_DRIVER_ORACLE)
    source = item["class"](db)
    accessor = getattr(source, acc_name)
    stream = StringIO.StringIO()

    for db_row in accessor():
        #
        # NB! This is not quite what we want. See comments in sanitize_group
        username = string.lower(db_row["username"])
                
        try:
            account.clear()
            account.find_by_name(username)
        except Cerebrum.Errors.NotFoundError:
            if report_missing:
                stream.write("No such account in Cerebrum: %s\n" % username)
            continue
        # yrt

        for function in func_list:
            message = function(account)
            if message:
                stream.write(message)
            # fi
        # od
    # od

    report_data = stream.getvalue()
    stream.close()
    return report_data
# end make_report



def usage():

    message = """
This script performes updates of certain groups in Cerebrum and fetches
information about certain kind of expired accounts

--ofprod		   update ofprod group
--fsprod		   update fsprod group
--fssbkurs                 update fssbkurs group
--ajprod		   update ajprod group
--oaprd			   update oaprd group
--basware-users            update basware-users group
--basware-masters          update basware-masters group
--basware-monitor-test     update basware-monitor-test group
--basware-readsoft-test    update basware-readsoft-test group
--basware-useradmin-test   update basware-useradmin-test group
--expired-file, -e=file	locate expired accounts and generate a report
"""
    logger.info(message)
# end usage
                
    

def main():
    """
    Start method for this script. 
    """
    global logger

    logger = Factory.get_logger("cronjob")
    logger.info("Performing group synchronization")

    external_dbs = { "ofprod" : { "dbname"    : "OFPROD.uio.no",
                                  "dbuser"    : "ureg2000",
                                  "class"     : OF,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "report_accessor" : "list_applsys_usernames",
                                  "ceregroup" : "ofprod" },
                     "fsprod" : { "dbname"    : "FSPROD.uio.no",
                                  "dbuser"    : "I0185_ureg2000",
                                  "class"     : FS,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "report_accessor" : "list_dba_usernames",
                                  "ceregroup" : "fsprod" },
                     "fssbkurs" : { "dbname"    : "FSSBKURS.uio.no",
                                    "dbuser"    : "ureg2000",
                                    "class"     : FS,
                                    "sync_accessor"  : "list_dbfg_usernames",
                                    "report_accessor" : "list_dba_usernames",
                                    "ceregroup" : "fssbkurs" },                     
                     "ajprod" : { "dbname"    : "AJPROD.uio.no",
                                  "dbuser"    : "ureg2000",
                                  "class"     : AJ,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "ceregroup" : "ajprod" },
                     "oaprd" : { "dbname"    : "OAPRD.uio.no",
                                 "dbuser"    : "ureg2000",
                                 "class"     : OA,
                                 "sync_accessor"  : "list_dbfg_usernames",
                                 "report_accessor" : "list_applsys_usernames",
                                 "ceregroup" : "oaprd" },
                     "basware-users" : { "dbname"        : "OEPAPRD.uio.no",
                                         "dbuser"        : "ureg2000",
                                         "class"         : OEP,
                                         "sync_accessor" : "list_dbfg_users",
                                         "report_accessor" : "list_dbfg_users",
                                         "ceregroup"     : "basware-users",
                                         "db_charset"    : "utf-16-be", },
                     "basware-masters" : { "dbname"        : "OEPAPRD.uio.no",
                                           "dbuser"        : "ureg2000",
                                           "class"         : OEP,
                                           "sync_accessor" : "list_dbfg_masters",
                                           "report_accessor" : "list_dbfg_masters",
                                           "ceregroup"     : "basware-masters",
                                           "db_charset"    : "utf-16-be", },
                     "basware-users-test" : { "dbname"        : "OEPATST.uio.no",
                                              "dbuser"        : "ureg2000",
                                              "class"         : OEP,
                                              "sync_accessor" : "list_dbfg_users",
                                              "report_accessor" : "list_dbfg_users",
                                              "ceregroup"     : "basware-users-test", },
                     "basware-masters-test" : { "dbname"        : "OEPATST.uio.no",
                                                "dbuser"        : "ureg2000",
                                                "class"         : OEP,
                                                "sync_accessor" : "list_dbfg_masters",
                                                "report_accessor" : "list_dbfg_masters",
                                                "ceregroup"     : "basware-masters-test", },
                     "basware-monitor-test" : { "dbname"        : "OEPATST.uio.no",
                                                "dbuser"        : "ureg2000",
                                                "class"         : OEP,
                                                "sync_accessor" : "list_dbfg_monitor",
                                                "report_accessor" : "list_dbfg_monitor",
                                                "ceregroup"     : "basware-monitor-test", },
                     "basware-readsoft-test" : { "dbname"        : "OEPATST.uio.no",
                                                 "dbuser"        : "ureg2000",
                                                 "class"         : OEP,
                                                 "sync_accessor" : "list_dbfg_readsoft",
                                                 "report_accessor" : "list_dbfg_readsoft",
                                                 "ceregroup"     : "basware-readsoft-test", },
                     "basware-useradmin-test" : { "dbname"        : "OEPATST.uio.no",
                                                  "dbuser"        : "ureg2000",
                                                  "class"         : OEP,
                                                  "sync_accessor" : "list_dbfg_useradmin",
                                                  "report_accessor" : "list_dbfg_useradmin",
                                                  "ceregroup"     : "basware-useradmin-test", },
                     "basware-monitor" : { "dbname"        : "OEPAPRD.uio.no",
                                           "dbuser"        : "ureg2000",
                                           "class"         : OEP,
                                           "sync_accessor" : "list_dbfg_monitor",
                                           "report_accessor" : "list_dbfg_monitor",
                                           "ceregroup"     : "basware-monitor",
                                           "db_charset"    : "utf-16-be", },
                     "basware-readsoft" : { "dbname"        : "OEPAPRD.uio.no",
                                            "dbuser"        : "ureg2000",
                                            "class"         : OEP,
                                            "sync_accessor" : "list_dbfg_readsoft",
                                            "report_accessor" : "list_dbfg_readsoft",
                                            "ceregroup"     : "basware-readsoft",
                                            "db_charset"    : "utf-16-be", },
                     "basware-useradmin" : { "dbname"        : "OEPAPRD.uio.no",
                                             "dbuser"        : "ureg2000",
                                             "class"         : OEP,
                                             "sync_accessor" : "list_dbfg_useradmin",
                                             "report_accessor" : "list_dbfg_useradmin",
                                             "ceregroup"     : "basware-useradmin",
                                             "db_charset"    : "utf-16-be", },
                     }
    try:
        options, rest = getopt.getopt(sys.argv[1:],
                                      "dhe:",
                                      ["dryrun",
                                       "help",
                                       "expired-file="] + external_dbs.keys())
    except getopt.GetoptError:
        usage()
        raise
        sys.exit(1)
    # yrt

    services = []
    global dryrun
    dryrun = False

    for option, value in options:
        if option in ("-d", "--dryrun"):
            dryrun = True
        elif option in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif option in ("-e", "--expired-file"):
            report_users(value, external_dbs)
        elif option in [ "--" + x for x in external_dbs.keys() ]:
            key = option[2:]
            services.append( external_dbs[key] )

    # preload the account id -> uname mappings used later.
    db = Factory.get("Database")()
    const = Factory.get("Constants")()
    group = Factory.get("Group")(db)
    global account2name
    account2name = dict((x["entity_id"], x["entity_name"]) for x in 
                        group.list_names(const.account_namespace))

    perform_synchronization(services)
# end main





if __name__ == "__main__":
    main()
