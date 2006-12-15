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
from gettext import gettext as _

class SideMenu(Menu.Menu):
    def __init__(self):
        Menu.Menu.__init__(self)
        self.makePerson()
        self.makeAccount()
        self.makeGroup()
        self.makeOU()
        self.makeHost()
        self.makeDisk()
        self.makeEmail()
        #self.makePermissions()
        self.makeOptions()
        self.makeLogout()

    def makePerson(self):
        self.person = self.addItem("person", _("Person"), "/person")
        self.person.addItem("search", _("Search"), "/person/search")
        self.person.addItem("create", _("Create"), "/person/create")
        self.person.addItem("view", _("View"), "/person/view?id=%s")
        self.person.addItem("edit", _("Edit"), "/person/edit?id=%s")
    
    def makeAccount(self):
        self.account = self.addItem("account", _("Account"), "/account")
        self.account.addItem("search", _("Search"), "/account/search")
        self.account.addItem("view", _("View"), "/account/view?id=%s")
        self.account.addItem("edit", _("Edit"), "/account/edit?id=%s")

    def makeGroup(self):    
        self.group = self.addItem("group", _("Group"), "/group")
        self.group.addItem("search", _("Search"), "/group")
        self.group.addItem("create", _("Create"), "/group/create")
        self.group.addItem("view", _("View"), "/group/view?id=%s")
        self.group.addItem("edit", _("Edit"), "/group/edit?id=%s")

    def makeOU(self):
        self.ou = self.addItem("ou", _("OU"), "/ou")
        self.ou.addItem("search", _("Search"), "/ou")
        self.ou.addItem("tree", _("Tree"), "/ou/tree")
        self.ou.addItem("create", _("Create"), "/ou/create")
        self.ou.addItem("view", _("View"), "/ou/view?id=%s")
        self.ou.addItem("edit", _("Edit"), "/ou/edit?id=%s")
    
    def makeHost(self):
        self.host = self.addItem("host", _("Host"), "/host")
        self.host.addItem("search", _("Search"), "/host")
        self.host.addItem("create", _("Create"), "/host/create")
        self.host.addItem("view", _("View"), "/host/view?id=%s")
        self.host.addItem("edit", _("Edit"), "/host/edit?id=%s")

    def makeDisk(self):
        self.disk = self.addItem("disk", _("Disk"), "/disk")
        self.disk.addItem("search", _("Search"), "/disk")
        self.disk.addItem("create", _("Create"), "/disk/create")
        self.disk.addItem("view", _("View"), "/disk/view?id=%s")
        self.disk.addItem("edit", _("Edit"), "/disk/edit?id=%s")
        
    def makeEmail(self):
        self.email = self.addItem("email", _("Email"), "/email")
        self.email.addItem("search", _("Search"), "/email/search")
        self.email.addItem("categories", _("Categories"), "/email/categories")
        self.email.addItem("create", _("Create"), "/email/create")
        self.email.addItem("view", _("View"), "/email/view?id=%s")
        self.email.addItem("addresses", _("Addresses"), "/email/addresses?id=%s")
        self.email.addItem("edit", _("Edit"), "/email/edit?id=%s")

    def makePermissions(self):
        self.perms = self.addItem("permissions", _("Permissions"), "/permissions")
        self.perms.addItem("view", _("View"), "/permissions/view?id=%s")
        self.perms.addItem("edit", _("Edit"), "/permissions/edit?id=%s")
        self.perms.addItem("users", _("Users"), "/permissions/users?id=%s")

    def makeOptions(self):
        self.options = self.addItem("options", _("Options"), "/options")

    def makeLogout(self):
        self.logout = self.addItem("logout", _("Logout"), "/logout")

# arch-tag: 6af7ba3d-76dc-46e1-8327-1ed3e307e9e8
