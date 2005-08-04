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

import Menu
import utils
from gettext import gettext as _

class FixUrlMixin:
    def addItem(self, name, label, url):
            # fix url
            url = utils.url(url)    
            item = MenuItem(name, label, url) 
            self.addMenuItem(item) 
            return item

class MenuItem(FixUrlMixin, Menu.MenuItem):
    def __init__(self, *args, **kwargs):
        Menu.MenuItem.__init__(self, *args, **kwargs)

class SideMenu(FixUrlMixin, Menu.Menu):
    def __init__(self):
        Menu.Menu.__init__(self)
        self.makeMain()
        self.makePerson()
        self.makeAccount()
        self.makeGroup()
        self.makeOU()
        self.makeEmail()
        #self.makeRoles()
        #self.makeSpread()
        self.makeOptions()

    def makeMain(self):
        self.main = self.addItem("main", _("Main") ,"index")

    def makePerson(self):
        self.person = self.addItem("person", _("Person") ,"person")
        self.person.addItem("search", _("Search") ,"person/search")
        self.person.addItem("list", _("List") ,"person/list")
        self.person.addItem("create", _("Create") ,"person/create")
        self.person.addItem("view", _("View") ,"person/view?id=%s")
        self.person.addItem("edit", _("Edit") ,"person/edit?id=%s")
    
    def makeAccount(self):
        self.account = self.addItem("account", _("Account") ,"account")
        self.account.addItem("search", _("Seach") ,"account/search")
        self.account.addItem("list", _("List") ,"account/list")

    def makeGroup(self):    
        self.group = self.addItem("group", _("Group") ,"group")
        self.group.addItem("search", _("Search") ,"group")
        self.group.addItem("list", _("List") ,"group/list")
        self.group.addItem("create", _("Create") ,"group/create")
        self.group.addItem("view", _("View") ,"group/view?id=%s")
        self.group.addItem("edit", _("Edit") ,"group/edit?id=%s")

    def makeOU(self):
        self.ou = self.addItem("ou", _("OU") ,"ou")
        self.ou.addItem("search", _("Search") ,"ou")
        self.ou.addItem("list", _("List") ,"ou/list")
        self.ou.addItem("tree", _("Tree") ,"ou/tree")
        self.ou.addItem("create", _("Create") ,"ou/create")
        self.ou.addItem("view", _("View") ,"ou/view?id=%s")
        self.ou.addItem("edit", _("Edit") ,"ou/edit?id=%s")
    
    def makeEmail(self):    
        self.email = self.addItem("email", _("Email") ,"email")
        domain = self.email.addItem("domain", _("Domain") ,"emaildomain")
        domain.addItem("list", _("List"), "emaildomain/list")
        domain.addItem("create", _("Create"), "emaildomain/create")
        domain.addItem("view", _("View"), "emaildomain/view?id=%s")
        domain.addItem("addresses", _("Addresses"), "emaildomain/addresses?id=%s")
        domain.addItem("edit", _("Edit"), "emaildomain/edit?id=%s")

        target = self.email.addItem("target", _("Target"), "emailtarget")
        target.addItem("create", _("Create"), "emailtarget/create")
        target.addItem("view", _("View"), "emailtarget/view?id=%s")
        target.addItem("edit", _("Edit"), "emailtarget/edit?id=%s")


    def makeRoles(self):
        self.roles = self.addItem("roles", _("Roles") ,"roles")
        self.roles.addItem("search", _("Search") ,"roles/search")
        self.roles.addItem("list", _("List") ,"roles/list")
        self.roles.addItem("view", _("View") ,"roles/view?id=%s")
        self.roles.addItem("edit", _("Edit") ,"roles/edit?id=%s")

    def makeSpread(self):
        self.spread = self.addItem("spread", _("Spread") ,"spread")
        self.spread.addItem("search", _("Search") ,"spread/search")
        self.spread.addItem("list", _("List") ,"spread/list")
        self.spread.addItem("view", _("View") ,"spread/view?id=%s")
        self.spread.addItem("edit", _("Edit") ,"spread/edit?id=%s")

    def makeOptions(self):
        self.options = self.addItem("options", _("Options") ,"options")
        self.options.addItem("view", _("View") ,"options/view")
        self.options.addItem("edit", _("Edit") ,"options/edit")

# arch-tag: 6af7ba3d-76dc-46e1-8327-1ed3e307e9e8
