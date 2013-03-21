# -*- coding: iso-8859-1 -*-
# 
# Copyright 2013 University of Oslo, Norway
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
"""Help text for bofhd in the TSD project."""

from Cerebrum.modules.no.uio.bofhd_uio_help import group_help
from Cerebrum.modules.no.uio.bofhd_uio_help import command_help
from Cerebrum.modules.no.uio.bofhd_uio_help import arg_help

# Add instance specific help text:

group_help['project'] = 'Project related commands'

# The texts in command_help are automatically line-wrapped, and should
# not contain \n
command_help['user'].update({
    'user_approve': 
        'Activate a user in the systems, after checking',
    'user_set_otpkey':
        'Regenerate a One Time Password (OTP) key for an account',
    })

command_help['project'] = {
    'project_create':
        'Create a new project manually',
    'project_approve':
        'Approve a project with the given name',
    'project_freeze_request':
        'Add a BofhdRequest for freezing a project',
    'project_list':
        'List all projects according to given filter',
    'project_set_enddate':
        'Reset the end date for a project',
    'project_terminate':
        'Terminate a project by removing all data',
    }

arg_help.update({
    'project_name':
        ['projectname', 'Project name',
         'Short, unique name of the project, around 6 digits'],
    'project_longname':
        ['longname', "Project's full name",
         'The full, long name of the project'],
    'project_shortname':
        ['shortname', "Project's short name",
         'The short, descriptive name of the project'],
    'project_start_date':
        ['startdate', "Project's start date",
         'The day the project should be activated'],
    'project_end_date':
        ['enddate', "Project's end date",
         'The day the project should be ended and frozen'],
    'project_statusfilter':
        ['filter', 'Filter on project status',
         'Not implemented yet'],
    })

