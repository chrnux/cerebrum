#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import sys
import cerebrum_path
import cereconf
from Cerebrum import Account
from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules.no import fodselsnr
from Cerebrum.modules.no.ntnu import access_BDB
from Cerebrum.modules import PosixUser
from Cerebrum.modules import PosixGroup
from Cerebrum.modules import Email

import mx.DateTime
from Cerebrum.modules.no.ntnu import util
import getopt
import logging
import time
import os
import traceback
from sets import Set as set


import locale
locale.setlocale(locale.LC_CTYPE,'nb_NO')


class BDBImportError(Exception):
    pass

"""
Import orgunits,persons and accounts from NTNUs old UserAdministrative System.
"""

# Set the client encoding for the Oracle client libraries
os.environ['NLS_LANG'] = cereconf.BDB_ENCODING
missing_personnr = 0
wrong_nss_checksum = 0
num_accounts = 0
num_persons = 0
ant_persons = 0
verbose = False
dryrun = False
show_traceback = False

def dictcompare(old, new, union=False):
    oldk = set(old.keys())
    newk = set(new.keys())
    
    addk = newk - oldk
    delk = oldk - newk
    
    modk = set()
    for i in newk & oldk:
        if new[i] != old[i]:
            modk.add(i)

    if union:
        return addk | modk | delk
    else:
        return addk, modk, delk


def dictinverse(d):
    r={}
    for k,v in d.iteritems():
        if r.has_key(v): raise KeyError("Duplicate key", v)
        r[v]=k
    return r


def _get_password(_account):
    return _account.get('password2')

def _is_posix(_account):
    res = True
    if not 'unix_uid' in _account:
        res = False
    if not 'unix_gid' in _account:
        res = False
    return res

def _is_primary(_account):
    if _account.get('status') == 1:
        return True
    else:
        return False

def valid_nin(dato, personnr):
    # Valid date-formats are DDMMYYYY and DDMMYY
    # dato = string, personnr = str/int
    fnr = dato[:4] + dato[-2:] + "%0.5d" % int(personnr)

    vekt1 = [3,7,6,1,8,9,4,5,2]
    vekt2 = [5,4,3,2,7,6,5,4,3,2]

    sum1 = sum2 = 0
    for i in range(9): sum1 += vekt1[i] * int(fnr[i])
    for i in range(10): sum2 += vekt2[i] * int(fnr[i])

    sif1 = sum1 % 11
    sif2 = sum2 % 11

    if (sif1>0): sif1 = 11-sif1
    if (sif2>0): sif2 = 11-sif2

    return ( (str(sif1) == fnr[-2]) and (str(sif2)==fnr[-1]) )


def avknekk_ytlendinger(fnr):
    #    Foreign student have +40 on days, or +50 on months in their
    #    birthdate. This is stripped by BDB, and we're now putting it
    #    back.
    if valid_nin(fnr[:6], fnr[6:]):
        return fnr

    day = int(fnr[0:2])
    month = int(fnr[2:4])

    pluss40 = str("%0.2d" % (day+40)) + fnr[2:]
    if valid_nin(pluss40[:6], pluss40[6:]):
        return pluss40

    pluss50 = fnr[0:2]  + str("%0.2d" % (month+50)) + fnr[4:]
    if valid_nin(pluss50[:6], pluss50[6:]):
        return pluss50

    return fnr



class spread_mapping(object):
    def __init__(self, co, logger):
        self.co = co
        self.logger = logger
        self._cache = dict()
    def __getitem__(self, key):
        if not key in self._cache:
            try:
                self._cache[key] = int(self.co.Spread("user@%s" % key))
            except Errors.NotFoundError:
                self.logger.warn("Spread: Unhandled BDB system spread %s" % key)
                self._cache[key] = None
        return self._cache[key]


class BDBSync:
    def __init__(self):
        self.bdb = access_BDB.BDB()
        self.db = Factory.get('Database')()
        self.db.cl_init(change_program='import_BDB')
        self.const = Factory.get('Constants')(self.db)
        self.ou = Factory.get('OU')(self.db)
        self.new_person = Factory.get('Person')(self.db)
        self.fnr_person = Factory.get('Person')(self.db)
        self.ac = Factory.get('Account')(self.db)
        #self.ac = Account.Account(self.db)
        self.group = Factory.get('Group')(self.db)
        self.posix_group = PosixGroup.PosixGroup(self.db)
        self.posix_user = PosixUser.PosixUser(self.db)
        self.posix_user2 = PosixUser.PosixUser(self.db)
        self.et = Email.EmailTarget(self.db)
        self.epat = Email.EmailPrimaryAddressTarget(self.db)
        self.ea = Email.EmailAddress(self.db)
        self.ed = Email.EmailDomain(self.db)
        self.ev = Email.EmailVacation(self.db)
        self.ef = Email.EmailForward(self.db)
        self.es = Email.EmailServer(self.db)
        self.logger = Factory.get_logger("console")
        self.logger = Factory.get_logger("syslog")
        self.logger.info("Starting import_BDB")

        self.ac.find_by_name('bootstrap_account')
        self.initial_account = self.ac.entity_id
        self.default_shell = self.const.posix_shell_bash
        self.ac.clear()
        self.spread_mapping = spread_mapping(self.const, self.logger)

        self.np_owner = Factory.get('Group')(self.db)
        try:
            self.np_owner.find_by_name(cereconf.BDB_NP_OWNER_GROUP)
        except Errors.NotFoundError:
            self.np_owner.populate(self.initial_account,
                                   self.const.group_visibility_all,
                                   cereconf.BDB_NP_OWNER_GROUP)
            self.np_owner.write_db()
            self.db.commit()
        self.group.clear()
        
                                
        self.ac.clear()
        self.ac.find_by_name(cereconf.INITIAL_ACCOUNTNAME)
        self.default_creator_id = self.ac.entity_id
        self.ac.clear()


    def check_commit(self, fun, *args, **kw):
        msg='syncing'
        if 'msg' in kw:
            msg=kw['msg']
            del kw['msg']
        try:
            fun(*args, **kw)
        except (self.db.IntegrityError,
                Errors.CerebrumError,
                Errors.DatabaseException,
                LookupError), e:
            self.logger.exception('Error while %s: %s' % (msg, e))
            self.db.rollback()
        else:
            if dryrun:
                self.db.rollback()
            else:
                self.db.commit()


    def sync_vacation(self):
        """Not implemented yet"""
        vacations = self.bdb.get_vacations()
        for vacation in vacations:
            _sync_vacation(vacation)
        return

    def _sync_vacation(self,vac):
        const = self.const
        person = self.new_person
        person.clear()
        ev = self.ev
        ev.clear()
        ac = self.ac
        ac.clear()
        try:
            person.find_by_external_id(const.externalid_bdb_person,str(vac['person']))
        except Errors.NotFoundError:
            return

        # For this person, we need to find an EmailTarget, but to get that, we need an account
        account = person.get_primary_account()
        if not account:
            return
            # FIXME lookup other accounts
        ac.find(account)
        try:
            ev.find_by_target_entity(ac.entity_id)
        except Errors.NotFoundError:
            # No EmailTarget for this Entity
            return
        except Errors.TooManyRowsError:
            # Narrow down the search.. how?
            return
        if dryrun:
            self.db.rollback()
        else:
            self.db.commit()
        return

    def _sync_forward(self,forward):
        # This method to be called from sync_persons, so person.entity_id should
        # already be set.
        person = self.new_person
        account = self.ac
        const = self.const
        fwd = self.ef
        fwd.clear()
        # See if a forward is already set.
        try:
            fwd.find_by_target_entity(person.entity_id)
            fwd.delete()
        except Errors.NotFoundError:
            pass
        fwd.populate(type=const.email_target_forward, entity_id=person.entity_id, entity_type=const.entity_person)
        fwd.writedb()
        if dryrun:
            fwd.rollback()
        else:
            fwd.commit()
        return

    def sync_affiliations(self):
        #  1 student
        #  2 fast ansatt
        #  3 midlertidig ansatt
        #  4 stipendiat
        #  5 alias
        #  7 gjest
        #  9 alumnus
        # 12 familie
        self.logger.debug("Getting affiliations from BDB...")
        aff_map = {}
        aff_map[1] = self.const.affiliation_status_student_student
        aff_map[2] = self.const.affiliation_status_ansatt_ansatt
        aff_map[3] = self.const.affiliation_status_ansatt_ansatt
        aff_map[4] = self.const.affiliation_status_student_drgrad
        aff_map[5] = self.const.affiliation_status_tilknyttet_annen
        aff_map[7] = self.const.affiliation_status_tilknyttet_gjest
        aff_map[9] = self.const.affiliation_status_alumni_aktiv
        aff_map[12] = self.const.affiliation_status_tilknyttet_annen

        const = self.const

        bdbaffs = self.bdb.get_affiliations()
        cereaffs = self.new_person.list_affiliations(
            source_system=const.system_bdb)

        kjerneider = self.ou.list_external_ids(const.system_kjernen,
                                               const.externalid_kjerneid_ou)
        kjerne_map = {}
        for k in kjerneider:
            kjerne_map[k['external_id']] = k['entity_id']

        stedkoder = self.ou.list_external_ids(
            id_type=self.const.externalid_stedkode,
            entity_type=self.const.entity_ou,
            source_system=self.const.system_kjernen)
        sted_map = {}
        for s in stedkoder:
            kode = s['external_id'][5:]
            sted_map[kode] = s['entity_id']

        bdb_pers_ids = self.new_person.list_external_ids(
            source_system=const.system_bdb,
            id_type=const.externalid_bdb_person,
            entity_type=const.entity_person)
        pers_id_map={}
        for eid in bdb_pers_ids:
            pers_id_map[int(eid['external_id'])] = eid['entity_id']

        oldaffs = set([(a['person_id'], a['ou_id'], a['status'])
                       for a in cereaffs])
        newaffs=set()
        for a in bdbaffs:
            try:
                person_id = pers_id_map[a['person']]
            except KeyError:
                self.logger.warning("Affiliation: Person (bdb-id %d) does not exist" %
                                    a['person'])
                continue
            try:
                ou_id = kjerne_map[str(a['ou_kjcode'])]
            except KeyError:
                try:
                    ou_id = sted_map["%06d" % a['ou_code']]
                except KeyError:
                    self.logger.warning("Affiliation: OU (stedkode %06d, kjerneid %d) does not exist" % (a['ou_code'], a['ou_kjcode']))
                    continue
            try:
                status = int(aff_map[a['aff_type']])
            except KeyError:
                self.logger.error("Affiliation (bdb-type %d) is not handled" %
                                  a['aff_type'])
                continue
            newaffs.add((person_id, ou_id, status))

        self.logger.debug("affiliations: bdb %d, filtered %d, old %d" % (
            len(bdbaffs), len(newaffs), len(oldaffs)))

        delaffs={}
        for person_id, ou_id, status in oldaffs - newaffs:
            aff=const.PersonAffStatus(status).affiliation
            if not delaffs.has_key(person_id):
                delaffs[person_id]=[]
            delaffs[person_id].append((ou_id, aff))

        addaffs={}
        for person_id, ou_id, status in newaffs - oldaffs:
            aff=const.PersonAffStatus(status).affiliation
            if not addaffs.has_key(person_id):
                addaffs[person_id]=[]
            addaffs[person_id].append((ou_id, aff, status))

        chpers = set(delaffs.keys()) | set(addaffs.keys())

        self.logger.debug("affiliations: deleting on %d, adding on %d, total %d persons" % (len(delaffs), len(addaffs), len(chpers)))

        for person_id in chpers:
            self.check_commit(self.person_change_affiliations,
                              person_id,
                              delaffs.get(person_id, []),
                              addaffs.get(person_id, []))

    def person_change_affiliations(self, person_id, delaffs, addaffs):
        const = self.const
        person = self.new_person
        person.clear()
        person.find(person_id)
        for ou_id, aff in delaffs:
            self.logger.info("Removing affiliation %d person cerebrum-%d ou %d" %
                             (aff, person_id, ou_id))
            person.delete_affiliation(ou_id, aff, const.system_bdb)
        for ou_id, aff, status in addaffs:
            self.logger.info("Adding affiliation %d person cerebrum-%d ou %d status %d" %
                             (aff, person_id, ou_id, status))
            person.add_affiliation(ou_id, aff, const.system_bdb, status)


    def delete_bdb_fodselsnr(self, entity_id):
        person=self.new_person
        person.clear()
        person.find(entity_id)
        person.affect_external_id(self.const.system_bdb,
                                       self.const.externalid_fodselsnr)
        person.write_db()
        

    def clean_persons_extids(self, persons):
        bdbfnr={}
        oldbdbfnr={}
        bdbid={}
        rbdbid={}
        person=self.new_person
        self.logger.debug("Looking for invalid bdb NINs")

        self.logger.debug("Fetching bdb NINs")
        for p in persons:
            if p.get("birth_date") and p.get("person_number"):
                bdbfnr[p['id']] = self.__get_fodselsnr(p)

        self.logger.debug("Fetching cerebrum bdb-ids")
        for i in person.list_external_ids(source_system=self.const.system_bdb,
                                          id_type=self.const.externalid_bdb_person):
            #bdbid[i['external_id']] = i['entity_id']
            bdbid[int(i['entity_id'])] = int(i['external_id'])

        self.logger.debug("Fetching bdb NINs in cerebrum")
        for i in person.list_external_ids(source_system=self.const.system_bdb,
                                          id_type=self.const.externalid_fodselsnr):
            if not i['entity_id'] in bdbid:
                self.logger.warning(("cerebrum person %s " +
                                     "has BDB fnr but not BDB-id")
                                    % i['entity_id'])
                continue
            bid = bdbid[int(i['entity_id'])]
            fnr = i['external_id']
            if bdbfnr.has_key(bid) and bdbfnr[bid] == fnr:
                pass
            else:
                self.logger.debug("Deleting invalid bdb fodselsnr on cerebrum-%s"
                                  % i['entity_id'])
                self.check_commit(self.delete_bdb_fodselsnr, i['entity_id'],
                                  msg='deleting invalid bdb fodselsnr')
                


    def compare_person_bdbids(self):

        cerebrum=set()
        bdb=set()
        person=self.new_person
        for i in person.list_external_ids(source_system=self.const.system_bdb,
                                          id_type=self.const.externalid_bdb_person):
            cerebrum.add(str(i['external_id']))

        for p in self.bdb.get_persons():
            bdb.add(str(p['id']))

        print "cerebrum - BDB:", ",".join(cerebrum - bdb)
        print "BDB - cerebrum:", ",".join(bdb - cerebrum)
        


    def sync_persons(self):
        self.logger.debug("Getting persons from BDB...")
        global ant_persons, num_persons
        persons = self.bdb.get_persons()
        #self.clean_persons_extids(persons)
        ant_persons = len(persons)
        self.logger.debug("Done fetching persons from BDB")
        for person in persons:
            self.logger.debug('Syncronizing BDB-person %s' % person['id'])
            try:
                self._sync_person(person)
            except Exception, e:
                if show_traceback:
                    traceback.print_exc()
                self.db.rollback()
                self.logger.error('Syncronizing of BDB-person %s failed: %s' % (
                    person['id'], e))
            else:
                if dryrun:
                    self.db.rollback()
                    self.logger.debug('Rollback called. Changes omitted.')
                else:
                    num_persons+=1
                    self.db.commit()
                    self.logger.debug('Changes on BDB-%s commited to Cerebrum' % person['id'])
        self.logger.debug("%s persons had missing personnumber" % missing_personnr)
        self.logger.debug("%s persons had bad checksum on personnumber" % wrong_nss_checksum)
        self.logger.debug("%s persons where added or updated" % num_persons)


    def __validate_person(self, person):
        # Returns true||false if enough attributes are set
        if not self.__validate_names(person):
            self.logger.warn("Person with bdb-external-id %s has bad names" % person['id'])
            return False
        if not person.get("birth_date"): 
            self.logger.warn("Person with bdb-external-id %s has no birthdate" % person['id'])
            return False
        try:
            #XXX check with mx.DateTime....
            person.get("birth_date")
        except:
            self.logger.warn("Person with bdb-external-id %s has bad birthdate" % person['id'])
            return False
        if person['no_nin'] is None:
            if not person.get("person_number"):
                self.logger.warn("Person with bdb-external-id %s has no person-number" % person['id'])
                return False
            try:
                fnr = self.__get_fodselsnr(person)
            except fodselsnr.InvalidFnrError,e:
                return False
        return True

    def __get_gender(self,person):
        try:
            fnr = self.__get_fodselsnr(person)
            if (fodselsnr.er_kvinne(fnr)):
                return self.const.gender_female
            else:
                return self.const.gender_male
        except fodselsnr.InvalidFnrError,e:
            return self.const.gender_unknown

    def __get_fodselsnr(self,person):
        # We should not get a key-error since __validate_person should take care
        # of non-existing person_number
        pnr = str(person.get("person_number"))
        year,month,day = person.get("birth_date").split('-')
        year = year[2:]
        # Format fnr correctly
        try:
            fnr = "%02d%02d%02d%05d" % (int(day),int(month),int(year),int(pnr))
        except ValueError:
            raise fodselsnr.InvalidFnrError()
        fnr = avknekk_ytlendinger(fnr)
        return fnr

    def __validate_names(self,person): 
        #To be called from __validate_person
        if (person.get('first_name', ' ').isspace() or
            person.get('last_name',' ').isspace()):
            self.logger.warn("Missing name for BDB-person %s " % person['id'])
            return False
        else:
            return True


    def check_free_fnr(self, fnr, new_person):
        p = self.fnr_person
        const=self.const
        p.clear()
        try:
            p.find_by_external_id(const.externalid_fodselsnr, fnr,
                                  const.system_bdb)
        except Errors.NotFoundError:
            pass
        else:
            if p.entity_id != new_person.entity_id:
                raise self.db.IntegrityError(
                    "Person cerebrum-%s's BDB-fnr <%s> is used by cerebrum-%s!" %
                    (new_person.entity_id, fnr,
                     p.entity_id))

    def _sync_person(self, person):
        global num_persons,ant_persons
        self.logger.debug("Process person BDB-%s" % person['id'])
        const = self.const
        new_person = self.new_person

        if not self.__validate_person(person):
            return

        gender = self.__get_gender(person)
        birth_date = mx.DateTime.DateFrom(person.get("birth_date"))

        try:
            fnr = self.__get_fodselsnr(person)
        except fodselsnr.InvalidFnrError, e:
            fnr = None

        new_person.clear()
        found_person=False
        try:
            new_person.find_by_external_id(const.externalid_bdb_person,str(person['id']))
        except Errors.NotFoundError:
            if fnr:
                self.logger.debug("No match on bdb-id. Filtering by fodselsnr instead")
                try:
                    new_person.find_by_external_id(const.externalid_fodselsnr,fnr)
                except Errors.TooManyRowsError:
                    self.logger.debug("Too many matching fodselsnr. Narrow down the filter")
                    # Iterate over the different source-systems
                    for source in (const.system_lt,const.system_bdb,const.system_fs,
                                   const.system_manual):
                        try:
                            new_person.find_by_external_id(const.externalid_fodselsnr,fnr,
                                                       source)
                        except Errors.NotFoundError:
                            pass
                        else:
                            found_person=True
                            self.logger.debug("Found matching fnr in source-system %s" % source)
                            break
                    else:
                        self.logger.debug("No fnr in any prefered system")
                        raise Errors.NotFoundError
                except Errors.NotFoundError:
                    self.logger.debug("No fnr in any system")
                else:
                    found_person=True
                    self.logger.debug("Found person by fnr")
        else:
            found_person=True
            self.logger.debug("Found BDB-id %s in cerebrum" % person['id'])

        if found_person:
            self.logger.info("Updating cerebrum person %s from BDB-person %s" %
                              (new_person.entity_id, person['id']))
            if new_person.birth_date != birth_date:
                new_person.birth_date = birth_date
            if new_person.gender != gender:
                new_person.gender = gender
        else:
            self.logger.info("Creating new cerebrum person from BDB-person %s" %
                              person['id'])
            new_person.populate(birth_date, gender)
        new_person.write_db()

        # Populate person with names 

        new_person.affect_names(const.system_bdb,
                                const.name_first,
                                const.name_last,
                                const.name_personal_title)
        new_person.populate_name(const.name_first, person['first_name'])
        new_person.populate_name(const.name_last, person['last_name'])

        if person.get('tittel_personlig'):
            new_person.populate_name(const.name_personal_title,
                                     person['tittel_personlig'])

        new_person.affect_external_id(const.system_bdb,
                                      const.externalid_fodselsnr, 
                                      const.externalid_bdb_person)
        new_person.populate_external_id(const.system_bdb,
                                        const.externalid_bdb_person,
                                        person['id'])
        if fnr:
            self.check_free_fnr(fnr, new_person)
            new_person.populate_external_id(const.system_bdb,
                                            const.externalid_fodselsnr,
                                            fnr)

        email_addr = person.get('mail')
        if email_addr:
            # Use a lower preference than normal, for easy overriding.
            new_person.populate_contact_info(const.system_bdb,
                                             type=const.contact_email,
                                             value=email_addr,
                                             contact_pref=30)
        else:
            # This will mark any contact_info for deletion
            new_person.populate_contact_info(const.system_bdb)

        # Write to database
        new_person.write_db()

        newquarantines = set()
        if person.get('sperret', False):
            newquarantines.add(new_person.const.quarantine_sperret)
        
        oldquarantines = set([q['quarantine_type']
                              for q in new_person.get_entity_quarantine()])

        for s in oldquarantines - newquarantines:
            new_person.delete_entity_quarantine(s)

        for s in newquarantines - oldquarantines:
            new_person.add_entity_quarantine(s, creator=self.initial_account,
                                             description="imported from BDB",
                                             start=mx.DateTime.now())

        self.logger.info("Wrote cerebrum person %s", new_person.entity_id)

    def _is_posix_group(self,group):
        res = False
        if 'gid' in group:
            res = True
        return res

    def _validate_group(self,group):
        res = True
        if not 'name' in group:
            self.logger.error("Group BDB-%s is invalid, has no name." % grp['id'])
            res = False
        return res

    def group_clean_name(self,name):
        name = name.replace('-','_')
        name = name.replace(' ','_')
        name = name.lower()
        return name

        
    def sync_groups(self):
        """
        This method synchronizes all BDB groups into Cerebrum.
        """
        groups = self.bdb.get_groups()
        posix_group = self.posix_group
        group = self.group
        creator_id = self.initial_account
        const = self.const

        posix_group.clear()
        try:
            # Every installation should have this group. Make one if it doesn't exist.
            posix_group.find_by_name('posixgroup')
        except Errors.NotFoundError:
            posix_group.populate(creator_id, visibility=self.const.group_visibility_all,\
                                 name='posixgroup', description='Bootstrapped posixgroup')
            try:
                posix_group.write_db()
            except self.db.IntegrityError,ie: 
                self.logger.error("Integrity error catched while trying to add posixgroup named 'posixgroup' . Reason: %s" % \
                                  (str(ie)))
                self.db.rollback()
            else:
                if not posix_group.has_spread(const.spread_ntnu_group):
                    posix_group.add_spread(const.spread_ntnu_group)
                    posix_group.write_db()
        else:
            if dryrun:
                self.db.rollback()
            else:
                self.db.commit()

        for grp in groups:
            posix_group.clear()
            group.clear()
            if not self._validate_group(grp):
                continue
            grp['name'] = self.group_clean_name(grp['name'])
            if self._is_posix_group(grp):
                try:
                    posix_group.find_by_name(grp['name'])
                    self.logger.debug("Updating group %s" % grp['name'])
                    _has_changed = False
                    _gid = posix_group.posix_gid
                    if posix_group.posix_gid != grp['gid']:
                        posix_group.posix_gid = grp['gid']
                        _has_changed = True
                    if not posix_group.has_spread(const.spread_ntnu_group):
                        posix_group.add_spread(const.spread_ntnu_group)
                    if _has_changed:
                        posix_group.write_db()
                    if dryrun:
                        self.db.rollback()
                    else:
                        self.db.commit()
                    continue
                except Errors.NotFoundError:
                    posix_group.populate(creator_id,
                                         visibility=self.const.group_visibility_all,
                                         name=grp['name'],
                                         description=grp['description'],
                                         gid=grp['gid'])
                    try:
                        posix_group.write_db()
                    except self.db.IntegrityError,ie: 
                        self.logger.error("Integrity error catched on bdb group %s. Reason: %s" % (grp['name'],str(ie)))
                        continue
                    if not posix_group.has_spread(const.spread_ntnu_group):
                        posix_group.add_spread(const.spread_ntnu_group)
                    posix_group.write_db()
                    self.logger.debug("PosixGroup %s written to db" % grp['name'])
            else:
                try:
                    group.find_by_name(grp['name'])
                    self.logger.debug("Group %s already exists." % grp['name'])
                    continue
                except Errors.NotFoundError:
                    group.populate(creator_id,visibility=const.group_visibility_all,\
                                   name=grp['name'], description=grp['description'])
                    group.write_db()
                    self.logger.debug("Group %s written to db" % grp['name'])
                except Errors.IntegrityError,ie:
                    self.logger.error("Integrity error catched on bdb group %s. Reason: %s" % \
                                       (grp['name'],str(ie)))
                    continue
            if dryrun:
                self.db.rollback()
                self.logger.debug("Dryrun. Adding group rolled back")
            else:
                self.db.commit()
                self.logger.debug("Adding group commited")

    def _promote_posix(self, account_info, ac):
        # TBD: rewrite and consolidate this method and the method of same name
        #      from process_employees.py
        global num_accounts
        group = self.group
        posix_user = self.posix_user
        posix_group = self.posix_group

        posix_user.clear()
        posix_group.clear()

        self.check_uid(account_info)

        uid = account_info.get('unix_uid', None)
        shell = self.default_shell


        username = account_info.get('name')

        if uid == 0:
            self.logger.warn("User %s has uid=0. Not promoted to posix" % username)
            return
        try:
            posix_group.find_by_gid(account_info.get('unix_gid'))
        except Errors.NotFoundError:
            grp_name = account_info.get('group_name','posixgroup')
            posix_group.find_by_name(grp_name,domain=self.const.group_namespace)
            pass

        posix_user.populate(uid, posix_group.entity_id, None, shell, parent=ac)
        posix_user.write_db()

        self.logger.info("Account %s with posix-uid %s promoted to posix." % (username,uid))


    def check_uid(self, account_info):
        # self.posix_user may already be used by caller
        posix_user = self.posix_user2
        uid=account_info['unix_uid']
        posix_user.clear()
        try:
            posix_user.find_by_uid(uid)
        except Errors.NotFoundError:
            pass
        else:
            raise self.db.IntegrityError("Account %s's uid %d is used by %s!" %
                                             (account_info["name"], uid,
                                              posix_user.get_account_name()))

    def _copy_posixuser(self, account_info, posix_user):
        self.logger.info("Account %s is already posix. Updating" %
                         account_info["name"])

        posix_group = self.posix_group
        
        _has_changed = False
        _uid = posix_user.posix_uid
        _gid = posix_user.gid_id

        if account_info['unix_uid'] == 0:
            self.logger.warn("User %s has uid=0. Not updated posix" % username)
            return
            
        if posix_user.posix_uid != account_info['unix_uid']:
            self.check_uid(account_info)
            posix_user.posix_uid = account_info['unix_uid']
            _has_changed = True

        posix_group.clear()
        try:
            posix_group.find(posix_user.gid_id)
        except Errors.NotFoundError:
            posix_group.find_by_name('posixgroup')
            
        if posix_group.posix_gid != account_info['unix_gid']:
            posix_group.clear()
            # Denne kan kaste exception hvis unix_gid ikke finnes
            try:
                posix_group.find_by_gid(account_info['unix_gid'])
            except Errors.NotFoundError:
                posix_group.find_by_name('posixgroup')
            posix_user.gid_id = posix_group.entity_id
            _has_changed = True

        if _has_changed:
            try:
                posix_user.write_db()
            except self.db.IntegrityError,ie:
                uid,gid,name = account_info['unix_uid'],account_info['unix_gid'],account_info['name']
                self.logger.error('Uid/gid (%s/%s) already in use for account %s' % (uid,gid,name))
                raise ie

    def _validate_account(self, account_info):
        res = True
        if not 'name' in account_info:
            self.logger.error("Account BDB-%s has no name." % account_info['id'])
            res = False
        return res

    def _sync_account(self,account_info,update_password_only=False,add_missing=True):
        """Callback-function. To be used from sync_accounts-method."""
        global num_accounts
        logger = self.logger
        logger.debug("Callback for BDB-%s (%s)" % (account_info['id'],account_info['name']))
        
        # TODO: IMPLEMENT SYNC OF ACCOUNTS WITHOUT A PERSON
        if not 'person' in account_info:
            logger.error('Account BDB-%s has no person, skipping.' % account_info)
            return

        if not self._validate_account(account_info):
            return

        # At this point, we have enough to populate/update an account
        person = self.new_person
        ac = self.ac
        posix_user = self.posix_user
        posix_group = self.posix_group
        group = self.group

        person.clear()
        ac.clear()
        posix_user.clear()
        posix_group.clear()
        group.clear()

        # XXX who should be the creator of impoted accounts.
        # Use BDB-creator?
        default_expire_date = None
        const = self.const
        shell = self.default_shell

        bdb_account_type = const.externalid_bdb_account
        bdb_person_type = const.externalid_bdb_person
        bdb_source_type = const.system_bdb
        np_type = None

        if account_info.get('account_type') == 'programvare':
            np_type = const.Account('programvare')
            owner = self.np_owner
        elif account_info.get("posix_uid") == "0":
            np_type = const.Account('programvare')
            owner = self.np_owner
        else:
            person.clear()
            try:
                person.find_by_external_id(bdb_person_type,
                                           str(account_info['person']),bdb_source_type)
                logger.debug('Found person for account %s' % account_info['name'])
            except Errors.NotFoundError,e:
                logger.warn('Found no person for account %s (BDB-id %s)' %
                            (account_info['name'], account_info['person']))
                if not add_missing:
                    raise BDBImportError('No person for account %s (BDB-id %s)' %
                                      (account_info['name'], account_info['person']))
                    
                bdb_person = self.bdb.get_persons(bdbid=account_info['person'])
                self._sync_person(bdb_person[0])
                person.clear()
                try:
                    person.find_by_external_id(bdb_person_type,str(account_info['person']),bdb_source_type)
                except Errors.NotFoundError,e:
                    raise BDBImportError('Failed syncronizing person for account %s (BDB-id %s)' %
                                      (account_info['name'], account_info['person']))
            else:
                logger.info("Wrote bdb-person with bdb-id %s" %
                            account_info['person'])
            owner=person

        ac.clear()
        try:
            ac.find_by_name(account_info.get('name'))
        except Errors.NotFoundError:
            # Add account if it doesn't exists ?
            if add_missing:
                self._make_account(account_info, ac, owner, np_type)
        else:
            if update_password_only:
                self._sync_account_password(account_info, ac)
            else:
                self._copy_account_data(account_info, ac, owner, np_type)
                self._sync_account_password(account_info, ac)

        if _is_primary(account_info) and np_type is None:
            person.clear()
            person.find(ac.owner_id)
            t = person.get_trait(const.trait_primary_account)
            if not t or t['target_id'] != ac.entity_id:
                person.populate_trait(const.trait_primary_account,
                                      target_id=ac.entity_id)
                person.write_db()


    def _update_password(self, _account, ac):
        bdb_blowfish = None
        const=self.const
        logger=self.logger
        try:
            bdb_blowfish = ac.get_account_authentication(const.auth_type_bdb_blowfish)
            self.logger.debug("Found blowfish in cerebrum")
        except Errors.NotFoundError:
            pass

        if bdb_blowfish == _account.get('password'):
            logger.debug("Password has not changed since last run")
            return
        else:
            # Store the blowfish directly first.
            logger.debug("Password has changed since last. Updating blowfish and other auth-types")
            ac.affect_auth_types(const.auth_type_bdb_blowfish)
            ac.populate_authentication_type(const.auth_type_bdb_blowfish, _account.get('password'))
            ac.write_db()
            ac.set_password(_get_password(_account))
            ac.write_db()

    def _sync_account_password(self, account_info, ac):
        logger=self.logger
        _pwd = _get_password(account_info)
        if _pwd is None:
            logger.warning('Account %s has no password!' %
                           account_info.get('name'))
            return

        self._update_password(account_info, ac)


    # copy data from account_info to ac.
    # ac is a valid cerebrum account object.
    def _copy_account_data(self, account_info, ac, owner, np_type=None):

        username = account_info["name"]
        logger = self.logger
        posix_user = self.posix_user

        person_entity = owner.entity_id
        if ac.owner_id != owner.entity_id or ac.np_type != np_type:
            old_account_types = list(ac.get_account_types(filter_expired=False))
            for at in old_account_types:
                ac.del_account_type(at['ou_id'], at['affiliation'])
            ac.owner_id = owner.entity_id
            ac.owner_type = owner.entity_type
            ac.np_type = np_type
            ac.write_db()
            if ac.owner_type == ac.const.entity_person:
                owneraffs=set()
                for aff in owner.get_affiliations():
                    owneraffs.add((aff['ou_id'], aff['affiliation']))
                for at in old_account_types:
                    if (at['ou_id'], at['affiliation']) in owneraffs:
                        ac.set_account_type(at['ou_id'], at['affiliation'])
            

        # ... we'll update expire-date 
        logger.info('Updating account %s on person cerebrum-%s' % (username,person_entity))
        create_date = account_info.get('creation_date')
        if create_date:
            create_date = mx.DateTime.DateFrom(create_date)
            if ac.create_date != create_date:
                ac.set_create_date(create_date)
        
        expire_date = account_info.get('expire_date',None)
        if expire_date:
            expire_date = mx.DateTime.DateFrom(expire_date)
        if ac.expire_date != expire_date:
            ac.expire_date = expire_date
            ac.write_db()


        # promote the account to posix if we have enough information
        if _is_posix(account_info):
            try:
                posix_user.clear()
                posix_user.find(ac.entity_id)
            except Errors.NotFoundError:
                self._promote_posix(account_info, ac)
            else:
                self._copy_posixuser(account_info, posix_user)

    def _make_account(self, account_info, ac, owner, np_type=None):
        
        ac.clear()
        try:
            ac.find_by_name(account_info['name'])
        except Errors.NotFoundError:
            uname = account_info['name']


        expire_date = account_info.get('expire_date',None)
        if expire_date:
            expire_date = mx.DateTime.DateFrom(expire_date)
        create_date = mx.DateTime.DateFrom(account_info.get('creation_date'))

        uid = account_info.get('unix_uid',None)
        
        if uid and uid == 0:
            # Accounts with uidNumber=0 should be of non-personal type. I.e. some odd system-user
            np_type = self.co.account_program
            # These users should have a group as owner, not person. FIXME

        self.logger.info('Adding new account %s on owner cerebrum-%s' % (uname,owner.entity_id))
        ac.populate(name=uname,
                    owner_type = owner.entity_type,
                    owner_id = owner.entity_id,
                    np_type = np_type,
                    creator_id = self.default_creator_id,
                    expire_date = expire_date)
        ac.create_date = create_date
        
        ac.write_db()
        
        if owner.entity_type == self.const.entity_person:
            for aff in owner.get_affiliations():
                ac.set_account_type(aff['ou_id'], aff['affiliation'])
                
        if _is_posix(account_info):
            self._promote_posix(account_info, ac)

        self._sync_account_password(account_info, ac)
        


    def sync_accounts(self,username=None,password_only=False, add_missing=False):
        """
        This method synchronizes all BDB accounts into Cerebrum.
        """
        global num_accounts
        self.logger.debug("Fetching accounts from BDB")

        accounts = self.bdb.get_accounts(username)

        for account in accounts:
            self.logger.debug('Syncronizing %s' % account['name'])
            try:
                self._sync_account(account,password_only, add_missing)
            except Exception, e:
                self.db.rollback()
                if show_traceback:
                    traceback.print_exc()
                self.logger.error('Syncronizing %s failed: %s' % (
                    account['name'], e))
            else:
                num_accounts += 1
                if dryrun:
                    self.db.rollback()
                    self.logger.debug('Rollback called. Changes omitted.')
                else:
                    self.db.commit()
                    self.logger.debug('Changes on %s commited to Cerebrum' % account['name'])
        self.logger.debug("%s accounts added or updated in sync_accounts." % str(num_accounts))
        return

        

    def sync_group_members(self):
        const=self.const

        oldprimary={}
        oldgroup={}
        self.logger.debug("Fetching data from Cerebrum")
        account_by_name = {}
        for n in self.ac.list_names(const.account_namespace):
            account_by_name[n['entity_name']] = n['entity_id']

        group_by_name = {}
        for n in self.group.list_names(const.group_namespace):
            group_by_name[n['entity_name']] = n['entity_id']
        
        for gm in self.group.search_members(member_filter_expired=False):
            if gm['member_type'] == self.const.entity_account:
                oldgroup.setdefault(gm['member_id'], set()).add(gm['group_id'])

        for pu in self.posix_user.list_posix_users():
            oldprimary[pu['account_id']]=pu['gid']

        bdbgroups=set()
        self.logger.debug("Fetching groups from BDB")
        for g in self.bdb.get_groups():
            groupname=self.group_clean_name(g['name'])
            if not group_by_name.has_key(groupname): continue
            bdbgroups.add(group_by_name[groupname])

        newprimary={}
        newgroup={}
        self.logger.debug("Fetching accounts/spread-groupmembers from BDB")
        for s in self.bdb.get_account_spreads():
            if not account_by_name.has_key(s['username']):
                #self.logger.warn("Groupmember: Account %s does not exist" % s['username'])
                continue
            account_id=account_by_name[s['username']]

            groupname=self.group_clean_name(s['groupname'])
            if not group_by_name.has_key(groupname):
                self.logger.warn("Groupmember: Group %s does not exist" % groupname)
                continue
            group_id=group_by_name[groupname]
            newgroup.setdefault(account_id, set()).add(group_id)

        bdbaccounts=set()
        self.logger.debug("Fetching account-groupmembers from BDB")
        for a in self.bdb.get_accounts():
            if not account_by_name.has_key(a['name']):
                #self.logger.warn("Groupmember: Account %s does not exist" % a['name'])
                continue
            account_id=account_by_name[a['name']]

            if not a.has_key('group'): continue
            groupname=self.group_clean_name(a['group'])
            if not account_by_name.has_key(groupname):
                self.logger.warn("Groupmember: Group %s does not exist" % groupname)
                continue
            group_id=group_by_name[groupname]
            newgroup.setdefault(account_id, set()).add(group_id)
            newprimary[account_id]=group_id

        # Only change groups actually in BDB.
        for account_id in oldgroup.keys():
            oldgroup[account_id] &= bdbgroups
            if not oldgroup[account_id]:
                del oldgroup[account_id]

        for account_id in oldprimary.keys():
            if not oldprimary[account_id] in bdbgroups:
                del oldprimary[account_id]

        modgroups = dictcompare(oldgroup, newgroup, union=True)

        modprimary = dictcompare(oldprimary, newprimary, union=True)
        # Only change primary group on cerebrum PosixUser accounts
        modprimary &= set(oldprimary.keys())

        modaccounts = modprimary | modgroups

        self.posix_group.clear()
        # The installation should have this group. Created by sync_group.
        self.posix_group.find_by_name('posixgroup')
        posix_group_id = self.posix_group.entity_id
        
        self.logger.info("Groupmember: Changing %d accounts",
                         len(modaccounts))
        for account_id in modaccounts:
            oldgr = oldgroup.get(account_id, set())
            newgr = newgroup.get(account_id, set())
            oldprigr=oldprimary.get(account_id)
            newprigr=newprimary.get(account_id, posix_group_id)
            self.logger.debug("Groupmember: updating account %s, primary %s->%s, groups (%s)->(%s)" %
                              (account_id, repr(oldprigr), repr(newprigr),
                               ", ".join([str(g) for g in oldgr]),
                               ", ".join([str(g) for g in newgr])))
            self.check_commit(self.group_members_mod_account,
                              account_id,
                              oldprigr,
                              newprigr,
                              oldgr - newgr,
                              newgr - oldgr,
                              msg=("changing memberships of account %d" %
                                   account_id))

    def group_members_mod_account(self, account_id, oldprimary, newprimary, delgroups, addgroups):
        pu=self.posix_user
        gr=self.group
        for group_id in addgroups:
            gr.clear()
            gr.find(group_id)
            gr.add_member(account_id)
            gr.write_db()
        if newprimary != oldprimary and oldprimary is not None:
            pu.clear()
            pu.find(account_id)
            pu.gid_id = newprimary
            pu.write_db()
        for group_id in delgroups:
            gr.clear()
            gr.find(group_id)
            gr.remove_member(account_id)
            gr.write_db()

    def sync_spreads_quarantines(self):
        const=self.const
        
        self.logger.debug("Fetching data from Cerebrum")

        ignorespreads = [int(self.const.Spread(s))
                         for s in getattr(cereconf, "BDB_IGNORESPREADS", [])]

        oldquarantines={}
        for q in self.ac.list_entity_quarantines(entity_types=const.entity_account):
            oldquarantines.setdefault(q['entity_id'], set()).add(int(q['quarantine_type']))

        oldspreads={}
        for s in self.ac.list_entity_spreads(entity_types=const.entity_account):
            if not int(s['spread']) in ignorespreads:
                oldspreads.setdefault(s['entity_id'], set()).add(int(s['spread']))
            
        account_by_name = {}
        for n in self.ac.list_names(const.account_namespace):
            account_by_name[n['entity_name']] = n['entity_id']
        
        self.logger.debug("Fetching accounts with spreads from BDB")

        newspreads = {}
        newquarantines = {}
        for s in self.bdb.get_account_spreads():
            if not account_by_name.has_key(s['username']):
                self.logger.warn("Spread: Account %s does not exist" % s['username'])
                continue
            account_id = account_by_name[s['username']]

            spread = self.spread_mapping[s['spread_name']]
            if spread is not None and not int(spread) in ignorespreads:
                newspreads.setdefault(account_id, set()).add(int(spread))

            if s['shell'] == '/bin/badpw':
                newquarantines.setdefault(account_id, set()).add(int(const.quarantine_svakt_passord))
            if s['shell'] == '/bin/sperret':
                if s['spread_name'] in ('oppringt', 'ansoppr'):
                    newquarantines.setdefault(account_id, set()).add(int(const.quarantine_remote))
                else:
                    newquarantines.setdefault(account_id, set()).add(int(const.quarantine_sperret))

        self.logger.debug("Spread: from %d to %d accounts with spreads" %
                          (len(oldspreads), len(newspreads)))

        self.logger.debug("Spread: from %d to %d accounts with quarantines" %
                          (len(oldquarantines), len(newquarantines)))

        modaccounts = dictcompare(oldspreads, newspreads, union=True)
        modaccounts |= dictcompare(oldquarantines, newquarantines, union=True)
        
        self.logger.debug("Spread: changing %d accounts" % len(modaccounts))

        for account in modaccounts:
            self.check_commit(self.spreads_quarantines_account,
                              account,
                              oldspreads.get(account, set()),
                              newspreads.get(account, set()),
                              oldquarantines.get(account, set()),
                              newquarantines.get(account, set()),
                              msg=("changing quarantines and spreads on %d" % account))

    def spreads_quarantines_account(self, account_id,
                                    oldspreads, newspreads,
                                    oldquarantines, newquarantines):
        self.ac.clear()
        self.ac.find(account_id)

        for q in oldquarantines - newquarantines:
            self.logger.info("Deleting quarantine %d from account cerebrum-%d", q, account_id)
            self.ac.delete_entity_quarantine(q)

        for q in newquarantines - oldquarantines:
            self.logger.info("Adding quarantine %d to account cerebrum-%d", q, account_id)
            self.ac.add_entity_quarantine(q, creator=self.initial_account,
                                          description="imported from BDB",
                                          start=mx.DateTime.now())

        for s in oldspreads - newspreads:
            self.logger.info("Deleting spread %d from account cerebrum-%d", s, account_id)
            self.ac.delete_spread(s)

        for s in newspreads - oldspreads:
            self.logger.info("Adding spread %d to account cerebrum-%d", s, account_id)
            self.ac.add_spread(s)

        
    def sync_email_domains(self):
        self.logger.debug("Fetching email-domains")
        domains = self.bdb.get_email_domains()
        for domain in domains:
            self._sync_email_domain(domain)
        return

    def _sync_email_domain(self,domain):
        self.logger.info("Syncronizing %s" % domain.get('email_domain'))
        ed=self.ed
        ed.clear()
        try:
            ed.find_by_domain(domain.get('email_domain'))
        except Errors.NotFoundError:
            description = "Domain imported from BDB"
            self.logger.info("Adding EmailDomain %s" % domain.get('email_domain'))
            ed.populate(domain.get('email_domain'),description)
            ed.write_db()
        else:
            self.logger.debug("EmailDomain %s already exists." % domain.get('email_domain'))
        if dryrun:
            self.db.rollback()
        else:
            self.db.commit()

    def sync_email(self):
        const = self.const
        
        self.logger.debug("Start syncing email addresses")
        
        self.logger.debug("Fetching data from Cerebrum")

        names = self.ac.list_names(const.account_namespace)
        account_by_name = {}
        for n in names:
            account_by_name[n['entity_name']] = n['entity_id']

        emaildomain_by_name = {}
        for d in self.ed.list_email_domains():
            emaildomain_by_name[d['domain']] = d['domain_id']

        emailserver_by_name = {}
        for s in self.es.list_email_server_ext():
            emailserver_by_name[s['name']] = s['server_id']

        emailserver_by_bdbsystem = {}
        for bdbsys,esrv in cereconf.BDB_EMAIL_SERVER.items():
            emailserver_by_bdbsystem[bdbsys] = emailserver_by_name[esrv]
        
        account_by_target = {}
        for t in self.et.list_email_targets_ext():
            account_by_target[t['target_id']] = (t['target_entity_id'],
                                                 t['server_id'])

        old_addrs = {}
        old_trgts = {}
        for a in self.ea.list_email_addresses_ext():
            if not account_by_target.has_key(a['target_id']):
                self.logger.error("Email: Target %d does not exist" %
                                  a['target_id'])
                continue
            account_id, server_id = account_by_target[a['target_id']]
            local_part = a['local_part']
            domain = a['domain']
            old_addrs[(local_part, domain)] = (account_id, False)
            old_trgts[(local_part, domain)] = a['target_id']

        for a in self.epat.list_email_target_primary_addresses():
            account_id = a['target_entity_id']
            local_part = a['local_part']
            domain = a['domain']
            server_id = a['server_id']
            old_addrs[(local_part, domain)] = (account_id, server_id)
            old_trgts[(local_part, domain)] = a['target_id']

        self.logger.debug("Fetching email addresses from BDB")
        addresses = self.bdb.get_email_addresses()
        
        aliases = self.bdb.get_email_aliases()

        new_addrs = {}
        for a in addresses:
            if not account_by_name.has_key(a['username']):
                self.logger.warn("Email: Account %s does not exist" %
                                 a.get('username'))
                continue
            account_id = account_by_name[a['username']]
            local_part = a['email_address']
            domain = a['email_domain_name']
            server_id = emailserver_by_bdbsystem.get(a['system'])
            new_addrs[(local_part, domain)] = (account_id, server_id)

        for a in aliases:
            if not account_by_name.has_key(a['username']):
                self.logger.warn("Email: Account %s does not exist" %
                                 a.get('username'))
                continue
            account_id = account_by_name[a['username']]
            local_part = a['email_address']
            domain = a['email_domain_name']
            server_id = emailserver_by_bdbsystem.get(a['system'])
            new_addrs[(local_part, domain)] = (account_id, False)
            
        self.logger.debug("Email: from %d to %d adresses" %
                          (len(old_addrs), len(new_addrs)))
        addk, modk, delk = dictcompare(old_addrs, new_addrs)
        self.logger.debug("Email: Adding %d changing %d deleting %d addresses"
                          % (len(addk), len(modk), len(delk)))

        for addr in addk | modk | delk:
            local_part, domain = addr
            if not emaildomain_by_name.has_key(domain):
                self.logger.error("Email: Emaildomain %s does not exist" %
                                  domain)
                continue
            domain_id = emaildomain_by_name[domain]
            oaccount_id, oprimary = old_addrs.get(addr, (None, False))
            otarget_id = old_trgts.get(addr, None)
            account_id, primary = new_addrs.get(addr, (None, False))
            msg=[]
            if oprimary != False:
                msg.append("deleting primary")
            if oaccount_id != account_id:
                if oaccount_id:
                    msg.append("deleting from account %s" % oaccount_id)
                if account_id:
                    msg.append("adding to account %s" % account_id)
            if primary != False:
                msg.append("adding primary")
            self.logger.debug("Email: %s@%s: %s" %
                              (local_part, domain, ", ".join(msg)))
            self.check_commit(self.email_addr_mod,
                              local_part, domain_id, domain,
                              account_id, primary,
                              oaccount_id, otarget_id, oprimary,
                              msg="syncing email address")

        self.logger.debug("Finished syncing email addresses")
        

    def email_addr_mod(self, local_part, domain_id, domain,
                       account_id, primary,
                       oaccount_id, otarget_id, oprimary):
        const = self.const
        addr = "%s@%s" % (local_part, domain)
        self.ea.clear()

        if account_id == oaccount_id:
            target_id = otarget_id
        elif account_id:
            self.et.clear()
            try:
                self.et.find_by_target_entity(account_id)
            except Errors.NotFoundError:
                self.logger.info("%s: making to new target" % addr)
                self.et.populate(const.email_target_account,
                                 target_entity_id=account_id,
                                 target_entity_type=const.entity_account)
                self.et.write_db()
            target_id = self.et.entity_id
            
        if otarget_id:
            self.ea.find_by_local_part_and_domain(local_part, domain_id)
            if oprimary != False and ( primary == False or
                                       otarget_id != target_id ):
                self.epat.clear()
                self.epat.find(otarget_id)
                if self.epat.email_primaddr_id == self.ea.entity_id:
                    self.logger.info("%s: removing primary" % addr)
                    self.epat.delete()
            if account_id and account_id != oaccount_id:
                self.logger.info("%s: assigning to new target" % addr)
                self.ea.email_addr_target_id = target_id
                self.ea.write_db()
            if account_id is None:
                self.logger.info("%s: deleting" % addr)
                self.ea.delete()
        else:
            self.logger.info("%s: creating" % addr)
            self.ea.populate(local_part, domain_id, target_id)
            self.ea.write_db()
        if primary != False:
            self.epat.clear()
            try:
                self.epat.find(target_id)
                if self.epat.email_primaddr_id != self.ea.entity_id:
                    self.logger.info("%s: making primary" % addr)
                    self.epat.email_primaddr_id = self.ea.entity_id
                if self.epat.email_server_id != primary:
                    self.logger.info("%s: changing email server" % addr)
                    self.epat.email_server_id = primary
            except Errors.NotFoundError:
                self.et.clear()
                self.et.find(target_id)
                self.epat.clear()
                self.epat.populate(self.ea.entity_id, parent=self.et)
                self.epat.email_server_id = primary
            self.epat.write_db()
        

def usage():
    print >>sys.stderr, """
    Usage: %s <options>

    Available options:

        --dryrun    (-d) Does not commit changes to Cerebrum
        --traceback      Show traceback of errors
        --people    (-p) Syncronize persons
        --group     (-g) Syncronise posixGrourp
        --account   (-a) Syncronize posixAccounts
        --spread    (-s) Syncronize account-spreads
        --affiliations (-t)   Syncronize affiliations on persons
        --email_domains       Syncronize email-domains
        --email_address (-e)  Syncronize email-addresses
        --verbose   (-v) Prints debug-messages to STDOUT
        --help      (-h)

        --personid       the BDB-id or the nssn of the person
        --accountname    the username of the user to import from BDB
        --password-only  To be used only with syncronization of all accounts or a given accountname

    """ % sys.argv[0]
    sys.exit(0)

def main():
    global verbose,dryrun
    opts,args = getopt.getopt(sys.argv[1:],
                    'dptgmasvhe',
                    ['email_alias','password-only','traceback','personid=','accountname=','spread','email_domains','email_address','affiliations','dryrun','people','group','account','groupmembers','compare-people', 'verbose','help'])

    sync = BDBSync()
    if (('--password-only','')) in opts:
        _password_only = True
    else:
        _password_only = False
    for opt,val in opts:
        if opt in ('-h','--help'):
            usage()
        elif opt in ('-v','--verbose'):
            verbose = True
        elif opt in ('-d','--dryrun'):
            dryrun = True
        elif opt in ('--traceback',):
            global show_traceback
            show_traceback = True
        elif opt in ('--personid',):
            # Konverter val til noe saklig
            print "Syncronizing BDBPerson: %s" % val
            if len(val) == 11:
                person = sync.bdb.get_persons(fdato=val[:6],pnr=val[6:])
            else:
                person = sync.bdb.get_persons(bdbid=val) 
            # person is now a list of one element (dict)
            if len(person) == 1:
                sync.check_commit(sync._sync_person, person[0])
            else:
                print "No person or too many persons match criteria. Exiting.."
            sys.exit()
        elif opt in ('--compare-people',):
            sync.compare_person_bdbids()
        elif opt in ('-p','--people'):
            sync.sync_persons()
        elif opt in ('-g','--group'):
            sync.sync_groups()
        elif opt in ('-m', '--groupmembers'):
            sync.sync_group_members()
        elif opt in ('-a','--account'):
            sync.sync_accounts(password_only=_password_only,add_missing=True)
        elif opt in ('-s','--spread'):
            sync.sync_spreads_quarantines()
        elif opt in ('-t','--affiliations'):
            sync.sync_affiliations()
        elif opt in ('--email_domains',):
            sync.sync_email_domains()
        elif opt in ('-e','--email_address'):
            sync.sync_email()
        elif opt in ('--password-only',):
            accounts = sync.bdb.get_accounts(last=30)
            for account in accounts:
                sync.check_commit(sync._sync_account, account,
                                  update_password_only=True,add_missing=True)
        elif opt in ('--accountname',):
            print "Syncronizing account: %s" % val
            sync.sync_accounts(username=val,password_only=_password_only,add_missing=True)
        else:
            usage()

if __name__ == '__main__':
    main()

