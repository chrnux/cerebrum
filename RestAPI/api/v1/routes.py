from . import api
from authtest import AuthTest
from account import (AccountListResource,
                     AccountResource,
                     AccountGroupListResource,
                     AccountEmailAddressResource,
                     AccountAffiliationListResource,
                     AccountContactInfoListResource,
                     AccountHomeListResource)
from group import (GroupListResource,
                   GroupResource,
                   GroupMemberListResource)
from person import PersonResource
from emailaddress import EmailAddressResource
from ou import OrganizationalUnitResource

api.add_resource(AuthTest, '/auth-test')

api.add_resource(
    AccountListResource,
    '/accounts',
    endpoint='accounts')

api.add_resource(
    AccountResource,
    '/accounts/<string:id>',
    endpoint='account')

api.add_resource(
    AccountGroupListResource,
    '/accounts/<string:id>/groups',
    endpoint='accountgroups')

api.add_resource(
    AccountAffiliationListResource,
    '/accounts/<string:id>/affiliations',
    endpoint='accountaffiliations')

api.add_resource(
    AccountContactInfoListResource,
    '/accounts/<string:id>/contacts',
    endpoint='accountcontacts')

api.add_resource(
    AccountHomeListResource,
    '/accounts/<string:id>/homes',
    endpoint='accounthomes')

api.add_resource(
    AccountEmailAddressResource,
    '/accounts/<string:id>/emailaddresses',
    endpoint='accountemailaddresses')

api.add_resource(
    GroupListResource,
    '/groups',
    endpoint='groups')

api.add_resource(
    GroupResource,
    '/groups/<string:id>',
    endpoint='group')

api.add_resource(
    GroupMemberListResource,
    '/groups/<string:id>/members',
    endpoint='groupmembers')

api.add_resource(
    PersonResource,
    '/persons/<int:id>',
    endpoint='person')

api.add_resource(
    EmailAddressResource,
    '/emailaddresses/<string:address>',
    endpoint='emailaddress')

api.add_resource(
    OrganizationalUnitResource,
    '/ous/<int:id>',
    endpoint='ou')
