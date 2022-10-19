import slotted
from tippo import AbstractSet, Iterable, TypeVar
from basicco.runtime_final import final
from basicco.abstract_class import abstract

from ._base import BaseUniformCollection, BaseImmutableUniformCollection, BaseMutableUniformCollection


T = TypeVar("T")


class BaseSet(BaseUniformCollection[T], slotted.SlottedSet[T]):
    __slots__ = ()

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

    @final
    def _add(self, value):
        # type: (BS, T) -> BS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._update((value,))

    @final
    def _remove(self, *values):
        # type: (BS, T) -> BS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)

        missing = set(values).difference(self.intersection(values))
        if len(missing) == 1:
            error = "value {!r} is not in the set".format(next(iter(missing)))
            raise KeyError(error)
        elif missing:
            error = "values {} are not in the set".format(", ".join(repr(v) for v in missing))
            raise KeyError(error)

        return self._discard(*values)

    @abstract
    def _discard(self, *values):
        # type: (BS, T) -> BS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abstract
    def _update(self, iterable):
        # type: (BS, Iterable[T]) -> BS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        raise NotImplementedError()

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


BS = TypeVar("BS", bound=BaseSet)


# noinspection PyAbstractClass
class BaseImmutableSet(BaseSet[T], BaseImmutableUniformCollection[T]):
    __slots__ = ()

    @final
    def add(self, value):
        # type: (BIS, T) -> BIS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._add(value)

    @final
    def discard(self, *values):
        # type: (BIS, T) -> BIS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._discard(*values)

    @final
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

    @final
    def update(self, iterable):
        # type: (BIS, Iterable[T]) -> BIS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._update(iterable)


BIS = TypeVar("BIS", bound=BaseImmutableSet)


# noinspection PyAbstractClass
class BaseMutableSet(BaseSet[T], BaseMutableUniformCollection[T], slotted.SlottedMutableSet[T]):
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
            self._update(inverse_difference)
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
        self.add(value)

    @final
    def discard(self, *values):
        # type: (T) -> None
        """
        Discard value(s).

        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self.discard(*values)

    @final
    def remove(self, *values):
        # type: (T) -> None
        """
        Remove existing value(s).

        :param values: Value(s).
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        self.remove(*values)

    @final
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        self.update(iterable)
