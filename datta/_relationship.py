from tippo import TypeVar
from estruttura import Relationship


T_co = TypeVar("T_co", covariant=True)  # covariant value type


class DataRelationship(Relationship[T_co]):
    """Data relationship."""

    __slots__ = ()
