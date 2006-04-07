# -*- coding: iso-8859-1 -*-

# Copyright 2002, 2003, 2004 University of Oslo, Norway
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
                               _PersonAffiliationCode, \
                               _PersonAffStatusCode, \
                               _EntityExternalIdCode, \
                               _AccountCode
from Cerebrum.modules.PosixUser import _PosixShellCode


class Constants(Constants.Constants):
    system_migrate = _AuthoritativeSystemCode('MIGRATE', 'Migrate from files')
    system_override = _AuthoritativeSystemCode('Override',
                                               'Override information fetched from proper authoritative systems')
    system_manual =  _AuthoritativeSystemCode('MANUELL',
                                              'Manually added information')
    # Disse fins i Cerebrum.modules.no/ConstantsHigherEdu  
    system_sap = _AuthoritativeSystemCode('SAP', 'SAP')
    system_fs = _AuthoritativeSystemCode('FS', 'FS')
    # external id definitions (NO_NIN, norwegian national id number)
    externalid_fodselsnr = _EntityExternalIdCode('NO_BIRTHNO',
                                                 Constants.Constants.entity_person,
                                                 'Norwegian birth number')    

    account_test = _AccountCode('testbruker', 'Testkonto')
    account_kurs = _AccountCode('kursbruker', 'Kurskonto')
    # account_studorg = _AccountCode('studorgbruker','Studentorganisasjonsbruker')
    account_felles  = _AccountCode('fellesbruker','Fellesbruker')
    account_system  = _AccountCode('systembruker', 'Systembruker') 
## AFFILIATIONS FOR ANSATTE
    affiliation_ansatt = _PersonAffiliationCode('ANSATT', 'Ansatt ved HiOf')
    affiliation_status_ansatt_manuell = _PersonAffStatusCode(
        affiliation_ansatt, 'ans_manuell', 'Ansatt, manuell import')
    affiliation_status_ansatt_vitenskapelig = _PersonAffStatusCode(
        affiliation_ansatt, 'vitenskapelig', 'Ansatt, vitenskapelige ansatte')
    affiliation_status_ansatt_tekadm = _PersonAffStatusCode(
        affiliation_ansatt, 'tekadm', 'Tekniske/administrative ansatte')
    affiliation_status_ansatt_primaer = _PersonAffStatusCode(
        affiliation_ansatt, 'primaer', 'Prim�rtilknytning for SAP ansatte')
    
## AFFILIATIONS FOR STUDENTER
    affiliation_student = _PersonAffiliationCode('STUDENT', 'Student ved HiOf')
    affiliation_status_student_manuell = _PersonAffStatusCode(
        affiliation_student, 'stud_manuell', 'Student, manuell import')
    affiliation_status_student_evu = _PersonAffStatusCode(
        affiliation_student, 'evu', 'Student, etter og videre utdanning')
    affiliation_status_student_aktiv = _PersonAffStatusCode(
        affiliation_student, 'aktiv', 'Student, aktiv')
    affiliation_status_student_tilbud = _PersonAffStatusCode(
        affiliation_student, 'tilbud', 'Student, tilbud')
    affiliation_status_student_privatist = _PersonAffStatusCode(
        affiliation_student, 'privatist', 'Student, privatist')
## We are not going to use this affiliation for the time being
##     affiliation_status_student_opptak = _PersonAffStatusCode(
##         affiliation_student, 'opptak', 'Student, opptak')

## AFFILIATIONS FOR ASSOSIERTE PERSONER
    affiliation_tilknyttet = _PersonAffiliationCode(
        'TILKNYTTET',
        ('Personer tilknyttet HiOf og registrert i SAP med utvalgte stillingskoder'))
    affiliation_status_tilknyttet_pensjonist = _PersonAffStatusCode(
        affiliation_tilknyttet, 'pensjonist',
        'Personer registrert i SAP som pensjonister')
    affiliation_status_tilknyttet_timelonnet = _PersonAffStatusCode(
        affiliation_tilknyttet, 'timelonnet',
        'Personer registrert i SAP som timel�nnet')

## AFFILIATIONS FOR ANDRE
    affiliation_manuell = _PersonAffiliationCode(
        'MANUELL',
        ('Tilknyttet HiOf uten � v�re registrert i et av de'
         ' autoritative kildesystemene'))
    affiliation_status_manuell_ekstern = _PersonAffStatusCode(
        affiliation_manuell, 'ekstern',
        'Eksternt tilknyttet person, n�r spesifikke kategorier ikke passer')
    affiliation_status_manuell_pensjonist = _PersonAffStatusCode(
        affiliation_manuell, 'pensjonist',
        'Pensjonist ved HiOf, ikke registrert i SAP')
    affiliation_status_manuell_gjest = _PersonAffStatusCode(
        affiliation_manuell, 'gjest', 'Gjesteopphold ved HiOf')
    # affiliation_status_manuell_ans_uten_sap = _PersonAffStatusCode(
    #     affiliation_manuell, 'ans_uten_sap',
    #     'Ansatt som ikke er lagt inn i SAP. En midlertidig status for folk')
    # affiliation_status_manuell_gjest_ikke_epost = _PersonAffStatusCode(
    #     affiliation_manuell, 'gjest_no_epost', 
    #     'Gjesteopphold som ansatt ved HiOf. Skal ikke ha epost')
    # affiliation_status_manuell_gjest_student = _PersonAffStatusCode(
    #     affiliation_manuell, 'gjest_student', 
    #     'Gjesteopphold for student ved HiOf. Epost skal tildeles')
    # affiliation_status_manuell_gjest_student_ikke_epost = _PersonAffStatusCode(
    #     affiliation_manuell, 'gj_st_no_epost', 
    #     'Gjesteopphold for student ved HiOf. Epost skal ikke tildeles')

    affiliation_upersonlig = _PersonAffiliationCode(
        'UPERSONLIG', 'Fellesbrukere, samt andre brukere uten eier')
    affiliation_upersonlig_felles = _PersonAffStatusCode(
        affiliation_upersonlig, 'felles', 'Felleskonti')
    affiliation_upersonlig_kurs = _PersonAffStatusCode(
        affiliation_upersonlig, 'kurs', 'Kurskonti')
    affiliation_upersonlig_pvare = _PersonAffStatusCode(
        affiliation_upersonlig, 'pvare', 'Programvarekonti')
    
## DEFINISJON AV SHELL 
    # We override the default Cerebrum paths for shells, thus this
    # file should appear before PosixUser in cereconf.CLASS_CONSTANTS
    posix_shell_bash = _PosixShellCode('bash', '/bin/bash')
    posix_shell_tcsh = _PosixShellCode('tcsh', '/bin/tcsh')
    posix_shell_csh = _PosixShellCode('csh', '/bin/csh')
    posix_shell_sh = _PosixShellCode('sh', '/bin/sh')

## DEFINISJON AV SPREAD
    spread_nis_account = _SpreadCode(
        'account@nis', Constants.Constants.entity_account,
        'Account in NIS')
    spread_nis_fg = _SpreadCode(
        'fgroup@nis', Constants.Constants.entity_group,
        'File group in NIS')
    spread_nis_ng = _SpreadCode(
        'netgroup@nis', Constants.Constants.entity_group,
        'Net group in NIS')
    spread_email_account = _SpreadCode(
        'account@imap', Constants.Constants.entity_account,
        'Email account at HiOf')
    spread_ldap_person = _SpreadCode(
        'person@ldap', Constants.Constants.entity_person, 
        'Person included in LDAP directory')
    spread_ad_account = _SpreadCode(
        'account@ad', Constants.Constants.entity_account,
        'Account included in Active Directory')
    spread_ad_group = _SpreadCode(
        'group@ad', Constants.Constants.entity_group,
        'group included in Active Directory')   
