# -*- coding: iso-8859-1 -*-

# Copyright 2004, 2005 University of Oslo, Norway
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
from lib.utils import commit, commit_url, object_link
from lib.utils import transaction_decorator, redirect_object
from lib.utils import spine_to_web, web_to_spine
from lib.Searchers import DiskSearcher
from lib.templates.SearchTemplate import SearchTemplate
from lib.templates.DiskViewTemplate import DiskViewTemplate
from lib.templates.DiskEditTemplate import DiskEditTemplate
from lib.templates.DiskCreateTemplate import DiskCreateTemplate

def search_form(remembered):
    page = SearchTemplate()
    page.title = _("Disk")
    page.set_focus("disk/search")
    page.search_title = _('disk(s)')
    page.search_fields = [("path", _("Path")),
                          ("description", _("Description"))
                        ]
    page.search_action = '/disk/search'
    page.form_values = remembered
    return page.respond()
    
def search(transaction, **vargs):
    """Search after disks and displays result and/or searchform."""
    args = ('path', 'description')
    searcher = DiskSearcher(transaction, *args, **vargs)
    return searcher.respond() or search_form(searcher.get_remembered())

search = transaction_decorator(search)
search.exposed = True
index = search

def view(transaction, id):
    """Creates a page with a view of the disk given by id."""
    disk = transaction.get_disk(int(id))
    page = DiskViewTemplate()
    page.title = _('Disk %s') % spine_to_web(disk.get_path())
    page.set_focus('disk/view')
    page.entity_id = int(id)
    page.entity = disk
    page.tr = transaction

    return page.respond()
view = transaction_decorator(view)
view.exposed = True

def edit(transaction, id):
    """Creates a page with the form for editing a disk."""
    disk = transaction.get_disk(int(id))
    page = Main()
    disk_name = spine_to_web(disk.get_name())
    page.title = _("Edit ") + object_link(disk, text=disk_name)
    page.set_focus("disk/edit")

    edit = DiskEditTemplate()
    content = edit.editDisk(disk)
    page.content = lambda: content
    return page
edit = transaction_decorator(edit)
edit.exposed = True

def save(transaction, id, path="", description="", submit=None):
    """Saves the information for the disk."""
    disk = transaction.get_disk(int(id))

    if submit == 'Cancel':
        redirect_object(disk)
        return
    if path:
        path = web_to_spine(path.strip())
    disk.set_path(path)
    if description:
        description = web_to_spine(description.strip())
    disk.set_description(description)
    
    commit(transaction, disk, msg=_("Disk successfully updated."))
save = transaction_decorator(save)
save.exposed = True

def create(transaction, host=""):
    """Creates a page with the form for creating a disk."""
    page = Main()
    page.title = _("Disk")
    page.set_focus("disk/create")

    hosts = [(html_quote(i.get_id()), spine_to_web(i.get_name())) for i in
                    transaction.get_host_searcher().search()]

    create = DiskCreateTemplate()
    if host:
        create.formvalues = {'host': int(host)}
    content = create.form(hosts)
    page.content = lambda: content
    return page
create = transaction_decorator(create)
create.exposed = True

def make(transaction, host, path="", description=""):
    """Creates the host."""
    host = transaction.get_host(int(host))
    thePath = web_to_spine(path.strip())
    desc = web_to_spine(description.strip())
    disk = transaction.get_commands().create_disk(host, thePath, desc)
    commit(transaction, disk, msg=_("Disk successfully created."))
make = transaction_decorator(make)
make.exposed = True

def delete(transaction, id):
    """Delete the disk from the server."""
    disk = transaction.get_disk(int(id))
    msg = _("Disk '%s' successfully deleted.") % spine_to_web(disk.get_path())
    disk.delete()
    commit_url(transaction, 'index', msg=msg)
delete = transaction_decorator(delete)
delete.exposed = True

# arch-tag: 6cf3413e-3bf4-11da-9d43-c8c980cc74d7
