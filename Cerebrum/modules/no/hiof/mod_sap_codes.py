# -*- coding: iso8859-1 -*-
#
# Copyright 2007 University of Oslo, Norway
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

"""
This file provides code values to be used with Hi�f's SAP extension to
Cerebrum -- mod_sap.
"""

from Cerebrum import Constants
from Cerebrum.modules.no.Constants import SAPForretningsOmradeKode, \
                                          SAPLonnsTittelKode, \
                                          SAPPermisjonsKode



class SAPConstants(Constants.Constants):
    """
    This class embodies all constants that we need to address HR-related
    tables in HiA.
    """

    # ----[ SAPForretningsOmradeKode ]----------------------------------
    sap_remmen = SAPForretningsOmradeKode(
        "0110",
        "Remmen - Halden"
    )

    sap_violgaten = SAPForretningsOmradeKode(
        "0115",
        "Violgaten - Halden"
    )

    sap_tune = SAPForretningsOmradeKode(
        "0120",
        "Tune - Sarpsborg"
    )

    sap_krakeroy = SAPForretningsOmradeKode(
        "0130",
        "Kr�ker�y - Fredrikstad",
    )
    
    sap_gamlebyen = SAPForretningsOmradeKode(
        "0135",
        "Gamlebyen - Fredrikstad",
    )

    sap_sykehuset = SAPForretningsOmradeKode(
        "0140",
        "Sykehuset - T�nsberg",
    )


    # ----[ SAPLonnsTittelKode ]----------------------------------
    sap_1004_rektor = SAPLonnsTittelKode(
        "20001004",
        "1004 Rektor",
        "�VR"
    )

    sap_1006_edb_sjef = SAPLonnsTittelKode(
        "20001006",
        "1006 EDB-sjef",
        "�VR"
    )

    sap_1007_hogskolelaerer_ovings = SAPLonnsTittelKode(
        "20001007",
        "1007 H�gskolel�rer/�vings",
        "�VR"
    )

    sap_1008_hogskolelektor = SAPLonnsTittelKode(
        "20001008",
        "1008 H�gskolelektor",
        "VIT"
    )

    sap_1010_amanuensis = SAPLonnsTittelKode(
        "20001010",
        "1010 Amanuensis",
        "VIT"
    )

    sap_1011_forsteamanuensis = SAPLonnsTittelKode(
        "20001011",
        "1011 F�rsteamanuensis",
        "VIT"
    )


    sap_1013_professor = SAPLonnsTittelKode(
        "20001013",
        "1013 Professor",
        "VIT"
    )

    sap_1017_stipendiat = SAPLonnsTittelKode(
        "20001017",
        "1017 Stipendiat",
        "VIT"
    )

    sap_1018_vitenskapelig_assistent = SAPLonnsTittelKode(
        "20001018",
        "1018 Vitenskapelig assistent",
        "VIT"
    )

    sap_1054_kontorsjef = SAPLonnsTittelKode(
        "20001054",
        "1054 Kontorsjef",
        "�VR"
    )

    sap_1059_underdirektor = SAPLonnsTittelKode(
        "20001059",
        "1059 Underdirekt�r",
        "�VR"
    )

    sap_1060_avdelingsdirektor = SAPLonnsTittelKode(
        "20001060",
        "1060 Avdelingsdirekt�r",
        "�VR"
    )

    sap_1062_direktor = SAPLonnsTittelKode(
        "20001062",
        "1062 Direkt�r",
        "�VR"
    )

    sap_1063_forstesekretaer = SAPLonnsTittelKode(
        "20001063",
        "1063 F�rstesekret�r",
        "�VR"
    )

    sap_1065_konsulent = SAPLonnsTittelKode(
        "20001065",
        "1065 Konsulent",
        "�VR"
    )

    sap_1069_forstefullmektig = SAPLonnsTittelKode(
        "20001069",
        "1069 F�rstefullmektig",
        "�VR"
    )

    sap_1070_sekretaer = SAPLonnsTittelKode(
        "20001070",
        "1070 Sekret�r",
        "�VR"
    )

    sap_1072_arkivleder = SAPLonnsTittelKode(
        "20001072",
        "1072 Arkivleder",
        "�VR"
    )

    sap_1077_hovedbibliotekar = SAPLonnsTittelKode(
        "20001077",
        "1077 Hovedbibliotekar",
        "�VR"
    )

    sap_1078_betjent = SAPLonnsTittelKode(
        "20001078",
        "1078 Betjent",
        "�VR"
    )

    sap_1083_ingenior = SAPLonnsTittelKode(
        "20001083",
        "1083 Ingeni�r",
        "�VR"
    )

    sap_1085_avdelingsingenior = SAPLonnsTittelKode(
        "20001085",
        "1085 Avdelingsingeni�r",
        "�VR"
    )

    sap_1087_overingenior = SAPLonnsTittelKode(
        "20001087",
        "1087 Overingeni�r",
        "�VR"
    )

    sap_1091_tekniker = SAPLonnsTittelKode(
        "20001091",
        "1091 Tekniker",
        "�VR"
    )

    sap_1113_prosjektleder = SAPLonnsTittelKode(
        "20001113",
        "1113 Prosjektleder",
        "�VR"
    )

    sap_1129_renholdsbetjent = SAPLonnsTittelKode(
        "20001129",
        "1129 Renholdsbetjent",
        "�VR"
    )

    sap_1130_renholder = SAPLonnsTittelKode(
        "20001130",
        "1130 Renholder",
        "�VR"
    )

    sap_1136_driftstekniker = SAPLonnsTittelKode(
        "20001136",
        "1136 Driftstekniker",
        "�VR"
    )

    sap_1183_forsker = SAPLonnsTittelKode(
        "20001183",
        "1183 Forsker",
        "VIT"
    )

    sap_1198_forstelektor = SAPLonnsTittelKode(
        "20001198",
        "1198 F�rstelektor",
        "VIT"
    )

    sap_1199_universitetsbibliote = SAPLonnsTittelKode(
        "20001199",
        "1199 Universitetsbibliote",
        "VIT"
    )

    sap_1213_bibliotekar = SAPLonnsTittelKode(
        "20001213",
        "1213 Bibliotekar",
        "�VR"
    )

    sap_1216_driftsoperator = SAPLonnsTittelKode(
        "20001216",
        "1216 Driftsoperat�r",
        "�VR"
    )

    sap_1275_ingenior = SAPLonnsTittelKode(
        "20001275",
        "1275 Ingeni�r",
        "�VR"
    )

    sap_1362_laerling = SAPLonnsTittelKode(
        "20001362",
        "1362 L�rling",
        "�VR"
    )

    sap_1363_seniorkonsulent = SAPLonnsTittelKode(
        "20001363",
        "1363 Seniorkonsulent",
        "�VR"
    )

    sap_1407_avdelingsleder = SAPLonnsTittelKode(
        "20001407",
        "1407 Avdelingsleder",
        "�VR"
    )

    sap_1408_forstekonsulent = SAPLonnsTittelKode(
        "20001408",
        "1408 F�rstekonsulent",
        "�VR"
    )

    sap_1434_radgiver = SAPLonnsTittelKode(
        "20001434",
        "1434 R�dgiver",
        "�VR"
    )

    sap_1474_dekan = SAPLonnsTittelKode(
        "20001474",
        "1474 Dekan",
        "�VR"
    )

    sap_1475_instituttleder = SAPLonnsTittelKode(
        "20001475",
        "1475 Instituttleder",
        "�VR"
    )

    sap_1515_bibliotekar = SAPLonnsTittelKode(
        "20001515",
        "1515 Bibliotekar",
        "�VR"
    )

# end SAPConstants
