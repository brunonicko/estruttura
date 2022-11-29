"""Set structures."""

import six
import slotted
from basicco import custom_repr
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import AbstractSet, Any, Iterable, Type, TypeVar

from ._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseMutableCollectionStructure,
    BaseProxyCollectionStructure,
    BaseProxyImmutableCollectionStructure,
    BaseProxyMutableCollectionStructure,
    BaseProxyUserCollectionStructure,
    BaseProxyUserImmutableCollectionStructure,
    BaseProxyUserMutableCollectionStructure,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserMutableCollectionStructure,
)
from .exceptions import ProcessingError, SerializationError

T = TypeVar("T")


class SetStructure(BaseCollectionStructure[T], slotted.SlottedSet[T]):
    """Set structure."""

    __slots__ = ()

    def __init__(self, initial=()):  # noqa
        # type: (Iterable[T]) -> None
        """
        :param initial: Initial values.
        """
        initial_values = frozenset(initial)
        if self.relationship.will_process:
            try:
                initial_values = frozenset(self.relationship.process_value(v, v) for v in initial_values)
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        self._do_init(initial_values)

    @final
    def __le__(self, other):
        # type: (AbstractSet) -> bool
        """
        Less equal operator (self <= other).

        :param other: Another set or any object.
        :return: True if considered less equal.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__le__(other)

    @final
    def __lt__(self, other):
        # type: (AbstractSet) -> bool
        """
        Less than operator: `self < other`.

        :param other: Another set or any object.
        :return: True if considered less than.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__lt__(other)

    @final
    def __gt__(self, other):
        # type: (AbstractSet) -> bool
        """
        Greater than operator: `self > other`.

        :param other: Another set or any object.
        :return: True if considered greater than.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__gt__(other)

    @final
    def __ge__(self, other):
        # type: (AbstractSet) -> bool
        """
        Greater equal operator: `self >= other`.

        :param other: Another set or any object.
        :return: True if considered greater equal.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__ge__(other)

    @final
    def __and__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection: `self & other`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.intersection(other)

    @final
    def __rand__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection: `other & self`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        return self.__and__(other)

    @final
    def __sub__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get difference: `self - other`.

        :param other: Iterable or any other object.
        :return: Difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.difference(other)

    @final
    def __rsub__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get inverse difference: `other - self`.

        :param other: Iterable or any other object.
        :return: Inverse difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.inverse_difference(other)

    @final
    def __or__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get union: `self | other`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.union(other)

    @final
    def __ror__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get union: `other | self`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        return self.__or__(other)

    @final
    def __xor__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference: `self ^ other`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    @final
    def __rxor__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference: `other ^ self`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        return self.__xor__(other)

    def _repr(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.iterable_repr(
            self, prefix="{}({{".format(type(self).__qualname__), suffix="})", sort_key=lambda v: id(v), sorting=True
        )

    @abstract
    def _do_init(self, initial_values):
        # type: (frozenset[T]) -> None
        """
        Initialize values (internal).

        :param initial_values: New values.
        """
        raise NotImplementedError()

    @classmethod
    @abstract
    def _do_deserialize(cls, values):
        # type: (Type[SS], frozenset[T]) -> SS
        raise NotImplementedError()

    def serialize(self):
        # type: () -> list[Any]
        """
        Serialize.

        :return: Serialized list.
        :raises SerializationError: Error while serializing.
        """
        return [type(self).relationship.serialize_value(v) for v in self]

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[SS], Iterable[Any]) -> SS
        """
        Deserialize.

        :param serialized: Serialized iterable.
        :return: Structure.
        :raises SerializationError: Error while deserializing.
        """
        values = frozenset(cls.relationship.deserialize_value(s) for s in serialized)
        return cls._do_deserialize(values)

    @abstract
    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        raise NotImplementedError()

    @abstract
    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        raise NotImplementedError()

    @abstract
    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        raise NotImplementedError()

    @abstract
    def intersection(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        raise NotImplementedError()

    @abstract
    def symmetric_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        raise NotImplementedError()

    @abstract
    def union(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        raise NotImplementedError()

    @abstract
    def difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        raise NotImplementedError()

    @abstract
    def inverse_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        raise NotImplementedError()


SS = TypeVar("SS", bound=SetStructure)  # set structure self type


# noinspection PyAbstractClass
class UserSetStructure(SetStructure[T], BaseUserCollectionStructure[T]):
    """User set structure."""

    __slots__ = ()

    @final
    def _add(self, value):
        # type: (USS, T) -> USS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._update((value,))

    @abstract
    def _do_remove(self, old_values):
        # type: (USS, frozenset[T]) -> USS
        """
        Remove values (internal).

        :param old_values: Old values.
        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @final
    def _remove(self, *values):
        # type: (USS, T) -> USS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        old_values = frozenset(values)
        if not old_values:
            return self

        missing = old_values.difference(old_values.intersection(self))
        if len(missing) == 1:
            raise KeyError(next(iter(missing)))
        elif missing:
            raise KeyError(tuple(missing))

        return self._do_remove(old_values)

    @final
    def _discard(self, *values):
        # type: (USS, T) -> USS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        """
        if not values:
            return self

        old_values = frozenset(values).intersection(self)
        if not old_values:
            return self

        return self._do_remove(old_values)

    @abstract
    def _do_update(self, new_values):
        # type: (USS, frozenset[T]) -> USS
        """
        Add values (internal).

        :param new_values: New values.
        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @final
    def _update(self, iterable):
        # type: (USS, Iterable[T]) -> USS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        if self.relationship.will_process:
            try:
                new_values = frozenset(self.relationship.process_value(v, v) for v in iterable)
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        else:
            new_values = frozenset(iterable)

        new_values = frozenset(self.difference(new_values))
        if not new_values:
            return self

        return self._do_update(new_values)


USS = TypeVar("USS", bound=UserSetStructure)  # user set structure self type


class ProxySetStructure(BaseProxyCollectionStructure[SS, T], SetStructure[T]):
    """Proxy set structure."""

    __slots__ = ()

    def _do_init(self, initial_values):  # noqa
        """
        Initialize keys and values (internal).

        :param initial_values: Initial values.
        """
        error = "{!r} object already initialized".format(type(self).__name__)
        raise RuntimeError(error)

    @classmethod
    def _do_deserialize(cls, values):  # noqa
        """
        Deserialize (internal).

        :param values: Deserialized values.
        :return: Set structure.
        :raises SerializationError: Error while deserializing.
        """
        error = "can't deserialize proxy object {!r}".format(cls.__name__)
        raise SerializationError(error)

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._wrapped.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._wrapped.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._wrapped.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return self._wrapped.intersection(iterable)

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return self._wrapped.symmetric_difference(iterable)

    def union(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return self._wrapped.union(iterable)

    def difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return self._wrapped.difference(iterable)

    def inverse_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return self._wrapped.inverse_difference(iterable)


PSS = TypeVar("PSS", bound=ProxySetStructure)  # proxy set structure self type


# noinspection PyAbstractClass
class ProxyUserSetStructure(
    ProxySetStructure[USS, T],
    BaseProxyUserCollectionStructure[USS, T],
    UserSetStructure[T],
):
    """Proxy user set structure."""

    __slots__ = ()


PUSS = TypeVar("PUSS", bound=ProxyUserSetStructure)  # proxy user set structure self type


# noinspection PyAbstractClass
class ImmutableSetStructure(SetStructure[T], BaseImmutableCollectionStructure[T]):
    """Immutable set structure."""

    __slots__ = ()


ISS = TypeVar("ISS", bound=ImmutableSetStructure)  # immutable set structure self type


# noinspection PyAbstractClass
class UserImmutableSetStructure(
    ImmutableSetStructure[T],
    UserSetStructure[T],
    BaseUserImmutableCollectionStructure[T],
):
    """User immutable set structure."""

    __slots__ = ()

    @final
    def add(self, value):
        # type: (UISS, T) -> UISS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._add(value)

    @final
    def discard(self, *values):
        # type: (UISS, T) -> UISS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        """
        return self._discard(*values)

    @final
    def remove(self, *values):
        # type: (UISS, T) -> UISS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        return self._remove(*values)

    @final
    def update(self, iterable):
        # type: (UISS, Iterable[T]) -> UISS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._update(iterable)


UISS = TypeVar("UISS", bound=UserImmutableSetStructure)  # user immutable set structure self type


# noinspection PyAbstractClass
class ProxyImmutableSetStructure(
    ProxySetStructure[ISS, T],
    BaseProxyImmutableCollectionStructure[ISS, T],
    ImmutableSetStructure[T],
):
    """Proxy immutable set structure."""

    __slots__ = ()


PISS = TypeVar("PISS", bound=ProxyImmutableSetStructure)  # proxy immutable set structure self type


class ProxyUserImmutableSetStructure(
    ProxyImmutableSetStructure[UISS, T],
    BaseProxyUserImmutableCollectionStructure[UISS, T],
    UserImmutableSetStructure[T],
):
    """Proxy user immutable set structure."""

    __slots__ = ()

    def _do_remove(self, old_values):
        # type: (PUISS, frozenset[T]) -> PUISS
        """
        Remove values (internal).

        :param old_values: Old values.
        :return: Transformed.
        """
        return self._wrapped.remove(old_values)

    def _do_update(self, new_values):
        # type: (PUISS, frozenset[T]) -> PUISS
        """
        Add values (internal).

        :param new_values: New values.
        :return: Transformed.
        """
        return self._wrapped.update(new_values)


PUISS = TypeVar("PUISS", bound=ProxyUserImmutableSetStructure)  # proxy user immutable set structure self type


# noinspection PyAbstractClass
class MutableSetStructure(SetStructure[T], BaseMutableCollectionStructure[T]):
    """Mutable set structure."""

    __slots__ = ()


MSS = TypeVar("MSS", bound=MutableSetStructure)  # mutable set structure self type


# noinspection PyAbstractClass
class UserMutableSetStructure(
    MutableSetStructure[T],
    UserSetStructure[T],
    BaseUserMutableCollectionStructure[T],
    slotted.SlottedMutableSet[T],
):
    """User mutable set structure."""

    __slots__ = ()

    @final
    def __iand__(self, iterable):
        """
        Intersect in place: `self &= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.intersection_update(iterable)
        return self

    @final
    def __isub__(self, iterable):
        """
        Difference in place: `self -= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.difference(iterable)
        return self

    @final
    def __ior__(self, iterable):
        """
        Update in place: `self |= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.update(iterable)
        return self

    @final
    def __ixor__(self, iterable):
        """
        Symmetric difference in place: `self ^= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        if iterable is self:
            self.clear()
        else:
            self.symmetric_difference_update(iterable)
        return self

    @final
    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.
        :raises KeyError: Empty set.
        """
        value = next(iter(self))
        self.remove(value)
        return value

    @final
    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        """
        difference = self.difference(iterable)
        if difference:
            self.remove(*difference)

    @final
    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        """
        inverse_difference = self.inverse_difference(iterable)
        intersection = self.intersection(iterable)
        if inverse_difference:
            self.update(inverse_difference)
        if intersection:
            self.remove(*intersection)

    @final
    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        """
        intersection = self.intersection(iterable)
        if intersection:
            self.remove(*intersection)

    @final
    def add(self, value):
        # type: (T) -> None
        """
        Add value.

        :param value: Value.
        """
        self._add(value)

    @final
    def discard(self, *values):
        # type: (T) -> None
        """
        Discard value(s).

        :param values: Value(s).
        """
        self._discard(*values)

    @final
    def remove(self, *values):
        # type: (T) -> None
        """
        Remove existing value(s).

        :param values: Value(s).
        :raises KeyError: Value is not present.
        """
        self._remove(*values)

    @final
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        self._update(iterable)


UMSS = TypeVar("UMSS", bound=UserMutableSetStructure)  # user mutable set structure self type


# noinspection PyAbstractClass
class ProxyMutableSetStructure(
    ProxySetStructure[MSS, T],
    BaseProxyMutableCollectionStructure[MSS, T],
    MutableSetStructure[T],
):
    """Proxy mutable set structure."""

    __slots__ = ()


PMSS = TypeVar("PMSS", bound=ProxyMutableSetStructure)  # proxy mutable set structure self type


class ProxyUserMutableSetStructure(
    ProxyMutableSetStructure[UMSS, T],
    BaseProxyUserMutableCollectionStructure[UMSS, T],
    UserMutableSetStructure[T],
):
    """Proxy user mutable set structure."""

    __slots__ = ()

    def _do_remove(self, old_values):
        # type: (PUMSS, frozenset[T]) -> PUMSS
        """
        Remove values (internal).

        :param old_values: Old values.
        :return: Self.
        """
        self._wrapped.remove(old_values)
        return self

    def _do_update(self, new_values):
        # type: (PUMSS, frozenset[T]) -> PUMSS
        """
        Add values (internal).

        :param new_values: New values.
        :return: Self.
        """
        self._wrapped.update(new_values)
        return self


PUMSS = TypeVar("PUMSS", bound=ProxyUserMutableSetStructure)  # proxy user mutable set structure self type
