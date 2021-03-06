# -*- coding: iso-8859-1 -*-

# Copyright 2002, 2003, 2004, 2005 University of Oslo, Norway
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

from Cerebrum import Database
from Cerebrum import Errors

from Cerebrum.modules.no import access_FS

class UiOStudent40(access_FS.Student):
    def list_aktiv(self):  # GetStudinfAktiv
        """Hent f�dselsnummer+studieprogram for alle aktive studenter.
        Som aktive studenter regner vi alle studenter med opptak til
        et studieprogram som samtidig har en eksamensmelding eller en
        avlagt eksamen inneverende semester i et emne som kan inng� i
        dette studieprogrammet, eller som har bekreftet sin
        utdanningsplan.  Disse f�r affiliation student med kode aktiv
        til sp.faknr_studieansv+sp.instituttnr_studieansv+
        sp.gruppenr_studieansv.  Vi har alt hentet opplysninger om
        adresse ol. efter som de har opptak.  Henter derfor kun
        f�dselsnummer og studieprogram.  Medf�rer at du kan f� med
        linjer som du ikke har personinfo for, dette vil v�re snakk om
        ekte-d�de personer."""

        qry = """
        SELECT DISTINCT
          s.fodselsdato, s.personnr, sp.studieprogramkode,
          st.studieretningkode
        FROM fs.studieprogram sp, fs.studierett st, fs.student s,
          fs.registerkort r, fs.eksamensmelding em,
          fs.emne_i_studieprogram es
        WHERE s.fodselsdato=r.fodselsdato AND
          s.personnr=r.personnr AND
          s.fodselsdato=st.fodselsdato AND
          s.personnr=st.personnr AND
          s.fodselsdato=em.fodselsdato AND
          s.personnr=em.personnr AND
          es.studieprogramkode=sp.studieprogramkode AND
          em.emnekode=es.emnekode AND
          st.status_privatist='N' AND 
          st.studieprogramkode=sp.studieprogramkode AND
          r.regformkode IN ('STUDWEB','DOKTORREG','MANUELL') AND
          NVL(st.dato_gyldig_til,SYSDATE) >= sysdate AND
          %s
        UNION """ %(self._get_termin_aar(only_current=1))
        qry = qry + """
        SELECT DISTINCT
          s.fodselsdato, s.personnr, sp.studieprogramkode, st.studieretningkode
        FROM fs.student s, fs.studierett st,
          fs.studprogstud_planbekreft r, fs.studieprogram sp
        WHERE s.fodselsdato=st.fodselsdato AND
          s.personnr=st.personnr AND
          s.fodselsdato=r.fodselsdato AND
          s.personnr=r.personnr AND
          sp.status_utdplan='J' AND
          st.status_privatist='N' AND     
          r.studieprogramkode=st.studieprogramkode AND
          st.studieprogramkode=sp.studieprogramkode AND
          NVL(st.dato_gyldig_til,SYSDATE) >= sysdate AND
          r.dato_bekreftet < SYSDATE AND
          r.arstall_bekreft = %d AND
          r.terminkode_bekreft = '%s'
        UNION""" %(self.year, self.semester)
        qry = qry + """
        SELECT DISTINCT
          sp.fodselsdato, sp.personnr, st.studieprogramkode,
          st.studieretningkode
        FROM fs.studentseksprotokoll sp, fs.studierett st,
          fs.emne_i_studieprogram es
        WHERE sp.arstall >= %s AND
          (%s <= 6 OR sp.manednr > 6 ) AND
          sp.fodselsdato = st.fodselsdato AND
          sp.personnr = st.personnr AND
          sp.institusjonsnr = '185' AND
          sp.emnekode = es.emnekode AND
          es.studieprogramkode = st.studieprogramkode AND
          (st.opphortstudierettstatkode IS NULL OR
          st.DATO_GYLDIG_TIL >= sysdate) AND
          st.status_privatist = 'N'
          """ %(self.year, self.mndnr)
     	return self.db.query(qry)

class UiOPortal40(access_FS.FSObject):
    def list_eksmeld(self):  # GetPortalInfo
        """
        Hent ut alle eksamensmeldinger i n�v�rende semester med all
        interessant informasjon for portaldumpgenerering.

        SQL-sp�rringen er dyp magi. Sp�rsm�l rettes til baardj.
        """

        #
        # NB! Det er ikke meningen at vanlige d�delige skal kunne forst�
        # denne SQL-sp�rringen. Lurer du p� noe, plag baardj
        # 

        # Velg ut studentens eksamensmeldinger for innev�rende og
        # fremtidige semestre.  S�ket sjekker at studenten har
        # rett til � f�lge kurset, og at vedkommende er
        # semesterregistrert i innev�rende semester (eller,
        # dersom fristen for semesterregistrering dette
        # semesteret enn� ikke er utl�pt, hadde
        # semesterregistrert seg i forrige semester)

        query = """
        SELECT m.fodselsdato, m.personnr,
               m.emnekode, m.arstall, m.manednr,
               sprg.studienivakode,
               e.institusjonsnr_reglement, e.faknr_reglement,
               e.instituttnr_reglement, e.gruppenr_reglement,
               es.studieprogramkode
        FROM fs.eksamensmelding m, fs.emne e, fs.studierett st,
             fs.emne_i_studieprogram es, fs.registerkort r,
             fs.studieprogram sprg, fs.person p
        WHERE
            m.arstall >= :aar1 AND
            m.fodselsdato = st.fodselsdato AND
            m.personnr = st.personnr AND
            m.fodselsdato = r.fodselsdato AND
            m.personnr = r.personnr AND
            m.fodselsdato = p.fodselsdato AND
            m.personnr = p.personnr AND
            NVL(p.status_dod, 'N') = 'N' AND
            %s AND
            NVL(st.dato_gyldig_til,SYSDATE) >= sysdate AND
            st.status_privatist = 'N' AND
            m.institusjonsnr = e.institusjonsnr AND
            m.emnekode = e.emnekode AND
            m.versjonskode = e.versjonskode AND
            m.institusjonsnr = es.institusjonsnr AND
            m.emnekode = es.emnekode AND
            es.studieprogramkode = st.studieprogramkode AND
            es.studieprogramkode = sprg.studieprogramkode
        """ % self._get_termin_aar()

        # Velg ut studentens avlagte UiO eksamener i innev�rende
        # semester (studenten er fortsatt gyldig student ut
        # semesteret, selv om alle eksamensmeldinger har g�tt
        # over til � bli eksamensresultater).
        #
        # S�ket sjekker _ikke_ at det finnes noen
        # semesterregistrering for innev�rende registrering
        # (fordi dette skal v�re implisitt garantert av FS)
        query += """ UNION
        SELECT sp.fodselsdato, sp.personnr,
               sp.emnekode, sp.arstall, sp.manednr,
               sprg.studienivakode,
               e.institusjonsnr_reglement, e.faknr_reglement,
               e.instituttnr_reglement, e.gruppenr_reglement,
               st.studieprogramkode
        FROM fs.studentseksprotokoll sp, fs.emne e, fs.studierett st,
             fs.emne_i_studieprogram es, fs.studieprogram sprg, fs.person p
        WHERE
            sp.arstall >= :aar2 AND
            sp.fodselsdato = st.fodselsdato AND
            sp.personnr = st.personnr AND
            sp.fodselsdato = p.fodselsdato AND
            sp.personnr = p.personnr AND
            NVL(p.status_dod, 'N') = 'N' AND
            NVL(st.DATO_GYLDIG_TIL,SYSDATE) >= sysdate AND
            st.status_privatist = 'N' AND
            sp.emnekode = e.emnekode AND
            sp.versjonskode = e.versjonskode AND
            sp.institusjonsnr = e.institusjonsnr AND
            sp.institusjonsnr = '185' AND
            sp.emnekode = es.emnekode AND
            es.studieprogramkode = st.studieprogramkode AND
            es.studieprogramkode = sprg.studieprogramkode
        """

        # Velg ut alle studenter som har opptak til et studieprogram
        # som krever utdanningsplan og som har bekreftet utdannings-
        # planen dette semesteret.
        #
        # NB! TO_*-konverteringene er p�krevd
        query += """ UNION
        SELECT stup.fodselsdato, stup.personnr,
               TO_CHAR(NULL) as emnekode, TO_NUMBER(NULL) as arstall,
               TO_NUMBER(NULL) as manednr,
               sprg.studienivakode,
               sprg.institusjonsnr_studieansv, sprg.faknr_studieansv,
               sprg.instituttnr_studieansv, sprg.gruppenr_studieansv,
               st.studieprogramkode
        FROM fs.studprogstud_planbekreft stup,fs.studierett st,
             fs.studieprogram sprg, fs.person p
        WHERE
              stup.arstall_bekreft=:aar3 AND
              stup.terminkode_bekreft=:semester AND
              stup.fodselsdato = st.fodselsdato AND
              stup.personnr = st.personnr AND
              stup.fodselsdato = p.fodselsdato AND
              stup.personnr = p.personnr AND
              NVL(p.status_dod, 'N') = 'N' AND
              NVL(st.DATO_GYLDIG_TIL, SYSDATE) >= sysdate AND
              st.status_privatist = 'N' AND
              stup.studieprogramkode = st.studieprogramkode AND
              stup.studieprogramkode = sprg.studieprogramkode AND
              sprg.status_utdplan = 'J'
        """
        semester = "%s" % self.semester
        # FIXME! Herregud da, hvorfor m� de ha hver sitt navn?
        return self.db.query(query,
                             {"aar1" : self.year,
                              "aar2" : self.year,
                              "aar3" : self.year,
                              "semester": semester},
                             False)
    
class FS(access_FS.FS):
    def __init__(self, db=None, user=None, database=None):
        super(FS, self).__init__(db=db, user=user, database=database)
        # override neccessary classes
        self.student = UiOStudent40(self.db)
        self.portal = UiOPortal40(self.db)

