/*

Konvensjoner:

 * Fors�ker � f�lge ANSI SQL ('92, uten at jeg helt vet forskjellen p�
   denne og '99); dette betyr f.eks. at "CHAR VARYING" brukes i stedet
   for Oracle-datatypen "VARCHAR2", selv om begge disse er
   implementert identisk i Oracle.

 * Kolonner som er hele prim�rn�kkelen i en tabell, har ofte samme
   navn som tabellen + suffikset "_key".  Kun kolonner som er hele
   prim�rn�kkelen i tabellen sin har dette suffikset.

 * N�r det refereres til en _key-kolonne har kolonnen som inneholder
   referansen alts� IKKE navn med suffiks _key (da referanse-kolonnen
   ikke alene er prim�rn�kkel i tabellen det refereres fra).

 * Alle _key-kolonner bruker type NUMERIC(12,0), alts� et heltall med
   maks 12 sifre.

 * For alle tabeller med en _key-kolonne finnes det en sekvens med
   samme navn som _key-kolonnen.  Ved innlegging av nye data i en slik
   tabell skal _key-kolonnen f� sin verdi hentet fra denne
   sekvensen.NEXTVAL (for � unng� race conditions).

 * Vi benytter ikke cascading deletes, da dette vil v�re lite
   kompatibelt med at ymse personer "fikser litt" direkte i SQL.

*/

/***********************************************************************
   Tables for defining user accounts.
 ***********************************************************************/

/*

Data assosiert direkte med en enkelt konto:

 * Eier							== 1

   Kontoen _m�_ ha en eier; dette kan enten v�re en
   person, eller en IT-gruppe (det siste kun for
   upersonlige konti, siden disse ikke eies av�noen
   person :-).

 * Kontotype						1..N

   Kontotype bestemmes av et sett med affiliations.
   Alle disse m� tilh�re den samme eieren (person
   eller IT-gruppe), slik at en konto kun kan ha
   typer avledet av sin egen eier.

   For upersonlige konti (som alts� eies av en
   gruppe) m� det settes n�yaktig en konto-type.

 * Brukernavn						1..N

   NoTuR vil, s� vidt jeg har skj�nt, at vi skal ta
   h�yde for f�lgende rariteter:

   * Enhver konto f�r tildelt minst ett
     "hjemme"-brukernavn ved opprettelse.  Dette
     brukernavnet er til bruk internt p� brukerens
     egen institusjon.

   * Internt p� brukerens egen institusjon (alts�
     _ikke_ i NoTuR-sammenheng) har
     hjemme-brukernavnet en Unix UID det st�r
     hjemme-institusjonen helt fritt � velge.

   * I det kontoen skal inn i en NoTuR-sammenheng
     skjer f�lgende:

     * Kontoen bruker en egen NoTuR-spesifikk Unix
       UID.  Denne er den samme uansett hvilken
       NoTuR-site man opererer p�.

     * Kontoen _kan_ m�tte bruke andre brukernavn
       for � autentisere seg, da man pre-NoTuR hadde
       opprettet separate sett med brukernavn ved
       hver enkelt NoTuR-site.

    Site	Brukernavn	UID
	"Hjemme"
    UiO		hmeland		29158
	Noen andre ble NoTuR-bruker med
	UiO-brukernavn "hmeland" f�r hmeland.
    NoTuR/UiO	hameland	51073
	Brukeren som har f�tt NoTur-brukernavn
	"hmeland" ved UiO har kanskje f�tt sitt
	�nskede hjemme-brukernavn, "haraldme", p�
	NTNU -- men dette var opptatt ved NoTuR/UiO.
    NoTuR/NTNU	hmeland		51073
    NoTuR/UiB
    NoTuR/UiT

   Foresl�r at dette l�ses ved:

   * Mulighet til � reservere brukernavn i kjernen
     (uten at de n�dvendigvis er tilknyttet noen
     bruker i ureg2000).

   * Egen modul for NoTuR-opplegget, som s�rger for
     � mappe fra "hjemme"-brukernavn til
     NoTuR-brukernavn for riktig site i de
     situasjonenen dette trengs.

 * Autentiseringsdata					0..N

   Om det ikke finnes _noen_ autentiseringsentries
   for en konto, betyr det at man ikke _kan_
   autentisere seg som denne kontoen (og ikke at
   hvem som helst er pre-autentisert som den
   kontoen, i.e. et tomt passord :-).

   En konto kan maks ha en entry
   pr. autentiseringstype.

   type			X.509, MD5, DES
   identifikator	hmeland@foo, NULL, NULL
   private		0x..., NULL, NULL
   public		0x.-.., md5-crypt, DES-crypt

 * Hjemmeomr�de						0..1
   Noen typer bruker har ikke noe assosiert
   hjemmeomr�de i det hele tatt, mens i andre
   sammenhenger b�r det kunne knyttes separate
   hjemmeomr�der til hver av de brukernavnene
   kontoen har.

   (I NoTuR-sammenheng kan ogs� samme brukernavn ha
   forskjellig hjemmeomr�de, alt etter hvilken site
   brukernavnet brukes ved, men dette tas h�nd om i
   den NoTuR-spesifikke modulen)

 * Sperring (potensielt flere samtidige, potensielt	0..N
   med forskjellig prioritet)

   Sperring kan ogs� skje p� person-niv� (type
   karantene); disse vil da affektere alle kontoene
   personen eier.

   Hver enkelt konto-sperring vil ha tilsvarende
   effekt i _alle_ kontekster der kontoen er kjent.
   Sperring p� kontekst-niv� m� gj�res ved � fjerne
   aktuell spread.

 * Aktiv/slettet (b�r ligge en stund med alle		0..1
   tabell-entries intakt, men flagget som
   slettet, for � lett kunne gj�re restore).

   Dersom vi hadde hatt datostempel for alle
   medlemmers innmeldelse i grupper, kunne dette ha
   blitt implementert som (nok) en gruppe.  Det har
   vi ikke, og vil nok heller ikke ha, s� dermed
   fremst�r gruppe-implementasjon ikke som noen lur
   m�te � gj�re dette p�.

 * Spread (hvilke systemer skal kontoen v�re		0..N
   kjent i)
   Implementeres vha. grupper med egen nomenklatur
   for gruppenavnene.

   Ved fjerning av spread en spread er det opp til
   hver enkelt eksportmodul � evt. flagge tidspunkt
   for forsvinningen, slik at man unng�r "sletting"
   etterfulgt av gjenoppretting (i systemer der
   dette er veldig dumt).

 * Unix UID						0..N

 * Unix prim�rgruppe					0..N

 * Unix shell						0..N

 * Printerkvote						0..N
   Har/har ikke, ukekvote, maxkvote, semesterkvote.

 * Mailadresser						0..N

 * Plassering i organisasjon (stedkode)			== 1

 * Opprettet av						== 1

   Kontoen som foretok opprettelsen.  Konti som er
   registrert som "oppretter" kan ikke fjernes (men
   kan markeres som inaktive).

 * Opprettet dato					== 1

 * Ekspirasjonsdato					0..1

 * LITA(-gruppe) som er ansvarlig kontakt for		== 1
   brukeren

*/


/*	account

Konto kan v�re tilknyttet en person.  Kontoens type indikerer hvorvidt
kontoen kan v�re upersonlig; integriteten av dette tas h�nd om utenfor
SQL.

Konto kan ha forskjellig brukernavn i forskjellige kontekster, men
alle disse skal til enhver tid kunne autentisere seg p� (de) samme
m�te(ne).

Hvert brukernavn (kontekst?) kan ha tilknyttet et eget hjemmeomr�de.

 * "User" is an Oracle reserved word, so we're probably better off if
 * we avoid using that as a table or column name.  Besides, "account"
 * probably is the more accurate term anyway.

 np_type: Account type for non-personal accounts.  For personal
          accounts there's a separate user_type table.

 */
CREATE TABLE account
(
  /* Dummy column, needed for type check against `entity_id'. */
  entity_type	CHAR VARYING(16)
		NOT NULL
		DEFAULT 'u'
		CONSTRAINT account_entity_type_chk CHECK (entity_type = 'u'),

  account_id	NUMERIC(12,0)
		CONSTRAINT account_pk PRIMARY KEY,
  owner_type	CHAR VARYING(16)
		NOT NULL
		CONSTRAINT account_owner_type_chk
		  CHECK (owner_type IN ('p', 'g')),
  owner		NUMERIC(12,0)
		NOT NULL,
  np_type	CHAR VARYING(16)
		CONSTRAINT account_np_type REFERENCES account_code(code),
  create_date	DATE
		DEFAULT SYSDATE
		NOT NULL,
  creator	NUMERIC(12,0)
		NOT NULL
		CONSTRAINT account_creator REFERENCES account(account_id),
  expire_date	DATE
		DEFAULT NULL,
  deleted	CHAR(1)
		NOT NULL
		CONSTRAINT account_deleted_bool
		  CHECK (deleted IN ('T', 'F')),
  CONSTRAINT account_entity_id FOREIGN KEY (entity_type, account_id)
    REFERENCES entity_id(entity_type, id),
  CONSTRAINT account_owner FOREIGN KEY (owner_type, owner)
    REFERENCES entity_id(entity_type, id),
  CONSTRAINT account_np_type_chk
    CHECK ((owner_type = 'p' AND np_type IS NULL) OR
	   (owner_type = 'g' AND np_type IS NOT NULL)),
  CONSTRAINT account_id_plus_owner_unique UNIQUE (account_id, owner)
);


/*	account_type

  Indicate which of the owner's affiliations a specific `account' is
  meant to cover.

  Keeping foreign keys involving person_id against both
  `person_affiliation' and `account' (which in turn has a foreign key
  against `person') ensures that all affiliations connected to a
  specific (personal) user_account belongs to the same person.

*/
CREATE TABLE account_type
(
  person_id	NUMERIC(12,0),
  ou_id		NUMERIC(12,0),
  affiliation	CHAR VARYING(16),
  user_id	NUMERIC(12,0),
  CONSTRAINT account_type_pk
    PRIMARY KEY (person_id, ou_id, affiliation, user_id),
  CONSTRAINT account_type_affiliation
    FOREIGN KEY (person_id, ou_id, affiliation)
    REFERENCES person_affiliation(person_id, ou_id, affiliation),
  CONSTRAINT account_type_user
    FOREIGN KEY (user_id, person_id)
    REFERENCES account(account_id, owner)
);


/*	authentication_code



*/
CREATE TABLE authentication_code
(
  code		CHAR VARYING(16)
		CONSTRAINT authentication_code_pk PRIMARY KEY,
  description	CHAR VARYING(512)
		NOT NULL
);


/*	account_authentication

  Keep track of the data needed to authenticate each account.

  TBD:

   * `method_data' is currently as large as Oracle will allow a "CHAR
     VARYING" column to be.  Is that large enough, or should we use a
     completely different data type?  The column should probably be at
     least large enough to hold one X.509 certificate (or maybe even
     several).

   * Should the auth_data column be split into multiple columns,
     e.g. for "private" and "public" data?

   * Password history (i.e. don't allow recycling of passwords); this
     should be implemented as an optional add-on module.

*/
CREATE TABLE account_authentication
(
  account_id	NUMERIC(12,0)
		CONSTRAINT account_authentication_account_id
		  REFERENCES account(account_id),
  method	CHAR VARYING(16)
		CONSTRAINT account_authentication_method
		  REFERENCES authentication_code(code),
  auth_data	CHAR VARYING(4000)
		NOT NULL,
  CONSTRAINT account_auth_pk PRIMARY KEY (account_id, method)
);


/*	reserved_name

  Generic name reservation table.  Value_domain can indicate what kind
  of name (username, groupname, etc.) it is that's being reserved,
  what kind of system the name is being reserved on (Unix, Windows,
  Notes, etc.), and so on -- the exact partitioning of value spaces is
  done in the value_domain_code table.

  TBD: Denne m�ten � gj�re navne-reservasjon p� er s�pass generell at
       det blir vanskelig � skrive constraints som sikrer at et navn
       ikke kan finnes b�de i reservasjons- og definisjons-tabellen
       (alts� f.eks. b�de som reservert og aktivt brukernavn).

       Dersom man skal kunne legge slike skranker i databasen, ender
       man gjerne opp med � m�tte ha b�de reserverte og aktive navn i
       samme tabell, og bruke en egen kolonne i denne tabellen for �
       indikere om det dreier seg om en reservasjon eller
       registrering.  Dette vil igjen f�re til nye problemer dersom
       man skal lage foreign keys mot en slik tvetydig navne-kolonne.

*/
CREATE TABLE reserved_name
(
  value_domain	CHAR VARYING(16)
		CONSTRAINT reserved_name_value_domain
		  REFERENCES value_domain_code(code),
  name		CHAR VARYING(128),
  why		CHAR VARYING(512)
		NOT NULL,
  CONSTRAINT reserved_name_pk PRIMARY KEY (value_domain, name)
);
