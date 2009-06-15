from lib.data.ConstantsDTO import ConstantsDTO
import cerebrum_path
from Cerebrum import Utils
from Cerebrum.Errors import NotFoundError
Database = Utils.Factory.get("Database")
Constants = Utils.Factory.get("Constants")
Person = Utils.Factory.get("Person")

def get_group_spreads():
    dao = ConstantsDAO()
    return dao.get_group_spreads()

def get_group_visibilities():
    dao = ConstantsDAO()
    return dao.get_group_visibilities()

def get_email_target_types():
    return ConstantsDAO().get_email_target_types()

class ConstantsDAO(object):
    def __init__(self, db=None):
        if db is None:
            db = Database()
        self.constants = Constants(db)

    def get_group_visibilities(self):
        names = self._get_names("group_visibility_")
        return self._get_constant_dtos(names, Constants.GroupVisibility)

    def get_group_spreads(self):
        names = self._get_names("spread_")
        for c in self._get_constants(names, Constants.Spread):
            if not c.entity_type == self.constants.entity_group:
                continue

            yield ConstantsDTO(c)

    def get_email_target_types(self):
        names = self._get_names("email_target_")
        return self._get_constant_dtos(names, Constants.EmailTarget)

    def get_quarantine(self, id):
        q = self.constants.Quarantine(id)
        return ConstantsDTO(q)

    def _get_constant_dtos(self, names, filter_type=None):
        for c in self._get_constants(names, filter_type):
            yield ConstantsDTO(c)

    def _get_constants(self, names, filter_type=None):
        for c in [getattr(self.constants, n) for n in names]:
            if filter_type is None or isinstance(c, filter_type):
                yield c

    def _get_names(self, str):
        return [n for n in dir(self.constants) if n.startswith(str)]
