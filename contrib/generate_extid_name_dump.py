#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
# vim: encoding=iso-8859-1:fileencoding=iso-8859-1
# vim: ts=4:sw=4:expandtab
# 
# Copyright 2012 University of Oslo, Norway
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

"""This script produces a dump of names and external ID's from a source system.
The dump is colon-separated data with the external ID and name of the person
tied to the ID.

Eg. To dump all employee-numbers from SAP:
    <scipt name> -s SAP -t NO_SAPNO

will produce a file:
    9831:Ola Normann:7321:Kari Normann:<employee_no>:<employee_name>...
"""

import sys
import getopt

import cerebrum_path
import cereconf
from Cerebrum.Utils import Factory
from Cerebrum import Errors


# Get logger
logger = Factory.get_logger('cronjob')

# Database-setup
db = Factory.get('Database')()
pe = Factory.get('Person')(db)
co = Factory.get('Constants')(db)


def usage():
    """Prints a usage string for the script."""

    print """Usage:
    %s [Options]

    Generate a colon-separated file with employee ids and employee names.

    Options:
    -o, --output <file>            The file to print the report to. Defaults to 
                                   stdout.

    -s, --source_system <code>     The code name for the source system.
    -t, --id_type <code>           The code name for the external ID type.
    """ % sys.argv[0]


#def resolve_preferred_name(entity_id):

    #systems = [getattr(co, system) for system in cereconf.SYSTEM_LOOKUP_ORDER]

    #pe.clear()
    #pe.find(entity_id)

    #name = ''

    #for s in systems:
        #fname = ''
        #lname = ''
        #try:
            #name = pe.get_name(s, co.name_full)
        #except Errors.NotFoundError:
            #pass

        #try:
            #fname = pe.get_name(s, co.name_first)
        #except Errors.NotFoundError:
            #pass

        #try:
            #lname = pe.get_name(s, co.name_last)
        #except Errors.NotFoundError:
            #pass

        #if name:
            #break

        #if fname and lname:
            #name = "%s %s" % (fname, lname)
            #break

    #return name


def getdict_external_ids(source_system, id_type):
    """Fetches a list of employees with employee number.
    
    @type  logger: CerebrumLogger
    @param logger: Logger to use.

    @type  source_sys: Subclass of Constants.AuthoritativeSystem
    @param source_sys: The authorative system to list

    @type  id_type: Subclass of Constants.EntityExternalId
    @param id_type: The external ID type to list

    @rtype:  list
    @return: A list of dictionary objects with the keys:
               'entity_id' -> <int> Entity id of the person
               'ext_id'    -> <string> External id
               'name'      -> <string> Full name of the employee
    """

    ext_ids = [] # Return list

    employees = pe.list_external_ids(source_system=source_system, 
                                     id_type=id_type, 
                                     entity_type=co.entity_person)

    # Name lookup dict
    names = pe.getdict_persons_names(source_system=co.system_cached, 
                                     name_types=co.name_full)

    for employee in employees:
        try:
            name = names[employee['entity_id']][int(co.name_full)]
        except KeyError:
            logger.warn("No name for person with external id '%d'. \
                         Excluded from list" % employee['entity_id'])
            continue

        # Each entry in the result list is a dictionary:
        tmp = {
                 'entity_id': employee['entity_id'],
                 'ext_id':    employee['external_id'],
                 'name':      name
              }
    
        ext_ids.append(tmp)
    print len(ext_ids)
    return ext_ids


def write_dump_file(output, employees):
    """Writes a list of employees to a file object
    
    @type  logger: CerebrumLogger
    @param logger: Logger to use.

    @type  output: file
    @param output: Output file handle to write to

    @type  employees: list
    @param employees: List of dictionary objects, each dictionary must contain:
                        'ext_id' -> <string> External id
                        'name'   -> <string> Full name of the employee
    """

    first = employees.pop(0)
    if first:
        output.write("%s:%s" % (first['ext_id'], first['name']))

    for employee in employees:
        output.write(":%s:%s" % (employee['ext_id'], employee['name']))


def main(argv=None):
    """Main runtime as a function, for invoking the script from other scripts /
    interactive python session.
    
    @type  argv: List of string arguments.
    @param argv: Script args, see 'usage' for details. Defaults to 'sys.argv'
    """

    # Default opts
    output = sys.stdout
    source_system = None
    id_type = None

    ## Parse args
    if not argv:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], 
                                   "s:t:o:", 
                                   ["source_system=", "id_type=", "output="])
    except getopt.GetoptError, e:
        logger.error(e)
        usage()
        return 1

    for o, v in opts:
        if o in ('-o', '--output'):
            try:
                output = open(v, 'w')
            except IOError, e:
                logger.error(e)
                sys.exit(1)

        elif o in ('-s', '--source_system'):
            source_system = co.human2constant(v, co.AuthoritativeSystem)
            if not source_system:
                logger.warn("No source system matching '%s'" % v)

        elif o in ('-t', '--id_type'):
            id_type = co.human2constant(v, co.EntityExternalId)
            if not id_type:
                logger.warn("No external ID type matching '%s'" % v)

    # Check that source system and external id type is set
    if not source_system:
        logger.error("No valid source system provided")
        sys.exit(1)

    if not id_type:
        logger.error("No valid external ID type provided")
        sys.exit(1)
    

    # Generate selected report
    logger.info("Start dumping external id's")
    external_ids = getdict_external_ids(source_system, id_type)
    write_dump_file(output, external_ids)
    logger.info("Done dumping external id's")


    # Close output if we explicitly opened a file for writing
    if not output is sys.stdout:
        output.close()


# If started as a program
if __name__ == "__main__":
    sys.exit(main())

