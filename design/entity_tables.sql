/*	entity_info

  When an entity is to be created within an installation, it is given
  a numeric ID -- an `entity_id'.  These IDs are generated using a
  single, entity-type-independent sequence.  They are purely internal,
  i.e. they should never in any way be exported outside this system.

  This table keeps track of which entity IDs are in use, and what type
  of entity each `entity_id' is connected to.

  Garbage collection: The data model can not ensure that there will
    actually exist an entry in the `entity_type'-specific table for
    all the `entity_id's in this table.  To reduce the amount of
    `entity_info' rows with no corresponding entity we need some kind
    of garbage collector.

  TBD: Need separate `entity_type's for
	* name reservations (to be kept in the `entity_name' table)
	* ldap DNs (to allow these to members of groups)

*/
CREATE SEQUENCE entity_id_seq;
CREATE TABLE entity_info
(
  entity_id	NUMERIC(12,0)
		CONSTRAINT entity_info_pk PRIMARY KEY,
  entity_type	CHAR VARYING(16)
		NOT NULL
		CONSTRAINT entity_info_entity_type
		  REFERENCES entity_type_code(code),
  CONSTRAINT entity_info_type_unique
    UNIQUE (entity_type, entity_id)
);


/*	entity_name



*/
CREATE TABLE entity_name
(
  entity_id	NUMERIC(12,0)
		CONSTRAINT entity_name_entity_id
		  REFERENCES entity_info(entity_id),
  value_domain	CHAR VARYING(16)
		CONSTRAINT entity_name_value_domain
		  REFERENCES value_domain_code(code),
  entity_name	CHAR VARYING(256)
		NOT NULL,
  CONSTRAINT entity_name_pk
    PRIMARY KEY (entity_id, value_domain),
  CONSTRAINT entity_name_unique_per_domain
    UNIQUE (value_domain, entity_name)
);


/*	entity_address

  The column `address_text' is a (near) free-form textual
  representation of the address, with '$' used to indicate newlines.

*/
CREATE TABLE entity_address
(
  entity_id	NUMERIC(12,0)
		CONSTRAINT entity_address_entity_id
		  REFERENCES entity_info(entity_id),
  source_system	CHAR VARYING(16)
		CONSTRAINT entity_address_source_system
		  REFERENCES authoritative_system_code(code),
  address_type	CHAR VARYING(16)
		CONSTRAINT entity_address_address_type
		  REFERENCES address_code(code),
  address_text	CHAR VARYING(256),
  p_o_box	CHAR VARYING(10),
  postal_number	CHAR VARYING(8),
  city		CHAR VARYING(128),
  country	CHAR VARYING(16)
		CONSTRAINT entity_address_country
		  REFERENCES country_code(code),
  CONSTRAINT entity_address_pk
    PRIMARY KEY (entity_id, source_system, address_type)
);


/*	entity_phone

  `phone_number' should contain no dashes/letters/whitespace, and
  should be fully specified.  Examples: "+4712345678" and "*12345".

  If there exists multiple `phone_number's of the same `phone_type'
  for an entity, the `phone_pref' column can be used to indicate an
  ordering between these `phone_number's; high `phone_pref' values are
  preferred.

  TBD: Do we really need a separate set of tables for phone number
       info?  That is, why can't phone info merely be treated as just
       another kind of "contact info"?

*/
CREATE TABLE entity_phone
(
  entity_id	NUMERIC(12,0)
		CONSTRAINT entity_phone_entity_id
		  REFERENCES entity_info(entity_id),
  source_system	CHAR VARYING(16)
		CONSTRAINT entity_phone_source_system
		  REFERENCES authoritative_system_code(code),
  phone_type	CHAR VARYING(16)
		CONSTRAINT entity_phone_phone_type
		  REFERENCES phone_code(code),
  phone_pref	NUMERIC(2,0)
		DEFAULT 50,
  phone_number	CHAR VARYING(20)
		NOT NULL,
  description	CHAR VARYING(512),
  CONSTRAINT entity_phone_pk
    PRIMARY KEY (entity_id, source_system, phone_type, phone_pref)
);


/*	entity_contact_info

  If there exists multiple `contact_value's of the same `contact_type'
  for an entity, the `contact_pref' column can be used to indicate an
  ordering between these `contact_values's; high `contact_pref' values
  are preferred.

*/
CREATE TABLE entity_contact_info
(
  entity_id	NUMERIC(12,0)
		CONSTRAINT entity_contact_info_entity_id
		 REFERENCES entity_info(entity_id),
  source_system	CHAR VARYING(16)
		CONSTRAINT entity_contact_info_source_sys
		  REFERENCES authoritative_system_code(code),
  contact_type	CHAR VARYING(16)
		CONSTRAINT entity_contact_info_cont_type
		  REFERENCES contact_info_code(code),
  contact_pref	NUMERIC(2,0)
		DEFAULT 50,
  contact_value	CHAR VARYING(255)
		NOT NULL,
  description	CHAR VARYING(512),
  CONSTRAINT entity_contact_info_pk
    PRIMARY KEY (entity_id, source_system, contact_type, contact_pref)
);


/*	entity_quarantine

  When `end_date' is NULL, the `entity_id' is quarantined
  indefinitely.

  Use the column `disable_until' to indicate that a quarantine should
  be lifted from now until the date in `disable_until'.  This is
  useful e.g. for giving users who have been quarantined for having
  too old passwords a limited time to change their password; in order
  to change their password they must use their old password, and this
  won't work when they're quarantined.

  Garbage collection: Remove rows where non-NULL `end_date' is in the
    past.

*/
CREATE TABLE entity_quarantine
(
  entity_id	NUMERIC(12,0)
		CONSTRAINT entity_quarantine_entity_id
		  REFERENCES entity_info(entity_id),
  quarantine_type
		CHAR VARYING(16)
		CONSTRAINT entity_quarantine_quar_type
		  REFERENCES quarantine_code(code),
  creator_id	NUMERIC(12,0)
		NOT NULL
		CONSTRAINT entity_quarantine_creator_id
		  REFERENCES account_info(account_id),
  description	CHAR VARYING(512),
  create_date	DATE
		DEFAULT SYSDATE
		NOT NULL,
  start_date	DATE
		NOT NULL,
  disable_until DATE,
  end_date	DATE,
  CONSTRAINT entity_quarantine_pk
    PRIMARY KEY (entity_id, quarantine_type)
);
