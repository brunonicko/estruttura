from enum import Enum


class MissingType(Enum):
    MISSING = "MISSING"


MISSING = MissingType.MISSING


class DeletedType(Enum):
    DELETED = "DELETED"


DELETED = DeletedType.DELETED
