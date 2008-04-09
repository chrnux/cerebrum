#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import getopt, sys
import xmlrpclib
import cerebrum_path
import cereconf

from Cerebrum.Utils import Factory
from Cerebrum import Entity
from Cerebrum.modules import ADutilMixIn

db = Factory.get('Database')()
co = Factory.get('Constants')(db)
logger = Factory.get_logger("cronjob")



class ADfuSync(ADutilMixIn.ADuserUtil):
    def __init__(self, *args, **kwargs):
        super(ADfuSync, self).__init__(*args, **kwargs)
        self.person = Factory.get('Person')(self.db)
        self.qua = Entity.EntityQuarantine(self.db)
        self.ou =  Factory.get('OU')(self.db)

    def fetch_cerebrum_data(self, spread):
        """For all accounts that has spread, returns a list of dicts with
        the keys: uname, fullname, account_id, person_id, host_name
        """

        #Fetch the mapping person_id to full_name.
        pid2name = self.person.getdict_persons_names(name_types=(co.name_full,
                                                                 co.name_first,
                                                                 co.name_last))
        self.logger.info("Fetched %i person names" % len(pid2name))
        #Hack OU-akronym.
        id2ou = {1561 : {'acronym' : 'KONG'},
                 1558 : {'acronym' : 'ALN'},
                 1559 : {'acronym' : 'GIS'},
                 1560 : {'acronym' : 'GOD'},
                 1562 : {'acronym' : 'SKJ'},
                 1563 : {'acronym' : 'VBS'},
                 1564 : {'acronym' : 'VUS'},
                 1565 : {'acronym' : 'VIG'}} 
        #Fetching OUid2name mapping.
        for row in self.ou.list_all():
            if id2ou.has_key(row['ou_id']):
                id2ou[row['ou_id']]['name'] = row['name']
        self.logger.info("Fetched %i OUs" % len(id2ou))

        accinfo = {}
        miss_OU = 0

        #Fetching accountinfo with AD-spread sorting on affiliation and OU.
        for row in self.ac.list_accounts_by_type(account_spread=spread):
            #No defined affiliation for l�rer.
            if row['affiliation'] == co.affiliation_ansatt or row['affiliation'] == co.affiliation_teacher:
                accinfo[row['account_id']] = {'OU' : 'OU=TILSETTE,%s' % cereconf.AD_LDAP,
                                              'title' : 'Tilsett',
                                              'url' : ['https://portal.skule.giske.no/skule/%s/tilsette'
                                                       % id2ou[row['ou_id']]['acronym']],
                                              #Constraint i AD, homeMDB must be valid LDAP path.  
                                              'homeMDB' : 'CN=Tilsette (LOMVI),CN=Storage Group,CN=InformationStore,CN=LOMVI,CN=Servers,CN=First Administrative Group,CN=Administrative Groups,CN=Giske grunnskule,CN=Microsoft Exchange,CN=Services,CN=Configuration,DC=skule,DC=giske,DC=no'}
            else:
                if id2ou.has_key(row['ou_id']):
                    accinfo[row['account_id']] = {'OU' : 'OU=ELEVER,OU=%s,%s' %
                                                  (id2ou[row['ou_id']]['acronym'], cereconf.AD_LDAP),
                                                  'title' : 'Elev',
                                                  'url' : ['https://portal.skule.giske.no/skule/%s/elever'
                                                           % id2ou[row['ou_id']]['acronym']],
                                                  #Constraint i AD, homeMDB must be valid LDAP path.	  
                                                  'homeMDB' : 'CN=Elever (LOMVI),CN=Storage Group,CN=InformationStore,CN=LOMVI,CN=Servers,CN=First Administrative Group,CN=Administrative Groups,CN=Giske grunnskule,CN=Microsoft Exchange,CN=Services,CN=Configuration,DC=skule,DC=giske,DC=no'}
                else:
                    miss_OU = miss_OU + 1
                    #self.logger.info('%s missing OU info, skipping' % row['account_id'])
                    continue
            if id2ou.has_key(row['ou_id']):
                accinfo[row['account_id']]['department'] = unicode(id2ou[row['ou_id']]['name'],
                                                                   'ISO-8859-1')
            if pid2name.has_key(row['person_id']):
                accinfo[row['account_id']]['sn'] = unicode(pid2name[row['person_id']][int(co.name_last)],
                                                           'ISO-8859-1')
                accinfo[row['account_id']]['givenName'] = unicode(pid2name[row['person_id']][int(co.name_first)],
                                                                  'ISO-8859-1')
                accinfo[row['account_id']]['displayName'] = unicode(pid2name[row['person_id']][int(co.name_full)],
                                                                    'ISO-8859-1')
        self.logger.info("Fetched %i accounts with AD spread" % len(accinfo))
        self.logger.info('%i accounts missing OU info' % miss_OU)
        pid2name = None 
				
        #Filter quarantined users.
        qcount = 0
        for row in self.qua.list_entity_quarantines(only_active=True,
                                                    entity_types=co.entity_account):
            if not accinfo.has_key(int(row['entity_id'])):
                continue
            else:
                accinfo[int(row['entity_id'])]['ACCOUNTDISABLE'] = True
                qcount = qcount +1
        self.logger.info("Fetched %i quarantined accounts" % qcount)

        #Building return.
        retur = {}
		
        for row in self.ac.list_names(co.account_namespace):
            e_name = row['entity_name']
            if accinfo.has_key(row['entity_id']):
                retur[e_name] = accinfo[row['entity_id']]
                retur[e_name]['company'] = 'Giske kommune'
                retur[e_name]['co'] = 'Norway'
                retur[e_name]['homeDrive'] = cereconf.AD_HOME_DRIVE
                retur[e_name]['userPrincipalName'] = '%s@skule.giske.no' % e_name
                retur[e_name]['mailNickname'] = e_name
                retur[e_name]['mDBUseDefaults'] = True
                #Constraint in AD, must be a valid dn in AD.
                retur[e_name]['msRTCSIP-PrimaryHomeServer'] = 'CN=LC Services,CN=Microsoft,CN=skule01,CN=Pools,CN=RTC Service,CN=Microsoft,CN=System,DC=skule,DC=giske,DC=no'
                #Filtering roles on title field defined earlier.
                if retur[e_name]['title'] == 'Elev':
                    retur[e_name]['profilePath'] = '\\\\vipe\\profiler\\%s' % e_name
                    retur[e_name]['homeDirectory'] = '\\\\vipe\\elever\\%s' % e_name
                    retur[e_name]['msRTCSIP-PrimaryUserAddress'] = 'SIP:%s@skule.giske.no' % e_name
                elif retur[e_name]['title'] == 'Tilsett':
                    retur[e_name]['profilePath'] = '\\\\spurv\\profiler\\%s' % e_name
                    retur[e_name]['homeDirectory'] = '\\\\spurv\\tilsette\\%s' % e_name
                    retur[e_name]['msRTCSIP-PrimaryUserAddress'] = 'SIP:%s@skule.giske.no' % e_name
                else:
                    self.logger.info("unknown title field: %s" % retur[e_name]['title'])
                if accinfo[int(row['entity_id'])].has_key('ACCOUNTDISABLE'):
                    #The Account field is present, account disabled.
                    retur[e_name]['msExchHideFromAddressList'] = True
                    retur[e_name]['msRTCSIP-UserEnabled'] = False
                else:
                    #Missing ACCOUNTDISABLE field, not disabled.
                    retur[e_name]['ACCOUNTDISABLE'] = False
                    retur[e_name]['msExchHideFromAddressLists'] = False
                    retur[e_name]['msRTCSIP-UserEnabled'] = True
        return retur

    def create_object(self, chg, dry_run):
        #CreateUser mixin overides version in ADutilMixIn class.
        if chg.has_key('OU'):
            ou = chg['OU']
        else:
            ou = self.get_default_ou(chg)
        ret = self.run_cmd('createObject', dry_run, 'User', ou,
                           chg['sAMAccountName'])
        if not ret[0]:
            self.logger.warning("create user %s failed: %r", chg['sAMAccountName'],
                                ret)
        else:
            if not dry_run:
                self.logger.info("created user %s", ret)

        pw = unicode(self.ac.make_passwd(chg['sAMAccountName']),
                     'iso-8859-1')

        ret = self.run_cmd('setPassword', dry_run, pw)
        if not ret[0]:
            self.logger.warning("setPassword on %s failed: %s", chg['sAMAccountName'],
                                ret)
        else:
            #Important not to enable a new account if setPassword
            #fail, it will have a blank password.
            uname = ""
            del chg['type']
            if chg.has_key('distinguishedName'):
                del chg['distinguishedName']
            if chg.has_key('sAMAccountName'):
                uname = chg['sAMAccountName']       
                del chg['sAMAccountName']               

            #Setting default for undefined AD_ACCOUNT_CONTROL values.
            for acc, value in cereconf.AD_ACCOUNT_CONTROL.items():
                if not chg.has_key(acc):
                    chg[acc] = value                
            ret = self.run_cmd('putProperties', dry_run, chg)
            if not ret[0]:
                self.logger.warning("putproperties on %s failed: %r", uname,
                                    ret)
            ret = self.run_cmd('setObject', dry_run)
            if not ret[0]:
                self.logger.warning("setObject on %s failed: %r", uname,
                                    ret)
            else:
                #Additonal lines below that overided create method in Adfusync class.
                #So far so good, setObject worked, now create homedir, profileDir
                #and exchangeaccount.
                ret = self.run_cmd('createDir', dry_run)
                if not ret[0]:
                    self.logger.warning("createDir on %s failed: %r", uname, ret)
                else:
                    #Checking existence of homedir.
                    ret = self.run_cmd('checkDir', dry_run)
                    if not ret:
                        self.logger.warning("HomeDir for %s not found: %r", uname, ret)

                ret = self.run_cmd('createDir', dry_run, 'profilePath')						
                if not ret[0]:
                    self.logger.warning("createDir on %s failed: %r", uname, ret)
                else:	
                    #Checking existence of profileDir.
                    ret = self.run_cmd('checkDir', dry_run, "profilePath")
                    if not ret:
                        self.logger.warning("ProfileDir for %s not found: %r", uname,
                                                ret)
                #Creating mailbox in Exchange
                ret = self.run_cmd('createMDB', dry_run)
                if not ret[0]:
                    self.logger.warning("Create exchange mailbox for %s failed: %r", uname,
                                         ret)

class ADfgSync(ADutilMixIn.ADgroupUtil):
    #Groupsync
    def __init__(self, *args, **kwargs):
        super(ADfgSync, self).__init__(*args, **kwargs)
		
    def get_default_ou(self, change = None):
        #Returns default OU in AD.
        return "OU=GRUPPER,%s" % cereconf.AD_LDAP

    def fetch_cerebrum_data(self, spread):		
        all_groups = []
        for (grp_id, grp, description) in self.group.search(spread):
            all_groups.append((grp_id, grp.replace(':','_'), description))
        return all_groups

def usage(exitcode=0):
    print """Usage:
    [--user_sync | --group_sync]
    [--delete_objects]
    [--disk_spread spread] 
    [--user_spread spread]
    [--dry_run]
    [--help]
    """
    sys.exit(exitcode)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], '', ['user_sync',
                                                      'group_sync',
                                                      'delete_objects',
                                                      'user_spread',
                                                      'group_spread',
                                                      'help',
                                                      'dry_run'])

    except getopt.GetoptError:
        usage(1)

    delete_objects = False
    user_spread = co.spread_ad_acc
    group_spread = co.spread_ad_grp
    dry_run = False	
    user_sync = False
    group_sync = False
	
    for opt, val in opts:
        if opt == '--delete_objects':
            delete_objects = True
        elif opt == '--user_sync':
            user_sync = True
        elif opt == '--group_sync':
            group_sync = True
        elif opt == '--disk_spread':
            disk_spread = getattr(co, val)  # TODO: Need support in Util.py
        elif opt == '--user_spread':
            user_spread = getattr(co, val)  # TODO: Need support in Util.py
        elif opt == '--group_spread':
            group_spread = getattr(co, val)  # TODO: Need support in Util.py
        elif opt == '--help':
            usage(1)
        elif opt == '--dry_run':
            dry_run = True

    if user_sync:
        ADfullUser = ADfuSync(db, co, logger)	
        try:
            ADfullUser.full_sync('user', delete_objects,
                                 user_spread, dry_run)
        except xmlrpclib.ProtocolError, xpe:
            logger.critical("Error connecting to AD service. Giving up: %s %s" %
                            (xpe.errcode, xpe.errmsg))

    if group_sync:
        ADfullGroup = ADfgSync(db, co, logger)
        try:
            ADfullGroup.full_sync('group', delete_objects,
                                  group_spread, dry_run, user_spread)
        except xmlrpclib.ProtocolError, xpe:
            logger.critical("Error connecting to AD service. Giving up: %s %s" %
                            (xpe.errcode, xpe.errmsg))

if __name__ == '__main__':
    main()
