# -*- coding: iso-8859-1 -*-

# Copyright 2007-2008 University of Oslo, Norway
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

from Cerebrum import Constants
from Cerebrum import Errors
from Cerebrum import Person
from Cerebrum.Constants import ConstantsBase, _CerebrumCode, _SpreadCode
from Cerebrum.modules.CLConstants import _ChangeTypeCode
from Cerebrum.DatabaseAccessor import DatabaseAccessor
from Cerebrum.Utils import Factory
from Cerebrum.modules.bofhd.errors import CerebrumError

class _EphorteRoleTypeCode(_CerebrumCode):
    "Mappings stored in the contact_info_code table"
    _lookup_table = '[:table schema=cerebrum name=ephorte_role_type_code]'
    pass

class _EphortePermTypeCode(_CerebrumCode):
    "Mappings stored for 'tilgangskoder' i UiOs Ephorte"
    _lookup_table = ' [:table schema=cerebrum name=ephorte_perm_type_code]'
    pass

class _EphorteArkivdelCode(_CerebrumCode):
    "Mappings stored in the contact_info_code table"
    _lookup_table = '[:table schema=cerebrum name=ephorte_arkivdel_code]'
    pass

class _EphorteJournalenhetCode(_CerebrumCode):
    "Mappings stored in the contact_info_code table"
    _lookup_table = '[:table schema=cerebrum name=ephorte_journalenhet_code]'
    pass

class EphorteConstants(ConstantsBase):
    # Values from the ePhorte table ROLE
    ephorte_role_ar1 = _EphorteRoleTypeCode('AR1', 'Arkivansvarlig')
    ephorte_role_ar2 = _EphorteRoleTypeCode('AR2', 'Arkivar')
    ephorte_role_ar3 = _EphorteRoleTypeCode('AR3', 'Arkivledelsen')    
    ephorte_role_ld = _EphorteRoleTypeCode('LD', 'Leder/saksfordeler')
    ephorte_role_ld_les = _EphorteRoleTypeCode('LD LES', 'Leserolle - leder')
    ephorte_role_sb = _EphorteRoleTypeCode('SB', 'Saksbehandler')
    ephorte_role_sy = _EphorteRoleTypeCode('SY', 'Systemansvarlig')
    ephorte_role_mal = _EphorteRoleTypeCode('MAL', 'Mal-ansvarlige')

    #Values from the ePhorte table tilgang_type_code
    ephorte_perm_us = _EphortePermTypeCode('US', 'Unntatt etter offentlighetsloven ved SO')
    ephorte_perm_un = _EphortePermTypeCode('UN', 'Unntatt etter offentlighetsloven ved NIKK')
    ephorte_perm_ua = _EphortePermTypeCode('UA', 'Under arbeid')    
    ephorte_perm_uo = _EphortePermTypeCode('UO', 'Unntatt etter offentlighetsloven')
    ephorte_perm_p = _EphortePermTypeCode('P', 'Personalsaker')
    ephorte_perm_p2 = _EphortePermTypeCode('P2', 'Personers �konomiske forhold')
    ephorte_perm_p3 = _EphortePermTypeCode('P3', 'Disiplin�rsaker personal')
    ephorte_perm_p4 = _EphortePermTypeCode('P4', 'Rettssaker')
    ephorte_perm_s = _EphortePermTypeCode('S', 'Studentsaker')
    ephorte_perm_s2 = _EphortePermTypeCode('S2', 'Disiplin�rsaker studenter')
    ephorte_perm_b = _EphortePermTypeCode('B', 'Begrenset etter sikkerhetsloven')
    ephorte_perm_f = _EphortePermTypeCode('F', 'Fortrolig etter beskyttelsesinstruksen')
    ephorte_perm_k = _EphortePermTypeCode('K', 'Kontrakter og avtaler')                
    
    # Values from the ePhorte table ARKIVDEL
    ephorte_arkivdel_avtale_uio = _EphorteArkivdelCode(
        'AVTALE UIO', 'Avtalearkiv ved Universitetet i Oslo')
    ephorte_arkivdel_eiend_uio = _EphorteArkivdelCode(
        'EIEND UIO', 'Eiendomsarkiv ved Universitetet i Oslo')
    ephorte_arkivdel_khm_forn = _EphorteArkivdelCode(
        'KHM FORN', 'KHM (Kulturhistorisk museum) - Fornminnneforvaltning')
    ephorte_arkivdel_pers_uio = _EphorteArkivdelCode(
        'PERS UIO', 'Personalarkiv ved Universitetet i Oslo')
    ephorte_arkivdel_persav_uio = _EphorteArkivdelCode(
        'PERSAV UIO', 'Avsluttede personalmapper ved UiO')
    ephorte_arkivdel_sak_nikk = _EphorteArkivdelCode(
        'SAK NIKK', 'Saksarkiv ved NIKK')
    ephorte_arkivdel_sak_so = _EphorteArkivdelCode(
        'SAK SO', 'Saksarkiv ved Samordna Opptak')
    ephorte_arkivdel_sak_uio = _EphorteArkivdelCode(
        'SAK UIO', 'Saksarkiv ved Universitetet i Oslo')
    ephorte_arkivdel_stud_uio = _EphorteArkivdelCode(
        'STUD UIO', 'Studentarkiv ved Universitetet i Oslo')
    ephorte_arkivdel_studav_uio = _EphorteArkivdelCode(
        'STUDAV UIO', 'Avsluttede studentmapper ved UiO')

    # Values from the ePhorte table JOURNENHET
    ephorte_journenhet_uio = _EphorteJournalenhetCode(
        'J-UIO', 'Journalenhet for UiO - Universitetet i Oslo')
    ephorte_journenhet_so = _EphorteJournalenhetCode(
        'J-SO', 'Journalenhet for SO - Samordna Opptak')
    ephorte_journenhet_nikk = _EphorteJournalenhetCode(
        'J-NIKK', 'Journalenhet for NIKK - Nordisk institutt for kvinne- og kj�nnsforskn')

    spread_ephorte_person = _SpreadCode('ePhorte_person',
                                        Constants.Constants.entity_person,
                                        'Person included in ePhorte export')
    spread_ephorte_ou = _SpreadCode('ePhorte_ou',
                                    Constants.Constants.entity_ou,
                                    'OU included in ePhorte export')

    EphorteRole = _EphorteRoleTypeCode
    EphorteArkivdel = _EphorteArkivdelCode
    EphorteJournalenhet = _EphorteJournalenhetCode
    EphortePermission = _EphortePermTypeCode
    
    # ChangeLog constants
    ephorte_role_add = _ChangeTypeCode(
        'ephorte', 'role_add', 'add ephorte role @ %(dest)s')

    ephorte_role_rem = _ChangeTypeCode(
        'ephorte', 'role_rem', 'remove ephorte role @ %(dest)s')

    ephorte_perm_add = _ChangeTypeCode(
        'ephorte', 'perm_add', 'add ephorte perm')

    ephorte_perm_rem = _ChangeTypeCode(
        'ephorte', 'perm_rem', 'remove ephorte perm')    


##
## TBD: B�r denne klassen egentlig v�re en PersonMixin? Fordi alle
##      disse funksjonene er relative til personer. Da vil det v�re
##      lettere � f� til f�lgende businesslogikk som n� er
##      implementert litt teit:
##      
##        * hvis en person slettes skal dens ephorte-roller og spreads
##          automatisk fjernes
##        * hvis en person mister alle sine roller, skal ogs� spread
##          fjernes automatisk.
##
class EphorteRole(DatabaseAccessor):
    def __init__(self, database):
        super(EphorteRole, self).__init__(database)
        self.co = Factory.get('Constants')(database)
        self.pe = Factory.get('Person')(database)

    def add_role(self, person_id, role, sko, arkivdel, journalenhet,
                 rolletittel='', stilling='', standard_role='F', auto_role='T'):
        # TODO: Skrive noe om start_date/end_date
        # TODO: Bruke account_id for brukerens prim�rbruker
        binds = {
            'person_id': person_id,
            'role_type': role,
            # TODO: Hva skal standard_role v�re? B�r i hvert fall ikke
            # hardkodes p� denne m�ten.
            'standard_role': standard_role,  
            'auto_role': auto_role,  
            'adm_enhet': sko,
            'arkivdel': arkivdel,
            'journalenhet': journalenhet,
            'rolletittel': rolletittel,
            'stilling': stilling
            }
        self.execute("""
        INSERT INTO [:table schema=cerebrum name=ephorte_role]
          (%s) VALUES (%s)""" % (", ".join(binds.keys()),
                                 ", ".join([":%s" % k for k in binds.keys()])),
                                 binds)
        self._db.log_change(person_id, self.co.ephorte_role_add,
                            sko, change_params={
            'arkivdel': arkivdel and str(arkivdel) or '',
#            'adm_enhet': adm_enhet and str(adm_enhet) or '',
            'rolle_type': str(role)})
    
    def _remove_role(self, person_id, role, sko, arkivdel, journalenhet):
        binds = {
            'person_id': person_id,
            'role_type': role,
            'adm_enhet': sko,
            'arkivdel': arkivdel,
            'journalenhet': journalenhet
            }
            
        self.execute("""
        DELETE FROM [:table schema=cerebrum name=ephorte_role]
        WHERE %s""" % " AND ".join(
            ["%s=:%s" % (x, x) for x in binds.keys() if binds[x] is not None] +
            ["%s IS NULL" % x for x in binds.keys() if binds[x] is None]),
                     binds)
        self._db.log_change(person_id, self.co.ephorte_role_rem,
                            sko, change_params={
            'arkivdel': arkivdel and str(arkivdel) or '',
#            'adm_enhet': adm_enhet and str(adm_enhet) or '',
            'rolle_type': str(role)})

    # Wrapper for _remove_role.
    # This is a bit hackish, see the class comment for more info.
    def remove_role(self, person_id, role, sko, arkivdel, journalenhet):
        self._remove_role(person_id, role, sko, arkivdel, journalenhet)
        # If person doesn't have any roles left the ephorte-spread
        # should be removed
        if not self.list_roles(person_id=person_id):
            self.pe.clear()
            self.pe.find(person_id)
            self.pe.delete_spread(self.co.spread_ephorte_person)
            
    def list_roles(self, person_id=None):
        if person_id:
            where = "WHERE person_id=:person_id"
        else:
            where = ""
        return self.query("""
        SELECT person_id, role_type, standard_role, adm_enhet,
               arkivdel, journalenhet, rolletittel, stilling,
               start_date, end_date, auto_role
        FROM [:table schema=cerebrum name=ephorte_role] %s""" % where, {
            'person_id': person_id})

##
## Vi skal oppdatere tilgangskoder for personer i Ephorte
## via web-servicen. Denne klassen inneholder metodene
## n�dvendige for � lagre, modifisere/slette tilganskoder
## for personer i Cerebrum slik at informasjon om disse kan
## overf�res til Ephorte
##
class EphortePermission(DatabaseAccessor):
    def __init__(self, database):
        super(EphortePermission, self).__init__(database)
        self.co = Factory.get('Constants')(database)
        self.pe = Factory.get('Person')(database)
        
    def add_permission(self, person_id, tilgang, sko, requestee):
        binds = {
            'person_id': person_id,
            'perm_type': tilgang,
            'adm_enhet': sko,
            'requestee_id': requestee
            }
        self.execute("""
        INSERT INTO [:table schema=cerebrum name=ephorte_permission]
          (%s) VALUES (%s)""" % (", ".join(binds.keys()),
                                 ", ".join([":%s" % k for k in binds.keys()])),
                                 binds)
        self._db.log_change(person_id, self.co.ephorte_perm_add,
                            sko, change_params={
            'adm_enhet': sko or '',
            'perm_type': str(tilgang)})

    def remove_permission(self, person_id, tilgang, sko):
        binds = {
            'person_id': person_id,
            'perm_type': tilgang,
            'adm_enhet': sko
            }
        self.execute("""
        DELETE FROM [:table schema=cerebrum name=ephorte_permission]
        WHERE %s""" % " AND ".join(
            ["%s=:%s" % (x, x) for x in binds.keys() if binds[x] is not None] +
            ["%s IS NULL" % x for x in binds.keys() if binds[x] is None]),
                     binds)
        self._db.log_change(person_id, self.co.ephorte_perm_rem,
                            sko, change_params={
            'adm_enhet': sko or '',
            'perm_type': str(tilgang)})

    def list_permission(self, person_id=None):
        if person_id:
            where = "WHERE person_id=:person_id"
        else:
            where = ""
        return self.query("""
        SELECT person_id, perm_type, adm_enhet,
               requestee_id, start_date, end_date
        FROM [:table schema=cerebrum name=ephorte_permission] %s""" % where, {
            'person_id': person_id})
    
## Denne koden er ikke klar enn�
# class PersonEphorteMixin(Person.Person):
#     """Ephorte specific methods for Person entities"""
# 
#     def delete(self):
#         """Remove any ephorte roles before deleting"""
#         for row in ephorte_role.list_roles(person_id=self.entity_id):
#             ephorte_role.remove_role(old_id, int(row['role_type']), int(row['adm_enhet']),
#                                      row['arkivdel'], row['journalenhet'])
#         self.__super.delete()
