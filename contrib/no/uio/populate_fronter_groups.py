#!/usr/bin/env python2.2

import sys
import getopt
import re

from Cerebrum import Database
from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules.no.uio.access_FS import FS

db = Factory.get('Database')()
db.cl_init(change_program='CF_gen_groups')
co = Factory.get('Constants')(db)

def main():
    fnr2uname = get_primusers()
    account_id2fnr = {}
    undervEnhet = {}
    get_undervisningsenheter(undervEnhet)    # Utvider undervEnhet med mer data
    get_undervisningsaktiviteter(undervEnhet)
    get_evukurs_aktiviteter(unervEnhet)

    for k in unervEnhet.keys():
        # Legger inn brukere i gruppene p� niv� 3.
        #
        # $enhet er her enten en undervisningsenhet (starter med "kurs:")
        # eller en EVU-enhet (starter med "evu:"); vi overlater til
        # populate_enhet_groups � behandle forskjellige type enheter p�
        # passende vis.
        populate_enhet_groups(k)

    # Oppdaterer gruppene p� niv� 2.
    #
    # M� skille mellom EVU-kurs og vanlige kurs da identifikatorene deres
    # har forskjellig antall felter i $kurs_id.
    #
    logging.info("Oppdaterer enhets-supergrupper:")
    for kurs_ud in affiliatedGroups.keys():
        rest = kurs_id.split(":")
        type = rest.pop(0).lower()
        if type == 'kurs':
            instnr, emnekode, versjon, termk, aar = rest
            sync_group("%s:%s" % (type, emnekode), kurs_id,
                       "Ikke-eksporterbar gruppe.  Brukes for � definere hvor"+
                       " data om kurset <> skal eksporteres." % kurs_id,
                       co.entity_group,
                       AffiliatedGroups[kurs_id])
        elif type == 'evu':
            kurskode, tidsrom = rest
            sync_group("s:%s" % (type, kurskode), kurs_id,
                       "Ikke-eksporterbar gruppe.  Brukes for � definere hvor"+
                       " data om emnet <%s> skal eksporteres. " % kurs_id,
                       co.entity_group,
                       AffiliatedGroups[kurs_id])
        else:
            logger.warn("Ukjent kurstype <%s> for kurs <%s>" % (type, k))

        # Kallene p� sync_group legger inn nye entries i
        # %AffiliatedGroups; ting blir mye greiere � holde rede p� om vi
        # fjerner "v�re" n�kler derfra s� snart vi er ferdige.
        del(affiliatedGroups[kurs_id])
    logging.info(" ... done")

    # Oppdaterer gruppene p� niv� 1.
    #
    # Alle grupper knyttet til en undervisningsenhet skal meldes inn i den
    # u2k-interne emnekode-gruppen.  Man benytter s� emnekode-gruppen til
    # � definere eksport-egenskaper for alle grupper tilknyttet en
    # undervisningsenhet.
    logging.info("Oppdaterer emne-supergrupper:")
    for gname in affiliatedGroups.keys():
        sync_group(fs_supergroup, gname,
                   "Ikke-eksporterbar gruppe.  Brukes for � samle kursene"+
                   " knyttet til %s." % gname,
                   co.entity_group, AffiliatedGroups[gname]);
    logging.info(" ... done")


    #
    # Alle emnekode-supergrupper skal meldes inn i en supergruppe
    # spesifikk for denne importmekanismen.
    #
    # P� denne m�ten holdes det oversikt over hvilke grupper som er
    # automatisk opprettet p� bakgrunn av import fra FS.  Uten en slik
    # oversikt vil man ikke kunne foreta automatisk sletting av grupper
    # tilh�rende "utg�tte" undervisningsenheter og -aktiviteter.
    logging.info("Oppdaterer supergruppe for alle emnekode-supergrupper")
    sync_group(undef, fs_supergroup,
               "Ikke-eksporterbar gruppe.  Definerer hvilke andre grupper "+
               "som er opprettet automatisk som f�lge av FS-import.",
               co.entity_group,
               AffiliatedGroups[fs_supergroup])
    logging.info(" ... done")



## send_mail("\n$warn_msg",
##        sender => 'ureg2000-core@usit.uio.no',
##        recips => [ split(m/\s+/, $warn_addr) ],
##        subject => 'Bygging av ureg2000-grupper fra FS-data',
##        dryrun => $dryrun,
##        dryrun_output => '>&STDOUT')
##   if $warn_msg;

## $u2k.commit() unless $dryrun;

def get_undervisningsenheter(undervEnhet):
    # TODO: Dumpe alle unervisningsenheter til fil
    for enhet in fs.GetUndervEnhetAll()[1]:
        # Prefikser alle n�kler i %UndervEnhet som stammer fra
        # undervisningsenheter med "kurs:".
        enhet_id =":".join("kurs", enhet['ue.institusjonsnr'],
                           enhet['ue.emnekode'],
                           enhet['ue.versjonskode'], enhet['ue.terminkode'],
                           enhet['ue.arstall'], enhet['ue.terminnr'])
        if undervEnhet.has_key(enhet_id):
            raise ValueError, "Duplikat undervisningsenhet: <%s>" % enhet_id
        undervEnhet[enhet_id] = {}
        multi_id = ".".join(enhet['ue.institusjonsnr'], enhet['ue.emnekode'],
                            enhet['ue.terminkode'], enhet['ue.arstall'])
        # Finnes det flere enn en undervisningsenhet tilknyttet denne
        # emnekoden i innev�rende semester?
        emne_versjon[multi_id][enhet['ue.versjonskode']] = 1
        emne_termnr[multi_id][enhet['ue.terminnr']] = 1

def get_undervisningsaktiviteter():
    for akt in fs.GetUndAktivitet()[1]:
        enhet_id =":".join("kurs", akt['ua.institusjonsnr'],
                           akt['ua.emnekode'],
                           akt['ua.versjonskode'], akt['ua.terminkode'],
                           akt['ua.arstall'], akt['ua.terminnr'])
        if not undervEnhet.has_key(enhet_id):
            raise ValueError, "Ikke-eksisterende enhet <%s> har aktiviteter" %\
                  enhet_id
        if undervEnhet[enhet_id]['aktivitet'].has_key(akt['aktkode']):
            raise ValueError, "Duplikat undervisningsaktivitet <%s:%s>" % (
                enhet_id, akt['aktkode'])
        undervEnhet[enhet_id][
            'aktivitet'][akt['aktkode']] = akt['ua.aktivitetsnavn']


def get_evukurs_aktiviteter(undervEnhet):
    for kurs in fs.GetEvuKurs()[1]:
        kurs_id = ":".join('evu', kurs['kurskode'], kurs['tidsrom'])
        undervEnhet[kurs_id] = {}
        for aktivitet in fs.GetAktivitetEvuKurs(
            kurs['kurskode'], kurs['tidsrom'])[1]:
            undervEnhet[kurs_id][
                'aktivitet'][aktivitet['aktkode']] = aktivitet['aktnavn']
        tmp = []
        for evuansv in fs.GetAnsvEvuKurs(kurs['kurskode'], kurs['tidsrom'])[1]:
            fnr = "%06d%05d" % (
                int(evuansv['fodselsdato']), int(evuansv['fodselsnr']))
            tmp.append(fnr2uname.get(fnr, None))
        undervEnhet[kurs_id]['fagansv'] = tmp[:]
        tmp = []
        for student in fs.GetStudEvuKurs(kurskode, tidsrom)[1]:
            fnr = "%06d%05d" % (
                int(student['fodselsdato']), int(student['fodselsnr']))
            tmp.append(fnr2uname.get(fnr, None))
        undervEnhet[kurs_id]['students'] = tmp[:]

def get_evu_ansv(kurskode, tidsrom):
    kurs_id = ":".join('evu', kurskode, tidsrom)
    return undervEnhet[kurs_id]['fagansv']

def get_evu_students(kurskode, tidsrom):
    kurs_id = ":".join('evu', kurskode, tidsrom)
    return undervEnhet[kurs_id]['students']

def populate_enhet_groups(enhet_id):
    type_id = enhet_id.split(":")
    type = type_id.pop(0).lower()

    if type == 'kurs':
        Instnr, emnekode, versjon, termk, aar, termnr = type_id

        # Finnes det mer enn en undervisningsenhet knyttet til dette
        # emnet, kun forskjellig p� versjonskode og/eller terminnr?  I
        # s� fall b�r gruppene f� beskrivelser som gj�r det mulig �
        # knytte dem til riktig undervisningsenhet.
        multi_enhet = []
        multi_id = ":",join(Instnr, emnekode, termk, aar)
        if emne_termnr[multi_id].keys() > 1:
            multi_enhet.append("%s. termin" % termnr)
        if emne_versjon[multi_id].keys() > 1:
            multi_enhet.append("v%s" % versjon)
        if multi_enhet:
            enhet_suffix = ", %s" % ", ".join(multi_enhet)
        else:
            enhet_suffix = ""
        logging.debug("Oppdaterer grupper for %s %s %s%s:" % (
            emnekode, termk, aar, enhet_suffix))

        #
        # Ansvarlige for undervisningsenheten.
        logging.debug(" enhetsansvar")
        enhet_ansv = {}
        for uname in fnrs2unames(
            fs.GetAnsvUndervEnhet(Instnr, emnekode, versjon, termk,
                                  aar, termnr))[1]:
            enhet_ansv[uname] = 1

        # Finnes kurs som g�r over mer enn et semester, samtidig som
        # at kurset/emnet starter hvert semester.  Utvider strukturen
        # til � ta h�yde for at det til enhver tid kan finnes flere
        # kurs av samme type til en hver tid.
        kurs_id = UE2KursID('kurs', Instnr, emnekode, versjon, termk,
                            aar, termnr)

        # Ogs� supergruppene til undervisningsenhet - og
        # -aktivitets-avledede grupper skal ha "kurs:"-prefiks.
        sync_group(kurs_id, "%s:enhetsansvar" % enhet_id,
                   "Ansvarlige %s %s %s%s" % (emnekode, termk,
                                              aar, enhet_suffix),
                   co.entity_account, enhet_ansv);
        #
        # Alle n�v�rende undervisningsmeldte samt n�v�rende+fremtidige
        # eksamensmeldte studenter.
        logging.debug(" student")
        alle_stud = {}
        for uname in fnrs2unames(
            fs.GetStudUndervEnhet(Instnr, emnekode, versjon, termk,
                                  aar, termnr))[1]:
            alle_stud[uname] = 1

        sync_group(kurs_id, "%s:student" % enhet_id,
                   "Studenter %s %s %s%s" % (emnekode, termk,
                                             aar, enhet_suffix),
                   co.entity_account, alle_stud);

        for aktkode in UndervEnhet[enhet_id]['aktivitet'].keys():
            #
            # Ansvarlige for denne undervisningsaktiviteten.
            logging.debug(" aktivitetsansvar:%s" % aktkode)
            akt_ansv = {}
            for uname in fnrs2unames(
                fs.GetAnsvUndAktivitet(Instnr, emnekode, versjon, termk,
                                       aar, termnr, aktkode))[1]:
                akt_ansv[uname] = 1
                
            sync_group(kurs_id, "%s:aktivitetsansvar:%s" % (enhet_id, aktkode),
                       "Ansvarlige %s %s %s%s %s" % (
                emnekode, termk, aar, enhet_suffix,
                UndervEnhet[enhet_id]['aktivitet'][aktkode]),
                       co.entity_account, akt_ansv);

            # Studenter meldt p� denne undervisningsaktiviteten.
            logging.debug(" student:%s" % aktkode)
            akt_stud = ()
            for uname in fnrs2unames(
                fs.GetStudUndAktivitet(Instnr, emnekode, versjon, termk,
                                       aar, termnr, aktkode))[1]:
                if not alle_stud.has_key(uname):
                    warn_msg += (
                        "OBS: Bruker <%s> (fnr <%s>) er med i"+
                        " undaktivitet <%s>, men ikke i"+
                        " undervisningsenhet <%s>.\n" % (
                        uname, account_id2fnr[uname],
                              "%s:%s" % (enhet_id, aktkode), enhet_id))
                akt_stud[uname] = 1

            sync_group(kurs_id, "%s:student:%s" % (enhet_id, aktkode),
                       "Studenter %s %s %s%s %s" % (
                emnekode, termk, aar, enhet_suffix,
                UndervEnhet[enhet_id]['aktivitet'][aktkode]),
                       co.entity_account, akt_stud)

    elif type == 'evu':
        kurskode, tidsrom = type_id
        kurs_id = UE2KursID("evu", kurskode, tidsrom)
        logging.debug("Oppdaterer grupper for %s: " % enhet_id)
        #
        # Ansvarlige for EVU-kurset
        logging.debug(" evuAnsvar")
        evuans = get_evu_ansv(kurskode, tidsrom)
        sync_group(kurs_id, "%s:enhetsansvar" % enhet_id,
                   "Ansvarlige EVU-kurs %s, %s" % (kurskode, tidsrom),
                   co.entity_account, evuans)
        #
        # Alle p�meldte studenter
        logging.debug(" evuStudenter")
        evustud = get_evu_students(kurskode, tidsrom)
        sync_group(kurs_id, "%s:student" % enhet_id,
                   "Studenter EVU-kurs %s, %s" % (kurskode, tidsrom),
                   co.entity_account, evustud)

        for aktkode in UndervEnhet[enhet_id]['aktivitet'].keys():
            #
            # Ansvarlige for kursaktivitet
            logging.debug(" aktivitetsansvar:%s" % aktkode)
            evu_akt_ansv = {}
            for uname in fnrs2unames(
                fs.GetAnsvEvuAktivitet(kurskode, tidsrom, aktkode))[1]:
                evu_akt_ansv[uname] = 1

            sync_group(kurs_id, "%s:aktivitetsansvar:%s" % (enhet_id, aktkode),
                       "Ansvarlige EVU-kurs %s, %s: %s" % (
                kurskode, tidsrom,
                UndervEnhet[enhet_id]['aktivitet'][aktkode]),
                       co.entity_account, evu_akt_ansv)

            # Studenter til denne kursaktiviteten
            logging.debug(" student:%s" % aktkode)
            evu_akt_stud = {}
            for uname in fnrs2unames(
                fs.GetStudEvuAktivitet(kurskode, tidsrom, aktkode))[1]:
                if not evustud.has_key(uname):
                    warn_msg += (
                        "OBS: Bruker <%s> (fnr <%s>) er med i" +
                        " aktivitet <%s>, men ikke i kurset <%s>.\n" % (
                        uname, account_id2fnr[uname],
                              "%s:%s" % (enhet_id, aktkode), enhet_id))
                evu_akt_stud[uname] = 1
            sync_group(kurs_id, "%s:student:%s" % (enhet_id, aktkode),
                       "Studenter EVU-kurs %s, %s: %s" % (
                kurskode, tidsrom,
                UndervEnhet[enhet_id]['aktivitet'][aktkode]),
                       co.entity_account, evu_akt_stud)
    logging.debug(" done")


def sync_group(affil, gname, descr, mtype, memb):
    members = memb.copy()
    gname = mkgname(gname, 'uio.no:fs:')
    correct_visib = co.group_visibility_none
    if (affil is None or               # Niv� 0; $gname er supergruppen
        affil == fs_supergroup or         # $gname er p� niv� 1
        re.search(r'^(evu|kurs):[^:]+$', affil, re.I)): # $gname er p� niv� 2
        # Grupper s� langt oppe i strukturen skal v�re rent interne;
        # de brukes kun til kontroll av hierarki og eksport.
        gname = mkgname(gname)
        correct_visib = co.group_visibility_internal
    if affil is not None:
        AffiliatedGroups[affil][gname] = 1
    known_FS_groups[gname] = 1

    # Gj�r objektet $Group klar til � modifisere gruppen med navn
    # $gname.
    try:
        gr = group.find_by_name(gname)
        # Dersom gruppen $gname fantes, er $gr n� en peker til samme
        # objekt som $Group; i motsatt fall er $gr false.
        if gr.visibility != correct_visib:
            logging.fatal("Group <%s> has wrong visibility." % gname)

        if gr.description != descr:
            gr.description = descr
            gr.write_db()

        u, i, d = gr.list_members(member_type=mtype)
        for member in u:
            if members.has_key(member):
                del(members[member])
            else:
                gr.remove_member(member, co.group_memberop_union)
                #
                # Supergroups will only contain groups that have been
                # automatically created by this script, hence it is
                # safe to automatically destroy groups that are no
                # longer member of their supergroup.

                if (mtype == co.entity_group and
                    correct_visib == co.group_visibility_internal and
                    (not known_FS_groups.has_key(member))):
                    destroy_group(member, 2)
    except Errors.NotFoundError:
        gr.populate(gname, correct_visib, descr)
        gr.write_db()

    for member in members.keys():
        gr.add_member(member)

def destroy_group(gname, max_recurse):
    gr = Group.Group(db)
    gr.find_by_name(gname)
    u, i, d = gr.list_members(member_type=co.entity_group)
    for subg in u:
        destroy_group(subg['entity_id'], max_recurse - 1)
    gr.delete()

def usage(exitcode=0):
    print """Usage: [optons]
    --db-user name: connect with given database username
    --db-service name: connect to given database"""
    sys.exit(exitcode)

if __name__ == '__main__':
    global fs
    try:
        opts, args = getopt.getopt(sys.argv[1:], "",
                                   ["db-user=", "db-service="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    db_user = None         # TBD: cereconf value?
    db_service = None      # TBD: cereconf value?
    for o, val in opts:
        if o in ('--db-user',):
            db_user = val
        elif o in ('--db-service',):
            db_service = val
    db = Database.connect(user=db_user, service=db_service,
                      DB_driver='Oracle')
    fs = FS(db)

