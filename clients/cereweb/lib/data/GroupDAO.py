import cerebrum_path
from mx import DateTime
from Cerebrum import Utils
from Cerebrum.Errors import NotFoundError
from Cerebrum.modules.bofhd.errors import PermissionDenied

Database = Utils.Factory.get("Database")
Group = Utils.Factory.get("Group")
PosixGroup = Utils.Factory.get("PosixGroup")

from lib.data.ConstantsDAO import ConstantsDAO
from lib.data.DTO import DTO
from lib.data.EntityDAO import EntityDAO
from lib.data.GroupDTO import GroupDTO
from lib.data.NoteDAO import NoteDAO
from lib.data.QuarantineDAO import QuarantineDAO
from lib.data.TraitDAO import TraitDAO

class GroupDAO(EntityDAO):
    EntityType = Group

    def get(self, id, include_extra=False):
        group = self._find(id)

        return self._create_dto(group, include_extra)

    def search(self, name):
        group = self._get_cerebrum_obj()
        name = name.strip("*") + '*'
        results = []
        for result in group.search(name=name):
            dto = DTO.from_row(result)
            dto.id = result.fields.group_id
            dto.type_name = self._get_type_name()
            results.append(dto)
        return results

    def get_by_name(self, name, include_extra=False):
        group = self._find_by_name(name)
        
        return self._create_dto(group, include_extra)

    def get_shallow(self, id):
        group = self._find(id)

        dto = GroupDTO()
        self._populate(dto, group)
        self._populate_posix(dto, group)
        self._populate_visibility(dto, group)
        return dto

    def get_groups_for(self, member_id):
        groups = []

        entity = self._get_cerebrum_obj()
        direct_groups = entity.search(member_id=member_id, filter_expired=False)
        for group in entity.search(member_id=member_id, indirect_members=True, filter_expired=False):
            dto = self._create_dto_from_search(group)
            dto.direct = group in direct_groups
            groups.append(dto)
        return groups

    def add_member(self, member_id, group_id):
        group = self._find(group_id)
        if not self.auth.can_edit_group_membership(self.db.change_by, group):
            raise PermissionDenied("No access to group")

        if not group.has_member(member_id):
            group.add_member(member_id)

    def remove_member(self, group_id, member_id):
        group = self._find(group_id)
        if not self.auth.can_edit_group_membership(self.db.change_by, group):
            raise PermissionDenied("No access to group")
        if group.has_member(member_id):
            group.remove_member(member_id)

    def promote_posix(self, id):
        group = self._find(id)
        if not self.auth.can_edit_group(self.db.change_by, group):
            raise PermissionDenied("No access to group")

        pgroup = PosixGroup(self.db)
        pgroup.populate(parent=group)
        pgroup.write_db()

    def demote_posix(self, id):
        pgroup = self._get_posix_group(id)
        if not self.auth.can_alter_group(self.db.change_by, pgroup):
            raise PermissionDenied("No access to group")

        pgroup.delete()

    def save(self, dto):
        group = self._find(dto.id)
        if not self.auth.can_alter_group(self.db.change_by, group):
            raise PermissionDenied("No access to group")

        group.group_name = dto.name
        group.description = dto.description
        group.expire_date = dto.expire_date or None
        group.visibility = self.constants.GroupVisibility(dto.visibility_value)
        
        self._save_posix(dto)
        group.write_db()

    def delete(self, group_id):
        group = self._find(group_id)
        if not self.auth.can_delete_group(self.db.change_by, group):
            raise PermissionDenied("No access to group")

        if self._is_posix(group_id):
            self.demote_posix(group_id)

        group.delete()

    def add(self, dto):
        if not self.auth.can_create_group(self.db.change_by):
            raise PermissionDenied("No access to group")

        group = Group(self.db)
        illegal_name = group.illegal_name(dto.name)
        if illegal_name:
            raise self.db.IntegrityError("Not a legal group-name")
        group.populate(
            self.db.change_by,
            self.constants.group_visibility_all,
            dto.name,
            dto.description,
            expire_date=dto.expire_date or None)
        group.write_db()
        dto.id = group.entity_id

    def _get_name(self, entity):
        return entity.get_name(self.constants.group_namespace)

    def _get_type(self):
         return self.constants.entity_group

    def _create_dto(self, group, include_extra=False):
        dto = GroupDTO()
        self._populate(dto, group)
        self._populate_posix(dto, group)
        self._populate_visibility(dto, group)

        if include_extra:
            dto.members = self._get_members(group)
            dto.quarantines = self._get_quarantines(group)
            dto.notes = self._get_notes(group)
            dto.spreads = self._get_spreads(group)
            dto.traits = self._get_traits(group)
            
        return dto

    def _create_dto_from_search(self, result):
        dto = DTO()
        dto.id = result.fields.group_id
        dto.name = result.fields.name
        dto.type_name = self._get_type_name()
        dto.type_id = self._get_type_id()
        dto.description = result.fields.description
        dto.is_posix = self._is_posix(result.fields.group_id)
        dto.create_date = result.fields.create_date
        dto.expire_date = result.fields.expire_date
        dto.is_expired = self._is_expired(dto.expire_date)

        return dto

    def _is_expired(self, expire_date):
        if not expire_date: return False
        return expire_date < DateTime.now()

    def _populate(self, dto, group):
        dto.id = group.entity_id
        dto.name = self._get_name(group)
        dto.description = group.description
        dto.type_name = self._get_type_name()
        dto.type_id = self._get_type_id()
        dto.is_expired = group.is_expired()
        dto.create_date = group.create_date
        dto.expire_date = group.expire_date

    def _is_posix(self, group_id):
        return self._get_posix_group(group_id) is not None
        
    def _populate_posix(self, dto, group):
        pgroup = self._get_posix_group(group.entity_id)
        dto.is_posix = pgroup is not None
        
        if not dto.is_posix:
            return

        dto.posix_gid = pgroup.posix_gid

    def _populate_visibility(self, dto, group):
        code = self.constants.GroupVisibility(group.visibility)
        dto.visibility_name = code.description
        dto.visibility_value = code.str

    def _save_posix(self, dto):
        if not dto.is_posix:
            return

        pgroup = self._get_posix_group(dto.id)
        pgroup.posix_gid = dto.posix_gid
        pgroup.write_db()

    def _get_posix_group(self, id):
        pgroup = PosixGroup(self.db)

        try:
            pgroup.find(id)
        except NotFoundError, e:
            return None

        return pgroup
        
    def _get_members(self, group):
        members = []
        for cerebrum_member in group.search_members(group_id=group.entity_id,
                                                    include_member_entity_name=True):
            member = DTO()
            member.id = cerebrum_member['member_id']
            member.type_id = cerebrum_member['member_type']
            member.type_name = self.constants.EntityType(member.type_id).str
            member.name = cerebrum_member['member_name']
            members.append(member)
        return members

    def _get_quarantines(self, group):
        return QuarantineDAO(self.db).create_from_entity(group)

    def _get_notes(self, group):
        return NoteDAO(self.db).create_from_entity(group)

    def _get_spreads(self, group):
        spreads = []
        const_dao = ConstantsDAO(self.db)
        for data in group.get_spread():
            sid = data['spread']
            dto = const_dao.get_spread(sid)
            spreads.append(dto)
        return spreads

    def _get_traits(self, group):
        return TraitDAO(self.db).create_from_entity(group)