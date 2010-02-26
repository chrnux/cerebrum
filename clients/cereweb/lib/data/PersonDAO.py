import cerebrum_path
from mx import DateTime
from Cerebrum import Utils
from Cerebrum.Errors import NotFoundError
from Cerebrum.modules.bofhd.errors import PermissionDenied

Database = Utils.Factory.get("Database")
Constants = Utils.Factory.get("Constants")
Person = Utils.Factory.get("Person")
OU_class = Utils.Factory.get("OU")

from lib.data.AccountDAO import AccountDAO
from lib.data.AffiliationDAO import AffiliationDAO
from lib.data.ConstantsDAO import ConstantsDAO
from lib.data.EntityDAO import EntityDAO
from lib.data.QuarantineDAO import QuarantineDAO
from lib.data.NoteDAO import NoteDAO
from lib.data.TraitDAO import TraitDAO
from lib.data.EntityDTO import EntityDTO
from lib.data.DTO import DTO

class PersonDAO(EntityDAO):
    EntityType = Person

    def get(self, id, include_extra=False):
        person = self._find(id)
        if not self.auth.can_read_person(self.db.change_by, person):
            raise PermissionDenied("Not authorized to view person")

        return self._create_dto(person, include_extra)

    def search(self, name, birth_date=None, person_id=None):
        name = name or None
        birth_date = birth_date or None
        person_id = person_id or None

        if name:
            name = name.rstrip("*") + '*'

        results = []
        name_variants = [self.constants.name_last, self.constants.name_first, self.constants.name_full]
        entity = self._get_cerebrum_obj()
        for result in entity.search(
                                        name=name,
                                        birth_date=birth_date,
                                        name_variants=name_variants,
                                        entity_id=person_id,
                                        exclude_deceased=True):
            dto = DTO.from_row(result)
            dto.id = dto.person_id
            dto.name = dto.full_name
            dto.type_name = self._get_type_name()
            dto.gender = self.constants.Gender(dto.gender)
            results.append(dto)
        return results

    def search_affiliated(self, ou_id, perspective_type, affiliation_type, recursive=False):
        p = Person(self.db)
        affiliation_type = affiliation_type and int(affiliation_type) or None

        ous = [int(ou_id)]
        if recursive:
            ou = OU_class(self.db)
            children = ou.list_children(int(perspective_type), entity_id=ou_id, recursive=True)
            ous.extend([c['ou_id'] for c in children])

        rows = p.list_affiliations(
                        affiliation=affiliation_type,
                        ou_id=ous)

        pids = [p.person_id for p in rows]
        people = dict(
            [(r.person_id, r) for r in self.search(name=None, person_id=pids)]
        )

        for row in rows:
            person = people[row.person_id]
            person.status = self.constants.PersonAffStatus(row['status'])

        return people.values()

    def get_accounts(self, *ids):
        if not ids:
            return []

        if len(ids) > 1:
            return AccountDAO(self.db).get_by_owner_ids(*ids)

        id = ids[0]

        person = self._find(id)
        account_ids = [a["account_id"] for a in person.get_accounts()]
        account_dtos = AccountDAO(self.db).get_accounts(*account_ids)
        primary_id = person.get_primary_account()
        for dto in account_dtos:
            dto.is_primary = dto.id == primary_id

        return account_dtos

    def get_affiliations(self, id):
        try:
            person = self._find(id)
        except NotFoundError, e:
            return []

        return self._get_affiliations(person)

    def create(self, dto):
        if not self.auth.can_create_person(self.db.change_by):
            raise PermissionDenied("Not authorized to create person")

        entity = self._get_cerebrum_obj()
        entity.populate(
            dto.birth_date,
            self.constants.Gender(dto.gender.id),
            dto.description)
        entity.affect_names(
            self.constants.system_manual,
            self.constants.name_first,
            self.constants.name_last)
        entity.populate_name(
            self.constants.name_first,
            dto.first_name)
        entity.populate_name(
            self.constants.name_last,
            dto.last_name)
        entity.write_db()

        dto.id = entity.entity_id

    def delete(self, person_id):
        person = self._find(person_id)
        if not self.auth.can_delete_person(self.db.change_by, person):
            raise PermissionDenied("Not authorized to delete person")

        dto = self._create_dto(person, False)
        person.delete()
        return dto

    def add_affiliation_status(self, person_id, ou_id, status):
        person = self._find(person_id)
        status = self.constants.PersonAffStatus(status)

        if not self.auth.can_edit_affiliation(
                self.db.change_by, person, ou_id, status.affiliation):
            raise PermissionDenied("Not authorized to edit affiliations")

        source = self.constants.AuthoritativeSystem("Manual")
        person.add_affiliation(ou_id, status.affiliation, source, status)
        person.write_db()

    def remove_affiliation_status(self, person_id, ou_id, status_id, ss):
        person = self._find(person_id)
        status = self.constants.PersonAffStatus(status_id)

        if not self.auth.can_edit_affiliation(
                self.db.change_by, person, ou_id, status.affiliation):
            raise PermissionDenied("Not authorized to edit affiliations")

        source = self.constants.AuthoritativeSystem(int(ss))
        person.delete_affiliation(ou_id, status.affiliation, source)
        person.write_db()

    def add_birth_no(self, person_id, birth_no):
        person = self._find(person_id)
        external_id_type = "NO_BIRTHNO"
        if not self.auth.can_edit_external_id(self.db.change_by, person, external_id_type):
            raise PermissionDenied("Not authorized to edit birth number")

        self.add_external_id(person_id, birth_no, "NO_BIRTHNO")

    def add_name(self, person_id, name_type, name):
        entity = self._find(person_id)
        if not self.auth.can_edit_person(self.db.change_by, entity):
            raise PermissionDenied("Not authorized to edit person")

        name_type = self.constants.PersonName(name_type)

        entity.affect_names(self.constants.system_manual, name_type)
        entity.populate_name(name_type, name)
        entity.write_db()

    def remove_name(self, person_id, name_type, source_system):
        entity = self._find(person_id)
        if not self.auth.can_edit_person(self.db.change_by, entity):
            raise PermissionDenied("Not authorized to edit person")

        name_type = self.constants.PersonName(name_type)
        source = self.constants.AuthoritativeSystem(source_system)

        if not source == self.constants.system_manual:
            raise PermissionDenied("Not authorized to delete name")
        
        entity.affect_names(self.constants.system_manual, name_type)
        entity.write_db()

    def save(self, dto):
        entity = self._find(dto.id)
        if not self.auth.can_edit_person(self.db.change_by, entity):
            raise PermissionDenied("Not authorized to edit person")

        entity.gender = self.constants.Gender(dto.gender.id)
        entity.birth_date = dto.birth_date
        entity.description = dto.description
        entity.deceased_date = dto.deceased_date

        entity.write_db()

    def _get_affiliations(self, entity):
        return AffiliationDAO(self.db).create_from_person_affiliations(entity.get_affiliations(include_deleted=True))

    def _get_name(self, entity):
        return entity.get_name(self.constants.system_cached, self.constants.name_full)

    def _get_names(self, entity):
        names = {}

        for name in entity.get_all_names():
            key = "%s:%s" % (name['name_variant'], name['name'])
            if not key in names:
                dto = DTO()
                dto.id = name['person_id']
                dto.value = name['name']
                dto.variant = ConstantsDAO(self.db).get_name_type(name['name_variant'])
                dto.source_systems = []
                names[key] = dto

            dto = names[key]
            source_system = ConstantsDAO(self.db).get_source_system(name['source_system'])
            if not source_system in dto.source_systems:
                dto.source_systems.append(source_system)
        return names.values()

    def _get_type(self):
        return self.constants.entity_person

    def _create_dto(self, person, include_extra):
        dto = DTO()
        self._populate(dto, person)
        if include_extra:
            dto.quarantines = QuarantineDAO(self.db).create_from_entity(person)
            dto.affiliations = self._get_affiliations(person)
            dto.names = self._get_names(person)
            dto.external_ids = self._get_external_ids(person)
            dto.contacts = self._get_contacts(person)
            dto.addresses = self._get_addresses(person)
            dto.notes = NoteDAO(self.db).create_from_entity(person)
            dto.traits = TraitDAO(self.db).create_from_entity(person)

        return dto

    def _populate(self, dto, person):
        dto.id = person.entity_id
        dto.name = self._get_name(person)
        dto.description = person.description
        dto.type_name = self._get_type_name()
        dto.type_id = self._get_type_id()
        dto.gender = self._get_gender(person)
        dto.birth_date = person.birth_date
        dto.deceased_date = person.deceased_date
        dto.is_deceased = self._is_deceased(person)

    def _is_deceased(self, person):
        if not person.deceased_date: return False
        return person.deceased_date < DateTime.now()

    def _get_gender(self, person):
        return ConstantsDAO(self.db).get_gender(person.gender)