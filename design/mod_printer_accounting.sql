/* TBD: B�r printerkvoter legges p� brukere eller personer, eller b�r
	man kanskje til og med ha mulighet for � legge innslag begge
	steder (og hvilke konsekvenser f�r i s� fall det for hvordan
	logikken rundt m� se ut)? */

/* TBD: Generaliseres til en entity_printer_quota-tabell. */
CREATE TABLE printer_quota
(
  person_id	NUMERIC(12,0)
		CONSTRAINT printer_quota_person_id
		  REFERENCES person(person_id),
  account_id	NUMERIC(12,0)
		CONSTRAINT printer_quota_account_id
		  REFERENCES account(account_id),
  active	BOOLEAN,
/* TBD: B�r vi splitte ut kolonnene under i en annen tabell, slik at
	det kun blir ett "active"-flagg for � si om en person/bruker
	har aktiv(e) printerkvotesettinger eller ei? */
  value_type	CHAR VARYING(16)
		REFERENCES printer_quota_value_code(code),
  value		NUMERIC(6,0)
		NOT NULL,
  PRIMARY KEY(person_id, value_type)
/* eller */
  PRIMARY KEY(account_id, value_type)
);
