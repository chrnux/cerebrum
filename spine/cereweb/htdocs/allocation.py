# -*- coding: iso-8859-1 -*-

# Copyright 2006 University of Oslo, Norway
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

import cherrypy

from gettext import gettext as _
from lib.Main import Main
from lib.utils import commit, commit_url, queue_message, object_link
from lib.utils import transaction_decorator, redirect, redirect_object
from lib.WorkList import remember_link
from lib.Search import get_arg_values, get_form_values, setup_searcher
from lib.templates.SearchResultTemplate import SearchResultTemplate
from lib.templates.AllocationSearchTemplate import AllocationSearchTemplate
from lib.templates.AllocationViewTemplate import AllocationViewTemplate
from lib.templates.AllocationEditTemplate import AllocationEditTemplate
#from lib.templates.AllocationCreateTemplate import AllocationCreateTemplate

def search(transaction, offset=0, **vargs):
    """Search for allocations and displays result and/or searchform."""
    page = Main()
    page.title = _("Search for allocation(s)")
    page.setFocus("allocation/search")
    page.add_jscript("search.js")

    searchform = AllocationSearchTemplate()
    arguments = ['allocation_name', 'period', 'status', 'machines',
                 'orderby', 'orderby_dir']
    values = get_arg_values(arguments, vargs)
    perform_search = len([i for i in values if i != ""])

    if perform_search:
        cherrypy.session['allocation_ls'] = values
        allocation_name, period, status, machines, orderby, orderby_dir = values

        searcher = transaction.get_allocation_searcher()
        setup_searcher([searcher], orderby, orderby_dir, offset)

        if allocation_name:
            an_searcher = transaction.get_project_allocation_name_searcher()
            an_searcher.set_name_like(allocation_name)
            searcher.add_join('allocation_name', an_searcher, '')

        #XXX status
        #XXX period

        allocations = searcher.search()

        result = []

        display_hits = cherrypy.session['options'].getint('search', 'display hits')
        # XXX
        for allocation in allocations[:display_hits]:
            edit = object_link(allocation, text='edit', method='edit', _class='actions')
            remb = remember_link(allocation, _class='actions')
            proj = object_link(allocation.get_allocation_name().get_project())
            period = allocation.get_period().get_name()
            status = allocation.get_status().get_name()
            machines = [m.get_name() for m in allocation.get_machines()]
            result.append((object_link(allocation), period, status,
                           "("+",".join(machines)+")",
                           str(edit) + str(remb)))

        headers = [('Allocation name', 'allocation_name'),
                   ('Period', 'period'),
                   ('Status', 'status'),
                   ('Machines', 'machines'),
                   ('Actions', '')]

        template = SearchResultTemplate()
        table = template.view(result, headers, arguments, values,
            len(allocations), display_hits, offset, searchform, 'search')

        page.content = lambda: table
    else:
        rmb_last = cherrypy.session['options'].getboolean('search', 'remember last')
        if 'allocation_ls' in cherrypy.session and rmb_last:
            values = cherrypy.session['allocation_ls']
            searchform.formvalues = get_form_values(arguments, values)
        page.content = searchform.form
    
    return page

search = transaction_decorator(search)
search.exposed = True
index = search

def view(transaction, id):
    """Creates a page with a view of the allocation given by id."""
    allocation = transaction.get_allocation(int(id))
    page = Main()
    page.title = _('Allocation %s %s') % (
        allocation.get_allocation_name().get_name(),
        allocation.get_period().get_name() )
    page.setFocus('allocation/view', id)
    content = AllocationViewTemplate().view(transaction, allocation)
    page.content = lambda: content
    return page
view = transaction_decorator(view)
view.exposed = True

def edit(transaction, id):
    """Creates a page with the form for editing a allocation."""
    allocation = transaction.get_allocation(int(id))
    page = Main()
    page.title = _("Edit ") + object_link(allocation)
    page.setFocus("allocation/edit", id)

    edit = AllocationEditTemplate()
    content = edit.editAllocation(allocation,transaction)
    page.content = lambda: content
    return page
edit = transaction_decorator(edit)
edit.exposed = True

def save(transaction, id, title="", description="", owner=None,
         science=None, submit=None):
    """Saves the information for the allocation."""
    allocation = transaction.get_allocation(int(id))

    if submit == 'Cancel':
        redirect_object(allocation)

    #XXX allocation.set_allocation_name( XXX...)
    #XXX allocation.set_period(period)

    allocation.set_status(transaction.get_allocation_status(status))
    commit(transaction, allocation, msg=_("Allocation successfully updated."))
save = transaction_decorator(save)
save.exposed = True

def create(transaction, title="", description="", owner=None, science=None):
    """Creates a page with the form for creating a allocation"""
    page = Main()
    page.title = _("Create a new allocation")
    page.setFocus("allocation/create")

    # Store given create parameters in create-form
    values = {}
    values['title'] = title
    values['description'] = description
    values['owner'] = owner
    values['science'] = science

    create = AllocationCreateTemplate(searchList=[{'formvalues': values}])

    content = create.form(transaction)
    page.content = lambda: content
    return page
create = transaction_decorator(create)
create.exposed = True

def make(transaction, title="", description="", owner=None, science=None):
    """Creates the allocation."""

    science = transaction.get_science(science)
    # XXX owner
    
    cmd = transaction.get_commands()
    allocation = cmd.create_allocation(owner, science,
                                 title, description)

    commit(transaction, host, msg=_("Allocation successfully created."))
make = transaction_decorator(make)
make.exposed = True

def delete(transaction, id):
    """Delete the allocation from the server."""
    allocation = transaction.get_allocation(int(id))
    msg = _("Allocation '%s' successfully deleted.") % allocation.get_title()
    allocation.delete()
    commit_url(transaction, 'index', msg=msg)
delete = transaction_decorator(delete)
delete.exposed = True

