CREATE TABLE mail_domain
(
  domain_name	CHAR VARYING(128),

/* TBD: �nsker � kunne legge inn innslag her om domener uten at det
	n�dvendigvis eksporteres noe data om dem til epostsystemet.
	Er det n�dvendig med muligheter for registrering av flere
	opplysninger rundt dette, s� som "starttidspunkt som lokalt
	domene", "tidspunkt for n�r domenet sluttet/vil slutte � v�re
	lokalt domene", etc.? */
  local		BOOLEAN
		NOT NULL,
  description	CHAR VARYING(512),
  PRIMARY KEY domain_name
);

/* TBD: Flere tabeller om mail. */
