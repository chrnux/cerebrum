# -*- coding: iso-8859-1 -*-

# Copyright 2002-2011 University of Oslo, Norway
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

"""Access to Cerebrum code values.

The Constants class defines a set of methods that should be used to
get the actual database code/code_str representing a given Entity,
Address, Gender etc. type."""

from Cerebrum import Constants
from Cerebrum.Constants import _AuthoritativeSystemCode, \
                              _SpreadCode, \
                              _QuarantineCode, \
                              _ContactInfoCode, \
                              _PersonAffiliationCode, \
                              _PersonAffStatusCode
from Cerebrum.modules.no.Constants import ConstantsHigherEdu
from Cerebrum.modules.no.Constants import ConstantsUniversityColleges
from Cerebrum.modules.PosixUser import _PosixShellCode
from Cerebrum.modules.EntityTrait import _EntityTraitCode

class Constants(Constants.Constants):
    system_fs_derived = _AuthoritativeSystemCode('FS-auto',
                                                 'Utledet av FS data')
    system_pbx = _AuthoritativeSystemCode('PBX', 'PBX')

## AFFILIATIONS FOR ANSATTE
    affiliation_ansatt = ConstantsHigherEdu.affiliation_ansatt
    affiliation_status_ansatt_manuell = _PersonAffStatusCode(
        affiliation_ansatt, 'ans_manuell', 'Ansatt, manuell import')
    affiliation_status_ansatt_primaer = _PersonAffStatusCode(
        affiliation_ansatt, 'primaer', 'Prim�rtilknytning for SAP ansatte')
    
## AFFILIATIONS FOR STUDENTER
    affiliation_student = ConstantsHigherEdu.affiliation_student
    affiliation_status_student_manuell = _PersonAffStatusCode(
        affiliation_student, 'stud_manuell', 'Student, manuell import')
    affiliation_status_student_tilbud = _PersonAffStatusCode(
        affiliation_student, 'tilbud', 'Student, tilbud')

## AFFILIATIONS FOR ASSOSIERTE PERSONER
    affiliation_tilknyttet = ConstantsUniversityColleges.affiliation_tilknyttet
    affiliation_status_tilknyttet_feide = _PersonAffStatusCode(
        affiliation_tilknyttet, 'feide',
        'Personer uten reg. i kildesystem som m� ha tilgang til FEIDE-baserte tjenester')

    affiliation_status_tilknyttet_ekstern = _PersonAffStatusCode(
        affiliation_tilknyttet, 'ekstern',
        'Registrert i HR, ekstern tilsatt')

## AFFILIATIONS FOR ANDRE
    affiliation_manuell = _PersonAffiliationCode(
        'MANUELL',
        ('Tilknyttet UiA uten � v�re registrert i et av de'
         ' autoritative kildesystemene'))
    affiliation_status_manuell_ekstern = _PersonAffStatusCode(
        affiliation_manuell, 'ekstern',
        'Eksternt tilknyttet person, n�r spesifikke kategorier ikke passer')
    affiliation_status_manuell_sia = _PersonAffStatusCode(
        affiliation_manuell, 'sia',
        'Person tilknyttet Studentsamskipnaden i Agder')
    affiliation_status_manuell_sta = _PersonAffStatusCode(
        affiliation_manuell, 'sta',
        'Person tilknyttet Studentorganisasjonen Agder')
    affiliation_status_manuell_filonova = _PersonAffStatusCode(
        affiliation_manuell, 'filonova',
        'Person tilknyttet Filonova kursstiftelse')
    affiliation_status_manuell_agderforskning = _PersonAffStatusCode(
        affiliation_manuell, 'agderforskning',
        'Person tilknyttet Agderforskning')
    affiliation_status_manuell_statsbygg = _PersonAffStatusCode(
        affiliation_manuell, 'statsbygg',
        'Person tilknyttet Statsbygg ved UiA')
    affiliation_status_manuell_pensjonist = _PersonAffStatusCode(
        affiliation_manuell, 'pensjonist',
        'Pensjonist ved UiA, ikke registrert i SAP')
    affiliation_status_manuell_gjest = _PersonAffStatusCode(
        affiliation_manuell, 'gjest', 'Gjesteopphold ved UiA')
    affiliation_status_manuell_ans_uten_sap = _PersonAffStatusCode(
        affiliation_manuell, 'ans_uten_sap',
        'Ansatt som ikke er lagt inn i SAP. En midlertidig status for folk')
    affiliation_status_manuell_gjest_ikke_epost = _PersonAffStatusCode(
        affiliation_manuell, 'gjest_no_epost', 
	'Gjesteopphold som ansatt ved UiA. Skal ikke ha epost')
    affiliation_status_manuell_gjest_student = _PersonAffStatusCode(
        affiliation_manuell, 'gjest_student', 
	'Gjesteopphold for student ved UiA. Epost skal tildeles')
    affiliation_status_manuell_gjest_student_ikke_epost = _PersonAffStatusCode(
	affiliation_manuell, 'gj_st_no_epost', 
	'Gjesteopphold for student ved UiA. Epost skal ikke tildeles')

    affiliation_upersonlig = _PersonAffiliationCode(
        'UPERSONLIG', 'Fellesbrukere, samt andre brukere uten eier')
    affiliation_upersonlig_felles = _PersonAffStatusCode(
        affiliation_upersonlig, 'felles', 'Felleskonti')
    affiliation_upersonlig_kurs = _PersonAffStatusCode(
        affiliation_upersonlig, 'kurs', 'Kurskonti')
    affiliation_upersonlig_pvare = _PersonAffStatusCode(
        affiliation_upersonlig, 'pvare', 'Programvarekonti')
    affiliation_upersonlig_studentforening = _PersonAffStatusCode(       
	affiliation_upersonlig, 'studorg', 
	'Studentforening eller -aktivitet ved UiA')

## DEFINISJON AV SHELL 
    # We override the default Cerebrum paths for shells, thus this
    # file should appear before PosixUser in cereconf.CLASS_CONSTANTS
    posix_shell_bash = _PosixShellCode('bash', '/bin/bash')
    posix_shell_tcsh = _PosixShellCode('tcsh', '/bin/tcsh')
    posix_shell_csh = _PosixShellCode('csh', '/bin/csh')
    posix_shell_sh = _PosixShellCode('sh', '/bin/sh')

## DEFINISJON AV SPREAD
    spread_hia_novell_user = _SpreadCode(
        'account@edir', Constants.Constants.entity_account,
        'User in Novell domain "uia"')
    spread_hia_novell_empl = _SpreadCode(
        'employee@edir', Constants.Constants.entity_account,
        'Employee in Novell domain "uia"')
    spread_hia_novell_labuser = _SpreadCode(
        'account@edirlab', Constants.Constants.entity_account,
        'User in Novell domain "uia", employee lab-users only')
    spread_hia_novell_group = _SpreadCode(
        'group@edir', Constants.Constants.entity_group,
        'Group in Novell domain "uia"')
    spread_hia_edir_grpemp = _SpreadCode(
        'group@ediremp', Constants.Constants.entity_group,
        'Group in Novell domain "UiA", ou=grp,ou=Ans')
    spread_hia_edir_grpstud = _SpreadCode(
        'group@edirstud', Constants.Constants.entity_group,
        'Group in Novell domain "UiA", ou=grp,ou=Stud')    
    spread_nis_user = _SpreadCode(
        'account@nis', Constants.Constants.entity_account,
        'User in NIS domain "stud"')
    spread_ans_nis_user = _SpreadCode(
        'account@nisans', Constants.Constants.entity_account,
        'User in NIS domain "ans"')
    spread_nis_fg = _SpreadCode(
        'group@nis', Constants.Constants.entity_group,
        'File group in NIS domain "stud"')
    spread_nis_ng = _SpreadCode(
        'netgroup@nis', Constants.Constants.entity_group,
        'Net group in NIS domain "stud"')
    spread_ans_nis_fg = _SpreadCode(
        'group@nisans', Constants.Constants.entity_group,
        'File group in NIS domain "ans"')
    spread_ans_nis_ng = _SpreadCode(
        'netgroup@nisans', Constants.Constants.entity_group,
        'Net group in NIS domain "ans"')
    spread_hia_adgang = _SpreadCode(
        'account@adgang', Constants.Constants.entity_person,
        'Person exported to Adgang system')
    spread_hia_email = _SpreadCode(
        'account@imap', Constants.Constants.entity_account,
        'Email user at UiA')
    spread_hia_bibsys = _SpreadCode(
        'account@bibsys', Constants.Constants.entity_person,
        'Person exported to BIBSYS')
    spread_hia_tele = _SpreadCode(
        'account@telefon', Constants.Constants.entity_person,
        'Person exported to phone system')
    spread_hia_ldap_ou = _SpreadCode(
        'ou@ldap', Constants.Constants.entity_ou,
        'OU included in LDAP directory')
    spread_hia_helpdesk = _SpreadCode(
        'account@helpdesk', Constants.Constants.entity_account, 
        'Account exported to helpdesk system')
    spread_hia_ad_account = _SpreadCode(
        'account@ad', Constants.Constants.entity_account,
        'Account included in Active Directory')
    spread_exchange_account = _SpreadCode(
        'account@exchange', Constants.Constants.entity_account,
        'Exchange-enabled account')
    spread_hia_ad_group = _SpreadCode(
        'group@ad', Constants.Constants.entity_group,
        'group included in Active Directory')
    spread_exchange_group = _SpreadCode(
        'group@exchange', Constants.Constants.entity_group,
        'Group exported to Exchange')       
    spread_hia_ezpublish = _SpreadCode(
        'group@ezpublish', Constants.Constants.entity_group,
        'Groups used by EZPublish')
    spread_hia_fronter = _SpreadCode(
        'group@fronter', Constants.Constants.entity_group,
        ('Group representing a course that should be exported to'
         ' the ClassFronter.  Should only be given to groups that'
         ' have been automatically generated from FS.'))
    spread_radius_user = _SpreadCode(
        'account@radius', Constants.Constants.entity_account,
        'User in Radius domain "stud"')
    spread_ans_radius_user = _SpreadCode(
        'account@radiusan', Constants.Constants.entity_account,
        'User in Radius domain "ans"')
    spread_it_radius_user = _SpreadCode(
        'account@radiusit', Constants.Constants.entity_account,
        'User in Radius domain "it"')
    spread_sia_radius_user = _SpreadCode(
        'account@radiusia', Constants.Constants.entity_account,
        'User in Radius domain "sia"')

    spread_uia_ad_account_ehelse_nhn = _SpreadCode(
        'acc@ehelse-nhn', Constants.Constants.entity_account,
        'Account included in AD: eHelse NHN')
    spread_uia_ad_group_ehelse_nhn = _SpreadCode(
        'group@ehelse-nhn', Constants.Constants.entity_group,
        'Group included in AD: eHelse NHN')

    ## Definisjon av traits
    trait_accept_nondisc = _EntityTraitCode(
        'acc_non_disc',
        Constants.Constants.entity_person,
        "Trait marking a person who has accepted a non-disclosure agreement with UiA.")
    trait_reject_nondisc = _EntityTraitCode(
        'rej_non_disc',
        Constants.Constants.entity_person,
        "Trait marking a person who has rejected a non-disclosure agreement with UiA.")
    trait_accept_rules = _EntityTraitCode(
        'accept_rules',
        Constants.Constants.entity_person,
        "Trait marking a person who has accepted terms and rule for use og IT services at UiA.")

    ## Contact info
    contact_office = _ContactInfoCode('OFFICE',
        'Office address (building code and room number')

## Kommenteres ut forel�pig, er usikkert om vi skal ha dem 

##     spread_hia_fs = _SpreadCode(
##         'FS@uia', Constants.Constants.entity_account,
##         'Account exported to FS')
##     spread_hia_sap = _SpreadCode(
##         'SAP@uia', Constants.Constants.entity_account,
##         'Account exported to SAP')

## KARANTENEGRUPPER
    quarantine_slutta = _QuarantineCode('slutta', 'Personen har slutta')
    quarantine_permisjon = _QuarantineCode('permisjon',
                                           'Brukeren har permisjon')
    quarantine_autoekstern = _QuarantineCode('autoekstern',
                                             'Ekstern konto g�tt ut p� dato')

# end Constants

# arch-tag: 7cf93c78-fe00-41f3-8fee-1289c86b7086
