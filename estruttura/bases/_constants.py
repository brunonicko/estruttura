from enum import Enum

from tippo import Protocol, TypeVar, Iterable


KT = TypeVar("KT")  # key type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type


class MissingType(Enum):
    MISSING = "MISSING"


MISSING = MissingType.MISSING


class DeletedType(Enum):
    DELETED = "DELETED"


DELETED = DeletedType.DELETED


class SupportsKeysAndGetItem(Protocol[KT, VT_co]):
    def keys(self):
        # type: () -> Iterable[KT]
        pass

    def __getitem__(self, __k):
        # type: (KT) -> VT_co
        pass
