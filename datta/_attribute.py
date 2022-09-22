from estruttura import Attribute
from tippo import TypeVar

T_co = TypeVar("T_co", covariant=True)  # covariant value type


class DataAttribute(Attribute[T_co]):
    """Data attribute."""

    __slots__ = ()
