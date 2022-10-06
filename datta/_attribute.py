from estruttura import Attribute
from tippo import Callable, TypeVar, cast


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class DataAttribute(Attribute[T_co]):
    """Data attribute."""

    __slots__ = ()


def getter(attribute, dependencies=()):
    # type: (T, tuple) -> Callable[[Callable[..., T]], Callable[..., T]]

    def decorator(func):
        return attribute.getter(*dependencies)(func)

    return decorator
