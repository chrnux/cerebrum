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

from gettext import gettext as _
from lib.Main import Main
from lib.utils import transaction_decorator, commit, html_quote, web_to_spine
from lib.utils import redirect_object, queue_message

def add(transaction, entity, subject="", description=""):
    """Adds a note to some entity."""
    entity = transaction.get_entity(int(entity))
    if not subject and not description:
        queue_message(_("Could not add blank note"), error=True)
        redirect_object(entity)
    else:
        entity.add_note(web_to_spine(subject), web_to_spine(description))
        commit(transaction, entity, msg=_("Added note '%s'") % subject)
add = transaction_decorator(add)
add.exposed = True

def delete(transaction, entity, id):
    """Removes a note."""
    entity = transaction.get_entity(int(entity))
    note = transaction.get_note(int(id))
    entity.remove_note(note)
    commit(transaction, entity, msg=_("Note deleted"))
delete = transaction_decorator(delete)
delete.exposed = True

# arch-tag: a346491e-4e47-42c1-8646-391b6375b69f
