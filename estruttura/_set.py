import abc

import slotted
from basicco import runtime_final
from tippo import TypeVar, AbstractSet, Iterable

from ._bases import BaseCollection, BaseInteractiveCollection, BaseMutableCollection, BasePrivateCollection


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class BaseSet(BaseCollection[T_co], slotted.SlottedSet[T_co]):
    """Base set collection."""

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: {!r}".format(type(self).__name__)
        raise TypeError(error)

    @runtime_final.final
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

    @runtime_final.final
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

    @runtime_final.final
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

    @runtime_final.final
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

    @runtime_final.final
    def __and__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get intersection: `self & other`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.intersection(other)

    @runtime_final.final
    def __rand__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get intersection: `other & self`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        return self.__and__(other)

    @runtime_final.final
    def __sub__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get difference: `self - other`.

        :param other: Iterable or any other object.
        :return: Difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.difference(other)

    @runtime_final.final
    def __rsub__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get inverse difference: `other - self`.

        :param other: Iterable or any other object.
        :return: Inverse difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.inverse_difference(other)

    @runtime_final.final
    def __or__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get union: `self | other`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.union(other)

    @runtime_final.final
    def __ror__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get union: `other | self`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        return self.__or__(other)

    @runtime_final.final
    def __xor__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference: `self ^ other`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    @runtime_final.final
    def __rxor__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference: `other ^ self`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        return self.__xor__(other)

    @abc.abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def intersection(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def symmetric_difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def union(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def inverse_difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        raise NotImplementedError()


# noinspection PyCallByClass
type.__setattr__(BaseSet, "__hash__", None)  # force non-hashable


class BasePrivateSet(BaseSet[T], BasePrivateCollection[T]):
    """Base private set collection."""

    __slots__ = ()

    @abc.abstractmethod
    def _add(self, value):
        # type: (BPS, T) -> BPS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _discard(self, *values):
        # type: (BPS, T) -> BPS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _remove(self, *values):
        # type: (BPS, T) -> BPS
        """
        Remove existing value(s).

        :param values: Value(s).

        :return: Transformed.

        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _replace(self, old_value, new_value):
        # type: (BPS, T, T) -> BPS
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _update(self, iterable):
        # type: (BPS, Iterable[T]) -> BPS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        raise NotImplementedError()


BPS = TypeVar("BPS", bound=BasePrivateSet)  # base private set type


# noinspection PyAbstractClass
class BaseInteractiveSet(BasePrivateSet[T], BaseInteractiveCollection[T]):
    """Base interactive set collection."""

    __slots__ = ()

    @runtime_final.final
    def add(self, value):
        # type: (BIS, T) -> BIS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._add(value)

    @runtime_final.final
    def discard(self, *values):
        # type: (BIS, T) -> BIS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._discard(*values)

    @runtime_final.final
    def remove(self, *values):
        # type: (BIS, T) -> BIS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        return self._remove(*values)

    @runtime_final.final
    def replace(self, old_value, new_value):
        # type: (BIS, T, T) -> BIS
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Old value is not present.
        """
        return self._replace(old_value, new_value)

    @runtime_final.final
    def update(self, iterable):
        # type: (BIS, Iterable[T]) -> BIS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._update(iterable)


BIS = TypeVar("BIS", bound=BaseInteractiveSet)  # base interactive set type


class BaseMutableSet(BasePrivateSet[T], BaseMutableCollection[T], slotted.SlottedMutableSet[T]):
    """Base mutable set collection."""

    __slots__ = ()

    @runtime_final.final
    def __iand__(self, iterable):
        """
        Intersect in place: `self &= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.intersection_update(iterable)
        return self

    @runtime_final.final
    def __isub__(self, iterable):
        """
        Difference in place: `self -= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.difference(iterable)
        return self

    @runtime_final.final
    def __ior__(self, iterable):
        """
        Update in place: `self |= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.update(iterable)
        return self

    @runtime_final.final
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

    @abc.abstractmethod
    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.
        :raises KeyError: Empty set.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @runtime_final.final
    def add(self, value):
        # type: (T) -> None
        """
        Add value.

        :param value: Value.
        """
        self._add(value)

    @runtime_final.final
    def discard(self, *values):
        # type: (T) -> None
        """
        Discard value(s).

        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._discard(*values)

    @runtime_final.final
    def remove(self, *values):
        # type: (T) -> None
        """
        Remove existing value(s).

        :param values: Value(s).
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        self._remove(*values)

    @runtime_final.final
    def replace(self, old_value, new_value):
        # type: (T, T) -> None
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        """
        self._replace(old_value, new_value)

    @runtime_final.final
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        self._update(iterable)
