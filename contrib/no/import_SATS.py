#!/usr/bin/env python2.2

import cerebrum_path

import pprint
import string
import sys

from Cerebrum import Errors
from Cerebrum import Person
from Cerebrum.Utils import Factory
from Cerebrum.modules.no import fodselsnr


pp = pprint.PrettyPrinter(indent=4)

Cerebrum = Factory.get('Database')()
co = Factory.get('Constants')(Cerebrum)
OU_class = Factory.get('OU')

source_system = co.system_sats
school2ouid = {}

def read_inputfile(filename):
    print "Processing %s" % filename
    f = open(filename, 'rb')
    spec = f.readline().strip().split(",")
    ret = []
    nlegal = nillegal = 0
    while 1:
        line = f.readline()
        if line == '': break
        
        dta = line.strip().split(",")
        if(len(dta) != len(spec)):
            # print "WARNING: Illegal line: '%s'" % line
            nillegal += 1
            continue
        nlegal += 1
        ret += [dta, ]
    print "Result: %i / %i" % (nlegal, nillegal)
    return (spec, ret)

def save_outputfile(filename, hdr, lst):
    """Save outputfile in a sorted format without duplicates or
    errenous lines """
    lst.sort(lambda a,b: cmp(",".join(a), ",".join(b)))
    prev = None
    f = open(filename, 'wb')
    f.write(",".join(hdr) + "\n")
    for t in lst:
        if prev <> t:
            f.write(",".join(t) + "\n")
        prev = t
    f.close()

def read_extra_person_info(ptype, level, schools):
    """Returns format_spec, dict{'oid': [[person_info]]}."""

    if ptype == 'l�rer':
        fname = 'person_ansatt_l�rere_%s.txt' % level
    elif ptype == 'admin':
        fname = 'person_ansatt_ikkeL�rer_%s.txt' % level
    elif ptype == 'elev':
        fname = 'person_elev_ekstra_opplys_%s.txt' % level

    spec, dta = read_inputfile("sats/%s" % fname)
    n = 0
    schoolcode_pos = None
    for k in spec:
        if(k.lower() == 'schoolcode'):
            schoolcode_pos = n
        n += 1
    ret = {}
    for t in dta:
        if not (t[schoolcode_pos] in schools):
            continue
        ret[t[0]] = ret.get(t[0], []) + [t[1:],]
    return spec[1:], ret

def populate_people(level, type, pspec, pinfo):
    print "Populating %i entries of type %s" % (len(pinfo), type)
    if type == 'elev':
        fname = 'person_elev_%s.txt' % level
        oidname = 'elevoid'
    elif type == 'admin' or type == 'l�rer':
        fname = 'person_ansatt_%s.txt' % level
        oidname = 'ansattoid'
    else:
        fname = 'person_foreldre_%s.txt' % level
        oidname = 'parentfid'
        elevoids2group = pinfo
        print "# elever %i" % len(elevoids2group.keys())
    spec, dta = read_inputfile("sats/%s" % fname)
    # Create mapping of locname to locid
    loc = {}
    n = 0
    for k in spec:
        loc[k.lower()] = n
        n += 1
    ploc = {}
    n = 0
    for k in pspec:
        ploc[k.lower()] = n
        n += 1
    ret = {}
    # Process all people in the input-file
    for p in dta:
        if type == 'foreldre':
            if not elevoids2group.has_key(p[loc['childfid']]):
                continue
        elif not (pinfo.has_key(p[loc[oidname]])):
            continue                          # Skip unknown person
        sys.stdout.write('.')
        sys.stdout.flush()

        # find all affiliations and groups for this person
        affiliations = []
        groups = {}
        if type == 'foreldre':
            h = elevoids2group[p[loc['childfid']]]
            for k in h.keys():
                k.replace('_elev', '_foreldre')
                groups[k] = 1
        else:
            for extra in pinfo[p[loc[oidname]]]:
                school = extra[ploc['schoolcode']]
                affiliations += [school, ]
                if type == 'elev':
                    groups["%s_%s_%s" % (school, extra[ploc['klassekode']], type)] = 1
                elif type == 'l�rer':
                    groups["%s_%s_%s" % (school, extra[ploc['elevgruppekode']], type)] = 1
            
        try:
            p_id = update_person(p, loc, type, affiliations, groups.keys())
            ret[p[loc[oidname]]] = groups
        except:
            print "WARNING: Error importing %s" % p[loc[oidname]]
            pp.pprint ((p, loc, type, affiliations, groups.keys() ))
            raise
    return ret

def do_all():
    schools = {'gs': ('VAHL', ), # 'JORDAL'),
               'vg': ('ELV', )}

    school2ouid = import_OU(schools)
    for level in schools.keys():

        espec, elev_info =  read_extra_person_info('elev', level, schools[level])
        elevoids2group = populate_people(level, 'elev', espec, elev_info)

        # Populate parents for the already imported students
        elevoid2entity_id = populate_people(level, 'foreldre', [], elevoids2group)

        tspec, teacheriod2info = read_extra_person_info('l�rer', level, schools[level])
        populate_people(level, 'l�rer', tspec, teacheriod2info)

        aspec, adminoid2info = read_extra_person_info('admin', level, schools[level])
        populate_people(level, 'ansatt', aspec, adminoid2info)

    # fordel � legge inn �pning for foreldre->barn rolle-mapping
    Cerebrum.commit()

def update_person(p, loc,type, affiliations, groupnames):
    """Create or update the persons name, address and contact info.

    TODO: Also set affiliation
    """
    person = Person.Person(Cerebrum)
    gender = co.gender_female
    if p[loc['sex']] == '1':
        gender = co.gender_male
    date = None
    try:
        day, mon, year = [int(x) for x in p[loc['birthday']].split('.')]
        date = Cerebrum.Date(year, mon, day)
    except:
        warn("\nWARNING: Bad date %s for %s" % (p[loc['birthday']],
                                                 p[loc['personoid']]))
    if p[loc['firstname']] == '' or p[loc['lastname']] == '':
        warn("\nWARNING: bad name for %s" % p[loc['personoid']])
        return

    person.clear()
    try:
        person.find_by_external_id(co.externalid_personoid,
                                   p[loc['personoid']])
    except Errors.NotFoundError:
        pass
    person.populate(date, gender)
    person.affect_names(source_system, co.name_first, co.name_last)
    person.populate_name(co.name_first, p[loc['firstname']])
    person.populate_name(co.name_last, p[loc['lastname']])
    if p[loc['socialsecno']] <> '':
        person.populate_external_id(source_system, co.externalid_fodselsnr,
                                    p[loc['socialsecno']])
    else:
        warn("\nWARNING: no ssid for %s" % p[loc['personoid']])
    person.populate_external_id(source_system, co.externalid_personoid,
                                p[loc['personoid']])

    op = person.write_db()
##     if op is None:
##         print "**** EQUAL ****"
##     elif op == True:
##         print "**** NEW ****"
##     elif op == False:
##         print "**** UPDATE ****"

    if op <> True:          # TODO: handle update/equal
        return person.entity_id

    try:
        postno, city = string.split(p[loc['address3']], maxsplit=1)
        if postno.isdigit():
            person.add_entity_address(source_system, co.address_post,
                                      address_text=p[loc['address1']],
                                      postal_number=postno, city=city)
        else:
            warn("\nWARNING: Bad address for %s" % p[loc['personoid']])
    except ValueError:
        warn("\nWARNING: Bad address for %s" % p[loc['personoid']])
        
    if p[loc['phoneno']] <> '':
        person.add_contact_info(source_system, co.contact_phone, p[loc['phoneno']])
    if p[loc['faxno']] <> '':
        person.add_contact_info(source_system, co.contact_fax, p[loc['faxno']])
    if p[loc['email']] <> '':
        person.add_contact_info(source_system, co.contact_email, p[loc['email']])
    return person.entity_id

def import_OU(schools):
    """Registers or updates information about all schools listed in the
    'schools' dict."""   # TODO: handle update
                         #       handle location in tree
    
    ou = OU_class(Cerebrum)
    ret = {}         # Python *****: can't declare a variable as local
    for level in schools.keys():
        spec, dta = read_inputfile("sats/sted_%s.txt" % level)
        loc = {}
        n = 0
        for k in spec:
            loc[k.lower()] = n
            n += 1
        for skole in dta:
            if not (skole[loc['institutioncode']] in schools[level]):
                continue
            sys.stdout.write('.')
            sys.stdout.flush()
            ou.clear()

            ou.populate(skole[loc['name']],
                        acronym=skole[loc['institutioncode']][:15],
                        short_name=skole[loc['institutioncode']][:30],
                        display_name=skole[loc['name']],
                        sort_name=skole[loc['name']])
            ou.write_db()
            ret["%s:%s" % (level, skole[loc['institutioncode']])] = ou.entity_id

            if skole[loc['address3']] == '': # or skole[loc['address1']] == '':
                print "\nWARNING: Bad info for %s" % skole[loc['name']]
                pp.pprint(skole)
            else:
                postno, city = skole[loc['address3']].split()
                ou.add_entity_address(source_system, co.address_post,
                                      address_text=skole[loc['address1']],
                                      postal_number=postno, city=city)
            if skole[loc['phoneno']] <> '':
                ou.add_contact_info(source_system, co.contact_phone, skole[loc['phoneno']])
            if skole[loc['faxno']] <> '':
                ou.add_contact_info(source_system, co.contact_fax, skole[loc['faxno']])
        Cerebrum.commit()
        print
    return ret

def convert_all():
    files = ("sted_vg.txt", "klasse_fag_emne_gs.txt",
             "klasse_fag_emne_vg.txt", "person_ansatt_gs.txt",
             "person_ansatt_ikkeL�rer_gs.txt",
             "person_ansatt_ikkeL�rer_vg.txt",
             "person_ansatt_l�rere_gs.txt",
             "person_ansatt_l�rere_vg.txt",
             "person_ansatt_vg.txt",
             "person_elev_ekstra_opplys_gs.txt",
             "person_elev_ekstra_opplys_vg.txt",
             "person_elev_gs.txt", "person_elev_vg.txt",
             "person_foreldre_gs.txt", "person_foreldre_vg.txt",
             "sted_gs.txt", "sted_vg.txt")
    
    for f in files:
        spec, ret = read_inputfile("sats/%s" % f)
        save_outputfile(f, spec, ret)

def warn(msg):
    # print "WARNING: %s" % msg
    pass

def main():
    do_all()

if __name__ == '__main__':
    main()
