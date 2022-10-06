from estruttura import Attribute
from tippo import TypeVar


T_co = TypeVar("T_co", covariant=True)


class DataAttribute(Attribute[T_co]):
    """Data attribute."""

    __slots__ = ()
