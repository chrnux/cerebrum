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
import string

from account import _get_links
from gettext import gettext as _
from lib.utils import queue_message, redirect_object, commit
from lib.utils import object_link, transaction_decorator, commit_url
from lib.utils import rollback_url, legal_date, remember_link
from lib.utils import spine_to_web, web_to_spine, session_required_decorator
from lib.Searchers import GroupSearcher
from lib.templates.GroupSearchTemplate import GroupSearchTemplate
from lib.templates.GroupViewTemplate import GroupViewTemplate
from lib.templates.NewGroupViewTemplate import NewGroupViewTemplate
from lib.templates.GroupCreateTemplate import GroupCreateTemplate
from SpineIDL.Errors import NotFoundError, AlreadyExistsError, ValueError

from lib.data import GroupDAO
from lib.data import HistoryDAO
from lib.data import ConstantsDAO
from lib.data import HostDAO

def search_form(remembered):
    page = GroupSearchTemplate()
    page.title = _("Group")
    page.search_title = _('group(s)')   
    page.set_focus("group/search")
    page.links = _get_links()
    page.jscripts.append("groupsearch.js")
    page.search_fields = [("name", _("Name")),
                          ("description", _("Description")),
                          ("spread", _("Spread name")),
                          ]
    page.search_action = '/group/search'
    page.form_values = remembered
    return page.respond()

def search(transaction, **vargs):
    """Search for groups and displays results and/or searchform."""
    args = ('name', 'description', 'spread', 'gid', 'gid_end', 'gid_option')
    searcher = GroupSearcher(transaction, *args, **vargs)
    return searcher.respond() or search_form(searcher.get_remembered())
search = transaction_decorator(search)
search.exposed = True
index = search

def view2(id, **vargs):
    page = NewGroupViewTemplate()
    page.group = GroupDAO.get(id)
    page.group.history = HistoryDAO.get_entity_history(id)
    page.visibilities = ConstantsDAO.get_group_visibilities()
    page.spreads = ConstantsDAO.get_group_spreads()
    page.email_target_types = ConstantsDAO.get_email_target_types()
    page.email_servers = HostDAO.get_email_servers()
    page.targets = HostDAO.get_email_targets(id)
    
    return page.respond()
view2 = session_required_decorator(view2)
view2.exposed = True

def view(transaction, id, **vargs):
    """Creates a page with the view of the group with the given by."""
    group = transaction.get_group(int(id))
    page = GroupViewTemplate()
    page.tr = transaction
    page.title = _('Group %s') % spine_to_web(group.get_name())
    page.set_focus('group/view')
    page.links = _get_links()
    page.entity_id = int(id)
    page.entity = group
    return page.respond()
view = transaction_decorator(view)
view.exposed = True
    
def add_member(transaction, id, name, type):
    group = transaction.get_group(int(id))
    cmd = transaction.get_commands()
    
    search = transaction.get_entity_name_searcher()
    if name:
        name = web_to_spine(name.strip())
    search.set_name(name)
    search.set_value_domain(cmd.get_namespace(web_to_spine(type)))
    try:
        entity_name, = search.search()
    except ValueError, e:
        queue_message(_("Could not find %s %s") % (type, name), True)
        redirect_object(group)
        return
    
    entity = entity_name.get_entity()
    try:
        group.add_member(entity)
    except AlreadyExistsError, e:
        msg = _("Entity is already a member of group %s") % name
        queue_message(msg, True, object_link(entity))
        redirect_object(entity)
    entity_name = spine_to_web(entity.get_name())
    msg = _("%s added as a member to group.") % object_link(entity, text=entity_name)
    commit(transaction, group, msg=msg)
add_member = transaction_decorator(add_member)
add_member.exposed = True

def remove_member(transaction, groupid, memberid):
    group = transaction.get_group(int(groupid))
    member = transaction.get_entity(int(memberid))

    group.remove_member(member)
    member_name = spine_to_web(member.get_name())
    msg = _("%s removed from group.") % object_link(member, text=member_name)
    commit(transaction, group, msg=msg)
remove_member = transaction_decorator(remove_member)
remove_member.exposed = True

def create(name="", expire="", description=""):
    """Creates a page with the form for creating a group."""
    page = GroupCreateTemplate()
    page.title = _("Group")
    page.set_focus('group/create')
    page.links = _get_links()

    page.data = {
        'name': name,
        'expire': expire,
        'description': description,
    }
    
    return page.respond()
create.exposed = True

def save(transaction, id, name, expire="",
         description="", visi="", gid=None, submit=None):
    """Save the changes to the server."""
    group = transaction.get_group(int(id))
    c = transaction.get_commands()
    
    if submit == 'Cancel':
        redirect_object(group)
        return
    
    if expire:
        expire = c.strptime(expire, "%Y-%m-%d")
    else:
	expire = None
    group.set_expire_date(expire)

    if gid is not None and group.is_posix():
        group.set_posix_gid(int(gid))

    if visi:
        visibility = transaction.get_group_visibility_type(visi)
        group.set_visibility(visibility)

    group.set_name(web_to_spine(name.strip()))
    group.set_description(web_to_spine(description.strip()))
    
    commit(transaction, group, msg=_("Group successfully updated."))
save = transaction_decorator(save)
save.exposed = True

def make(transaction, name, expire="", description=""):
    """Performs the creation towards the server."""
    msg=''
    if name:
        if len(name) < 3:
            msg=_("Group-name is too short( min. 3 characters).")
        elif len(name) > 16:
            msg=_("Group-name is too long(max. 16 characters).")
    else:
        msg=_("Group-name is empty.")
    if not msg and expire:
        if not legal_date( expire ):
            msg=_("Expire-date is not a legal date.")
    if not msg:
        commands = transaction.get_commands()
        try:
            group = commands.create_group(web_to_spine(name.strip()))
        except ValueError, e:
            msg = _("Group '%s' already exists.") % name
    if not msg:    
        if expire:
            expire = commands.strptime(expire, "%Y-%m-%d")
            group.set_expire_date(expire)

        if description:
            group.set_description(web_to_spine(description.strip()))
        commit(transaction, group, msg=_("Group successfully created."))
    else:
        rollback_url('/group/create', msg, err=True)
make = transaction_decorator(make)
make.exposed = True

def posix_promote(transaction, id):
    group = transaction.get_group(int(id))
    group.promote_posix()
    msg = _("Group successfully promoted to posix.")
    commit(transaction, group, msg=msg)
posix_promote = transaction_decorator(posix_promote)
posix_promote.exposed = True

def posix_demote(transaction, id):
    group = transaction.get_group(int(id))
    group.demote_posix()
    msg = _("Group successfully demoted from posix.")
    commit(transaction, group, msg=msg)
posix_demote = transaction_decorator(posix_demote)
posix_demote.exposed = True

def delete(transaction, id):
    """Delete the group from the server."""
    group = transaction.get_group(int(id))
    grp_name = spine_to_web(group.get_name())
    msg = _("Group '%s' successfully deleted.") % grp_name
    group.delete()
    commit_url(transaction, 'index', msg=msg)
delete = transaction_decorator(delete)
delete.exposed = True

def join_group(transaction, entity, name):
    """Join entity into group with name 'group'."""
    entity = transaction.get_entity(int(entity))
    try:
        # find the group by name.
        grp_name = web_to_spine(name.strip())
        group = transaction.get_commands().get_group_by_name(grp_name)
        group.add_member(entity)
    except NotFoundError, e:
        msg = _("Group '%s' not found") % name
        queue_message(msg, True, object_link(entity))
        redirect_object(entity)
    except AlreadyExistsError, e:
        msg = _("Entity is already a member of group %s") % name
        queue_message(msg, True, object_link(entity))
        redirect_object(entity)

    msg = _('Joined group %s successfully') % name
    commit(transaction, entity, msg=msg)
join_group = transaction_decorator(join_group)
join_group.exposed = True

# arch-tag: d14543c1-a7d9-4c46-8938-c22c94278c34
