# -*- coding: iso-8859-1 -*-
# Copyright 2002, 2003 University of Oslo, Norway
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

import time

from Cerebrum.modules.no import access_FS

class HiOfStudent(access_FS.Student):
    ## Vi bruker list_privatist, og list_tilbud fra no/access_FS
    def list_aktiv(self, fodselsdato=None, personnr=None):
	""" Hent opplysninger om studenter definert som aktive 
	ved HiOF. En aktiv student er en student som har et gyldig
        opptak til et studieprogram der studentstatuskode er 'AKTIV'
        eller 'PERMISJON' og sluttdatoen er enten i fremtiden eller
        ikke satt."""
        extra = ""
        if fodselsdato and personnr:
            extra = "s.fodselsdato=:fodselsdato AND s.personnr=:personnr AND"

	qry = """
        SELECT DISTINCT
          s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
          s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
          s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
          p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
          p.adresseland_hjemsted, p.status_reserv_nettpubl,
          p.sprakkode_malform, sps.studieprogramkode, sps.studieretningkode,
          sps.studierettstatkode, sps.studentstatkode, sps.terminkode_kull,
          sps.arstall_kull, p.kjonn, p.status_dod, p.telefonnr_mobil,
          s.studentnr_tildelt, kks.klassekode, kks.status_aktiv AS status_aktiv_klasse
        FROM fs.studieprogramstudent sps, fs.person p,
             fs.student s, fs.kullklassestudent kks
        WHERE p.fodselsdato = sps.fodselsdato AND
          p.personnr = sps.personnr AND
          p.fodselsdato = s.fodselsdato AND
          p.personnr = s.personnr AND
          sps.fodselsdato = kks.fodselsdato(+) AND
          sps.personnr = kks.personnr(+) AND
          sps.studieprogramkode = kks.studieprogramkode(+) AND
          sps.terminkode_start = kks.terminkode_start(+) AND
          sps.arstall_start = kks.arstall_start(+) AND
          %s AND
          %s
          sps.status_privatist = 'N' AND
          sps.studentstatkode IN ('AKTIV', 'PERMISJON', 'DELTID') AND
          NVL(sps.dato_studierett_gyldig_til,SYSDATE)>= SYSDATE
          """ % (self._is_alive(), extra)
        return self.db.query(qry, locals())

    def list_eksamensmeldinger(self):  # GetAlleEksamener
        """Hent ut alle eksamensmeldinger i n�v�rende sem."""

        qry = """
        SELECT p.fodselsdato, p.personnr, vm.emnekode, vm.studieprogramkode
        FROM fs.person p, fs.vurdkombmelding vm,
        fs.vurderingskombinasjon vk, fs.vurderingstid vt, 
        fs.vurdkombenhet ve
        WHERE p.fodselsdato=vm.fodselsdato AND
              p.personnr=vm.personnr AND
              vm.institusjonsnr = vk.institusjonsnr AND
              vm.emnekode = vk.emnekode AND
              vm.versjonskode = vk.versjonskode AND
              vm.vurdkombkode = vk.vurdkombkode AND
              vk.vurdordningkode IS NOT NULL and
              vm.arstall = vt.arstall AND
              vm.vurdtidkode = vt.vurdtidkode AND
              ve.emnekode = vm.emnekode AND
              ve.versjonskode = vm.versjonskode AND
              ve.vurdkombkode = vm.vurdkombkode AND 
              ve.vurdtidkode = vm.vurdtidkode AND
              ve.institusjonsnr = vm.institusjonsnr AND
              ve.arstall = vt. arstall AND
              ve.vurdtidkode = vt.vurdtidkode AND
              ve.arstall_reell = %s
              AND %s
        ORDER BY fodselsdato, personnr
        """ % (self.year, self._is_alive())                            
        return self.db.query(qry)

class HiOfUndervisning(access_FS.Undervisning):
    ## TBD: avskaffe UiO-spesifikke s�k for list_undervisningsenheter
    ##      og list_studenter_underv_enhet.
    ##      Pr�ve � lage generell list_studenter_kull.
    ##      Pr�ve � fjerne behov for override-metoder her 
    def list_undervisningenheter(self, sem="current"):
	"""Metoden som henter data om undervisningsenheter
	i n�verende (current) eller neste (next) semester. Default
	vil v�re n�v�rende semester. For hver undervisningsenhet 
	henter vi institusjonsnr, emnekode, versjonskode, terminkode + �rstall 
	og terminnr."""
	qry = """
        SELECT DISTINCT
          r.institusjonsnr, r.emnekode, r.versjonskode, e.emnenavnfork,
          e.emnenavn_bokmal, e.faknr_kontroll, e.instituttnr_kontroll, 
          e.gruppenr_kontroll, r.terminnr, r.terminkode, r.arstall
          FROM fs.emne e, fs.undervisningsenhet r
          WHERE r.emnekode = e.emnekode AND
          r.versjonskode = e.versjonskode AND """ 
        if (sem=="current"):
	    qry +="""%s""" % self._get_termin_aar(only_current=1)
        else: 
	    qry +="""%s""" % self._get_next_termin_aar()
	return self.db.query(qry)

    def list_studenter_underv_enhet(self, institusjonsnr, emnekode, versjonskode,
                                    terminkode, arstall, terminnr):
	"""Finn f�dselsnumrene til alle studenter p� et gitt 
	undervisningsenhet. Skal brukes til � generere grupper for
	adgang til CF."""
	qry = """
        SELECT DISTINCT
          fodselsdato, personnr
        FROM fs.undervisningsmelding
        WHERE
          institusjonsnr = :institusjonsnr AND
          emnekode = :emnekode AND
          versjonskode = :versjonskode AND
          terminnr = :terminnr AND
          terminkode = :terminkode AND
          arstall = :arstall """
        return self.db.query(qry, {'institusjonsnr': institusjonsnr,
                                   'emnekode': emnekode,
                                   'versjonskode': versjonskode,
                                   'terminnr': terminnr,
                                   'terminkode': terminkode,
                                   'arstall': arstall}
                             )

    def list_studenter_kull(self, studieprogramkode, terminkode, arstall):
        """Hent alle studentene som er oppf�rt p� et gitt kull."""

        query = """
        SELECT DISTINCT
            fodselsdato, personnr
        FROM
            fs.studieprogramstudent
        WHERE
            studentstatkode IN ('AKTIV', 'PERMISJON') AND
            NVL(dato_studierett_gyldig_til,SYSDATE)>= SYSDATE AND
            studieprogramkode = :studieprogramkode AND
            terminkode_kull = :terminkode_kull AND
            arstall_kull = :arstall_kull
        """

        return self.db.query(query, {"studieprogramkode" : studieprogramkode,
                                     "terminkode_kull"   : terminkode,
                                     "arstall_kull"      : arstall})

class FS(access_FS.FS):

    def __init__(self, db=None, user=None, database=None):
        super(FS, self).__init__(db=db, user=user, database=database)

        t = time.localtime()[0:3]
        self.year = t[0]
        self.mndnr = t[1]
        self.dday = t[2]
        
        # Override with HiOf-spesific classes
        self.student = HiOfStudent(self.db)
        self.undervisning = HiOfUndervisning(self.db)
