# -*- coding: utf-8 -*-
#
# Copyright 2014 University of Oslo, Norway
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

"""Client for connecting and consuming Ephorte-webservices."""
import types
import socket
from functools import wraps
import urllib2
from Cerebrum import https
import suds
from xml.sax import SAXParseException
import ssl


class EphorteWSError(Exception):
    """Exception class for Ephorte WebService errors."""
    pass


class HTTPSClientCertTransport(suds.transport.http.HttpTransport):
    """Transport wrapper for TLS."""
    # Partial copypasta from
    # http://stackoverflow.com/questions/6277027/suds-over-https-with-cert
    def __init__(self, ca_certs, cert_file, key_file, *args, **kwargs):
        """Instantiate TLS transport wrapper.

        :type ca_certs: str
        :param ca_certs: Path to CA certificate chain
        :type cert_file: str
        :param cert_file: Path to client certificate
        :type key_file: str
        :param key_file: Path to client key
        """
        suds.transport.http.HttpTransport.__init__(self, *args, **kwargs)
        self.ca_certs = ca_certs
        self.certfile = cert_file
        self.keyfile = key_file

    def u2open(self, u2request):
        """
        Open a connection.
        :param u2request: A urllib2 request.
        :type u2request: urllib2.Requet.
        :return: The opened file-like urllib2 object.
        :rtype: fp
        """
        tm = self.options.timeout
        ssl_conf = https.SSLConfig(self.ca_certs, self.certfile, self.keyfile)
        hc_cls = https.HTTPSConnection.configure(ssl_conf)
        ssl_conn = https.HTTPSHandler(ssl_connection=hc_cls)
        url = urllib2.build_opener(ssl_conn)
        if self.u2ver() < 2.6:
            socket.setdefaulttimeout(tm)
            return url.open(u2request)
        else:
            return url.open(u2request, timeout=tm)


class SudsClient(object):
    """Wrapper for suds.

    Provides a simple interface for function-calls against the web-service.
    Translates errors and exceptions into a single exception type."""
    def __init__(self, wsdl, timeout=None, client_key=None, client_cert=None,
                 ca_certs=None):
        """Initialize client.

        :type wsdl: str
        :param wsdl: The URL to the services WSDL
        :type timeout: int
        :param timeout: Timeout for connections the webservice in seconds
            (default: None)
        :type client_key: str
        :param client_key: Path to clients certificate
        :type ca_cert: str
        :param ca_cert: Path to CA certificate chain
        """
        self.wsdl = wsdl

        if client_key and client_cert and ca_certs:
            transport = HTTPSClientCertTransport(ca_certs, client_cert,
                                                 client_key)
        else:
            transport = suds.transport.http.HttpTransport()
        try:
            self.client = suds.client.Client(wsdl, timeout=timeout,
                                             cache=None, transport=transport)
        except urllib2.URLError, e:
            raise EphorteWSError(str(e))
        except socket.timeout:
            raise EphorteWSError('Timed out connecting to %s' % wsdl)
        except ssl.SSLError, e:
            raise EphorteWSError('Error in TLS communication: %s' % str(e))
        # TODO: Moar error handling?

    # TODO: Do something smart with the call stack, so this don't show up in
    # tracebacks?
    @classmethod
    def _handle_errors(cls, f, name):
        """Handle errors that might occur."""
        # suds.client.Method instances are kind of anonymous, so we have to set
        # the __name__-variable by hand.
        f.__name__ = name

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                r = f(*args, **kwargs)
            except socket.timeout:
                raise EphorteWSError(
                    'Timeout while calling %s with args %s and kwargs %s' %
                    (name, args, kwargs))
            except SAXParseException, e:
                raise EphorteWSError(
                    'Malformed reply from server: %s' % str(e))
            if r.HasError:
                raise EphorteWSError(r.ErrorMessage)
            return r
        return wrapper

    def __getattribute__(self, name):
        """Method override to allow a prettier interface in
        Cerebrum2EphorteClient."""
        try:
            r = object.__getattribute__(self, name)
        except AttributeError:
            # New-style… Old-style… Is this a TODO of some sort?
            r = getattr(self.client.service, name)
        if isinstance(r, suds.client.Method):
            # Actually decorate the method, if it is SOAP-function.
            return SudsClient._handle_errors(r, name)
        else:
            return r


class Cerebrum2EphorteClient(object):
    """Client for connecting and consuming the Cerebrum2Ephorte web-service."""
    def __init__(self, wsdl, customer_id, database, timeout=None,
                 client_key=None, client_cert=None, ca_certs=None):
        """Initialize client.

        :type wsdl: str
        :param wsdl: The URL to the services WSDL
        :type customer_id: str
        :param customer_id: The customer identificator, i.e. 'UiO'
        :type database: str
        :param database: The database to connect to
        :type timeout: int
        :param timeout: Timeout for connections the webservice in seconds
            (default: None)
        :type client_key: str
        :param client_key: Path to clients certificate
        :type client_cert: str
        :param client_cert: Path to client certificate
        :type ca_certs: str
        :param ca_certs: Path to CA certificate chain
        """
        self.wsdl = wsdl
        self.customer_id = customer_id
        self.database = database
        self.client = SudsClient(wsdl, timeout=timeout,
                                 client_key=client_key,
                                 client_cert=client_cert,
                                 ca_certs=ca_certs)

    @staticmethod
    def _convert_result(resp):
        """Convert a response object to a python dict.

        :type resp: suds.sudsobject
        :param resp: The response returned from suds

        :rtype: dict
        :return: The parsed response"""
        # Handle lists
        if isinstance(resp, types.ListType):
            res = [Cerebrum2EphorteClient._convert_result(x) for x in resp]
        # Handle other types, like dicts and strings
        else:
            res = {}
            for key in (set(resp.__keylist__) -
                        set(['ErrorMessage', 'HasError'])):
                # Pick conversion function
                if type(resp[key]) is suds.sax.text.Text:
                    converter = unicode
                # Dicts are really instances, in suds, so we have to recurse in
                # order to convert them.
                elif isinstance(resp[key], types.InstanceType):
                    converter = Cerebrum2EphorteClient._convert_result
                else:
                    # Pass-trough conversion function
                    converter = lambda x: x
                # TODO: Is it needed to implement more type converting?

                # Actually convert
                res[key] = converter(resp[key])
        return res

    def test(self, customer_id='UiO2', user_id='Dummy'):
        self.client.Test(customer_id, user_id)
        # TODO: Correct to assume that we are OK?
        return True

    def test_with_ephorte(self, user_id):
        """Test the connection to ePhorte, by doing a real user lookup.

        :type user_id: str
        :param user_id: The users identificator. I.e. 'jsama@uio.no'
        :rtype: dict
        :return: Dict with full name and user id.
        """
        r = self.c.TestWithEphorte(self.customer_id,
                                   self.database,
                                   user_id)

        return self._convert_result(r)

    def get_all_org_units(self):
        # TODO: Should we generate a tree?
        """Collect all active organizational units from Ephorte.

        :rtype: list(dict())
        :return: A list of dicts representing the different OUs.
            I.e. [{'OrgId': u'APOLLON',
                   'ParentOrgId': u'SADM',
                   'IsTop': False,
                   'Name': u'Apollon'}]
        """
        r = self.client.GetAllOrgUnits(self.customer_id, self.database)
        if r.OrgUnits:
            return self._convert_result(r.OrgUnits.EphorteOrg)
        else:
            return []

    def get_all_roles(self):
        """Collect all roles from ePhorte.

        :rtype: dict()
        :return: Key is role-code, value is description.
            I.e. {u'SB2': u'Saksbehandler'}
        """
        r = self.client.GetAllRoles(self.customer_id, self.database)
        if r.Roles:
            return self._convert_result(r.Roles.EphorteRole)
        else:
            return []

    def get_all_access_codes(self):
        """Collect all access codes from ePhorte.

        :rtype: dict()
        :return: Key is AccessCode, value is description.
            I.e. {u'AR': u'AR - Under arbeid'}
        """
        r = self.client.GetAllAccessCodes(self.customer_id, self.database)
        res = {}
        if r.AccessCodes:
            for role in r.AccessCodes.EphorteAccessCode:
                tmp = self._convert_result(role)
                res[tmp['AccessCodeId']] = tmp['Description']
        return res

    def get_all_users(self):
        """Collect all active users in ePhorte.

        :rtype: list(dict())
        """
        r = self.client.GetAllUsers(self.customer_id, self.database)

        users = {}
        for user in r.Users.EphorteUser:
            tmp = self._convert_result(user)
            users[tmp['UserId']] = tmp
        return users

    def get_user_details(self, user_id):
        """Get detailed user information from ePhorte.

        :type user_id: str
        :param user_id: The users identificator

        :rtype: tuple(dict(), list(dict(), list(dict()))
        :return: Tuple consisting of user information, access codes and roles.
            I.e. ({'City': u'OSLO',
                   'StreetAddress': u'Gaustadalleen 23 A Kristen Nygaards hus',
                   'FirstName': u'Jo',
                   'Mobile': None,
                   'LastName': u'Sama',
                   'UserId': u'JSAMA@UIO.NO',
                   'ZipCode': u'0373',
                   'Telephone': u'+47xXxXxXxX',
                   'MiddelName': None,
                   'EmailAddress': u'jo.sama@usit.uio.no',
                   'FullName': u'Jo Sama',
                   'Initials': u'JSAMA'},
                  [{'AccessCodeId': u'AR',
                    'IsAutorizedForAllOrgUnits': False,
                    'OrgId': u'FA'}],
                  [{'FondsSeriesId': None,
                    'JobTitle': u'Arkivleder',
                    'RegistryManagementUnitId': u'J-UIO',
                    'Role': {'RoleId': u'SB2',
                             'Description': u'Saksbehandler'},
                    'Org': {'OrgId': u'USIT',
                            'ParentOrgId': u'UIO',
                            'IsTop': False,
                            'Name': u'Univ. senter for informasjonsteknologi'},
                    'RoleTitle': u'SB2 USIT',
                    'IsDefault': True}])
        """
        # TODO: Should we rather return a dict, than a tuple? Or maybee a named
        # TODO: tuple? Named tuples are kind of cute.
        r = self.client.GetUserDetails(self.customer_id,
                                       self.database,
                                       user_id)

        if r.User:
            usr = self._convert_result(r.User)
        else:
            usr = None

        authzs = []
        if r.UserAuthorizations:
            for authz in r.UserAuthorizations.EphorteUserAuthorization:
                authzs.append(self._convert_result(authz))

        roles = []
        if r.UserRoles:
            for role in r.UserRoles.EphorteUserRole:
                roles.append(self._convert_result(role))
        return (usr, authzs, roles)

    def search_users(self, pattern):
        """GetUserList from ephorte, limited on the pattern supplied.

        :type pattern: str
        :param pattern: The substring to search with
        :rtype: list(dict())
        :return: A list of dicts, with user information.
            I.e. [{'City': u'OSLO',
                   'StreetAddress': u'Gaustadalleen 23 A Kristen Nygaards hus',
                   'FirstName': u'Jo',
                   'Mobile': None,
                   'LastName': u'Sama',
                   'UserId': u'JSAMA@UIO.NO',
                   'ZipCode': u'0373',
                   'Telephone': u'+4722852707',
                   'MiddelName': None,
                   'EmailAddress': u'jo.sama@usit.uio.no',
                   'FullName': u'Jo Sama',
                   'Initials': u'JSAMA'}]
        """
        r = self.client.GetUserList(self.customer_id, self.database, pattern)

        if r.Users:
            return self._convert_result(r.Users.EphorteUser)
        else:
            return []

    def ensure_user(self, user_id, first_name=None, middle_name=None,
                    last_name=None, full_name=None, initials=None,
                    email_address=None, telephone=None, mobile=None,
                    street_address=None, zip_code=None,
                    city=None):
        """Create or update the user in ePhorte.

        If an argument is None, it will be cleared in ePhorte."""
        # Create the complex object describing our user
        u = self.client.client.factory.create('EphorteUser')
        # '' on vars will result in no-update
        # ' ' will empty field i ePhorte

        # Set vars
        # TODO: Makes this stuff pretty!
        u.UserId = user_id
        u.FirstName = ' ' if first_name is None else first_name
        u.MiddelName = ' ' if middle_name is None else middle_name
        u.LastName = ' ' if last_name is None else last_name
        u.FullName = ' ' if full_name is None else full_name
        u.Initials = ' ' if initials is None else initials
        u.EmailAddress = ' ' if email_address is None else email_address
        u.Telephone = ' ' if telephone is None else telephone
        u.Mobile = ' ' if mobile is None else mobile
        u.StreetAddress = ' ' if street_address is None else street_address
        u.ZipCode = ' ' if zip_code is None else zip_code
        u.City = ' ' if city is None else city

        # Ensure that user exists
        self.client.EnsureUser(self.customer_id, self.database, u)

# TODO: job_title, is this the description attached to role_id, as gotten from
# get_all_roles?! Can we omit?
# TODO: Missing docstrings
    def ensure_role_for_user(self, user_id, job_title, role_id, ou_id,
                             arkivdel, journalenhet, default_role):
        """Create or update a role for a user.

        :type user_id: str
        :param user_id: The users identificator
        :type job_title: str
        :param job_title: The roles description
        :type role_id: str
        :param role_id: The role identification code
        :type ou_id: str
        :param ou_id: The organisational units identificator
            (OrgId from get_all_org_units()).
        :type arkivdel: str
        :param arkivdel:
        :type journalenhet: str
        :param journalenhet:
        :type default_role: bool
        :param default_role: If this role should be the default role
        """
        self.client.EnsureRoleForUser(self.customer_id, self.database,
                                      user_id, job_title, role_id, ou_id,
                                      arkivdel, journalenhet, default_role)

    def ensure_access_code_authorization(self, user_id, access_code_id,
                                         ou_id, authz_for_all):
        """Create or update access code for a user.

        - In order to authorize access to the users own cases, set ou_id to
          None, and authz_for_all to False.
        - Authorize user to access all cases, set ou_id to None, and
          authz_for_all to True.
        - Authorize user to a specific OU, set the ou_id, and authz_for_all to
          False.

        :type user_id: str
        :param user_id: The users identificator
        :type access_code_id: str
        :param access_code_id: The access code id, as returned from
            get_all_access_codes().
        :type ou_id: str
        :param ou_id: The OU the role is attached to
            (OrgId from get_all_org_units()).
        :type authz_for_all: bool
        :param authz_for_all: Wether or not the user is authorized for
            the entire organization..
        """
        self.client.EnsureAccessCodeAuthorizationForUser(
            self.customer_id,
            self.database,
            user_id,
            access_code_id,
            ou_id,
            authz_for_all)

    def disable_user(self, user_id):
        """Disable a user in ePhorte.

        :type user_id: str
        :param user_id: The users identificator
        """
        self.client.DisableUser(self.customer_id, self.database, user_id)

    def disable_roles_and_authz_for_user(self, user_id):
        """Disable all roles and authz. for a user.

        :type user_id: str
        :param user_id: The users id
        """
        self.client.DisableRolesAndAuthorizationsForUser(self.customer_id,
                                                         self.database,
                                                         user_id)

    def get_user_backlog(self, user_id):
        # TODO: Moar doc
        # TODO: Moar result parsing?
        # TODO: We really need this?
        """Fetch information about the users open cases."""
        r = self.client.GetUserBacklog(self.customer_id,
                                       self.database,
                                       user_id)
        return self._convert_result(r)
