from enum import Enum

from tippo import Protocol, TypeVar, Iterable, final


KT = TypeVar("KT")  # key type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type


@final
class MissingType(Enum):
    MISSING = "MISSING"


MISSING = MissingType.MISSING


@final
class DeletedType(Enum):
    DELETED = "DELETED"


DELETED = DeletedType.DELETED


@final
class SupportsKeysAndGetItem(Protocol[KT, VT_co]):
    def keys(self):
        # type: () -> Iterable[KT]
        pass

    def __getitem__(self, __k):
        # type: (KT) -> VT_co
        pass
