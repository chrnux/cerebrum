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

"""Klasser for aksesering av FS.  Institusjons-spesifik bruk av FS b�r
h�ndteres ved � subklasse relevante deler av denne koden.  Tilsvarende
dersom man skal ha kode for en spesifik FS-versjon.

Disse klassene er ment brukt ved � instansiere klassen FS
"""

import re
import time

from Cerebrum import Database
from Cerebrum import Errors

# TODO: En del funksjoner finnes b�de som get_ og list_ variant.  Det
# kunne v�re en fordel om man etablerte en mekanisme for � sl� sammen
# disse.  Det vil b�de redusere kodeduplisering, og v�re nyttig dersom
# man skal foreta inkrementelle operasjoner basert p� endringer i FS.

# TODO: Man m� bestemme seg for � multiline qry strenger skal v�re
# indentert eller starte p� kolonne 0.

# Note: The oracle database-driver does not support dates before 1970.
# Thus TO_DATE must be used when inserting dates

class FSObject(object):
    """Parent class that all other fs-access methods inherit.
    Provides a number of utility methods."""

    def __init__(self, db):
        self.db = db
        t = time.localtime()[0:2]
        if t[1] <= 6:
            self.sem = 'V'
            self.semester = 'V�R'
        else:
            self.sem = 'H'
            self.semester = 'H�ST'
        self.year = t[0]
        self.mndnr = t[1]
        self.YY = str(t[0])[2:]

    def _is_alive(self):
	return "NVL(p.status_dod, 'N') = 'N'\n"

    def _get_termin_aar(self, only_current=0):
        yr, mon, md = time.localtime()[0:3]
        if mon <= 6:
            # Months January - June == Spring semester
            current = "(r.terminkode = 'V�R' AND r.arstall=%s)\n" % yr;
            if only_current or mon >= 3 or (mon == 2 and md > 15):
                return current
            return "(%s OR (r.terminkode = 'H�ST' AND r.arstall=%d))\n" % (
                current, yr-1)
        # Months July - December == Autumn semester
        current = "(r.terminkode = 'H�ST' AND r.arstall=%d)\n" % yr
        if only_current or mon >= 10 or (mon == 9 and md > 15):
            return current
        return "(%s OR (r.terminkode = 'V�R' AND r.arstall=%d))\n" % (current, yr)

class Person(FSObject):
    def get_person(self, fnr, pnr):
        return self.db.query("""
SELECT fornavn, etternavn, fornavn_uppercase, etternavn_uppercase,
       emailadresse, kjonn, dato_fodt
FROM fs.person
WHERE fodselsdato=:fnr AND personnr=:pnr""",  {'fnr': fnr, 'pnr': pnr})

    def add_person(self, fnr, pnr, fornavn, etternavn, email, kjonn,
                   birth_date):
        return self.db.execute("""
INSERT INTO fs.person
  (fodselsdato, personnr, fornavn, etternavn, fornavn_uppercase,
   etternavn_uppercase, emailadresse, kjonn, dato_fodt)
VALUES
  (:fnr, :pnr, :fornavn, :etternavn, UPPER(:fornavn2),
  UPPER(:etternavn2), :email, :kjonn, TO_DATE(:birth_date, 'YYYY-MM-DD'))""", {
            'fnr': fnr, 'pnr': pnr, 'fornavn': fornavn,
            'etternavn': etternavn, 'email': email,
            'kjonn': kjonn, 'birth_date': birth_date,
            'fornavn2': fornavn, 'etternavn2': etternavn})

    def get_fagperson(self, fnr, pnr):
        return self.db.query("""
SELECT
  fodselsdato, personnr, adrlin1_arbeide, adrlin2_arbeide,
  postnr_arbeide, adrlin3_arbeide, telefonnr_arbeide, arbeidssted,
  institusjonsnr_ansatt, faknr_ansatt, instituttnr_ansatt,
  gruppenr_ansatt, stillingstittel_norsk, telefonnr_fax_arb,
  status_aktiv
FROM fs.fagperson
WHERE fodselsdato=:fnr AND personnr=:pnr""", {'fnr': fnr, 'pnr': pnr})

    def add_fagperson(self, fnr, pnr, adr1, adr2, postnr, adr3,
                      arbsted, institusjonsnr, fakultetnr, instiuttnr,
                      gruppenr, tlf, tittel, fax, status):
        return self.db.execute("""
INSERT INTO fs.fagperson
  (fodselsdato, personnr, adrlin1_arbeide, adrlin2_arbeide,
   postnr_arbeide, adrlin3_arbeide, telefonnr_arbeide, arbeidssted,
   institusjonsnr_ansatt, faknr_ansatt, instituttnr_ansatt,
   gruppenr_ansatt, stillingstittel_norsk, telefonnr_fax_arb,
   status_aktiv)
VALUES
  (:fnr, :pnr, :adr1, :adr2, :postnr, :adr3, :tlf, :arbsted,
   :institusjonsnr, :fakultetnr, :instiuttnr, :gruppenr, :tittel, :fax,
   :status)""", {
            'fnr': fnr, 'pnr': pnr,
            'adr1': adr1, 'adr2': adr2, 'postnr': postnr, 'adr3': adr3,
            'tlf': tlf, 'arbsted': arbsted,
            'institusjonsnr': institusjonsnr , 'fakultetnr': fakultetnr,
            'instiuttnr': instiuttnr, 'gruppenr':gruppenr,
            'tittel': tittel, 'fax': fax, 'status': status})

    def update_fagperson(self, fnr, pnr, adr1, adr2, postnr, adr3,
                         arbsted, institusjonsnr, fakultetnr,
                         instiuttnr, gruppenr, tlf, tittel, fax,
                         status):
        return self.db.execute("""
UPDATE fs.fagperson
SET
  adrlin1_arbeide=:adr1, adrlin2_arbeide=:adr2,
  postnr_arbeide=:postnr, adrlin3_arbeide=:adr3,
  telefonnr_arbeide=:tlf, arbeidssted=:arbsted,
  institusjonsnr_ansatt=:institusjonsnr, faknr_ansatt=:fakultetnr,
  instituttnr_ansatt=:instiuttnr, gruppenr_ansatt=:gruppenr,
  stillingstittel_norsk=:tittel, telefonnr_fax_arb=:fax,
  status_aktiv=:status
WHERE fodselsdato=:fnr AND personnr=:pnr""", {
            'fnr': fnr, 'pnr': pnr,
            'adr1': adr1, 'adr2': adr2, 'postnr': postnr, 'adr3': adr3,
            'tlf': tlf, 'arbsted': arbsted,
            'institusjonsnr': institusjonsnr , 'fakultetnr': fakultetnr,
            'instiuttnr': instiuttnr, 'gruppenr':gruppenr,
            'tittel': tittel, 'fax': fax, 'status': status})


    def list_dead_persons(self): # GetDod
        """Henter en liste med de personer som ligger i FS og som er
           registrert som d�d.  Listen kan sikkert kortes ned slik at
           man ikke tar alle, men i denne omgang s� gj�r vi det
           slik."""
        qry = """
SELECT p.fodselsdato, p.personnr
FROM   fs.person p
WHERE  p.status_dod = 'J'"""
        return self.db.query(qry)

    def list_fnr_endringer(self): # GetFnrEndringer
        """Hent informasjon om alle registrerte f�dselsnummerendringer"""
        qry = """
SELECT fodselsdato_naverende, personnr_naverende,
       fodselsdato_tidligere, personnr_tidligere,
       TO_CHAR(dato_foretatt, 'YYYY-MM-DD HH24:MI:SS') AS dato_foretatt
FROM fs.fnr_endring
ORDER BY dato_foretatt"""
        return self.db.query(qry)

    def list_email(self, fetchall = False): # GetAllPersonsEmail
        return self.db.query("""
        SELECT fodselsdato, personnr, emailadresse
        FROM fs.person""", fetchall = fetchall)

    def write_email(self, fodselsdato, personnr, email): # WriteMailAddr
        self.db.execute("""
        UPDATE fs.person
        SET emailadresse=:email
        WHERE fodselsdato=:fodselsdato AND personnr=:personnr""",
                        {'fodselsdato': fodselsdato,
                         'personnr': personnr,
                         'email': email})

    def list_uname(self, fetchall = False): # GetAllPersonsUname
        return self.db.query("""
        SELECT fodselsdato, personnr, brukernavn
        FROM fs.personreg""", fetchall = fetchall)

    def write_uname(self, fodselsdato, personnr, uname): # WriteUname
        self.db.execute("""
        UPDATE fs.personreg
        SET brukernavn = :uname
        WHERE fodselsdato = :fodselsdato AND personnr = :personnr""",
                        {'fodselsdato': fodselsdato,
                         'personnr': personnr,
                         'uname': uname})

class Student(FSObject):
    def list_semreg(self):   # GetStudinfRegkort

        """Hent informasjon om semester-registrering og betaling"""
        qry = """
SELECT DISTINCT
       fodselsdato, personnr, regformkode, dato_endring, dato_opprettet
FROM fs.registerkort r
WHERE %s""" % self._get_termin_aar(only_current=1)
        return self.db.query(qry)

    def get_semreg(self,fnr,pnr):  # GetStudentSemReg
        """Hent data om semesterregistrering for student i n�v�rende semester."""
        qry = """
SELECT DISTINCT
  r.regformkode, r.betformkode, r.dato_betaling, r.dato_regform_endret
FROM fs.registerkort r, fs.person p
WHERE r.fodselsdato = :fnr AND
      r.personnr = :pnr AND
      %s AND
      r.fodselsdato = p.fodselsdato AND
      r.personnr = p.personnr AND
      %s
        """ %(self._get_termin_aar(only_current=1),self._is_alive())
	return self.db.query(qry, {'fnr': fnr, 'pnr': pnr})

    def list_eksamensmeldinger(self):  # GetAlleEksamener
	"""Hent ut alle eksamensmeldinger i n�v�rende sem.
	samt fnr for oppmeldte(topics.xml)"""
        # TODO: Det er mulig denne skal splittes i to s�k, ett som
        # returnerer lovlige, og et som returnerer "ulovlige"
        # eksamensmeldinger (sistnevnte er vel GetStudinfPrivatist?)
	aar = time.localtime()[0:1]
	qry = """
SELECT p.fodselsdato, p.personnr, e.emnekode, e.studieprogramkode
FROM fs.person p, fs.eksamensmelding e
WHERE p.fodselsdato=e.fodselsdato AND
      p.personnr=e.personnr AND
      e.arstall=%s 
      AND %s
ORDER BY fodselsdato, personnr
      """ %(aar[0],self._is_alive())                            
      	return self.db.query(qry)

    def get_emne_eksamensmeldinger(self, emnekode):  # GetEmneinformasjon
        """
        Hent informasjon om alle som er registrert p� EMNEKODE
        """

        query = """
                SELECT p.fodselsdato, p.personnr, p.fornavn, p.etternavn
                FROM
                     [:table schema=fs name=person] p,
                     [:table schema=fs name=eksamensmelding] e
                WHERE
                     e.emnekode = :emnekode AND
                     e.fodselsdato = p.fodselsdato AND
                     e.personnr = p.personnr
                """

        # NB! Oracle driver does not like :foo repeated multiple times :-(
        # That is why we interpolate variables into the query directly.
        year, month = time.localtime()[0:2]
        if month < 6:
            time_part = """
                        AND e.arstall >= %(year)d
                        AND e.manednr >= %(month)d
                        """ % locals()
        else:
            time_part = """
                        AND ((e.arstall = %(year)d AND
                              e.manednr >= %(month)d) OR
                             (e.arstall > %(year)d))
                        """ % locals()
        return self.db.query(query + time_part, {"emnekode" : emnekode})

    def get_eksamensmeldinger(self, fnr, pnr): # GetStudentEksamen
	"""Hent alle eksamensmeldinger for en student for n�v�rende
           semester"""
        qry = """
SELECT DISTINCT
  em.emnekode, em.dato_opprettet, em.status_er_kandidat
FROM fs.eksamensmelding em, fs.person p
WHERE em.fodselsdato = :fnr AND
      em.personnr = :pnr AND
      em.fodselsdato = p.fodselsdato AND
      em.personnr = p.personnr AND
      (em.arstall > :year1 OR (em.arstall = :year2 AND em.manednr > :mnd - 3))
      AND %s
        """ % self._is_alive()
        return self.db.query(qry, {'fnr': fnr,
                                   'pnr': pnr,
                                   'year1': self.year,
                                   'year2': self.year,
                                   'mnd': self.mndnr})

    def get_utdanningsplan(self, fnr, pnr): # GetStudentUtdPlan
        """Hent opplysninger om utdanningsplan for student"""
        qry = """
SELECT DISTINCT
  utdp.studieprogramkode, utdp.terminkode_bekreft, utdp.arstall_bekreft,
  utdp.dato_bekreftet
FROM fs.studprogstud_planbekreft utdp, fs.person p
WHERE utdp.fodselsdato = :fnr AND
      utdp.personnr = :pnr AND
      utdp.fodselsdato = p.fodselsdato AND
      utdp.personnr = p.personnr AND
      %s
        """ % self._is_alive()
	return self.db.query(qry, {'fnr': fnr, 'pnr': pnr})
    
    def list_tilbud(self, institutsjonsnr=0):  # GetStudentTilbud_50
        """Hent personer som har f�tt tilbud om opptak
	Disse skal gis affiliation student med kode tilbud til
        stedskoden sp.faknr_studieansv+sp.instituttnr_studieansv+
        sp.gruppenr_studieansv. Personer som har f�tt tilbud om
        opptak til et studieprogram ved institusjonen vil inng� i
        denne kategorien.  Alle s�kere til studierved institusjonen
	registreres i tabellen fs.soknadsalternativ og informasjon om
	noen har f�tt tilbud om opptak hentes ogs� derfra (feltet
        fs.soknadsalternativ.tilbudstatkode er et godt sted � 
        begynne � lete etter personer som har f�tt tilbud)."""

        qry = """
SELECT DISTINCT
      p.fodselsdato, p.personnr, p.etternavn, p.fornavn, 
      p.adrlin1_hjemsted, p.adrlin2_hjemsted,
      p.postnr_hjemsted, p.adrlin3_hjemsted, p.adresseland_hjemsted,
      p.sprakkode_malform, osp.studieprogramkode, 
      p.status_reserv_nettpubl, p.kjonn, p.status_dod
FROM fs.soknadsalternativ sa, fs.person p, fs.opptakstudieprogram osp,
     fs.studieprogram sp
WHERE p.fodselsdato=sa.fodselsdato AND
      p.personnr=sa.personnr AND
      sa.institusjonsnr='%s' AND 
      sa.opptakstypekode = 'NOM' AND
      sa.tilbudstatkode IN ('I', 'S') AND
      sa.studietypenr = osp.studietypenr AND
      osp.studieprogramkode = sp.studieprogramkode
      """ % (institutsjonsnr)
        return self.db.query(qry)
    
    def list_privatist(self): # GetStudentPrivatist_50
        """Hent personer med privatist 'opptak' til et studieprogram
        ved institusjonen og som enten har v�rt registrert siste �ret
        eller privatisk 'opptak' efter 2003-01-01.  Henter ikke de som
        har fremtidig opptak.  Disse kommer med 14 dager f�r dato for
        tildelt privatist 'opptak'.  Alle disse skal ha affiliation
        med status kode 'privatist' til stedskoden sp.faknr_studieansv
        + sp.instituttnr_studieansv + sp.gruppenr_studieansv"""

        qry = """
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform, sps.studieprogramkode, sps.studieretningkode,
       sps.studierettstatkode, sps.studentstatkode, sps.terminkode_kull,
       sps.arstall_kull, p.kjonn, p.status_dod
FROM fs.student s, fs.person p, fs.studieprogramstudent sps
WHERE  p.fodselsdato=s.fodselsdato AND
       p.personnr=s.personnr AND
       p.fodselsdato=sps.fodselsdato AND
       p.personnr=sps.personnr AND
       NVL(sps.dato_studierett_gyldig_til,SYSDATE) >= sysdate AND
       sps.status_privatist = 'J' AND
       sps.dato_studierett_tildelt < SYSDATE + 14 AND
       sps.dato_studierett_tildelt >= to_date('2003-01-01', 'yyyy-mm-dd')
       """
        qry += """ UNION
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl,
       p.sprakkode_malform, sps.studieprogramkode, sps.studieretningkode,
       sps.studierettstatkode, sps.studentstatkode, sps.terminkode_kull,
       sps.arstall_kull, p.kjonn, p.status_dod
FROM fs.student s, fs.person p, fs.studieprogramstudent sps, fs.registerkort r
WHERE  p.fodselsdato=s.fodselsdato AND
       p.personnr=s.personnr AND
       p.fodselsdato=sps.fodselsdato AND
       p.personnr=sps.personnr AND
       p.fodselsdato=r.fodselsdato AND
       p.personnr=r.personnr AND
       NVL(sps.dato_studierett_gyldig_til,SYSDATE) >= sysdate AND
       sps.status_privatist = 'J' AND
       r.arstall >= (%s - 1)
       """ % (self.year)
        return self.db.query(qry)

    def list_privatist_emne(self):  # GetStudentPrivatistEmne_50
        """Hent personer som er uekte privatister, dvs. som er
	eksamensmeldt til et emne i et studieprogram de ikke har
	opptak til. Disse tildeles affiliation privatist til stedet
	som eier studieprogrammet de har opptak til.  Dette blir ikke
	helt riktig efter som man kan ha opptak til studieprogramet
	'ENKELTEMNE' som betyr at man kan v�re ordnin�r student selv
	om man havner i denne gruppen som plukkes ut av dette s�ket"""

	qry = """
SELECT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform, p.kjonn, p.status_dod, em.emnekode
FROM fs.student s, fs. person p, fs.registerkort r,
     fs.eksamensmelding em
WHERE s.fodselsdato=p.fodselsdato AND
      s.personnr=p.personnr AND
      p.fodselsdato=r.fodselsdato AND
      p.personnr=r.personnr AND
      p.fodselsdato=em.fodselsdato AND
      p.personnr=em.personnr AND
       %s AND
      NOT EXISTS
      (SELECT 'x' FROM fs.studieprogramstudent sps,
                       fs.emne_i_studieprogram es
       WHERE p.fodselsdato=sps.fodselsdato AND
             p.personnr=sps.personnr AND
             es.emnekode=em.emnekode AND
             es.studieprogramkode = sps.studieprogramkode AND
             NVL(sps.dato_studierett_gyldig_til,SYSDATE) >= SYSDATE)
      """ % (self._get_termin_aar(only_current=1))
        return self.db.query(qry)

    def list_undervisningsenhet(self,  # GetStudUndervEnhet
                                Instnr, emnekode, versjon, termk, aar, termnr):
        if termk == 'V�R':
            minmaned, maxmaned = 1, 6
        elif termk == 'H�ST':
            minmaned, maxmaned = 7, 12
        else:
            # Ikke blant de terminkodene vi st�tter i dag; s�rg for at
            # eksamensmelding-delen av s�ket ikke gir noe resultat.
            minmaned, maxmaned = 13, 0
        # Den ulekre repetisjonen av bind-parametere under synes
        # dessverre � v�re n�dvendig; ut fra forel�pig testing ser det
        # ut til at enten Oracle eller DCOracle2 krever at dersom et
        # statement best�r av flere uavhengige SELECTs, og SELECT
        # nr. N bruker minst en bind-variabel nevnt i SELECT nr. x,
        # der x < N, m� SELECT nr. N *kun* bruke de bind-variablene
        # som ogs� finnes i SELECT nr. x.
        qry = """
SELECT
  fodselsdato, personnr
FROM
  FS.UNDERVISNINGSMELDING
WHERE
  institusjonsnr = :und_instnr AND
  emnekode       = :und_emnekode AND
  versjonskode   = :und_versjon AND
  terminkode     = :und_terminkode AND
  arstall        = :und_arstall AND
  terminnr       = :und_terminnr
UNION
SELECT
  fodselsdato, personnr
FROM
  FS.EKSAMENSMELDING
WHERE
  institusjonsnr = :instnr AND
  emnekode       = :emnekode AND
  versjonskode   = :versjon AND
  arstall        = :arstall AND
  manednr       >= :minmaned AND
  manednr       <= :maxmaned"""
        return self.db.query(qry, {'und_instnr': Instnr,
                                   'und_emnekode': emnekode,
                                   'und_versjon': versjon,
                                   'und_terminkode': termk,
                                   'und_arstall': aar,
                                   'und_terminnr': termnr,
                                   'instnr': Instnr,
                                   'emnekode': emnekode,
                                   'versjon': versjon,
                                   'arstall': aar,
                                   'minmaned': minmaned,
                                   'maxmaned': maxmaned})

    def _list_opptak_query(self):
	aar, maned = time.localtime()[0:2]

        """Hent personer med opptak til et studieprogram ved
        institusjonen og som enten har v�rt registrert siste �ret
        eller opptak efter 2003-01-01.  Henter ikke de som har
        fremtidig opptak.  Disse kommer med 14 dager f�r dato for
        tildelt opptak.  Med untak av de som har 'studierettstatkode'
        lik 'PRIVATIST' skal alle disse f� affiliation student med
        kode 'opptak' ('privatist' for disse) til stedskoden
        sp.faknr_studieansv + sp.instituttnr_studieansv +
        sp.gruppenr_studieansv"""

        qry = """
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform, st.studieprogramkode, st.studieretningkode,
       st.studierettstatkode, p.kjonn
FROM fs.student s, fs.person p, fs.studierett st, fs.studieprogram sp
WHERE  p.fodselsdato=s.fodselsdato AND
       p.personnr=s.personnr AND
       p.fodselsdato=st.fodselsdato AND
       p.personnr=st.personnr AND 
       st.studieprogramkode = sp.studieprogramkode AND
       NVL(st.dato_gyldig_til,SYSDATE) >= sysdate AND
       st.studierettstatkode IN (RELEVANTE_STUDIERETTSTATKODER) AND
       st.dato_tildelt < SYSDATE + 14 AND
       st.dato_tildelt >= to_date('2003-01-01', 'yyyy-mm-dd')
       """
        qry += """ UNION
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl,
       p.sprakkode_malform, st.studieprogramkode, st.studieretningkode,
       st.studierettstatkode, p.kjonn
FROM fs.student s, fs.person p, fs.studierett st, fs.registerkort r,
     fs.studieprogram sp
WHERE  p.fodselsdato=s.fodselsdato AND
       p.personnr=s.personnr AND
       p.fodselsdato=st.fodselsdato AND
       p.personnr=st.personnr AND
       st.studieprogramkode = sp.studieprogramkode AND
       p.fodselsdato=r.fodselsdato AND
       p.personnr=r.personnr AND
       NVL(st.dato_gyldig_til,SYSDATE) >= sysdate AND
       st.studierettstatkode IN (RELEVANTE_STUDIERETTSTATKODER) AND
       r.arstall >= (%s - 1)
       """ % (aar)
        return qry

    def list_opptak(self): # GetStudinfOpptak
        studierettstatkoder = """'AUTOMATISK','AVTALE','CANDMAG',
	'DIVERSE','EKSPRIV','ERASMUS','FJERNUND','GJEST','FULBRIGHT','HOSPITANT',
	'KULTURAVT','KVOTEPROG','LEONARDO','OVERGANG','NUFU','SOKRATES','LUBECK',
	'NORAD','ARKHANG','NORDPLUS','ORDOPPTAK','EVU','UTLOPPTAK'"""
        qry = self._list_opptak_query().replace("RELEVANTE_STUDIERETTSTATKODER",
                                             studierettstatkoder)
        return self.db.query(qry)
        

    def list_utvekslings_student(self): # GetStudinfUtvekslingsStudent
        qry = """
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform, p.kjonn, u.institusjonsnr_internt
       u.faknr_internt, u.instituttnr_internt, u.gruppenr_internt
FROM fs.student s, fs.person p, fs.utvekslingsperson u
WHERE s.fodselsdato = p.fodselsdato AND
      s.personnr = p.personnr AND
      s.fodselsdato = u.fodselsdato AND
      s.personnr = u.personnr AND
      u.status_innreisende = 'J' AND
      u.dato_fra <= SYSDATE AND
      u.dato_til >= SYSDATE
      """
        return self.db.query(qry)

    def list_privatist_studieprogram(self):
        studierettstatkoder = "'PRIVATIST'"
        qry = self._list_opptak_query().replace(
            "RELEVANTE_STUDIERETTSTATKODER", studierettstatkoder)
        return self.db.query(qry)

    def list_permisjon(self): # GetStudinfPermisjon
        """Hent personer som har innvilget permisjon.  Disse vil
        alltid ha opptak, s� vi henter bare noen f� kolonner.
        Disse tildeles affiliation student med kode permisjon
	til sp.faknr_studieansv, sp.instituttnr_studieansv, 
        sp.gruppenr_studieansv"""

        qry = """
SELECT  pe.studieprogramkode, pe.fodselsdato, pe.personnr,
	pe.fraverarsakkode_hovedarsak 
FROM fs.innvilget_permisjon pe, fs.person p
WHERE p.fodselsdato = pe.fodselsdato AND
      p.personnr = pe.personnr AND
      dato_fra < SYSDATE AND NVL(dato_til, SYSDATE) >= SYSDATE
      AND %s
        """ % self._is_alive()
        return self.db.query(qry)


    def list_drgrad(self): # GetStudinfDrgrad
	"""Henter info om aktive doktorgradsstudenter."""
        qry = """

SELECT fodselsdato, personnr, institusjonsnr, faknr, instituttnr, gruppenr
FROM fs.drgradsavtale
WHERE dato_start <= SYSDATE AND
      NVL(DATO_BEREGNET_SLUTT, sysdate) >= SYSDATE"""
        return self.db.query(qry)

    def get_studierett(self, fnr, pnr): # GetStudentStudierett_50
	"""Hent info om alle studierett en student har eller har hatt"""
        qry = """
SELECT DISTINCT
sps.studieprogramkode, sps.studierettstatkode,
sps.studieretningkode,sps.dato_studierett_tildelt, 
sps.dato_studierett_gyldig_til,sps.status_privatist, 
sps.studentstatkode
FROM fs.studieprogramstudent sps, fs.person p
WHERE sps.fodselsdato=:fnr AND
      sps.personnr=:pnr AND
      sps.fodselsdato=p.fodselsdato AND
      sps.personnr=p.personnr 
      AND %s
        """ % self._is_alive()
        return self.db.query(qry, {'fnr': fnr, 'pnr': pnr})

class Student40(FSObject):
    def list_tilbud(self, institutsjonsnr=0):  # GetStudinfTilbud
        """Hent personer som har f�tt tilbud om opptak
	Disse skal gis affiliation student med kode tilbud til
        stedskoden sp.faknr_studieansv+sp.instituttnr_studieansv+
        sp.gruppenr_studieansv. Personer som har f�tt tilbud om
        opptak til et studieprogram ved institusjonen vil inng� i
        denne kategorien.  Alle s�kere til studierved institusjonen
	registreres i tabellen fs.soknadsalternativ og informasjon om
	noen har f�tt tilbud om opptak hentes ogs� derfra (feltet
        fs.soknadsalternativ.tilbudstatkode er et godt sted � 
        begynne � lete etter personer som har f�tt tilbud)."""

        qry = """
SELECT DISTINCT
      p.fodselsdato, p.personnr, p.etternavn, p.fornavn, 
      p.adrlin1_hjemsted, p.adrlin2_hjemsted,
      p.postnr_hjemsted, p.adrlin3_hjemsted, p.adresseland_hjemsted,
      p.sprakkode_malform, osp.studieprogramkode, p.kjonn,
      p.status_reserv_nettpubl
FROM fs.soknadsalternativ sa, fs.person p, fs.opptakstudieprogram osp,
     fs.studieprogram sp
WHERE p.fodselsdato=sa.fodselsdato AND
      p.personnr=sa.personnr AND
      sa.institusjonsnr='%s' AND 
      sa.opptakstypekode = 'NOM' AND
      sa.tilbudstatkode IN ('I', 'S') AND
      sa.studietypenr = osp.studietypenr AND
      osp.studieprogramkode = sp.studieprogramkode
      AND %s
      """ % (institutsjonsnr, self._is_alive())
        return self.db.query(qry)

    def list_privatist(self): # GetStudinfPrivatist
	"""Hent personer som er uekte privatister ved UiO, 
        dvs. som er eksamensmeldt til et emne i et studieprogram 
        de ikke har opptak til. Disse tildeles affiliation privatist
        til stedet som eier studieprogrammet de har opptak til."""

	qry = """
SELECT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform, p.kjonn, em.emnekode
FROM fs.student s, fs. person p, fs.registerkort r,
     fs.eksamensmelding em
WHERE s.fodselsdato=p.fodselsdato AND
      s.personnr=p.personnr AND
      p.fodselsdato=r.fodselsdato AND
      p.personnr=r.personnr AND
      p.fodselsdato=em.fodselsdato AND
      p.personnr=em.personnr AND
       %s AND %s AND
      NOT EXISTS
      (SELECT 'x' FROM fs.studierett st, fs.emne_i_studieprogram es
       WHERE p.fodselsdato=st.fodselsdato AND
             p.personnr=st.personnr AND
             es.emnekode=em.emnekode AND
             es.studieprogramkode = st.studieprogramkode AND
             NVL(st.dato_gyldig_til,SYSDATE) >= SYSDATE)
      """ % (self._get_termin_aar(only_current=1),self._is_alive())
        return self.db.query(qry)

    def get_studierett(self, fnr, pnr):  # GetStudentStudierett
	"""Hent info om alle studierett en student har eller har hatt"""
        qry = """
SELECT DISTINCT
  st.studieprogramkode, st.studierettstatkode, st.dato_tildelt,
  st.dato_gyldig_til, st.status_privatist, st.opphortstudierettstatkode
FROM fs.studierett st, fs.person p
WHERE st.fodselsdato=:fnr AND
      st.personnr=:pnr AND
      st.fodselsdato=p.fodselsdato AND
      st.personnr=p.personnr 
      AND %s
        """ % self._is_alive()
        return self.db.query(qry, {'fnr': fnr, 'pnr': pnr})

class Undervisning(FSObject):
    def list_aktivitet(self, Instnr, emnekode, versjon, termk,
                       aar, termnr, aktkode): # GetStudUndAktivitet
        qry = """
SELECT
  su.fodselsdato, su.personnr
FROM
  FS.STUDENT_PA_UNDERVISNINGSPARTI su,
  FS.undaktivitet ua
WHERE
  ua.institusjonsnr = :instnr AND
  ua.emnekode       = :emnekode AND
  ua.versjonskode   = :versjon AND
  ua.terminkode     = :terminkode AND
  ua.arstall        = :arstall AND
  ua.terminnr       = :terminnr AND
  ua.aktivitetkode  = :aktkode AND
  su.terminnr       = ua.terminnr       AND
  su.institusjonsnr = ua.institusjonsnr AND
  su.emnekode       = ua.emnekode       AND
  su.versjonskode   = ua.versjonskode   AND
  su.terminkode     = ua.terminkode     AND
  su.arstall        = ua.arstall        AND
  su.undpartilopenr = ua.undpartilopenr AND
  su.disiplinkode   = ua.disiplinkode   AND
  su.undformkode    = ua.undformkode"""

        return self.db.query(qry, {
            'instnr': Instnr,
            'emnekode': emnekode,
            'versjon': versjon,
            'terminkode': termk,
            'arstall': aar,
            'terminnr': termnr,
            'aktkode': aktkode})

    def list_ansvarlig_for_enhet(self, Instnr, emnekode, versjon,
                                 termk, aar, termnr): # GetAnsvUndervEnhet
        qry = """
SELECT
  uan.fodselsdato AS fodselsdato,
  uan.personnr AS personnr
FROM
  fs.undervisningsansvarlig uan
WHERE
  uan.institusjonsnr = :instnr AND
  uan.emnekode       = :emnekode AND
  uan.versjonskode   = :versjon AND
  uan.terminkode     = :terminkode AND
  uan.arstall        = :arstall AND
  uan.terminnr       = :terminnr
UNION
SELECT
  ue.fodselsdato_Ansvarligkontakt AS fodselsdato,
  ue.personnr_Ansvarligkontakt AS personnr
FROM
  fs.undervisningsenhet ue
WHERE
  ue.institusjonsnr = :instnr AND
  ue.emnekode       = :emnekode AND
  ue.versjonskode   = :versjon AND
  ue.terminkode     = :terminkode AND
  ue.arstall        = :arstall AND
  ue.terminnr       = :terminnr AND
  ue.fodselsdato_Ansvarligkontakt IS NOT NULL AND
  ue.personnr_Ansvarligkontakt IS NOT NULL
UNION
SELECT
  ual.fodselsdato_fagansvarlig AS fodselsdato,
  ual.personnr_fagansvarlig AS personnr
FROM
  fs.undaktivitet ua, fs.undaktivitet_lerer ual
WHERE
  ua.institusjonsnr = :instnr AND
  ua.emnekode       = :emnekode AND
  ua.versjonskode   = :versjon AND
  ua.terminkode     = :terminkode AND
  ua.arstall        = :arstall AND
  ua.terminnr       = :terminnr AND
  ua.undformkode    = 'FOR' AND
  ua.institusjonsnr = ual.institusjonsnr AND
  ua.emnekode       = ual.emnekode AND
  ua.versjonskode   = ual.versjonskode AND
  ua.terminkode     = ual.terminkode AND
  ua.arstall        = ual.arstall AND
  ua.terminnr       = ual.terminnr AND
  ua.aktivitetkode  = ual.aktivitetkode"""

        return self.db.query(qry, {
            'instnr': Instnr,
            'emnekode': emnekode,
            'versjon': versjon,
            'terminkode': termk,
            'arstall': aar,
            'terminnr': termnr})

    def get_ansvarlig_for_enhet(self, Instnr, emnekode, versjon, termk,
                                aar, termnr, aktkode):  # GetAnsvUndAktivitet
        qry = """
SELECT
  ual.fodselsdato_fagansvarlig AS fodselsdato,
  ual.personnr_fagansvarlig AS personnr,
  ual.status_publiseres AS publiseres
FROM
  fs.undaktivitet_lerer ual
WHERE
  ual.institusjonsnr = :instnr AND
  ual.emnekode       = :emnekode AND
  ual.versjonskode   = :versjon AND
  ual.terminkode     = :terminkode AND
  ual.arstall        = :arstall AND
  ual.terminnr       = :terminnr AND
  ual.aktivitetkode  = :aktkode
UNION
SELECT
  ul.fodselsdato_underviser AS fodselsdato,
  ul.personnr_underviser AS personnr,
  ul.status_publiseres AS publiseres
FROM
  FS.UNDERVISNING_LERER ul
WHERE
  ul.institusjonsnr = :instnr AND
  ul.emnekode       = :emnekode AND
  ul.versjonskode   = :versjon AND
  ul.terminkode     = :terminkode AND
  ul.arstall        = :arstall AND
  ul.terminnr       = :terminnr AND
  ul.aktivitetkode  = :aktkode
UNION
SELECT ua.fodselsdato_fagansvarlig AS fodselsdato,
  ua.personnr_fagansvarlig AS personnr,
  ua.status_fagansvarlig_publiseres AS publiseres
FROM fs.undaktivitet ua
WHERE
  ua.institusjonsnr = :instnr AND
  ua.emnekode       = :emnekode AND
  ua.versjonskode   = :versjon AND
  ua.terminkode     = :terminkode AND
  ua.arstall        = :arstall AND
  ua.terminnr       = :terminnr AND
  ua.aktivitetkode  = :aktkode AND
  ua.fodselsdato_fagansvarlig IS NOT NULL AND
  ua.personnr_fagansvarlig IS NOT NULL"""

        return self.db.query(qry, {
            'instnr': Instnr,
            'emnekode': emnekode,
            'versjon': versjon,
            'terminkode': termk,
            'arstall': aar,
            'terminnr': termnr,
            'aktkode': aktkode})

    def list_enheter(self, year=None, sem=None): # GetUndervEnhetAll
        if year is None:
            year = time.localtime()[0]
        if sem is None:
            sem = self.semester
        return self.db.query("""
        SELECT
          ue.institusjonsnr, ue.emnekode, ue.versjonskode, ue.terminkode,
          ue.arstall, ue.terminnr, e.institusjonsnr_kontroll,
          e.faknr_kontroll, e.instituttnr_kontroll, e.gruppenr_kontroll,
          e.emnenavn_bokmal, e.emnenavnfork
        FROM
          fs.undervisningsenhet ue, fs.emne e, fs.arstermin t
        WHERE
          ue.institusjonsnr = e.institusjonsnr AND
          ue.emnekode       = e.emnekode AND
          ue.versjonskode   = e.versjonskode AND
          ue.terminkode IN ('V�R', 'H�ST') AND
          ue.terminkode = t.terminkode AND
          (ue.arstall > :aar OR
           (ue.arstall = :aar2 AND
            EXISTS(SELECT 'x' FROM fs.arstermin tt
            WHERE tt.terminkode = :sem AND
                  t.sorteringsnokkel >= tt.sorteringsnokkel)))""",
                             {'aar': year,
                              'aar2': year, # db-driver bug work-around
                              'sem': sem})

    def list_aktiviteter(self, start_aar=time.localtime()[0],
                                      start_semester=None):
        if start_semester is None:
            start_semester = self.semester
        return self.db.query("""
        SELECT  
          ua.institusjonsnr, ua.emnekode, ua.versjonskode,
          ua.terminkode, ua.arstall, ua.terminnr, ua.aktivitetkode,
          ua.undpartilopenr, ua.disiplinkode, ua.undformkode, ua.aktivitetsnavn
        FROM
          [:table schema=fs name=undaktivitet] ua,
          [:table schema=fs name=arstermin] t
        WHERE
          ua.undpartilopenr IS NOT NULL AND
          ua.disiplinkode IS NOT NULL AND
          ua.undformkode IS NOT NULL AND
          ua.terminkode IN ('V�R', 'H�ST') AND
          ua.terminkode = t.terminkode AND
          ((ua.arstall = :aar AND
            EXISTS (SELECT 'x' FROM fs.arstermin tt
                    WHERE tt.terminkode = :semester AND
                          t.sorteringsnokkel >= tt.sorteringsnokkel)) OR
           ua.arstall > :aar)""",
                             {'aar': start_aar,
                              'semester': start_semester})

    def list_fagperson_semester(self): # GetFagperson_50
        # (GetKursFagpersonundsemester var duplikat)
	"""Disse skal gis affiliation tilknyttet med kode fagperson 
        til stedskoden faknr+instituttnr+gruppenr
        Hent ut fagpersoner som har undervisning i innev�rende
        eller forrige kalender�r"""

        qry = """
SELECT DISTINCT 
      fp.fodselsdato, fp.personnr, p.etternavn, p.fornavn,
      fp.adrlin1_arbeide, fp.adrlin2_arbeide, fp.postnr_arbeide,
      fp.adrlin3_arbeide, fp.adresseland_arbeide,
      fp.telefonnr_arbeide, fp.telefonnr_fax_arb,
      p.adrlin1_hjemsted, p.adrlin2_hjemsted, p.postnr_hjemsted,
      p.adrlin3_hjemsted, p.adresseland_hjemsted, 
      p.telefonnr_hjemsted, fp.stillingstittel_engelsk, 
      r.institusjonsnr, r.faknr, r.instituttnr, r.gruppenr,
      r.status_aktiv, r.status_publiseres, r.terminkode, r.arstall,
      p.kjonn, p.status_dod
FROM fs.person p, fs.fagperson fp,
     fs.fagpersonundsemester r
WHERE r.fodselsdato = fp.fodselsdato AND
      r.personnr = fp.personnr AND
      fp.fodselsdato = p.fodselsdato AND
      fp.personnr = p.personnr AND 
      %s
        """ % (self._get_termin_aar(only_current=0))
        return self.db.query(qry)

    def get_fagperson_semester(self, fnr, pnr, institusjonsnr, fakultetnr,
                               instiuttnr, gruppenr, termin, arstall):
        return self.db.query("""
SELECT
  terminkode, arstall, institusjonsnr, faknr, instituttnr,
  gruppenr, status_aktiv, status_publiseres
FROM fs.fagpersonundsemester r
WHERE
  fodselsdato=:fnr AND personnr=:pnr AND
  terminkode=:termin AND arstall=:arstall AND
  institusjonsnr=:institusjonsnr AND faknr=:fakultetnr AND
  instituttnr=:instiuttnr AND gruppenr=:gruppenr""", {
            'fnr': fnr, 'pnr': pnr,
            'institusjonsnr': institusjonsnr, 'fakultetnr': fakultetnr,
            'instiuttnr': instiuttnr, 'gruppenr': gruppenr,
            'termin': termin, 'arstall': arstall})

    def add_fagperson_semester(self, fnr, pnr, institusjonsnr,
                               fakultetnr, instiuttnr, gruppenr, termin,
                               arstall, status_aktiv, status_publiseres):
        return self.db.execute("""
INSERT INTO fs.fagpersonundsemester
  (fodselsdato, personnr, terminkode, arstall, institusjonsnr, faknr,
   instituttnr, gruppenr, status_aktiv, status_publiseres)
VALUES
  (:fnr, :pnr, :termin, :arstall, :institusjonsnr, :fakultetnr,
  :instiuttnr, :gruppenr, :status_aktiv, :status_publiseres)""", {
            'fnr': fnr, 'pnr': pnr,
            'institusjonsnr': institusjonsnr, 'fakultetnr': fakultetnr,
            'instiuttnr': instiuttnr, 'gruppenr': gruppenr,
            'termin': termin, 'arstall': arstall,
            'status_aktiv': status_aktiv, 'status_publiseres': status_publiseres})

class EVU(FSObject):
    def list(self):  # GetDeltaker_50
    	"""Hent info om personer som er ekte EVU-studenter ved
    	UiO, dvs. er registrert i EVU-modulen i tabellen 
    	fs.deltaker,  Henter alle som er knyttet til kurs som
        tidligst ble avsluttet for 30 dager siden."""

 	qry = """
SELECT DISTINCT 
       p.fodselsdato, p.personnr, p.etternavn, p.fornavn,
       d.adrlin1_job, d.adrlin2_job, d.postnr_job, 
       d.adrlin3_job, d.adresseland_job, d.adrlin1_hjem, 
       d.adrlin2_hjem, d.postnr_hjem, d.adrlin3_hjem,
       d.adresseland_hjem, p.adrlin1_hjemsted, p.status_reserv_nettpubl, 
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, d.deltakernr, d.emailadresse,
       k.etterutdkurskode, e.studieprogramkode, 
       e.faknr_adm_ansvar, e.instituttnr_adm_ansvar, 
       e.gruppenr_adm_ansvar, p.kjonn, p.status_dod
FROM fs.deltaker d, fs.person p, fs.kursdeltakelse k,
     fs.etterutdkurs e
WHERE p.fodselsdato=d.fodselsdato AND
      p.personnr=d.personnr AND
      d.deltakernr=k.deltakernr AND
      e.etterutdkurskode=k.etterutdkurskode AND
      NVL(e.status_nettbasert_und,'J')='J' AND
      k.kurstidsangivelsekode = e.kurstidsangivelsekode AND
      NVL(e.dato_til, SYSDATE) >= SYSDATE - 30"""
	return self.db.query(qry)
        
    def list_kurs(self, date=time.localtime()):  # GetEvuKurs
        d = time.strftime("%Y-%m-%d", date)
        qry = """
SELECT e.etterutdkurskode, e.kurstidsangivelsekode, e.etterutdkursnavn,
       e.institusjonsnr_adm_ansvar, e.faknr_adm_ansvar,
       e.instituttnr_adm_ansvar, e.gruppenr_adm_ansvar,
       TO_CHAR(e.dato_til,'YYYY-MM-DD') AS dato_til
FROM fs.etterutdkurs e
WHERE NVL(TO_DATE('%s', 'YYYY-MM-DD'), SYSDATE) <  (e.dato_til+30)
        """ % d
        return self.db.query(qry)

    def get_kurs_informasjon(self, code): # GetEvuKursInformasjon
        """
        This one works similar to GetEvuKurs, except for the filtering
        criteria: in this method we filter by course code, not by time frame
        """

        query = """
                SELECT e.etterutdkurskode, e.kurstidsangivelsekode,
                       TO_CHAR(e.dato_fra, 'YYYY-MM-DD') as dato_fra,
                       TO_CHAR(e.dato_til, 'YYYY-MM-DD') as dato_til
                FROM [:table schema=fs name=etterutdkurs] e
                WHERE e.etterutdkurskode = :code
                """
        return self.db.query(query,
                             { "code" : code })

    def list_kurs_pameldte(self, kurskode, tid):  # GetEvuKursPameldte
        """
        List everyone registered for a given course
        """

        query = """
                SELECT p.fodselsdato, p.personnr,
                       p.fornavn, p.Etternavn
                FROM
                  [:table schema=fs name=person] p,
                  [:table schema=fs name=etterutdkurs] e,
                  [:table schema=fs name=kursdeltakelse] kd,
                  [:table schema=fs name=deltaker] d
                WHERE e.etterutdkurskode like :kurskode AND
                      e.kurstidsangivelsekode like :tid AND
                      e.etterutdkurskode = kd.etterutdkurskode AND
                      e.kurstidsangivelsekode = kd.kurstidsangivelsekode AND
                      kd.deltakernr = d.deltakernr AND
                      d.fodselsdato = p.fodselsdato AND
                      d.personnr = p.personnr
                """
        return self.db.query(query, {"kurskode" : kurskode,
                                     "tid" : tid})


    def get_kurs_aktivitet(self, kurs, tid): # GetAktivitetEvuKurs
        qry = """
SELECT k.etterutdkurskode, k.kurstidsangivelsekode, k.aktivitetskode,
       k.aktivitetsnavn
FROM fs.kursaktivitet k
WHERE k.etterutdkurskode='%s' AND
      k.kurstidsangivelsekode='%s'
      """ % (kurs, tid)

        return self.db.query(qry) 

    def get_kurs_ansv(self, kurs, tid):  # GetAnsvEvuKurs
        qry = """
SELECT k.fodselsdato, k.personnr
FROM fs.kursfagansvarlig k
WHERE k.etterutdkurskode=:kurs AND
      k.kurstidsangivelsekode=:tid"""
        return self.db.query(qry, {'kurs': kurs, 'tid': tid})

    def list_kurs_stud(self, kurs, tid):  # GetStudEvuKurs
        qry = """
SELECT d.fodselsdato, d.personnr
FROM fs.deltaker d, fs.kursdeltakelse k
WHERE k.etterutdkurskode=:kurs AND
      k.kurstidsangivelsekode=:tid AND
      k.deltakernr=d.deltakernr AND
      d.fodselsdato IS NOT NULL AND
      d.personnr IS NOT NULL"""
        return self.db.query(qry, {'kurs': kurs, 'tid': tid})

    def list_aktivitet_ansv(self, kurs, tid, aktkode):  # GetAnsvEvuAktivitet
        qry = """
SELECT k.fodselsdato, k.personnr
FROM fs.kursaktivitet_fagperson k
WHERE k.etterutdkurskode=:kurs AND
      k.kurstidsangivelsekode=:tid AND
      k.aktivitetskode=:aktkode"""
        return self.db.query(qry, {
            'kurs': kurs,
            'tid': tid,
            'aktkode': aktkode})

    def list_aktivitet_stud(self, kurs, tid, aktkode):  # GetStudEvuAktivitet
        qry = """
SELECT d.fodselsdato, d.personnr
FROM fs.deltaker d, fs.kursaktivitet_deltaker k
WHERE k.etterutdkurskode=:kurs AND
      k.kurstidsangivelsekode=:tid AND
      k.aktivitetskode=:aktkode AND
      k.deltakernr = d.deltakernr"""
        return self.db.query(qry, {
            'kurs': kurs,
            'tid': tid,
            'aktkode': aktkode})

class EVU40(FSObject):
    def list(self): # GetStudinfEvu
    	"""Hent info om personer som er ekte EVU-studenter ved
    	UiO, dvs. er registrert i EVU-modulen i tabellen 
    	fs.deltaker"""

 	qry = """
SELECT DISTINCT 
       p.fodselsdato, p.personnr, p.etternavn, p.fornavn,
       d.adrlin1_job, d.adrlin2_job, d.postnr_job, 
       d.adrlin3_job, d.adresseland_job, d.adrlin1_hjem, 
       d.adrlin2_hjem, d.postnr_hjem, d.adrlin3_hjem,
       d.adresseland_hjem, p.adrlin1_hjemsted, p.status_reserv_nettpubl, 
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, d.deltakernr, d.emailadresse,
       k.etterutdkurskode, e.studieprogramkode, 
       e.faknr_adm_ansvar, e.instituttnr_adm_ansvar, 
       e.gruppenr_adm_ansvar
FROM fs.deltaker d, fs.person p, fs.kursdeltakelse k,
     fs.etterutdkurs e
WHERE p.fodselsdato=d.fodselsdato AND
      p.personnr=d.personnr AND
      d.deltakernr=k.deltakernr AND
      e.etterutdkurskode=k.etterutdkurskode AND
      NVL(e.status_nettbasert_und,'J')='J' AND
      k.kurstidsangivelsekode = e.kurstidsangivelsekode AND
      e.dato_til > SYSDATE - 180 
      AND %s
      """ % self._is_alive()
	return self.db.query(qry)

class Alumni(FSObject):
    def list(self):  # GetAlumni_50
        """Henter informasjon om alle som har fullf�rt
        studium frem til en grad, min. Cand.Mag.  Disse regnes
        som 'Alumni' ved UiO."""
        qry = """
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform,sps.studieprogramkode, sps.studierettstatkode,
       p.kjonn, p.status_dod
FROM fs.student s, fs.person p, fs.studieprogramstudent sps, fs.studieprogram sp
WHERE  p.fodselsdato=s.fodselsdato AND
       p.personnr=s.personnr AND
       p.fodselsdato=sps.fodselsdato AND
       p.personnr=sps.personnr AND 
       sps.studieprogramkode = sp.studieprogramkode AND
       sps.studentstatkode = 'FULLF�RT'  AND
       sps.studierettstatkode IN ('AUTOMATISK', 'CANDMAG', 'DIVERSE',
       'OVERGANG', 'ORDOPPTAK')
       """
        return self.db.query(qry)
    
class Alumni40(FSObject):
    def list(self):  # GetAlumni
        qry = """
SELECT DISTINCT s.fodselsdato, s.personnr, p.etternavn, p.fornavn,
       s.adrlin1_semadr,s.adrlin2_semadr, s.postnr_semadr,
       s.adrlin3_semadr, s.adresseland_semadr, p.adrlin1_hjemsted,
       p.adrlin2_hjemsted, p.postnr_hjemsted, p.adrlin3_hjemsted,
       p.adresseland_hjemsted, p.status_reserv_nettpubl, 
       p.sprakkode_malform,st.studieprogramkode, st.studierettstatkode,
       p.kjonn
FROM fs.student s, fs.person p, fs.studierett st, fs.eksmeldinglogg el,
     fs.studieprogram sp
WHERE  p.fodselsdato=s.fodselsdato AND
       p.personnr=s.personnr AND
       p.fodselsdato=st.fodselsdato AND
       p.personnr=st.personnr AND 
       st.studieprogramkode = sp.studieprogramkode AND
       p.fodselsdato=el.fodselsdato AND
       p.personnr=el.personnr AND
       st.opphortstudierettstatkode = 'FULLF�RT'  AND
       st.studierettstatkode IN ('AUTOMATISK', 'CANDMAG', 'DIVERSE',
       'OVERGANG', 'ORDOPPTAK')
       """
        return self.db.query(qry)

class AdministrativInfo(FSObject):

    def list_studieprogrammer(self): # GetStudieproginf
	"""For hvert definerte studieprogram henter vi 
	informasjon om utd_plan og eier samt studieprogkode"""
        qry = """
SELECT studieprogramkode, status_utdplan, institusjonsnr_studieansv, faknr_studieansv,
       instituttnr_studieansv, gruppenr_studieansv, studienivakode
FROM fs.studieprogram"""
        return self.db.query(qry)

    def list_emner(self): # GetEmneinf
	"""For hvert definerte Emne henter vi informasjon om 
           ansvarlig sted."""
        qry = """
        SELECT e.emnekode, e.versjonskode, e.institusjonsnr,
               e.faknr_reglement, e.instituttnr_reglement,
               e.gruppenr_reglement, e.studienivakode
        FROM fs.emne e
        WHERE e.institusjonsnr = '185' AND
              NVL(e.arstall_eks_siste, :year) >= :year - 1"""
        return self.db.query(qry, {'year': self.year})

    def get_emne_i_studieprogram(self,emne): # GetEmneIStudProg
        """Hent alle studieprogrammer et gitt emne kan inng� i."""
        qry = """
SELECT DISTINCT 
  studieprogramkode   
FROM fs.emne_i_studieprogram
WHERE emnekode = :emne
       """ 
        return self.db.query(qry, {'emne': emne})

    def list_ou(self, institusjonsnr=0): # GetAlleOUer
	"""Hent data om stedskoder registrert i FS"""
        qry = """
SELECT DISTINCT
  institusjonsnr, faknr, instituttnr, gruppenr, stedakronym, stednavn_bokmal,
  faknr_org_under, instituttnr_org_under, gruppenr_org_under,
  adrlin1, adrlin2, postnr, adrlin3, stedkortnavn, telefonnr, faxnr,
  adrlin1_besok, adrlin2_besok, postnr_besok, url,
  bibsysbeststedkode
FROM fs.sted
WHERE institusjonsnr='%s'
""" % institusjonsnr
        return self.db.query(qry)

class FS(object):
    def __init__(self, db=None, user=None, database=None):
        if db is None:
            # TBD: Should user and database have default values in
            # cereconf?
            db = Database.connect(user = user, service = database,
                                  DB_driver = 'Oracle')
        self.db = db
        self.person = Person(db)
        self.student = Student(db)
        self.undervisning = Undervisning(db)
        self.evu = EVU(db)
        self.alumni = Alumni(db)
        self.info = AdministrativInfo(db)

    def list_dbfg_usernames(self, fetchall = False):
        """
        Get all usernames and return them as a sequence of db_rows.

        NB! This function does *not* return a 2-tuple. Only a sequence of
        all usernames (the column names can be obtains from db_row objects)
        """

        query = """
                SELECT username as username
                FROM all_users
                """
        return self.db.query(query, fetchall = fetchall)
