#!/usr/bin/env python2.2

import re
import os
import sys
from Cerebrum import cereconf

from modules.no.uio.access_LT import LT
from Cerebrum import Database,Errors
from Utils import XMLHelper

default_stedfile = "/u2/dumps/LT/sted.dat.2"
default_personfile = "/u2/dumps/LT/person.dat.2"

cereconf.DATABASE_DRIVER='Oracle'
Cerebrum = Database.connect(user="ureg2000", service="LTKURS.uio.no")
LT = LT(Cerebrum)
xml = XMLHelper()

def get_sted_info():
    f=open(default_stedfile, 'w')
    f.write(xml_hdr + "<data>\n")

    cols, steder = LT.GetSteder();
    for s in steder:
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'sted', 0) + "\n")
        cols2, komm = LT.GetStedKomm(s['fakultetnr'], s['instituttnr'], s['gruppenr'])
        for k in komm:
            f.write(xml.xmlify_dbrow(k, xml.conv_colnames(cols2), 'komm') + "\n")
        f.write("</sted>\n")
    f.write("</data>\n")

def get_person_info():
    """Henter info om alle personer i LT som er av interesse.
    Ettersom opplysningene samles fra flere datakilder, lagres de
    først i en dict persondta"""

    skode2tittel = {}
    for t in LT.GetTitler()[1]:
        skode2tittel[t['stillingkodenr']] = (t['tittel'], t['univstkatkode'])

    kate2hovedkat = {}
    for t in LT.GetHovedkategorier()[1]:
        kate2hovedkat[t['univstkatkode']] = t['hovedkatkode']

    f=open(default_personfile, 'w')
    f.write(xml_hdr + "<data>\n")
    tilscols, tils = LT.GetTilsettinger()
    persondta = {}
    for t in tils:
        # f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'tils', 0) + "\n")
        key = '-'.join((str(t['fodtdag']), str(t['fodtmnd']), str(t['fodtar']), str(t['personnr'])))
        if not persondta.has_key(key):
            persondta[key] = {}
        persondta[key]['tils'] = persondta[key].get('tils', []) + [t]

    # $tid er siste entry i lønnsposterings-cache. TODO
    tid = '20020601'
    lonnscols, lonnspost = LT.GetLonnsPosteringer(tid)
    for lp in lonnspost:
        key = '-'.join((str(lp['fodtdag']), str(lp['fodtmnd']), str(lp['fodtar']),
                        str(lp['personnr'])))
        if not persondta.has_key(key):
            persondta[key] = {}
        persondta[key]['bil'] = persondta[key].get('bil', []) + [
            "%02d%02d%02d" % (lp['fakultetnr_kontering'], lp['instituttnr_kontering'],
                              lp['gruppenr_kontering'])]

    for p in persondta.keys():
        fodtdag, fodtmnd, fodtar, personnr = p.split('-')
        picols, pi = LT.GetPersonInfo(fodtdag, fodtmnd, fodtar, personnr)
        f.write(xml.xmlify_dbrow(pi[0],  xml.conv_colnames(picols), 'person', 0,
                              extra_attr={'fodtdag': fodtdag, 'fodtmnd':fodtmnd,
                                          'fodtar':fodtar, 'personnr': personnr}) + "\n")
        tlfcols, tlf = LT.GetTelefon(fodtdag, fodtmnd, fodtar, personnr)
        for t in tlf:
            f.write(xml.xmlify_dbrow(t,  xml.conv_colnames(tlfcols), 'arbtlf') + "\n")

        kcols, komm = LT.GetKomm(fodtdag, fodtmnd, fodtar, personnr)
        for k in komm:
            f.write(xml.xmlify_dbrow(k,  xml.conv_colnames(kcols), 'komm') + "\n")

        for t in persondta[p].get('tils', ()):
            # Unfortunately the oracle driver returns
            # to_char(dato_fra,'yyyymmdd') as key for rows, so we use
            # indexes here :-(
            attr = " ".join(["%s=%s" % (tilscols[i], xml.escape_xml_attr(t[i]))
                             for i in (4,5,6,7,8,9,10,11, )])
            if t['stillingkodenr_beregnet_sist'] is not None:
                sk = skode2tittel[t['stillingkodenr_beregnet_sist']]
                attr += ' hovedkat=%s' % xml.escape_xml_attr(
                    kate2hovedkat[sk[1]])
                attr += ' tittel=%s' % xml.escape_xml_attr(sk[0])
                f.write("<tils "+attr+"/>\n")

        prev = ''
        persondta[p].get('bil', []).sort()
        for t in persondta[p].get('bil', []):
            if t == prev:
                continue
            f.write('<bilag stedkode="%s"' % t + "/>\n")
            prev = t
        f.write("</person>\n")

    f.write("</data>\n")

def main():
    get_sted_info()
    get_person_info()

if __name__ == '__main__':
    main()
