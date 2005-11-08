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

import forgetHTML as html
from gettext import gettext as _
from Cereweb.Main import Main
from Cereweb.utils import url, queue_message, redirect, redirect_object
from Cereweb.utils import transaction_decorator, object_link, commit, commit_url
from Cereweb.WorkList import remember_link
from Cereweb.Search import get_arg_values, get_form_values, setup_searcher
from Cereweb.templates.SearchResultTemplate import SearchResultTemplate
from Cereweb.templates.PersonSearchTemplate import PersonSearchTemplate
from Cereweb.templates.PersonViewTemplate import PersonViewTemplate
from Cereweb.templates.PersonEditTemplate import PersonEditTemplate
from Cereweb.templates.PersonCreateTemplate import PersonCreateTemplate

def index(req):
    """Redirects to the search for person page."""
    return search(req)

def search(req, transaction, offset=0, **vargs):
    """Search after hosts and displays result and/or searchform."""
    #FIXME: orderby name
    page = Main(req)
    page.title = _("Search for person(s)")
    page.setFocus("person/search")
    page.add_jscript("search.js")

    searchform = PersonSearchTemplate()
    arguments = ['name', 'accountname', 'birthdate',
                 'spread', 'orderby', 'orderby_dir']
    values = get_arg_values(arguments, vargs)
    perform_search = len([i for i in values if i != ""])

    if perform_search:
        req.session['person_ls'] = values
        name, accountname, birthdate, spread, orderby, orderby_dir = values

        search = transaction.get_person_searcher()
        setup_searcher([search], orderby, orderby_dir, offset)

        if accountname:
            searcher = transaction.get_account_searcher()
            searcher.set_name_like(accountname)
            search.add_intersection('', searcher, 'owner')
            
        if birthdate:
            date = transaction.get_commands().strptime(birthdate, "%Y-%m-%d")
            search.set_birth_date(date)

        if name:
            name_searcher = transaction.get_person_name_searcher()
            name_searcher.set_name_like(name)
            search.add_intersection('', name_searcher, 'person')

        if spread:
            person_type = transaction.get_entity_type('person')

            searcher = transaction.get_entity_spread_searcher()
            searcher.set_entity_type(person_type)

            spreadsearcher = transaction.get_spread_searcher()
            spreadsearcher.set_entity_type(person_type)
            spreadsearcher.set_name_like(spread)

            searcher.add_join('spread', spreadsearcher, '')
            search.add_intersection('', searcher, 'entity')

        persons = search.search()

        result = []
        display_hits = req.session['options'].getint('search', 'display hits')
        for person in persons[:display_hits]:
            date = person.get_birth_date().strftime('%Y-%m-%d')
            accounts = [str(object_link(i)) for i in person.get_accounts()[:4]]
            accounts = ', '.join(accounts[:3]) + (len(accounts) == 4 and '...' or '')
            edit = object_link(person, text='edit', method='edit', _class='actions')
            remb = remember_link(person, _class="actions")
            result.append((object_link(person), date, accounts, str(edit)+str(remb)))

        headers = [('Name', ''), ('Date of birth', 'birth_date'),
                   ('Account(s)', ''), ('Actions', '')]

        template = SearchResultTemplate()
        table = template.view(result, headers, arguments, values,
            len(persons), display_hits, offset, searchform, 'person/search')

        page.content = lambda: table
    else:
        rmb_last = req.session['options'].getboolean('search', 'remember last')
        if 'person_ls' in req.session and rmb_last:
            values = req.session['person_ls']
            searchform.formvalues = get_form_values(arguments, values)
        page.content = searchform.form

    return page
search = transaction_decorator(search)

def _primary_name(person):
    """Returns the primary display name for the person."""
    #until such an thing is set in the database, we just use this method.
    names = {}
    for name in person.get_names():
        names[name.get_name_variant().get_name()] = name.get_name()
    for type in ["FULL", "LAST", "FIRST"]:
        if names.has_key(type):
            return names[type]
    return "unknown name"

def _get_person(req, transaction, id):
    """Returns a Person-object from the database with the specific id."""
    try:
        return transaction.get_person(int(id))
    except Exception, e:
        queue_message(req, _("Could not find person with id=%s") % id, True)
        redirect(req, url("person"), temporary=True)

def view(req, transaction, id, addName=False, addAffil=False):
    """Creates a page with a view of the person given by id.

    If addName is True or "True", the form for adding a name is shown.
    If addAffil is True or "True", the form for adding an affiliation is shown.
    """
    person = transaction.get_person(int(id))
    page = Main(req)
    page.title = _("Person %s" % _primary_name(person))
    page.setFocus("person/view", id)
    view = PersonViewTemplate()
    content = view.viewPerson(transaction, person, addName, addAffil)
    page.content = lambda: content
    return page
view = transaction_decorator(view)

def edit(req, transaction, id):
    """Creates a page with the form for editing a person."""
    person = transaction.get_person(int(id))
    page = Main(req)
    page.title = _("Edit ") + object_link(person)
    page.setFocus("person/edit", id)

    genders = [(g.get_name(), g.get_description()) for g in 
               transaction.get_gender_type_searcher().search()]

    edit = PersonEditTemplate()
    content = edit.editPerson(person, genders)
    page.content = lambda: content
    return page
edit = transaction_decorator(edit)

def create(req, transaction):
    """Creates a page with the form for creating a person."""
    page = Main(req)
    page.title = _("Create a new person")
    page.setFocus("person/create")

    genders = [(g.get_name(), g.get_description()) for g in 
               transaction.get_gender_type_searcher().search()]
    
    genders = [(g.get_name(), g.get_description()) for g in 
               transaction.get_gender_type_searcher().search()]
    
    create = PersonCreateTemplate()
    content = create.form(genders)
    page.content = lambda: content
    return page
create = transaction_decorator(create)

def save(req, transaction, id, gender, birthdate,
         deceased="", description="", submit=None):
    """Store the form for editing a person into the database."""
    person = transaction.get_person(int(id))

    if submit == "Cancel":
        redirect_object(req, person, seeOther=True)
        return
    
    person.set_gender(transaction.get_gender_type(gender))
    person.set_birth_date(transaction.get_commands().strptime(birthdate, "%Y-%m-%d"))
    person.set_description(description)
    
    if deceased:
        deceased = transaction.get_commands().strptime(deceased, "%Y-%m-%d")
    else:
        deceased = transaction.get_commands().get_date_none()
        
    person.set_deceased_date(deceased)
    
    commit(transaction, req, person, msg=_("Person successfully updated."))
save = transaction_decorator(save)

def make(req, transaction, name, gender, birthdate, description=""):
    """Create a new person with the given values."""
    birthdate = transaction.get_commands().strptime(birthdate, "%Y-%m-%d")
    gender = transaction.get_gender_type(gender)
    source_system = transaction.get_source_system('Manual')
    
    person = transaction.get_commands().create_person(
               birthdate, gender, name, source_system)

    if description:
        person.set_description(description)
    
    commit(transaction, req, person, msg=_("Person successfully created."))
make = transaction_decorator(make)

def delete(req, transaction, id):
    """Delete the person from the server."""
    person = transaction.get_person(int(id))
    msg = _("Person '%s' successfully deleted.") % _primary_name(person)
    person.delete()
    commit_url(transaction, req, url("person/index"), msg=msg)
delete = transaction_decorator(delete)

def add_name(req, transaction, id, name, name_type):
    """Add a new name to the person with the given id."""
    person = transaction.get_person(int(id))

    name_type = transaction.get_name_type(name_type)
    source_system = transaction.get_source_system('Manual')
    person.set_name(name, name_type, source_system)

    commit(transaction, req, person, msg=_("Name successfully added."))
add_name = transaction_decorator(add_name)

def remove_name(req, id, transaction, variant, ss):
    """Remove the name with the given values."""
    person = transaction.get_person(int(id))
    variant = transaction.get_name_type(variant)
    ss = transaction.get_source_system(ss)

    person.remove_name(variant, ss)

    commit(transaction, req, person, msg=_("Name successfully removed."))
remove_name = transaction_decorator(remove_name)

def accounts(req, owner, transaction, add=None, delete=None, **checkboxes):
    if add:
        redirect(req, url('account/create?owner=%s' % owner), seeOther=True)

    elif delete:
        person = _get_person(req, transaction, owner)
        operation = transaction.get_group_member_operation_type("union")
        msgs = []
        for arg, value in checkboxes.items():
            if arg.startswith("account_"):
                id = arg.replace("account_", "")
                account = transaction.get_account(int(id))
                date = transaction.get_commands().get_date_now()
                account.set_expire_date(date)
                msgs.append(_("Expired account %s.") % account.get_name())
            elif arg.startswith("member_"):
                member_id, group_id = arg.split("_")[1:3]
                member = transaction.get_account(int(member_id))
                group = transaction.get_group(int(group_id))
                group_member = transaction.get_group_member(group, 
                            operation, member, member.get_type())
                group.remove_member(group_member)
                msgs.append(_("Removed %s from group %s") % 
                            (member.get_name(), group.get_name()))
        if msgs:
            olink = object_link(person)
            for msg in msgs:
                queue_message(req, msg, error=False, link=olink)
            commit(transaction, req, person)
        else:
            msg = _("No changes done since no groups/accounts were selected.")
            queue_message(req, msg, error=True)
            redirect_object(req, person, temporary=True)
        
    else:
        raise "I don't know what you want to do"
accounts = transaction_decorator(accounts)
                
def add_affil(req, transaction, id, status, ou, description=""):
    person = transaction.get_person(int(id))
    ou = transaction.get_ou(int(ou))
    status = transaction.get_person_affiliation_status_type(status)
    ss = transaction.get_source_system("Manual")

    affil = person.add_affiliation(ou, status, ss)
    
    if description:
        affil.set_description(description)
    
    commit(transaction, req, person, msg=_("Affiliation successfully added."))
add_affil = transaction_decorator(add_affil)

def remove_affil(req, transaction, id, ou, affil, ss):
    person = transaction.get_person(int(id))
    ou = transaction.get_ou(int(ou))
    ss = transaction.get_source_system(ss)
    affil = transaction.get_person_affiliation_type(affil)
    
    searcher = transaction.get_person_affiliation_searcher()
    searcher.set_person(person)
    searcher.set_ou(ou)
    searcher.set_source_system(ss)
    searcher.set_affiliation(affil)
    
    affiliation, = searcher.search()
    affiliation.delete()
    
    commit(transaction, req, person, msg=_("Affiliation successfully removed."))
remove_affil = transaction_decorator(remove_affil)

# arch-tag: bef096b9-0d9d-4708-a620-32f0dbf42fe6
