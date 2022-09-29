import abc

import six
import slotted
from basicco import BaseMeta, Base
from tippo import TypeVar, Iterator


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class StructureMeta(BaseMeta, slotted.SlottedABCMeta):
    """Metaclass for :class:`Structure`."""


class Structure(six.with_metaclass(StructureMeta, Base, slotted.SlottedABC)):
    """Non-hashable by default."""

    __slots__ = ()

    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__qualname__)
        raise TypeError(error)


# Set as non-hashable.
type.__setattr__(Structure, "__hash__", None)


class HashableStructure(Structure, slotted.SlottedHashable):
    """Forces implementation of `__hash__` method."""

    __slots__ = ()

    @abc.abstractmethod
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()


class SizedStructure(Structure, slotted.SlottedSized):
    """Forces implementation of `__len__` method."""

    __slots__ = ()

    # noinspection PyProtocol
    @abc.abstractmethod
    def __len__(self):
        # type: () -> int
        raise NotImplementedError()


class IterableStructure(Structure, slotted.SlottedIterable[T_co]):
    """Forces implementation of `__iter__` method."""

    __slots__ = ()

    @abc.abstractmethod
    def __iter__(self):
        # type: () -> Iterator[T_co]
        raise NotImplementedError()


class ContainerStructure(Structure, slotted.SlottedContainer[T_co]):
    """Forces implementation of `__contains__` method."""

    __slots__ = ()

    @abc.abstractmethod
    def __contains__(self, content):
        # type: (object) -> bool
        raise NotImplementedError()


SlottedCollection = slotted.SlottedCollection  # trick static type checking.
if SlottedCollection is None:
    globals()["SlottedCollection"] = object
assert SlottedCollection is not None


# noinspection PyAbstractClass
class CollectionStructure(SizedStructure, IterableStructure[T_co], ContainerStructure[T_co], SlottedCollection):
    """Sized iterable container structure."""

    __slots__ = ()
