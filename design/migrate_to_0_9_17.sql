/*
 * Copyright 2016 University of Oslo, Norway
 *
 * This file is part of Cerebrum.
 *
 * Cerebrum is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * Cerebrum is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cerebrum; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/* SQL script for migrating a 0.9.16 database to 0.9.17 */

/* First add precedence, and fill with nulls */
category:pre;
ALTER TABLE person_affiliation_source ADD COLUMN
    precedence NUMERIC(6,0) NULL DEFAULT NULL;

/* Migrate should now have filled with values */
category:post;
ALTER TABLE person_affiliation_source ALTER COLUMN
    precedence DROP DEFAULT;
category:post;
ALTER TABLE person_affiliation_source ALTER COLUMN
    precedence SET NOT NULL;
category:post;
ALTER TABLE person_affiliation_source
    ADD CONSTRAINT person_affiliation_source_p_u
    UNIQUE (person_id, precedence);
