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

"""
Constants common for higher education institutions in Norway.
"""

from Cerebrum import Constants
from Cerebrum.Constants import _EntityExternalIdCode, \
                               _AuthoritativeSystemCode, \
                               _OUPerspectiveCode, \
                               _AccountCode, \
                               _PersonNameCode, \
                               _ContactInfoCode, \
                               _CountryCode, \
                               _QuarantineCode, \
                               _SpreadCode,\
                               _PersonAffiliationCode,\
                               _PersonAffStatusCode

class ConstantsCommon(Constants.Constants):

    # external id definitions (NO_NIN, norwegian national id number)
    externalid_fodselsnr = _EntityExternalIdCode('NO_BIRTHNO',
                                                 Constants.Constants.entity_person,
                                                 'Norwegian birth number')
class ConstantsHigherEdu(Constants.Constants):

    # authoritative source systems (FS = student registry, SAP = common HR-system)
    system_fs = _AuthoritativeSystemCode('FS', 'FS')
    system_sap = _AuthoritativeSystemCode('SAP', 'SAP')

    # external id definitions (student and employee id)
    externalid_studentnr = _EntityExternalIdCode('NO_STUDNO',
                                                 Constants.Constants.entity_person,
                                                 'Norwegian student number')
    externalid_sap_ansattnr = _EntityExternalIdCode('SAP_NR',
                                                    Constants.Constants.entity_person,
                                                    'SAP employee number')
    externalid_uname = _EntityExternalIdCode('UNAME',
                                             Constants.Constants.entity_person,
                                             'User name (external system)')

    # OU-structure perspectives
    perspective_fs = _OUPerspectiveCode('FS', 'FS')
    perspective_sap = _OUPerspectiveCode('SAP', 'SAP')

class ConstantsUniversityColleges(Constants.Constants):

    ## Source systems
    system_migrate = _AuthoritativeSystemCode('MIGRATE', 'Migrate from files')
    system_override = _AuthoritativeSystemCode('Override',
                                               'Override information fetched from proper authoritative systems')
    system_manual =  _AuthoritativeSystemCode('MANUELL',
                                              'Manually added information')


    ## Affiliations for employees
    affiliation_ansatt = _PersonAffiliationCode('ANSATT', 'Ansatt')
    affiliation_status_ansatt_vitenskapelig = _PersonAffStatusCode(
        affiliation_ansatt, 'vitenskapelig', 'Ansatt, vitenskapelige ansatte')
    affiliation_status_ansatt_tekadm = _PersonAffStatusCode(
        affiliation_ansatt, 'tekadm', 'Tekniske/administrative ansatte')
    
    ## Affiliations for students
    affiliation_student = _PersonAffiliationCode('STUDENT', 'Student')
    affiliation_status_student_evu = _PersonAffStatusCode(
        affiliation_student, 'evu', 'Student, etter og videre utdanning')
    affiliation_status_student_aktiv = _PersonAffStatusCode(
        affiliation_student, 'aktiv', 'Student, aktiv')

    ## Affiliation for associated people
    affiliation_tilknyttet = _PersonAffiliationCode('TILKNYTTET',
                                                    'Assosiert, reg. i kildesystem')
    affiliation_status_tilknyttet_fagperson = _PersonAffStatusCode(affiliation_tilknyttet,
                                                                   'fagperson',
                                                                   'Registrert i FS, fagperson')
    affiliation_status_tilknyttet_pensjonist = _PersonAffStatusCode(affiliation_tilknyttet,
                                                                    'pensjonist',
                                                                    'Registrert i HR, pensjonist')
    affiliation_status_tilknyttet_bilag = _PersonAffStatusCode(affiliation_tilknyttet,
                                                               'bilag',
                                                               'Registrert i HR, bilagsl�nnet')
    affiliation_status_tilknyttet_gjest = _PersonAffStatusCode(affiliation_tilknyttet,
                                                               'gjest',
                                                               'Registrert i HR, gjest')
    affiliation_status_tilknyttet_gjestefors = _PersonAffStatusCode(affiliation_tilknyttet,
                                                                    'gjesteforsker',
                                                                    'Registrert i HR, gjesteforsker')    

    ## quarantine definitions
    quarantine_generell = _QuarantineCode('generell',
                                          'Generell sperring')
    quarantine_teppe = _QuarantineCode('teppe',
                                       'Kalt inn til samtale')
    quarantine_kunepost = _QuarantineCode('kunepost',
                                           'Tilgang kun til e-post')
    quarantine_svaktpassord = _QuarantineCode('svaktpassord',
                                               'For d�rlig passord')
    quarantine_system = _QuarantineCode('system',
                                        'Systembrukar som ikke skal logge inn')
    ## Cerebrum (internal), used by automagic only
    quarantine_auto_passord = _QuarantineCode('auto_passord',
                                             'Passord ikke skiftet trass p�legg')
    quarantine_auto_inaktiv = _QuarantineCode('auto_inaktiv',
                                              'Ikke aktiv student, utestengt')
    quarantine_auto_kunepost = _QuarantineCode('auto_kunepost',
                                               'Privatist, kun tilgang til e-post')
    quarantine_ou_notvalid = _QuarantineCode('ou_notvalid',
                                             'Sted ugyldig i autoritativ kildesystem')    
    quarantine_ou_remove = _QuarantineCode('ou_remove',
                                           'Sted fjernet fra autoritativ kildesystem')
    
    ## Non-personal account codes
    account_test = _AccountCode('testbruker', 'Testkonto')
    account_kurs = _AccountCode('kursbruker', 'Kurskonto')
    account_studorg = _AccountCode('studorgbruker','Studentorganisasjonsbruker')
    account_felles  = _AccountCode('fellesbruker','Fellesbruker')
    account_system  = _AccountCode('systembruker', 'Systembruker') 

    ## SAP name constants
    name_middle = _PersonNameCode('MIDDLE', 'Mellomnavn')
    name_initials = _PersonNameCode('INITIALS', 'Initialer')

    ## SAP comm. constants
    contact_phone_cellular = _ContactInfoCode("CELLPHONE",
                                              "Mobiltelefonnr")
    contact_phone_cellular_private = _ContactInfoCode(
                                       "PRIVCELLPHONE",
                                       "Privat mobiltefonnr")
    ## SAP country constants
    country_no = _CountryCode("NO", "Norway", "47", "Norway")
    country_gb = _CountryCode("GB", "Great Britain", "44", "Great Britain")
    country_fi = _CountryCode("FI", "Finland", "358", "Finland")
    country_se = _CountryCode("SE", "Sweden", "46", "Sweden")
    country_us = _CountryCode("US", "USA", "1", "United states of America")
    country_nl = _CountryCode("NL", "The Netherlands", "31", "The Netherlands")
    country_de = _CountryCode("DE", "Germany", "49", "Germany")
    country_au = _CountryCode("AU", "Australia", "61", "Australia")
    country_dk = _CountryCode("DK", "Denmark", "45", "Denmark")
    country_it = _CountryCode("IT", "Italy", "39", "Italy")
    country_sg = _CountryCode("SG", "Singapore", "65", "Singapore")
    country_at = _CountryCode("AT", "Austria", "43", "Austria")
    country_ca = _CountryCode("CA", "Canada", "11", "Canada")    

    ## Spread definitions - user related
    spread_ldap_account = _SpreadCode(
        'account@ldap', Constants.Constants.entity_account,
        'Brukeren kjent i LDAP (FEIDE)')
    spread_lms_account = _SpreadCode(
        'account@lms', Constants.Constants.entity_account,
        'Brukeren kjent i LMSen')

    ## Spread definitions - person related
    spread_ldap_person = _SpreadCode(
        'person@ldap', Constants.Constants.entity_person,
        'Person kjent i organisasjonstreet (FEIDE-person)')
    spread_lms_person = _SpreadCode(
        'person@lms', Constants.Constants.entity_person,
        'Person kjent i organisasjonens LMS')    



#
#  SAP magic below
#  
#  forretningsomr�de	- roughly geographical locations
#  stillingstype        - hoved/bistilling
#  l�nnstittel          - work title (sendemann, ekspedisjonssjef, etc)
#  permisjon            - leave of absence
#  utvalg               - commitees 
# 

class SAPForretningsOmradeKode(Constants._CerebrumCode):
    "This class represents GSBER/forretningsomr�de codes."
     
    _lookup_table = "[:table schema=cerebrum name=sap_forretningsomrade]"
# end SAPForretningsOmrade



class SAPStillingsTypeKode(Constants._CerebrumCode):
    "This class represents HOVEDSTILLING, BISTILLING codes."

    _lookup_table = "[:table schema=cerebrum name=sap_stillingstype]"
# end SAPStillingsType



class SAPLonnsTittelKode(Constants._CerebrumCode):
    """
    This class represents lonnstittel (SAP.STELL) codes.
    """

    _lookup_table = "[:table schema=cerebrum name=sap_lonnstittel]"


    def __init__(self, code, description=None, kategori=None):
        super(SAPLonnsTittelKode, self).__init__(code, description)
        self.kategori = kategori
    # end __init__


    def insert(self):
        self.sql.execute("""
          INSERT INTO %(code_table)s
            (%(code_col)s, %(str_col)s, %(desc_col)s, kategori)
          VALUES
            (%(code_seq)s, :str, :desc, :kategori) """ % {
              "code_table" : self._lookup_table,
              "code_col"   : self._lookup_code_column,
              "str_col"    : self._lookup_str_column,
              "desc_col"   : self._lookup_desc_column,
              "code_seq"   : self._code_sequence
              },
              { 'str'      : self.str,
                'desc'     : self._desc,
                'kategori' : self.kategori,
              })  
    # end insert


    def get_kategori(self):
        if self.kategori is not None:
            return self.kategori
        # fi

        return self.sql.query_1("""
                                SELECT 
                                  kategori
                                FROM
                                  %s
                                WHERE
                                  code = :code""" % self._lookup_table,
                                {'code': int(self)})
    # end get_kategori
# end SAPLonnsTittelKode



class SAPPermisjonsKode(Constants._CerebrumCode):
    "This class represents leave of absence (permisjon) codes."

    _lookup_table = "[:table schema=cerebrum name=sap_permisjon]"
# end SAPPermisjonsKode



class SAPUtvalgsKode(Constants._CerebrumCode):
    "This class represents utvalg (committee) codes."

    _lookup_table = "[:table schema=cerebrum name=sap_utvalg]"
# end SAPUtvalgsKode



class SAPCommonConstants(Constants.Constants):
    """This class embodies all constants common to Cerebrum installations with
    SAP"""

    # entries for this fo-kode will be ignored in all contexts. they mark
    # records that are no longer valid.
    sap_eksterne_tilfeldige = SAPForretningsOmradeKode(
        "9999",
        "Eksterne/tilfeldige"
    )

    # ----[ SAPStillingsTypeKode ]--------------------------------------
    sap_hovedstilling = SAPStillingsTypeKode(
        "H",
        "Hovedstilling"
    )

    sap_bistilling = SAPStillingsTypeKode(
        "B",
        "Bistilling"
    )

# end SAPCommonConstants

