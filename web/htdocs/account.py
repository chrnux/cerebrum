import cerebrum_path
import forgetHTML as html
from Cerebrum.Utils import Factory
ClientAPI = Factory.get_module("ClientAPI")
from Cerebrum.web.templates.AccountSearchTemplate import AccountSearchTemplate
from Cerebrum.web.templates.AccountViewTemplate import AccountViewTemplate
from Cerebrum.web.templates.HistoryLogTemplate import HistoryLogTemplate
from Cerebrum.web.Main import Main
from gettext import gettext as _
from Cerebrum.web.utils import url
from Cerebrum.web.utils import redirect
import xmlrpclib

def index(req):
    page = Main(req)
    page.menu.setFocus("account/search")
    accountsearch = AccountSearchTemplate()
    page.content = accountsearch.form
    return page

def search(req, name, owner, expire_date, create_date):
    page = Main(req)
    page.title = "Account search"
    page.setFocus("account/list")
    server = req.session['server']
    # Store given search parameters in search form
    formvalues = {}
    formvalues['name'] = name
    formvalues['owner'] = owner
    formvalues['expire_date'] = expire_date
    formvalues['create_date'] = create_date
    accountsearch = AccountSearchTemplate(
                       searchList=[{'formvalues': formvalues}])
    result = html.Division()
    result.append(html.Header(_("Account search results"), level=2))
    accounts = ClientAPI.Account.search(server, name or None,
                                        owner or None,
                                        expire_date or None,
                                        create_date or None)
    table = html.SimpleTable(header="row")
    table.add(_("Name"), _("Owner"))
    for (id, name, owner) in accounts:
        owner = owner or ""
        link = url("account/view?id=%s" % id)
        link = html.Anchor(name, href=link)
        table.add(link, desc)
    if accounts:    
        result.append(table)
    else:
        result.append(html.Emphasis(_("Sorry, no account(s) found matching the given criteria.")))
    result.append(html.Header(_("Search for other accounts"), level=2))
    result.append(accountsearch.form())
    page.content = result.output().encode("utf8")
    return page    

def create(req, ownerid="", ownertype="", id="", name="", affiliation="", 
           show_form=None, hide_form=None, create=None):
    if show_form:
        req.session['profile']['person']['edit']['show_account_create'] = True

    elif hide_form:
        req.session['profile']['person']['edit']['show_account_create'] = False

    elif create:
        server = req.session['server']
        try:
            owner = ClientAPI.fetch_object_by_id(server, ownerid)
            account = ClientAPI.Account.create(server, name, owner, affiliation)
        except xmlrpclib.Fault, e:
            req.session['profile']['last_error_message'] = e.faultString.split("CerebrumError: ")[-1]                    

    return redirect(req, url("%s/view?id=%s" % (ownertype, ownerid)), seeOther=True)

def _create_view(req, id):
    """Creates a page with a view of the account given by id, returns
       a tuple of a Main-template and an account instance"""
    server = req.session['server']
    page = Main(req)
    try:
        account = ClientAPI.Account.fetch_by_id(server, id)
    except:
        page.add_message(_("Could not load account with id %s") % id)
        return (page, None)

    page.menu.setFocus("account/view", id)
    view = AccountViewTemplate()
    page.content = lambda: view.viewAccount(account)
    return (page, account)

def view(req, id):
    (page, account) = _create_view(req, id)
    return page
