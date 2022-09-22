from tippo import TypeVar, Hashable

from estruttura import Relationship


T_co = TypeVar("T_co", covariant=True)  # covariant value type
IT = TypeVar("IT", bound=Hashable)  # internal type


class DataRelationship(Relationship[T_co]):
    """Data relationship."""

    __slots__ = ()
